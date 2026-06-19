"""ガードレールのレジストリ。

- public     : OptimalGuardrail（公開 LB の実体。public スコアと高相関）
- strict     : guardrail_rules ベースライン（http.post の data 走査・private-net 遮断）
- provenance : 自作の永続来歴ガードレール（非公開 LB の汎化を測る厳しめ代理）
- allow      : 全許可（プラグイン疎通確認・探索の上限把握用。LB とは無関係）

run_validation.py はここから guardrail_factory（引数なしで GuardrailBase を返す callable）
を取り出し、各候補のリプレイ時に新しいインスタンスを生成する。
"""

from __future__ import annotations

from collections.abc import Callable

from aicomp_sdk.attacks.baselines.guardrail_allow import Guardrail as AllowGuardrail
from aicomp_sdk.attacks.baselines.guardrail_rules import Guardrail as StrictGuardrail
from aicomp_sdk.guardrails.base import GuardrailBase
from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail

from validation.provenance_guardrail import Guardrail as ProvenanceGuardrail

GuardrailFactory = Callable[[], GuardrailBase]

GUARDRAILS: dict[str, GuardrailFactory] = {
    "public": OptimalGuardrail,
    "strict": StrictGuardrail,
    "provenance": ProvenanceGuardrail,
    "allow": AllowGuardrail,
}

# public は公開 LB と相関する本命。strict/provenance は非公開汎化の代理。
DEFAULT_GUARDRAILS = ["public"]


def get_guardrail_factory(name: str) -> GuardrailFactory:
    try:
        return GUARDRAILS[name]
    except KeyError:
        raise ValueError(
            f"未知のガードレール '{name}'。選択肢: {', '.join(GUARDRAILS)}"
        ) from None
