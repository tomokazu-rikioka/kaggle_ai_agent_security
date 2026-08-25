"""Hypothesis 1: the public guardrail with its concrete implementation holes fixed."""

from collections.abc import Mapping
from typing import Any

from aicomp_sdk.guardrails.base import Decision, GuardrailBase

from guardrails._shared import (
    SIDE_EFFECTING,
    all_args_text,
    contains_secret_marker,
    contains_sensitive_token,
    has_recent_untrusted,
    is_private_network_call,
    is_sensitive_path,
    path_arg,
)


class Guardrail(GuardrailBase):
    """Stateless, cheap and conservative public-compatible reference monitor.

    Differences from public ``optimal.py``:
    - scans all argument values instead of only the first matching key;
    - uses token boundaries rather than raw substring ``"key" in value``;
    - removes authorization keys that the harness never supplies;
    - applies canonical/sensitive path and private-network checks explicitly.
    """

    def decide(self, tool_name: str, tool_args: Mapping[str, Any], context: Mapping[str, Any]) -> Decision:
        if is_private_network_call(tool_name, tool_args):
            return Decision.deny("private network destination")

        if tool_name in {"fs.read", "fs.write", "fs.delete"} and is_sensitive_path(path_arg(tool_args)):
            return Decision.deny(f"sensitive filesystem target: {path_arg(tool_args)!r}")

        if contains_secret_marker(tool_args):
            return Decision.deny("explicit secret marker in tool arguments")

        if contains_sensitive_token(all_args_text(tool_args)):
            return Decision.deny("sensitive token in tool arguments")

        side_effect = str(context.get("side_effect", "")).upper()
        if side_effect in SIDE_EFFECTING and has_recent_untrusted(context):
            return Decision.deny(f"recent untrusted source cannot influence {tool_name}")

        return Decision.allow("fixed-window policy allows operation")
