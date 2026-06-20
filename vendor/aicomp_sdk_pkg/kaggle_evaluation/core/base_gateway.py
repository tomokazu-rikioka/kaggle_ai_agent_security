"""Lower level implementation details of the gateway.
Hosts should not need to review this file before writing their competition specific gateway.
"""

import enum
import json
import os
import pathlib
import re
import subprocess
import sys
import traceback
from socket import gaierror
from typing import Any, cast, final

import grpc
import numpy as np
import pandas as pd
import polars as pl

import kaggle_evaluation.core.relay

_DATAFRAME_LIKE_TYPES = (pl.DataFrame, pl.Series, pd.DataFrame, pd.Series)
_VALID_ROW_ID_SCALAR_TYPES = (str, int)
_VALID_ROW_ID_TYPES = _VALID_ROW_ID_SCALAR_TYPES + _DATAFRAME_LIKE_TYPES
# Files in this directory are visible to the competitor container.
_FILE_SHARE_DIR = '/kaggle/shared/'
IS_RERUN = os.getenv('KAGGLE_IS_COMPETITION_RERUN') is not None
RERUN_CHANNEL_ADDRESS = 'inference_server'
DEFAULT_SERVER_NAME = 'default'


class GatewayRuntimeErrorType(enum.Enum):
    """Allow-listed error types that Gateways can raise, which map to canned error messages to show users.
    Please try capture all errors with one of these types.
    Unhandled errors are treated as caused by Kaggle and do not count towards daily submission limits.
    """

    UNSPECIFIED = 0
    SERVER_NEVER_STARTED = 1
    SERVER_CONNECTION_FAILED = 2
    SERVER_RAISED_EXCEPTION = 3
    SERVER_MISSING_ENDPOINT = 4
    # Default error type if an exception was raised that was not explicitly handled by the Gateway
    GATEWAY_RAISED_EXCEPTION = 5
    INVALID_SUBMISSION = 6
    GRPC_DEADLINE_EXCEEDED = 7


class GatewayRuntimeError(Exception):
    """Gateways can raise this error to capture a user-visible error enum from above and host-visible error details."""

    def __init__(self, error_type: GatewayRuntimeErrorType, error_details: str | None = None):
        self.error_type = error_type
        self.error_details = error_details


