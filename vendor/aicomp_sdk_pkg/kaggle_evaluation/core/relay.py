"""
Core implementation of the client module, implementing generic communication
patterns with Python in / Python out supporting many (nested) primitives +
special data science types like DataFrames or np.ndarrays, with gRPC + protobuf
as a backing implementation.
"""

import dataclasses
import enum
import importlib
import inspect
import io
import json
import socket
import time
from concurrent import futures
from types import FunctionType, MethodType
from typing import Any, Optional, Tuple, get_args, get_origin

import grpc
import numpy as np
import pandas as pd
import polars as pl
import pyarrow
import pydantic

import kaggle_evaluation.core.generated.kaggle_evaluation_pb2 as kaggle_evaluation_proto
import kaggle_evaluation.core.generated.kaggle_evaluation_pb2_grpc as kaggle_evaluation_grpc


class GRPCDeadlineError(Exception):
    pass


class ServerDiedError(Exception):
    pass


# Allowlist of modules that can be imported during data model deserialization.
# If None, no data model deserialization is allowed. Set to '*' to enable all data models.
_ALLOWED_MODULES = None

_SERVICE_CONFIG = {
    # Service config proto: https://github.com/grpc/grpc-proto/blob/ec886024c2f7b7f597ba89d5b7d60c3f94627b17/grpc/service_config/service_config.proto#L377
    'methodConfig': [
        {
            'name': [{}],  # Applies to all methods
            # See retry policy docs: https://grpc.io/docs/guides/retry/
            'retryPolicy': {
                'maxAttempts': 5,
                'initialBackoff': '0.1s',
                'maxBackoff': '1s',
                'backoffMultiplier': 1,  # Ensure relatively rapid feedback in the event of a crash
                'retryableStatusCodes': ['UNAVAILABLE'],
            },
        }
    ]
}

NUM_FALLBACK_PORTS = 5
MAX_NUM_SERVERS = 10
PORT_SPACING = NUM_FALLBACK_PORTS + 5

# Include potential fallback ports
GRPC_PORTS = [50051] + [60053 + i * PORT_SPACING for i in range(MAX_NUM_SERVERS)]

_GRPC_CHANNEL_OPTIONS = [
    # -1 for unlimited message send/receive size
    # https://github.com/grpc/grpc/blob/v1.64.x/include/grpc/impl/channel_arg_names.h#L39
    ('grpc.max_send_message_length', -1),
    ('grpc.max_receive_message_length', -1),
    # https://github.com/grpc/grpc/blob/master/doc/keepalive.md
    ('grpc.keepalive_time_ms', 60_000),  # Time between heartbeat pings
    ('grpc.keepalive_timeout_ms', 5_000),  # Time allowed to respond to pings
    ('grpc.http2.max_pings_without_data', 0),  # Remove another cap on pings
    ('grpc.keepalive_permit_without_calls', 1),  # Allow heartbeat pings at any time
    ('grpc.http2.min_ping_interval_without_data_ms', 1_000),
    ('grpc.service_config', json.dumps(_SERVICE_CONFIG)),
]


DEFAULT_DEADLINE_SECONDS = 60 * 60
_RETRY_SLEEP_SECONDS = 1 / len(GRPC_PORTS)
# Enforce a relatively strict server startup time so users can get feedback quickly if they're not
# configuring KaggleEvaluation correctly. We really don't want notebooks timing out after nine hours
# somebody forgot to start their inference_server. Slow steps like loading models
# can happen during the first inference call if necessary.
STARTUP_LIMIT_SECONDS = 60 * 15

### Utils shared by client and server for data transfer

# pl.Enum is currently unstable, but we should eventually consider supporting it.
# https://docs.pola.rs/api/python/stable/reference/api/polars.datatypes.Enum.html#polars.datatypes.Enum
_POLARS_TYPE_DENYLIST = set([pl.Enum, pl.Object, pl.Unknown])


def _get_available_port(ports: list[int] | None = None) -> int:
    """Identify the first available port out of all GRPC_PORTS"""
    ports_to_check = ports if ports is not None else GRPC_PORTS
    for port in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
            except Exception:
                continue
        return port

    raise ValueError(f'None of the expected ports {ports_to_check} are available.')


def _get_ports_to_try(port: int | None, ports: list[int] | None, default_ports: list[int] | None) -> list[int] | None:
    if port and ports:
        return [port] + ports
    if port is not None:
        return [port + i for i in range(NUM_FALLBACK_PORTS + 1)]
    if ports is not None:
        return ports
    return default_ports


