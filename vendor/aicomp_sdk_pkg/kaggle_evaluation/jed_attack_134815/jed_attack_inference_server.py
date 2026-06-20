"""Inference server for JED Red-Team Attack Competition (ID: 134815).

Loads the competitor's attack.py submission and runs the attack algorithm
using a RemoteEnv proxy. The env operations are relayed to/from the gateway
via a command-response protocol over predict() calls.

Protocol:
  predict({"cmd": "init", "budget_s": ..., "seed": ...})
    → Loads attack module, starts attacker thread with RemoteEnv
    → Returns first env_op or {"status": "done", "candidates": [...]}

  predict({"cmd": "env_result", "result": ...})
    → Feeds env op result to attacker, waits for next env_op
    → Returns next env_op or {"status": "done", "candidates": [...]}
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any

import kaggle_evaluation.core.templates

from kaggle_evaluation.jed_attack_134815 import jed_attack_gateway
from kaggle_evaluation.jed_attack_134815 import remote_env as renv

from aicomp_sdk.attacks import AttackAlgorithmBase, AttackCandidate
from aicomp_sdk.core.env.api import MAX_USER_MESSAGE_CHARS
from aicomp_sdk.evaluation.ops import MAX_REPLAY_FINDINGS, MAX_REPLAY_MESSAGES_PER_FINDING

# Path where Kaggle mounts competitor submissions.
DEFAULT_SUBMISSION_DIR = Path("/kaggle/working")
ATTACK_MODULE_NAME = "user_attack"
ATTACK_FILE_NAME = "attack.py"
ATTACK_CLASS_NAME = "AttackAlgorithm"
ATTACK_TIMEOUT_ERROR_TYPE = "attack_time_budget_exceeded"

# Module-level state.
_attack_cls: type[AttackAlgorithmBase] | None = None
_session: renv.AttackSession | None = None


def _load_attack_module(submission_dir: Path | None = None) -> type[AttackAlgorithmBase]:
    """Dynamically load the competitor's AttackAlgorithm class.

    Expects the submission to contain an attack.py with a class named
    'AttackAlgorithm' that inherits from AttackAlgorithmBase.
    """
    if submission_dir is None:
        submission_dir = DEFAULT_SUBMISSION_DIR
    attack_path = submission_dir / ATTACK_FILE_NAME
    if not attack_path.exists():
        raise FileNotFoundError(
            f"Submission must contain {ATTACK_FILE_NAME} at {submission_dir}"
        )

    spec = importlib.util.spec_from_file_location(
        ATTACK_MODULE_NAME, str(attack_path)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {attack_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[ATTACK_MODULE_NAME] = module
    spec.loader.exec_module(module)

    if not hasattr(module, ATTACK_CLASS_NAME):
        raise AttributeError(
            f"{ATTACK_FILE_NAME} must define a class named '{ATTACK_CLASS_NAME}'"
        )

    attack_cls = getattr(module, ATTACK_CLASS_NAME)
    if not issubclass(attack_cls, AttackAlgorithmBase):
        raise TypeError(
            f"{ATTACK_CLASS_NAME} class must inherit from AttackAlgorithmBase"
        )

    return attack_cls


def _wait_for_env_op_or_done() -> dict[str, Any]:
    """Wait for the next env op from the attacker, or return done + candidates."""
    global _session
    assert _session is not None

    # Try to get the next env operation.
    env_op = _session.get_next_env_op(timeout=_env_op_timeout_s(_session))

    if env_op is renv.ATTACK_SESSION_DONE:
        if _session_completed_after_finalization_grace(_session):
            return _budget_exceeded_response()
        return _done_response(_session)

    if env_op is not None:
        if _session.remaining_budget_s() <= 0:
            return _budget_exceeded_response()
        return {"status": "env_op", **env_op}

    if _session.is_done():
        if _session_completed_after_finalization_grace(_session):
            return _budget_exceeded_response()
        return _done_response(_session)

    if _session.remaining_budget_s() <= 0:
        return _budget_exceeded_response()

    return {"status": "error", "error": "Timed out waiting for attack env operation"}


def _env_op_timeout_s(session: renv.AttackSession) -> float:
    remaining_s = session.remaining_budget_s()
    return max(0.0, remaining_s + jed_attack_gateway.ATTACK_ENV_OP_GRACE_S)


def _budget_exceeded_response() -> dict[str, str]:
    return {
        "status": "timeout",
        "error": "Attack time budget exceeded while waiting for attack env operation",
        "error_type": ATTACK_TIMEOUT_ERROR_TYPE,
    }


def _exception_response(err: Exception) -> dict[str, str]:
    return {
        "status": "error",
        "error": str(err),
        "error_type": type(err).__name__,
    }


def _session_completed_after_finalization_grace(session: renv.AttackSession) -> bool:
    """Return whether a completed session missed the accepted finalization window.

    Attack code cannot cancel an in-flight RemoteEnv operation. If the attacker
    returns a replayable candidate list shortly after the deadline, accept it;
    otherwise classify the model attempt as timed out.
    """
    completed_at_s = getattr(session, "completed_at_s", None)
    deadline_s = getattr(session, "deadline_s", None)
    if completed_at_s is None or deadline_s is None:
        return session.remaining_budget_s() <= 0
    return completed_at_s > deadline_s + jed_attack_gateway.ATTACK_ENV_OP_GRACE_S


def _done_response(session: renv.AttackSession) -> dict[str, Any]:
    if session.error:
        return {"status": "error", "error": str(session.error)}

    try:
        serialized = _serialize_candidates(session.candidates)
    except (TypeError, ValueError) as err:
        return _exception_response(err)

    return {
        "status": "done",
        "candidates": serialized,
        "candidates_count": len(serialized),
    }


def _serialize_candidates(candidates: Any) -> list[dict[str, list[str]]]:
    if not isinstance(candidates, list):
        raise TypeError("AttackAlgorithm.run must return list[AttackCandidate]")

    serialized: list[dict[str, list[str]]] = []
    for idx, candidate in enumerate(candidates[:MAX_REPLAY_FINDINGS]):
        if not isinstance(candidate, AttackCandidate):
            raise TypeError(
                f"AttackAlgorithm.run returned unsupported item at index {idx}; "
                "expected AttackCandidate"
            )
        serialized.append({
            "user_messages": list(_validate_candidate_messages(candidate, idx)),
        })
    return serialized


def _validate_candidate_messages(candidate: AttackCandidate, index: int) -> tuple[str, ...]:
    try:
        messages = tuple(candidate.user_messages)
    except TypeError as err:
        raise TypeError(f"AttackCandidate[{index}].user_messages must be iterable") from err

    if not messages:
        raise ValueError(f"AttackCandidate[{index}] must include at least one user message")
    if len(messages) > MAX_REPLAY_MESSAGES_PER_FINDING:
        raise ValueError(
            f"AttackCandidate[{index}] exceeds max chain length "
            f"({MAX_REPLAY_MESSAGES_PER_FINDING})"
        )
    for msg_idx, message in enumerate(messages):
        if not isinstance(message, str):
            raise TypeError(f"AttackCandidate[{index}].user_messages[{msg_idx}] must be a string")
        if not message.strip():
            raise ValueError(f"AttackCandidate[{index}].user_messages[{msg_idx}] cannot be empty")
        if len(message) > MAX_USER_MESSAGE_CHARS:
            raise ValueError(
                f"AttackCandidate[{index}].user_messages[{msg_idx}] exceeds max length "
                f"({MAX_USER_MESSAGE_CHARS})"
            )
    return messages


def predict(request: dict[str, Any]) -> dict[str, Any]:
    """Handle command-response protocol for attack evaluation.

    This is a module-level function (not a method) so it can be passed
    to InferenceServer.__init__() as an endpoint listener.
    """
    global _attack_cls, _session
    cmd = request.get("cmd", "init")

    if cmd == "init":
        # Load attack module if needed.
        if _attack_cls is None:
            try:
                _attack_cls = _load_attack_module()
            except Exception as err:
                return _exception_response(err)

        budget_s = float(request.get("budget_s", 9000.0))
        seed = int(request.get("seed", 123))

        # Start the attacker in a background thread with RemoteEnv.
        _session = renv.AttackSession(_attack_cls, budget_s, seed)
        _session.start()

        # Wait for the first env operation from the attacker.
        return _wait_for_env_op_or_done()

    if cmd == "env_result":
        # Feed the gateway's env operation result to the blocked attacker.
        assert _session is not None, "No active attack session"
        _session.send_env_result(request.get("result"))

        # Wait for the next env operation.
        return _wait_for_env_op_or_done()

    return {"status": "error", "error": f"Unknown command: {cmd}"}


class JEDAttackInferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    """Inference server that wraps the competitor's attack algorithm."""

    def __init__(self):
        super().__init__(predict)

    def _get_gateway_for_test(
        self, data_paths=None, file_share_dir=None, *args, **kwargs
    ):
        """Return a gateway instance for local testing."""
        return jed_attack_gateway.JEDAttackGateway(data_paths)
