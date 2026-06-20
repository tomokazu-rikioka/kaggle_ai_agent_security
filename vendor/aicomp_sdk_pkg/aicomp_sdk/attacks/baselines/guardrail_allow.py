from aicomp_sdk.guardrails.base import Decision, GuardrailBase


class Guardrail(GuardrailBase):
    def decide(self, tool_name, tool_args, context):
        return Decision.allow("allow all")