### Data model deserialization utils


def set_allowed_modules(modules: list[str] | None) -> None:
    """Set the allowlist of modules that can be imported during data_model deserialization.

    Args:
        modules: List of module names/prefixes allowed, or None to allow all.
                 Examples: ['myapp.models', 'shared.schemas']
    """
    global _ALLOWED_MODULES
    _ALLOWED_MODULES = modules


def _is_module_allowed(module_path: str) -> bool:
    """Check if a module is allowed to be imported based on the allowlist.
    Used by data model deserialization.

    Set _ALLOWED_MODULES to "*" to allow all modules.
    """
    if not _ALLOWED_MODULES:
        # No allowlist configured - reject all modules
        return False

    # Check for explicit wildcard in programmatically set allowlist
    if '*' in _ALLOWED_MODULES:
        return True
    return any(module_path.startswith(prefix) for prefix in _ALLOWED_MODULES)


def _reconstruct_dataclass(dataclass_type: type, json_data: str) -> Any:
    """Recursively reconstruct a dataclass instance from JSON data.

    Handles nested dataclasses by inspecting field types and recursively
    reconstructing them.

    Args:
        dataclass_type: The dataclass type to instantiate
        json_data: JSON string containing the field values

    Returns:
        Instance of the dataclass with all nested dataclasses properly reconstructed
    """
    data = json.loads(json_data)
    field_values = {}
    for field in dataclasses.fields(dataclass_type):
        field_name = field.name
        field_value = data.get(field_name)

        if field_value is not None:
            # Extract the actual type from annotations like Optional[T], Union[T, None], etc.
            actual_type = field.type
            origin = get_origin(actual_type)

            # Handle Union types (including Optional which is Union[T, None])
            if origin is not None:
                args = get_args(actual_type)
                # Find the first non-None type in the union
                for arg in args:
                    if arg is not type(None) and dataclasses.is_dataclass(arg):
                        actual_type = arg
                        break

            if dataclasses.is_dataclass(actual_type) and inspect.isclass(actual_type):
                field_values[field_name] = _reconstruct_dataclass(actual_type, json.dumps(field_value))
            else:
                field_values[field_name] = field_value
        else:
            field_values[field_name] = field_value

    return dataclass_type(**field_values)


def _validate_and_import_class(module_path: str, class_name: str) -> type[Any]:
    """Validate module allowlist and import a class for deserialization.

    Args:
        module_path: Full module path (e.g., 'myapp.models')
        class_name: Class name, potentially nested (e.g., 'MyClass.InnerClass')

    Returns:
        class_object

    Raises:
        PermissionError: If module is not in allowlist
        ImportError: If module cannot be imported
        AttributeError: If class not found in module
    """
    if not _is_module_allowed(module_path):
        raise PermissionError(f'Security error: Module "{module_path}" is not in the allowlist. Configure allowed modules via set_allowed_modules()')

    try:
        return _try_import_and_inspect_class(module_path, class_name)
    except ImportError as e:
        raise ImportError(
            f'Cannot deserialize: module "{module_path}" not found. Ensure the class is importable on both client and server. Error: {e}'
        )
    except AttributeError as e:
        raise AttributeError(
            f'Cannot deserialize: class "{class_name}" not found in module "{module_path}". Ensure the class is defined and importable. Error: {e}'
        )
    except Exception:
        raise


def _try_import_and_inspect_class(module_path: str, class_name: str) -> Any:
    """Import a module and inspect if a class is a Pydantic model, dataclass, or Enum.

    This approach works with wheel-installed packages, compiled modules, and source files.
    Security is enforced through:
    1. Module allowlist checking (before this function).
    2. Runtime type verification (in this function).
    3. Module must already be available.

    Args:
        module_path: Full module path (e.g., 'myapp.models')
        class_name: Class name, potentially nested (e.g., 'MyClass.InnerClass')

    Returns:
        class type.

    Raises:
        ImportError: If module cannot be imported
        TypeError: If module is not a class or the class is not a type.
    """

    module = importlib.import_module(module_path)

    # Navigate to the class through nested attributes
    target_class = module
    for attr_name in class_name.split('.'):
        target_class = getattr(target_class, attr_name)

    if not inspect.isclass(target_class):
        raise TypeError(
            f'Security error: "{module_path}.{class_name}" is not a class. Only classes can be deserialized as data models for security reasons.'
        )
    return target_class


