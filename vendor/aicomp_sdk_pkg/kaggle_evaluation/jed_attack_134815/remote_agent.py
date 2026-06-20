"""RemoteAgent: proxy that forwards agent operations through Hearth relay.

Analogous to RemoteGuardrail (which proxies guardrail.decide() calls),
RemoteAgent proxies AgentProtocol methods (next_action, reset_state, etc.)
through Hearth's predict() mechanism. This enables:
  1. Model running in a separate Hearth-hosted server (with GPU/GGUF)
  2. Gateway screening of model outputs (e.g., rejecting a stockfish binary)
  3. Multi-model evaluation without loading models in the gateway process

Protocol:
  predict({"cmd": "next_action", "history": {...}, "tools": [...]})
    → {"decision": "tool_call", "call": {...}} or {"decision": "final_response", "text": "..."}

  predict({"cmd": "reset_state"}) → {"ack": true}
  predict({"cmd": "snapshot_state"}) → {"snapshot": {...}}
  predict({"cmd": "restore_state", "snapshot": {...}}) → {"ack": true}
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aicomp_sdk.agents.types import (
    AgentDecision,
    AgentStateSnapshot,
    AgentToolSpec,
    AssistantMessageEvent,
    FinalResponseDecision,
    InstructionEvent,
    InvalidModelOutputError,
    ToolCall,
    ToolCallDecision,
    ToolRequestEvent,
    ToolResult,
    ToolResultEvent,
    UserMessageEvent,
)
from aicomp_sdk.core.runtime_history import RuntimeHistory


class RemoteAgentError(RuntimeError):
    """Raised when the model-server command protocol returns an invalid response."""


# ---------- Serialization Helpers ----------


def serialize_history(history: RuntimeHistory) -> dict[str, Any]:
    """Convert RuntimeHistory to a JSON-serializable dict."""
    return {
        "instructions": [
            {"type": "instruction", "text": e.text}
            for e in history.instructions
        ],
        "events": [_serialize_event(e) for e in history.events],
    }


def _serialize_event(event: Any) -> dict[str, Any]:
    if isinstance(event, UserMessageEvent):
        return {"type": "user_message", "text": event.text}
    if isinstance(event, AssistantMessageEvent):
        return {"type": "assistant_message", "text": event.text}
    if isinstance(event, ToolRequestEvent):
        return {
            "type": "tool_request",
            "call": {
                "call_id": event.call.call_id,
                "tool_name": event.call.tool_name,
                "arguments": dict(event.call.arguments),
            },
        }
    if isinstance(event, ToolResultEvent):
        return {
            "type": "tool_result",
            "result": {
                "call_id": event.result.call_id,
                "tool_name": event.result.tool_name,
                "output_text": event.result.output_text,
                "is_error": event.result.is_error,
            },
        }
    raise ValueError(f"Unknown event type: {type(event)}")


def deserialize_history(data: dict[str, Any]) -> RuntimeHistory:
    """Reconstruct RuntimeHistory from a serialized dict."""
    instructions = tuple(
        InstructionEvent(text=e["text"])
        for e in data.get("instructions", [])
    )
    events = tuple(
        _deserialize_event(e) for e in data.get("events", [])
    )
    return RuntimeHistory(instructions=instructions, events=events)


def _deserialize_event(data: dict[str, Any]) -> Any:
    t = data["type"]
    if t == "user_message":
        return UserMessageEvent(text=data["text"])
    if t == "assistant_message":
        return AssistantMessageEvent(text=data["text"])
    if t == "tool_request":
        c = data["call"]
        return ToolRequestEvent(
            call=ToolCall(
                call_id=c["call_id"],
                tool_name=c["tool_name"],
                arguments=c["arguments"],
            )
        )
    if t == "tool_result":
        r = data["result"]
        return ToolResultEvent(
            result=ToolResult(
                call_id=r["call_id"],
                tool_name=r["tool_name"],
                output_text=r["output_text"],
                is_error=r.get("is_error", False),
            )
        )
    raise ValueError(f"Unknown event type: {t}")


def serialize_tools(tools: Sequence[AgentToolSpec]) -> list[dict[str, Any]]:
    """Convert AgentToolSpec sequence to JSON-serializable list."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters_json_schema": dict(t.parameters_json_schema),
            "strict": t.strict,
        }
        for t in tools
    ]


def deserialize_tools(data: list[dict[str, Any]]) -> list[AgentToolSpec]:
    """Reconstruct AgentToolSpec list from serialized dicts."""
    return [
        AgentToolSpec(
            name=t["name"],
            description=t["description"],
            parameters_json_schema=t["parameters_json_schema"],
            strict=t.get("strict", True),
        )
        for t in data
    ]