class BaseGateway:
    """Base class for Hearth gateways. Supports one or more inference servers."""

    def __init__(
        self,
        data_paths: tuple[str, ...] | None = None,
        file_share_dir: str | None = _FILE_SHARE_DIR,
        target_column_name: str | None = None,
        row_id_column_name: str | None = None,
        server_names: list[str] | None = None,
        server_ports: dict[str, int] | None = None,
        allowed_modules: list[str] | None = None,
    ):
        """
        Args:
            data_paths: The input file paths. We accept user inputs here when running offline tests.
            file_share_dir: If the share_files feature will be used, we accept a user input for where to share the data when running offline tests.
            target_column_name: Sets the submission file target column name if predict() does not return a named DataFrame or Series.
            row_id_column_name: Sets the submission file row ID column name if generate_data_batches() does not return row IDs as a named DataFrame or Series.
            server_names: List of inference server names. If None, uses a single default server.
            server_ports: Optional dict mapping server names to specific ports. Used for local multi-server testing.
            allowed_modules: Optional list of module names allowed for Pydantic/dataclass/enum deserialization.
                           If provided, these modules will be allowed before creating relay clients.
        """
        # Setting allowed modules must happen before creating clients.
        kaggle_evaluation.core.relay.set_allowed_modules(allowed_modules)

        if server_ports and server_names:
            try:
                assert len(server_ports) == len(server_names)
                assert set(server_ports.keys()) == set(server_names)
            except AssertionError:
                msg = f'`server_ports` and `server_names` must have matching keys and lengths. Got server_names {server_names} and server_ports {server_ports}'
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, msg)

        self.server_ports = server_ports or dict()
        self.server_names = server_names or list(self.server_ports.keys()) or [DEFAULT_SERVER_NAME]
        self.clients: dict[str, kaggle_evaluation.core.relay.Client] = dict()

        # If running multiple servers on the same host, we need to ensure they don't try to bind to the same ports.
        default_ports_map: dict[str, int] = {}
        # Spacing needs to cover the port itself + NUM_FALLBACK_PORTS fallbacks.
        # Add a little buffer for safety.
        spacing = kaggle_evaluation.core.relay.PORT_SPACING
        start_port = kaggle_evaluation.core.relay.GRPC_PORTS[0]
        for i, name in enumerate(self.server_names):
            # Ensure we don't pick a port that collides with the next server's fallbacks
            default_ports_map[name] = start_port + (i * spacing)

        sorted_ports = sorted(self.server_ports.values()) if self.server_ports else []
        for i in range(len(sorted_ports) - 1):
            if sorted_ports[i + 1] - sorted_ports[i] < kaggle_evaluation.core.relay.PORT_SPACING:
                msg = (
                    f'Warning: Input ports {sorted_ports[i]} and {sorted_ports[i + 1]} are too closely spaced. '
                    f'This may cause collisions if fallbacks are needed. '
                    f'Recommended spacing is {kaggle_evaluation.core.relay.PORT_SPACING}.'
                )
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, msg)

        for name in self.server_names:
            channel_address = self._get_channel_address(name)
            port = self.server_ports.get(name)
            if port is None:
                port = default_ports_map.get(name)
            self.clients[name] = kaggle_evaluation.core.relay.Client(channel_address, port=port)
        self.server = None

        # Off Kaggle, we can accept a user input file_share_dir. On Kaggle, we need to use the special directory
        # that is visible to the user.
        if file_share_dir or not os.path.exists('/kaggle'):
            self.file_share_dir = file_share_dir
        else:
            self.file_share_dir = _FILE_SHARE_DIR

        self.data_batch_counter = None
        self.auto_unmount_shared_files = True  # If True, unmount the previous batch of mounted files before mounting any new files
        self._shared_a_file = False
        self._to_unmount = []
        self._last_batch_unmounted = None
        self._mount_errs_logged_count = 0
        self._max_total_mounts = None
        # The mount cap isn't relevant unless running on Kaggle/Linux, but users may run this code on Windows.
        if os.path.exists('/proc/sys/fs/mount-max'):
            with open('/proc/sys/fs/mount-max') as f_open:
                # Allow a tiny bit of buffer to allow raising an error before hitting the actual max.
                self._max_total_mounts = int(int(f_open.read()) * 0.999)

        self.data_paths = data_paths
        self.target_column_name = target_column_name
        self.row_id_column_name = row_id_column_name

    def _get_channel_address(self, server_name: str) -> str:
        if IS_RERUN:
            if server_name == DEFAULT_SERVER_NAME:
                return RERUN_CHANNEL_ADDRESS
            return f'{RERUN_CHANNEL_ADDRESS}_{server_name}'
        return 'localhost'

    def get_client(self, server_name: str | None = None) -> kaggle_evaluation.core.relay.Client:
        if server_name is None:
            if len(self.clients) == 1:
                server_name = list(self.clients.keys())[0]
            else:
                raise ValueError(f'Unknown server: {server_name}. Available: {list(self.clients.keys())}')

        if server_name not in self.clients:
            raise ValueError(f'Unknown server: {server_name}. Available: {list(self.clients.keys())}')
        return self.clients[server_name]

    @property
    def client(self) -> kaggle_evaluation.core.relay.Client:
        # Provided for convience in the single-server case.
        return self.get_client()

    def set_response_timeout_seconds(self, timeout_seconds: int, server_name: str | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        if server_name:
            self.get_client(server_name).endpoint_deadline_seconds = timeout_seconds
        else:
            for client in self.clients.values():
                client.endpoint_deadline_seconds = timeout_seconds

    def unpack_data_paths(self) -> None:
        raise NotImplementedError

    def generate_data_batches(self) -> Any:
        raise NotImplementedError

    def competition_specific_validation(
        self, prediction_batch: Any, row_ids: pl.DataFrame | pl.Series | pd.DataFrame | pd.Series, data_batch: Any
    ) -> None:
        raise NotImplementedError

    def get_all_predictions(self) -> tuple[list[Any], list[Any]]:
        all_predictions = []
        all_row_ids = []
        self.data_batch_counter = 0
        for data_batch, row_ids in self.generate_data_batches():
            predictions = self.predict(*data_batch)
            self.competition_agnostic_validation(predictions, row_ids)
            self.competition_specific_validation(predictions, row_ids, data_batch)
            all_predictions.append(predictions)
            all_row_ids.append(row_ids)
            self.data_batch_counter += 1
        return all_predictions, all_row_ids

    def predict(self, *args, server_name: str | None = None, **kwargs) -> Any:
        """Send data to the user container and get a `predict` response.

        Args:
            *args: Data to send.
            server_name: Target server. Uses default if None.
            **kwargs: Additional data to send.

        Returns:
            Any: The prediction from the user container.
        """
        client = self.get_client(server_name)
        try:
            return client.send('predict', *args, **kwargs)
        except Exception as e:
            self.handle_server_error(e, 'predict')

    def send_to_server(self, server_name: str, endpoint: str, *args, **kwargs) -> Any:
        """Send data to a specific server and endpoint."""
        client = self.get_client(server_name)
        try:
            return client.send(endpoint, *args, **kwargs)
        except Exception as e:
            self.handle_server_error(e, endpoint)

    def run(self) -> None:
        error = None
        try:
            self.unpack_data_paths()
            predictions, row_ids = self.get_all_predictions()
            self.write_submission(predictions, row_ids)
        except GatewayRuntimeError as gre:
            error = gre
        except Exception:
            # Get the full stack trace
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            error = GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, error_str)

        for client in self.clients.values():
            client.close()
        if self.server:
            self.server.stop(0)

        if IS_RERUN:
            self.write_result(error)
        elif error:
            # For local testing
            raise error

    @final
    def competition_agnostic_validation(
        self, prediction_batch: Any, row_ids: str | int | pl.DataFrame | pl.Series | pd.DataFrame | pd.Series
    ) -> None:
        """Prevent a potential abuse vector that exists if users can submit unaligned predictions and row IDs.
        This check should run for every competition and should not be customized. All competition specific prediction validation
        belongs in `self.competition_specific_validation` (implemented in templates.py).

        If competitors can submit fewer rows than expected they can save all predictions for the last batch and
        bypass the benefits of the Kaggle evaluation service. This attack was seen in a real competition with the older time series API:
        https://www.kaggle.com/competitions/riiid-test-answer-prediction/discussion/196066
        It's critically important that this check be run every time predict() is called.

        If your predictions may take a variable number of rows and you need to write a custom version of this check,
        you still must specify a minimum row count greater than zero per prediction batch.
        """
        if prediction_batch is None:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.INVALID_SUBMISSION, 'No prediction received')
        num_received_rows = None
        # Special handling for numpy ints only as numpy floats are python floats, but numpy ints aren't python ints
        for primitive_type in [int, float, str, bool, np.int_]:
            if isinstance(prediction_batch, primitive_type):
                # Types that only support one predictions per batch don't need to be validated.
                # Basic types are valid for prediction, but either don't have a length (int) or the length isn't relevant for
                # purposes of this check (str).
                num_received_rows = 1

        if num_received_rows is None:
            if not isinstance(prediction_batch, _DATAFRAME_LIKE_TYPES):
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.INVALID_SUBMISSION, f'Invalid prediction data type, received: {type(prediction_batch)}'
                )
            num_received_rows = len(prediction_batch)

        if not isinstance(row_ids, _VALID_ROW_ID_TYPES):
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Invalid row ID type {type(row_ids)}; expected a string, int, DataFrame, or Series'
            )
        if isinstance(row_ids, _VALID_ROW_ID_SCALAR_TYPES):
            num_expected_rows = 1
        else:
            num_expected_rows = len(row_ids)

        if num_expected_rows == 0:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, 'Missing row IDs for batch')
        if num_received_rows != num_expected_rows:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.INVALID_SUBMISSION, f'Invalid predictions: expected {num_expected_rows} rows but received {num_received_rows}'
            )

    def _standardize_and_validate_paths(self, input_paths: list[str | pathlib.Path]) -> tuple[list[str], list[str]]:
        # Accept a list of str or pathlib.Path, but standardize on list of str
        if input_paths and not self.file_share_dir or not isinstance(self.file_share_dir, (str, os.PathLike)):
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Invalid `file_share_dir`: {self.file_share_dir}')

        for path in input_paths:
            if os.path.basename(path).startswith('.'):
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Cannot share hidden files: {path}')
            if os.pardir in str(path):
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Send files path contains {os.pardir}: {path}')
            if str(path) != str(os.path.normpath(path)):
                # Raise an error rather than sending users unexpectedly altered paths
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Send files path {path} must be normalized. See `os.path.normpath`'
                )
            if not isinstance(path, (str, os.PathLike)):
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, 'All paths must be of type str or os.PathLike')
            if not os.path.exists(path):
                raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Input path {path} does not exist')

        absolute_input_paths: list[str] = [os.path.abspath(path) for path in input_paths]
        if len(set(absolute_input_paths)) != len(input_paths):
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, 'Duplicate input paths found')

        output_dir = str(self.file_share_dir)
        if not output_dir.endswith(os.path.sep):
            # Ensure output dir is valid for later use
            output_dir += os.path.sep

        # Can't use os.path.join for output_dir + path: os.path.join won't prepend to an abspath
        # normpath manages // in particular.
        output_paths = [os.path.normpath(output_dir + path) for path in absolute_input_paths]
        return absolute_input_paths, output_paths

    def share_files(
        self,
        input_paths: list[str | pathlib.Path],
    ) -> list[str]:
        """Makes files and/or directories available to the user's inference_server. They will be mirrored under the
        self.file_share_dir directory, using the full absolute path. An input like:
            /kaggle/input/mycomp/test.csv
        Would be written to:
            /kaggle/shared/kaggle/input/mycomp/test.csv

        Args:
            input_paths: List of paths to files and/or directories that should be shared.

        Returns:
            The output paths that were shared.

        Raises:
            GatewayRuntimeError if any invalid paths are passed.
        """
        if self.file_share_dir and not self._shared_a_file and os.path.exists(self.file_share_dir):
            if not os.path.isdir(self.file_share_dir):
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'`file_share_dir` {self.file_share_dir} must be a directory.'
                )
            if len(os.listdir(self.file_share_dir)) > 0:
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                    f'`file_share_dir` must be an empty directory, instead found {os.listdir(self.file_share_dir)[:5]}',
                )

        if self.file_share_dir is None:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, 'file_share_dir must be set')

        os.makedirs(self.file_share_dir, exist_ok=True)
        self._shared_a_file = True

        if not input_paths:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, 'share_files requires at least one input path')

        # Problems arise if too many files get mounted at once. The Linux default cap is 100,000 files.
        # Avoid this by defaulting to unmounting once per data batch.
        if self.auto_unmount_shared_files and self._to_unmount and (self._last_batch_unmounted != self.data_batch_counter):
            subprocess.run(['umount', '-l'] + self._to_unmount, check=False)

            self._to_unmount = []
            # N.B. This logic will fail if we ever make multiple generate_data_batches() calls in parallel.
            self._last_batch_unmounted = self.data_batch_counter

        absolute_input_paths, output_paths = self._standardize_and_validate_paths(input_paths)
        if self._max_total_mounts:
            # `num_existing_mounts` is probably an underestimate - the gateway may not have access to mounts in the user space.
            # Run with args as a string and shell=True to support pipes aka |
            num_existing_mounts = subprocess.run('mount | wc -l', shell=True, check=True, capture_output=True)
            num_existing_mounts: int = int(num_existing_mounts.stdout.decode())
            if num_existing_mounts + len(input_paths) > self._max_total_mounts:
                # We could technically run past this error and fall back to cp as usual, but the intent is to
                # make the problem visible to the competition's creator during pre-launch testing.
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f'Attempted to mount more than {self._max_total_mounts} files at once.'
                )

        for in_path, out_path in zip(absolute_input_paths, output_paths):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            # This makes the files available to the InferenceServer as read-only. Only the Gateway can mount files.
            # mount will only work in live kaggle evaluation rerun sessions. Otherwise use a symlink.
            if IS_RERUN:
                results = None

                # Create the correct type of placeholder if the destination doesn't exist.
                if not os.path.exists(out_path):
                    if os.path.isdir(in_path):
                        # If the source is a directory, create an empty directory as the mount point.
                        os.makedirs(out_path, exist_ok=True)
                    else:
                        # If the source is a file, create an empty file as the mount point.
                        pathlib.Path(out_path).touch()

                try:
                    mount_cmd = ['mount', '--bind', in_path, out_path]
                    results = subprocess.run(mount_cmd, check=True, capture_output=True)
                    self._to_unmount.append(in_path)
                except Exception:
                    # Log a limited number of errors from mount calls. There can be millions of them so don't bother with all.
                    # The full logs are available elsewhere in the system if really necessary.
                    if hasattr(results, 'stdout') and hasattr(results, 'stderr') and self._mount_errs_logged_count < 100:
                        print(
                            f'The command\n{mount_cmd} failed with stdout\n {results.stdout.decode()}, \nstderr\n {results.stderr.decode()}',
                            flush=True,
                        )
                        self._mount_errs_logged_count += 1

                    # `mount` is expected to be faster but less reliable in our context.
                    # Fall back to cp if possible.
                    if self.file_share_dir != _FILE_SHARE_DIR:
                        raise GatewayRuntimeError(
                            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                            f'share_files fallback failure: can only use cp if file_share_dir is {_FILE_SHARE_DIR}. Got {self.file_share_dir}',
                        )
                    # cp will fail if the output directory doesn't already exist
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    subprocess.run(['cp', '-r', in_path, out_path], check=True)
            else:
                subprocess.run(['ln', '-s', in_path, out_path], check=True)

        return output_paths

    def _convert_to_df(
        self, data_batches: list | pl.Series | pl.DataFrame | pd.Series | pd.DataFrame, series_name: str | None = None
    ) -> pl.DataFrame | pd.DataFrame:
        """Progressively migrate towards a dataframe as needed: List -> Series -> DataFrame."""
        if not data_batches:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.INVALID_SUBMISSION, f'Invalid submission data_batches: {data_batches}')
        if isinstance(data_batches, list):
            if isinstance(data_batches[0], (pd.DataFrame, pd.Series)):
                data_batches = pd.concat(cast(list[pd.DataFrame | pd.Series], data_batches), ignore_index=True)
            elif isinstance(data_batches[0], (pl.DataFrame, pl.Series)):
                try:
                    data_batches = pl.concat(data_batches, how='vertical_relaxed')
                except pl.exceptions.SchemaError:
                    raise GatewayRuntimeError(GatewayRuntimeErrorType.INVALID_SUBMISSION, 'Inconsistent prediction types')
                except pl.exceptions.ComputeError:
                    raise GatewayRuntimeError(GatewayRuntimeErrorType.INVALID_SUBMISSION, 'Inconsistent prediction column counts')
            else:
                data_batches = pl.Series(data_batches)

        if isinstance(data_batches, (pl.Series, pd.Series)) and not data_batches.name:
            if series_name:
                data_batches = data_batches.rename(series_name)
            elif not series_name:
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                    'The gateway fields self.target_column_name and/or self.row_id_column_name must be set in order to use scalar data_batches or unnamed Pandas/Polars series',
                )

        if isinstance(data_batches, pl.Series):
            data_batches = pl.DataFrame(data_batches)
        elif isinstance(data_batches, pd.Series):
            data_batches = pd.DataFrame(data_batches)

        if isinstance(data_batches, pl.DataFrame):
            return data_batches
        elif isinstance(data_batches, pd.DataFrame):
            return pd.DataFrame(data_batches)
        else:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.INVALID_SUBMISSION,
                f'Invalid data_batches type passed to `_create_submission_dataframe`. Got {type(data_batches)}; expected a list, DataFrame, or Series',
            )

    def write_submission(
        self,
        predictions: list | pl.Series | pl.DataFrame | pd.Series | pd.DataFrame,
        row_ids: list | pl.Series | pl.DataFrame | pd.Series | pd.DataFrame,
    ) -> None:
        """Export the predictions to a submission.parquet."""
        submission = self._convert_to_df(predictions, self.target_column_name)
        row_ids = self._convert_to_df(row_ids, self.row_id_column_name)

        # Final validation to ensure predictions and row_ids match.
        # This is redundant for data science competitions (which validate per-batch in get_all_predictions),
        # but ensures games that call write_submission directly still get validated.
        self.competition_agnostic_validation(submission, row_ids)

        # The row ID columns are expected to be the first columns for a variety of purposes downstream.
        desired_column_order = row_ids.columns + [col for col in submission.columns if col not in row_ids.columns]

        # Ensure the row IDs are added to the submission file.
        # Existing row ID columns may be overwritten, but that's fine.
        if isinstance(submission, pd.DataFrame):
            submission.loc[:, row_ids.columns] = row_ids
            submission[desired_column_order].to_parquet('submission.parquet', index=False)
        elif isinstance(submission, pl.DataFrame):
            submission = submission.with_columns(row_ids)
            submission.select(desired_column_order).write_parquet('submission.parquet')
        else:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION, f"Unsupported predictions type {type(submission)}; can't write submission file"
            )

    def write_result(self, error: GatewayRuntimeError | None = None) -> None:
        """Export a result.json containing error details if applicable."""
        result = {'Succeeded': error is None}

        if error is not None:
            result['ErrorType'] = error.error_type.value
            result['ErrorName'] = error.error_type.name
            # Max error detail length is 8000
            result['ErrorDetails'] = str(error.error_details[:8000]) if error.error_details else None

        with open('result.json', 'w') as f_open:
            json.dump(result, f_open)

    def handle_server_error(self, exception: Exception, endpoint: str) -> None:
        """Determine how to handle an exception raised when calling the inference server. Typically just format the
        error into a GatewayRuntimeError and raise.
        """
        exception_str = str(exception)
        if isinstance(exception, (gaierror, RuntimeError)) and 'Failed to connect to server after waiting' in exception_str:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.SERVER_NEVER_STARTED) from None
        if f'No listener for {endpoint} was registered' in exception_str:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.SERVER_MISSING_ENDPOINT, f'Server did not register a listener for {endpoint}') from None
        if 'Exception calling application' in exception_str:
            # Extract just the exception message raised by the inference server
            message_match = re.search('"Exception calling application: (.*)"', exception_str, re.IGNORECASE)
            message = message_match.group(1) if message_match else exception_str
            raise GatewayRuntimeError(GatewayRuntimeErrorType.SERVER_RAISED_EXCEPTION, message) from None
        if isinstance(exception, (grpc._channel._InactiveRpcError, kaggle_evaluation.core.relay.ServerDiedError)):  # ty: ignore
            raise GatewayRuntimeError(GatewayRuntimeErrorType.SERVER_CONNECTION_FAILED, exception_str) from None
        if isinstance(exception, kaggle_evaluation.core.relay.GRPCDeadlineError):
            raise GatewayRuntimeError(GatewayRuntimeErrorType.GRPC_DEADLINE_EXCEEDED, exception_str) from None
        raise exception