### Serialization & deserialization utils


def _serialize(data: Any) -> kaggle_evaluation_proto.Payload:
    """Maps input data of one of several allow-listed types to a protobuf message to be sent over gRPC.

    Args:
        data: The input data to be mapped. Any of the types listed below are accepted.

    Returns:
        The Payload protobuf message.

    Raises:
        TypeError if data is of an unsupported type.
    """
    # Python primitives and Numpy scalars
    if isinstance(data, np.generic):
        # Numpy functions that return a single number return numpy scalars instead of python primitives.
        # In some cases this difference matters: https://numpy.org/devdocs/release/2.0.0-notes.html#representation-of-numpy-scalars-changed
        # Ex: np.mean(1,2) yields np.float64(1.5) instead of 1.5.
        # Check for numpy scalars first since most of them also inherit from python primitives.
        # For example, `np.float64(1.5)` is an instance of `float` among many other things.
        # https://numpy.org/doc/stable/reference/arrays.scalars.html
        assert data.shape == ()  # Additional validation that the np.generic type remains solely for scalars
        assert isinstance(data, np.number) or isinstance(data, np.bool_)  # No support for bytes, strings, objects, etc
        buffer = io.BytesIO()
        np.save(buffer, data, allow_pickle=False)
        return kaggle_evaluation_proto.Payload(numpy_scalar_value=buffer.getvalue())
    elif isinstance(data, str):
        return kaggle_evaluation_proto.Payload(str_value=data)
    elif isinstance(data, bool):  # bool is a subclass of int, so check that first
        return kaggle_evaluation_proto.Payload(bool_value=data)
    elif isinstance(data, int):
        return kaggle_evaluation_proto.Payload(int_value=data)
    elif isinstance(data, float):
        return kaggle_evaluation_proto.Payload(float_value=data)
    elif data is None:
        return kaggle_evaluation_proto.Payload(none_value=True)
    # Iterables for nested types
    if isinstance(data, list):
        return kaggle_evaluation_proto.Payload(list_value=kaggle_evaluation_proto.PayloadList(payloads=map(_serialize, data)))
    elif isinstance(data, tuple):
        return kaggle_evaluation_proto.Payload(tuple_value=kaggle_evaluation_proto.PayloadList(payloads=map(_serialize, data)))
    elif isinstance(data, dict):
        serialized_dict = {}
        for key, value in data.items():
            if not isinstance(key, str):
                raise TypeError(f'KaggleEvaluation only supports dicts with keys of type str, found {type(key)}.')
            serialized_dict[key] = _serialize(value)
        return kaggle_evaluation_proto.Payload(dict_value=kaggle_evaluation_proto.PayloadMap(payload_map=serialized_dict))
    # Allowlisted special types
    if isinstance(data, pd.DataFrame):
        buffer = io.BytesIO()
        data.to_parquet(buffer, index=False, compression='lz4')
        return kaggle_evaluation_proto.Payload(pandas_dataframe_value=buffer.getvalue())
    elif isinstance(data, pl.DataFrame):
        data_types = set(i.base_type() for i in data.dtypes)
        banned_types = _POLARS_TYPE_DENYLIST.intersection(data_types)
        if banned_types:
            raise TypeError(f'Unsupported Polars data type(s): {banned_types}')

        table = data.to_arrow()
        buffer = io.BytesIO()
        with pyarrow.ipc.new_stream(buffer, table.schema, options=pyarrow.ipc.IpcWriteOptions(compression='lz4')) as writer:
            writer.write_table(table)
        return kaggle_evaluation_proto.Payload(polars_dataframe_value=buffer.getvalue())
    elif isinstance(data, pd.Series):
        buffer = io.BytesIO()
        # Can't serialize a pd.Series directly to parquet, must use intermediate DataFrame
        pd.DataFrame(data).to_parquet(buffer, index=False, compression='lz4')
        return kaggle_evaluation_proto.Payload(pandas_series_value=buffer.getvalue())
    elif isinstance(data, pl.Series):
        buffer = io.BytesIO()
        # Can't serialize a pl.Series directly to parquet, must use intermediate DataFrame
        pl.DataFrame(data).write_parquet(buffer, compression='lz4', statistics=False)
        return kaggle_evaluation_proto.Payload(polars_series_value=buffer.getvalue())
    elif isinstance(data, np.ndarray):
        buffer = io.BytesIO()
        np.save(buffer, data, allow_pickle=False)
        return kaggle_evaluation_proto.Payload(numpy_array_value=buffer.getvalue())
    elif isinstance(data, io.BytesIO):
        return kaggle_evaluation_proto.Payload(bytes_io_value=data.getvalue())
    elif isinstance(data, enum.Enum):
        enum_class = type(data)
        data_model = kaggle_evaluation_proto.DataModel(
            module=enum_class.__module__,
            class_name=enum_class.__qualname__,
            data=json.dumps(data.name),  # Use name instead of value for complex enums
        )
        return kaggle_evaluation_proto.Payload(enum_value=data_model)
    elif dataclasses.is_dataclass(data) and not isinstance(data, type):
        dataclass_type = type(data)
        data_model = kaggle_evaluation_proto.DataModel(
            module=dataclass_type.__module__,
            class_name=dataclass_type.__qualname__,
            data=json.dumps(dataclasses.asdict(data)),
        )
        return kaggle_evaluation_proto.Payload(dataclass_value=data_model)
    elif isinstance(data, pydantic.BaseModel):
        model_class = type(data)
        data_model = kaggle_evaluation_proto.DataModel(
            module=model_class.__module__,
            class_name=model_class.__qualname__,
            data=data.model_dump_json(),
        )
        return kaggle_evaluation_proto.Payload(pydantic_model_value=data_model)

    raise TypeError(f'Type {type(data)} not supported for KaggleEvaluation.')


