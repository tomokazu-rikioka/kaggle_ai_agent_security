"""RemoteEnv: proxy that forwards env operations to the gateway.

This is the inverse of RemoteGuardrail. While RemoteGuardrail proxies
guardrail.decide() calls from gateway → inference server, RemoteEnv proxies
env operations from inference server → gateway.

The attacker's run(env, config) call in the inference server uses this proxy.
Each env method call (reset, interact, snapshot, etc.) puts a request on
a queue and blocks until the gateway responds with the result via predict().

Protocol:
  predict({"cmd": "init", ...})           → starts attack, returns first env_op
  predict({"cmd": "env_result", ...})     → feeds result, returns next env_op or done
"""

import queue
import threading
import time
from collections.abc import Mapping
from dataclasses import fields
from typing import Any

from aicomp_sdk.core.env.api import (
    DEFAULT_MAX_TOOL_HOPS,
    EnvInteractionResult,
    validate_interact_args,
)
from aicomp_sdk.core.env.opaque import _OpaqueAttackEnv
from aicomp_sdk.guardrails.base import GuardrailBase


ATTACK_SESSION_DONE = object()


class RemoteEnv:
    """Env proxy that relays operations to the gateway via command-response.

    Each env method puts a request dict on _request_queue and blocks on
    _response_queue. The predict() handler reads requests and sends
    responses, acting as a broker between the attacker thread and gateway.
    """

    def __init__(self, seed: int = 0):
        self._request_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._response_queue: queue.Queue[Any] = queue.Queue()
        self.seed = seed
        self._trace: dict[str, Any] = {}
        self._tools: Any = None
        self._guardrail: GuardrailBase = GuardrailBase()

    @property
    def trace(self) -> Any:
        return self._trace

    @property
    def tools(self) -> Any:
        return self._tools

    @property
    def guardrail(self) -> GuardrailBase:
        return self._guardrail

    def reset(self, *args: Any, **kwargs: Any) -> Any:
        request: dict[str, Any] = {"op": "reset"}
        if args:
            request["args"] = list(args)
        if kwargs:
            request["kwargs"] = dict(kwargs)
        self._request_queue.put(request)
        result = self._response_queue.get()
        self._sync_seed_from_reset_result(result)
        return result

    def interact(
        self, user_message: str, max_tool_hops: int | None = DEFAULT_MAX_TOOL_HOPS
    ) -> EnvInteractionResult:
        resolved_max_tool_hops = validate_interact_args(
            user_message,
            max_tool_hops,
            caller="RemoteEnv.interact",
        )
        self._request_queue.put(
            {
                "op": "interact",
                "user_message": user_message,
                "max_tool_hops": resolved_max_tool_hops,
            }
        )
        result = self._response_queue.get()
        if isinstance(result, dict):
            # Reconstruct EnvInteractionResult from dict.
            valid_keys = {f.name for f in fields(EnvInteractionResult)}
            filtered = {k: v for k, v in result.items() if k in valid_keys}
            return EnvInteractionResult(**filtered)
        return result

    def export_trace_dict(self) -> dict[str, Any]:
        self._request_queue.put({"op": "export_trace_dict"})
        return self._response_queue.get()

    def snapshot(self) -> Any:
        """Request a snapshot. Gateway stores the actual state and returns a handle ID."""
        self._request_queue.put({"op": "snapshot"})
        return self._response_queue.get()  # Returns snapshot_id (string handle)

    def restore(self, snapshot: Any) -> None:
        """Restore from a snapshot handle ID."""
        self._request_queue.put({"op": "restore", "snapshot_id": snapshot})
        self._response_queue.get()  # Wait for ack

    def _sync_seed_from_reset_result(self, result: Any) -> None:
        if isinstance(result, Mapping) and "seed" in result:
            self.seed = int(result["seed"])
            return
        if not isinstance(result, tuple) or len(result) != 2:
            return
        _, info = result
        if not isinstance(info, Mapping):
            return
        trace = info.get("trace")
        if isinstance(trace, Mapping) and "seed" in trace:
            self.seed = int(trace["seed"])


class AttackSession:
    """Manages the attacker thread and its RemoteEnv communication."""

    def __init__(self, attack_cls, budget_s: float, seed: int):
        from aicomp_sdk.attacks import AttackRunConfig

        self.env_proxy = RemoteEnv(seed=seed)
        self.attacker = attack_cls(config={})
        self.config = AttackRunConfig(time_budget_s=budget_s)
        self.started_at_s = time.monotonic()
        self.deadline_s = self.started_at_s + float(budget_s)
        self.completed_at_s: float | None = None
        self.thread: threading.Thread | None = None
        self.candidates: list | None = None
        self.error: Exception | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run_attack, daemon=True)
        self.thread.start()

    def _run_attack(self) -> None:
        try:
            opaque_env = _OpaqueAttackEnv(self.env_proxy)
            opaque_env.reset()
            self.candidates = self.attacker.run(
                opaque_env,
                self.config,
            )
        except Exception as e:
            self.error = e
        finally:
            self.completed_at_s = time.monotonic()
            # Signal that no more env ops will come, so get_next_env_op()
            # returns immediately instead of blocking for the full timeout.
            self.env_proxy._request_queue.put(ATTACK_SESSION_DONE)

    def is_done(self) -> bool:
        return self.thread is not None and not self.thread.is_alive()

    def remaining_budget_s(self) -> float:
        return max(0.0, self.deadline_s - time.monotonic())

    def get_next_env_op(self, timeout: float = 60.0) -> dict[str, Any] | object | None:
        """Get the next env operation, completion sentinel, or None on timeout."""
        try:
            return self.env_proxy._request_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_env_result(self, result: Any) -> None:
        """Send the gateway's env operation result back to the attacker."""
        self.env_proxy._response_queue.put(result)
