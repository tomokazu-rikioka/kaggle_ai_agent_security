"""Hypothesis 3: user-intent and concrete-target-bound capabilities."""

from collections.abc import Mapping
from typing import Any

from aicomp_sdk.guardrails.base import Decision

from guardrails._shared import (
    EXTERNAL_TOOLS,
    SIDE_EFFECTING,
    StatefulGuardrail,
    contains_secret_marker,
    has_explicit_intent,
    is_private_network_call,
    is_sensitive_path,
    path_arg,
    target_is_user_bound,
)


class Guardrail(StatefulGuardrail):
    """Allow consequential work only when the trusted user bound action and target.

    Unlike blanket taint blocking, a user can explicitly request a web-informed action.
    Tool-derived content cannot choose a recipient, URL, path, or command on its own.
    """

    _TARGET_BOUND_TOOLS = {"email.send", "http.post", "fs.write", "fs.delete", "shell.run"}

    def decide(self, tool_name: str, tool_args: Mapping[str, Any], context: Mapping[str, Any]) -> Decision:
        self.observe_context(context)
        self.note_attempt(tool_name)
        last_user = context.get("last_user", "")
        side_effect = str(context.get("side_effect", "")).upper()

        if is_private_network_call(tool_name, tool_args):
            return Decision.deny("private network destination")

        if tool_name in {"fs.write", "fs.delete"} and is_sensitive_path(path_arg(tool_args)):
            return Decision.confirm("destructive change to a sensitive path requires fresh approval")

        if (
            tool_name == "fs.read"
            and is_sensitive_path(path_arg(tool_args))
            and (
                not has_explicit_intent(last_user, "READ") or not target_is_user_bound(tool_name, tool_args, last_user)
            )
        ):
            return Decision.confirm("sensitive read was not explicitly bound by the user")

        if tool_name in EXTERNAL_TOOLS and contains_secret_marker(tool_args):
            return Decision.deny("explicit secret marker cannot leave the trust boundary")

        if self.confidential and tool_name in EXTERNAL_TOOLS:
            return Decision.deny("confidential session data cannot flow to an external sink")

        if side_effect in SIDE_EFFECTING and not has_explicit_intent(last_user, side_effect):
            return Decision.confirm(f"{tool_name} is not aligned with an explicit user action")

        if tool_name in self._TARGET_BOUND_TOOLS and not target_is_user_bound(tool_name, tool_args, last_user):
            return Decision.confirm(f"the user did not bind the concrete target for {tool_name}")

        self.note_allowed_read(tool_name, tool_args)
        return Decision.allow("action and target are bound to the trusted user request")