def _deserialize(payload: kaggle_evaluation_proto.Payload) -> Any:
    """Maps a Payload protobuf message to a value of whichever type was set on the message.

    Args:
        payload: The message to be mapped.

    Returns:
        A value of one of several allow-listed types.

    Raises:
        TypeError if an unexpected value data type is found.
    """
    match payload.WhichOneof('value'):
        # Primitives
        case 'str_value':
            return payload.str_value
        case 'bool_value':
            return payload.bool_value
        case 'int_value':
            return payload.int_value
        case 'float_value':
            return payload.float_value
        case 'none_value':
            return None
        # Iterables for nested types
        case 'list_value':
            return list(map(_deserialize, payload.list_value.payloads))
        case 'tuple_value':
            return tuple(map(_deserialize, payload.tuple_value.payloads))
        case 'dict_value':
            return {key: _deserialize(value) for key, value in payload.dict_value.payload_map.items()}
        # Allowlisted special types
        case 'pandas_dataframe_value':
            return pd.read_parquet(io.BytesIO(payload.pandas_dataframe_value))
        case 'polars_dataframe_value':
            with pyarrow.ipc.open_stream(payload.polars_dataframe_value) as reader:
                table = reader.read_all()
            return pl.from_arrow(table)
        case 'pandas_series_value':
            # Pandas will still read a single column csv as a DataFrame.
            df = pd.read_parquet(io.BytesIO(payload.pandas_series_value))
            return pd.Series(df[df.columns[0]])
        case 'polars_series_value':
            return pl.Series(pl.read_parquet(io.BytesIO(payload.polars_series_value)))
        case 'numpy_array_value':
            return np.load(io.BytesIO(payload.numpy_array_value), allow_pickle=False)
        case 'numpy_scalar_value':
            data = np.load(io.BytesIO(payload.numpy_scalar_value), allow_pickle=False)
            # As of Numpy 2.0.2, np.load for a numpy scalar yields a dimensionless array instead of a scalar
            data = data.dtype.type(data)  # Restore the expected numpy scalar type.
            assert data.shape == ()  # Additional validation that the np.generic type remains solely for scalars
            assert isinstance(data, np.number) or isinstance(data, np.bool_)  # No support for bytes, strings, objects, etc
            return data
        case 'bytes_io_value':
            return io.BytesIO(payload.bytes_io_value)
        case 'enum_value':
            data_model = payload.enum_value
            target_class = _validate_and_import_class(module_path=data_model.module, class_name=data_model.class_name)
            assert issubclass(target_class, enum.Enum)
            enum_name = json.loads(data_model.data)
            return target_class[enum_name]  # Use name lookup instead of value lookup
        case 'dataclass_value':
            data_model = payload.dataclass_value
            target_class = _validate_and_import_class(module_path=data_model.module, class_name=data_model.class_name)
            assert dataclasses.is_dataclass(target_class)
            return _reconstruct_dataclass(target_class, data_model.data)
        case 'pydantic_model_value':
            data_model = payload.pydantic_model_value
            target_class = _validate_and_import_class(module_path=data_model.module, class_name=data_model.class_name)
            assert issubclass(target_class, pydantic.BaseModel)
            return target_class.model_validate_json(payload.pydantic_model_value.data)
        case _:
            raise TypeError(f'Found unknown Payload case {payload.WhichOneof("value")}')


