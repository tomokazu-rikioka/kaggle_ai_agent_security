"""Stable names used by the local replay evaluator."""

from collections.abc import Callable

from aicomp_sdk.guardrails.base import GuardrailBase

from guardrails.private_01_public_fixed import Guardrail as PublicFixedGuardrail
from guardrails.private_02_persistent_provenance import Guardrail as PersistentProvenanceGuardrail
from guardrails.private_03_intent_bound import Guardrail as IntentBoundGuardrail
from guardrails.private_04_information_flow import Guardrail as InformationFlowGuardrail
from guardrails.private_05_risk_adaptive import Guardrail as RiskAdaptiveGuardrail

GuardrailFactory = Callable[[], GuardrailBase]

GUARDRAIL_FACTORIES: dict[str, GuardrailFactory] = {
    "private01_fixed": PublicFixedGuardrail,
    "private02_provenance": PersistentProvenanceGuardrail,
    "private03_intent": IntentBoundGuardrail,
    "private04_ifc": InformationFlowGuardrail,
    "private05_risk": RiskAdaptiveGuardrail,
}

__all__ = ["GUARDRAIL_FACTORIES"]
