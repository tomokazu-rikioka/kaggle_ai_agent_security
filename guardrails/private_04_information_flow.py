"""Hypothesis 4: deterministic confidentiality and integrity flow control."""

from collections.abc import Mapping
from typing import Any

from aicomp_sdk.guardrails.base import Decision

from guardrails._shared import (
    EXTERNAL_TOOLS,
    SIDE_EFFECTING,
    StatefulGuardrail,
    contains_secret_marker,
    is_private_network_call,
    is_sensitive_path,
    path_arg,
)


class Guardrail(StatefulGuardrail):
    """A compact FIDES/CaMeL-style dual-label approximation.

    All tool-derived file/web/email data lowers integrity. Sensitive-file access raises
    confidentiality. Low-integrity control cannot invoke a side effect, and confidential
    data cannot flow to external tools. This is strongest but intentionally over-blocks
    workflows because the SDK context exposes neither values nor field-level labels.
    """

    def decide(self, tool_name: str, tool_args: Mapping[str, Any], context: Mapping[str, Any]) -> Decision:
        self.observe_context(context, include_files=True)
        self.note_attempt(tool_name)
        side_effect = str(context.get("side_effect", "")).upper()

        if is_private_network_call(tool_name, tool_args):
            return Decision.deny("private network destination")

        if tool_name in {"fs.write", "fs.delete"} and is_sensitive_path(path_arg(tool_args)):
            return Decision.deny("integrity policy protects sensitive filesystem state")

        if tool_name in EXTERNAL_TOOLS and contains_secret_marker(tool_args):
            return Decision.deny("confidential marker cannot flow to an external sink")

        if self.confidential and tool_name in EXTERNAL_TOOLS:
            return Decision.deny("no-write-down: confidential data to external sink")

        if self.low_integrity and side_effect in SIDE_EFFECTING:
            return Decision.deny(f"no-write-up: low-integrity data cannot influence {tool_name}")

        self.note_allowed_read(tool_name, tool_args, include_files=True)
        return Decision.allow("information-flow policy allows operation")