### Client code


class Client:
    """
    Class which allows callers to make KaggleEvaluation requests.
    """

    def __init__(self, channel_address: str = 'localhost', port: Optional[int] = None, ports: list[int] | None = None) -> None:
        self.channel_address = channel_address
        self.port = port
        self.ports = ports
        self.channel: Optional[grpc.Channel] = None
        self._made_first_connection = False
        self.endpoint_deadline_seconds = DEFAULT_DEADLINE_SECONDS
        self.stub: Optional[kaggle_evaluation_grpc.KaggleEvaluationServiceStub] = None
        self._hostname_was_valid = False

    def _send_with_deadline(self, request) -> kaggle_evaluation_proto.KaggleEvaluationResponse:
        """Sends a message to the server while also:
        - Throwing an error as soon as the inference_server container has been shut down.
        - Setting a deadline of STARTUP_LIMIT_SECONDS for the inference_server to startup.
        """
        if self._made_first_connection:
            if self.stub is None:
                raise RuntimeError('Stub is not initialized')
            try:
                return self.stub.Send(request, wait_for_ready=False, timeout=self.endpoint_deadline_seconds)
            except grpc._channel._InactiveRpcError as err:  # ty: ignore
                if 'StatusCode.DEADLINE_EXCEEDED' in str(err):
                    raise GRPCDeadlineError()
                else:
                    raise err
            except Exception as err:
                raise err

        first_call_time = time.time()
        ports_to_try = _get_ports_to_try(port=self.port, ports=self.ports, default_ports=GRPC_PORTS)
        if ports_to_try is None:
            raise RuntimeError('Failed to determine ports to try')

        # Allow time for the server to start as long as its container is running
        while time.time() - first_call_time < STARTUP_LIMIT_SECONDS:
            for port in ports_to_try:
                self.channel = grpc.insecure_channel(f'{self.channel_address}:{port}', options=_GRPC_CHANNEL_OPTIONS)
                self.stub = kaggle_evaluation_grpc.KaggleEvaluationServiceStub(self.channel)
                try:
                    response = self.stub.Send(request, wait_for_ready=False)
                    self._made_first_connection = True
                    return response
                except grpc._channel._InactiveRpcError as err:  # ty: ignore
                    if 'StatusCode.UNAVAILABLE' not in str(err):
                        raise err
                # Confirm the inference_server container is still alive & it's worth waiting on the server.
                # If the inference_server container is no longer running or the channel address is invalid this will throw a socket.gaierror.
                try:
                    socket.gethostbyname(self.channel_address)
                    self._hostname_was_valid = True
                except socket.gaierror as err:
                    if self._hostname_was_valid:
                        raise ServerDiedError(f'The inference_server container has died after startup, causing: {err}')
                    else:
                        raise err
                time.sleep(_RETRY_SLEEP_SECONDS)

        if not self._made_first_connection:
            raise RuntimeError(f'Failed to connect to server after waiting {STARTUP_LIMIT_SECONDS} seconds')

        raise RuntimeError('Unreachable')

    def serialize_request(self, name: str, *args, **kwargs) -> kaggle_evaluation_proto.KaggleEvaluationRequest:
        """Serialize a single request. Exists as a separate function from `send`
        to enable gateway concurrency for some competitions.
        """
        already_serialized = (len(args) == 1) and isinstance(args[0], kaggle_evaluation_proto.KaggleEvaluationRequest)
        if already_serialized:
            return args[0]  # args is a tuple of length 1 containing the request
        return kaggle_evaluation_proto.KaggleEvaluationRequest(
            name=name, args=map(_serialize, args), kwargs={key: _serialize(value) for key, value in kwargs.items()}
        )

    def send(self, name: str, *args, **kwargs) -> Any:
        """Sends a single KaggleEvaluation request.

        Args:
            name: The endpoint name for the request.
            *args: Variable-length/type arguments to be supplied on the request.
            **kwargs: Key-value arguments to be supplied on the request.

        Returns:
            The response, which is of one of several allow-listed data types.
        """
        request = self.serialize_request(name, *args, **kwargs)
        response = self._send_with_deadline(request)
        return _deserialize(response.payload)

    def close(self) -> None:
        if self.channel is not None:
            self.channel.close()