def serialize_decision(decision: AgentDecision) -> dict[str, Any]:
    """Convert AgentDecision to JSON-serializable dict."""
    if isinstance(decision, ToolCallDecision):
        return {
            "decision": "tool_call",
            "call": {
                "call_id": decision.call.call_id,
                "tool_name": decision.call.tool_name,
                "arguments": dict(decision.call.arguments),
            },
            "assistant_message": decision.assistant_message,
        }
    if isinstance(decision, FinalResponseDecision):
        return {
            "decision": "final_response",
            "text": decision.text,
        }
    raise ValueError(f"Unknown decision type: {type(decision)}")


def deserialize_decision(data: dict[str, Any]) -> AgentDecision:
    """Reconstruct AgentDecision from a serialized dict."""
    d = data.get("decision")
    if d == "tool_call":
        c = _require_mapping_field(data, "call")
        arguments = _require_mapping_field(c, "arguments")
        assistant_message = data.get("assistant_message")
        if assistant_message is not None and not isinstance(assistant_message, str):
            raise RemoteAgentError("tool_call assistant_message must be a string or null")
        return ToolCallDecision(
            call=ToolCall(
                call_id=_require_non_empty_string(c, "call_id"),
                tool_name=_require_non_empty_string(c, "tool_name"),
                arguments=arguments,
            ),
            assistant_message=assistant_message,
        )
    if d == "final_response":
        text = data.get("text")
        if not isinstance(text, str):
            raise RemoteAgentError("final_response text must be a string")
        return FinalResponseDecision(text=text)
    raise RemoteAgentError(f"Unknown decision type: {d}")


# ---------- RemoteAgent ----------


class RemoteAgent:
    """Agent proxy that delegates all operations through Hearth's predict() relay.

    Analogous to RemoteGuardrail but for the AgentProtocol interface.
    The actual model runs in a separate Hearth-hosted inference server.
    """

    def __init__(self, predict_fn):
        """Initialize with the gateway's predict function.

        Args:
            predict_fn: Callable that sends a request dict to the model
                inference server and returns the response dict.
        """
        self._predict = predict_fn

    def next_action(
        self,
        *,
        history: RuntimeHistory,
        tools: Sequence[AgentToolSpec],
    ) -> AgentDecision:
        """Forward the agent decision to the model inference server."""
        response = self._predict({
            "cmd": "next_action",
            "history": serialize_history(history),
            "tools": serialize_tools(tools),
        })
        response = _require_response(response, command="next_action")
        _raise_if_error(response, command="next_action")
        try:
            return deserialize_decision(response)
        except RemoteAgentError:
            raise
        except Exception as err:
            raise RemoteAgentError("Invalid next_action response from model server") from err

    def reset_state(self) -> None:
        """Reset provider-private state on the remote model server."""
        response = _require_response(self._predict({"cmd": "reset_state"}), command="reset_state")
        _require_ack(response, command="reset_state")

    def snapshot_state(self) -> AgentStateSnapshot:
        """Get a snapshot from the remote model server."""
        response = _require_response(
            self._predict({"cmd": "snapshot_state"}),
            command="snapshot_state",
        )
        _raise_if_error(response, command="snapshot_state")
        snapshot = response.get("snapshot")
        if not _is_agent_state_snapshot(snapshot):
            raise RemoteAgentError("Invalid snapshot_state response from model server")
        return snapshot

    def restore_state(self, snapshot: AgentStateSnapshot) -> None:
        """Restore state on the remote model server."""
        response = _require_response(
            self._predict({
                "cmd": "restore_state",
                "snapshot": snapshot,
            }),
            command="restore_state",
        )
        _require_ack(response, command="restore_state")


def _require_response(response: Any, *, command: str) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise RemoteAgentError(f"Model server returned non-object response for {command}")
    return dict(response)


def _raise_if_error(response: Mapping[str, Any], *, command: str) -> None:
    error = response.get("error")
    if error is None:
        return
    error_type = response.get("error_type")
    if error_type == "InvalidModelOutputError":
        raise InvalidModelOutputError(str(error))
    prefix = f"{error_type}: " if isinstance(error_type, str) and error_type else ""
    raise RemoteAgentError(f"Model server {command} failed: {prefix}{error}")


def _require_ack(response: Mapping[str, Any], *, command: str) -> None:
    _raise_if_error(response, command=command)
    if response.get("ack") is not True:
        raise RemoteAgentError(f"Model server did not acknowledge {command}")


def _is_agent_state_snapshot(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if isinstance(value.get("version"), bool) or not isinstance(value.get("version"), int):
        return False
    if not isinstance(value.get("backend"), str) or not value.get("backend"):
        return False
    return isinstance(value.get("data"), dict)


def _require_mapping_field(data: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, Mapping):
        raise RemoteAgentError(f"{field} must be an object")
    return dict(value)


def _require_non_empty_string(data: Mapping[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RemoteAgentError(f"{field} must be a non-empty string")
    return value