### Server code


def _get_endpoint_name(func: FunctionType | MethodType) -> str:
    """Get the endpoint name for a function or method.

    For functions, returns the function name.
    For bound methods, returns 'ClassName.method_name' to ensure uniqueness.
    """
    if isinstance(func, MethodType):
        class_name = type(func.__self__).__name__
        return f'{class_name}.{func.__name__}'
    return func.__name__


class KaggleEvaluationServiceServicer(kaggle_evaluation_grpc.KaggleEvaluationServiceServicer):
    """
    Class which allows serving responses to KaggleEvaluation requests. The inference_server will run this service to listen for and respond
    to requests from the Gateway. The Gateway may also listen for requests from the inference_server in some cases.
    """

    def __init__(self, listeners: Tuple[FunctionType | MethodType, ...]) -> None:
        self.listeners_map = {}
        for func in listeners:
            qualified_name = _get_endpoint_name(func)
            simple_name = func.__name__
            # Register under the qualified name (ClassName.method_name for methods)
            self.listeners_map[qualified_name] = func
            # Also register under the simple name so gateways can call without knowing the class or whether the callable is a method or function.
            if simple_name != qualified_name:
                if simple_name in self.listeners_map:
                    raise ValueError(f"Endpoint '{simple_name}' is already registered. Cannot register {qualified_name} under the same simple name.")
                self.listeners_map[simple_name] = func

    # pylint: disable=unused-argument
    def Send(
        self, request: kaggle_evaluation_proto.KaggleEvaluationRequest, context: grpc.ServicerContext
    ) -> kaggle_evaluation_proto.KaggleEvaluationResponse:
        """Handler for gRPC requests that deserializes arguments, calls a user-registered function for handling the
        requested endpoint, then serializes and returns the response.

        Args:
            request: The KaggleEvaluationRequest protobuf message.
            context: (Unused) gRPC context.

        Returns:
            The KaggleEvaluationResponse protobuf message.

        Raises:
            NotImplementedError if the caller has not registered a handler for the requested endpoint.
        """
        if request.name not in self.listeners_map:
            raise NotImplementedError(f'No listener for {request.name} was registered.')

        args = map(_deserialize, request.args)
        kwargs = {key: _deserialize(value) for key, value in request.kwargs.items()}
        response_function = self.listeners_map[request.name]
        response_payload = _serialize(response_function(*args, **kwargs))
        return kaggle_evaluation_proto.KaggleEvaluationResponse(payload=response_payload)


def define_server(*endpoint_listeners: FunctionType | MethodType, port: int | None = None, ports: list[int] | None = None) -> Tuple[grpc.Server, int]:
    """Registers the endpoints that the container is able to respond to, then starts a server which listens for
    those endpoints. The endpoints that need to be implemented will depend on the specific competition.

    Args:
        endpoint_listeners: Tuple of functions or bound methods that define how requests to the endpoint of the
            function/method name should be handled.
        port: Optional specific port to bind to. If None, finds an available port.
        ports: Optional list of ports to try binding to. Used if port is None.

    Returns:
        A tuple of (gRPC server object, port number). Server should be stopped at exit time.

    Raises:
        ValueError if parameter values are invalid.
    """
    if not endpoint_listeners:
        raise ValueError('Must pass at least one endpoint listener, e.g. `predict`')
    for func in endpoint_listeners:
        if not isinstance(func, (FunctionType, MethodType)):
            raise ValueError(f'Endpoint listeners must be functions or bound methods, got {type(func)}')
        if func.__name__ == '<lambda>':
            raise ValueError('Endpoint listeners must be named (lambdas are not allowed)')

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1), options=_GRPC_CHANNEL_OPTIONS)
    kaggle_evaluation_grpc.add_KaggleEvaluationServiceServicer_to_server(KaggleEvaluationServiceServicer(endpoint_listeners), server)
    ports_to_try = _get_ports_to_try(port=port, ports=ports, default_ports=None)
    grpc_port = _get_available_port(ports_to_try)
    server.add_insecure_port(f'[::]:{grpc_port}')
    return server, grpc_port
