"""r192の平均応答速度順をexp021へ適用してexp025を生成する。"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import sys
import textwrap
import zlib
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "experiments/exp021/attack.py"
PAYLOAD = REPO_ROOT / "benchmarks/scripts/colab_a100/results/r192_exp021_candidate_orders_payload.json"
DESTINATION = REPO_ROOT / "experiments/exp025"


def _load_attack() -> ModuleType:
    sdk_root = REPO_ROOT / "vendor/aicomp_sdk_pkg"
    sys.path.insert(0, str(sdk_root))
    spec = importlib.util.spec_from_file_location("_exp021_attack", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode_order(encoded: str) -> tuple[str, ...]:
    metadata = json.loads(base64.b64decode(encoded))
    order = tuple(zlib.decompress(base64.b85decode(metadata["payload"])).decode("ascii").splitlines())
    digest = hashlib.sha256("\n".join(order).encode("ascii")).hexdigest()
    if metadata["count"] != len(order) or metadata["sha256"] != digest:
        raise RuntimeError("r192 order payload checksum mismatch")
    return order


def _literal_chunks(value: str, width: int = 100) -> str:
    chunks = textwrap.wrap(value, width=width)
    return "(\n" + "".join(f'    "{chunk}"\n' for chunk in chunks) + ")"


def _replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"expected one replacement for {pattern!r}, got {count}")
    return updated


def main() -> None:
    payload = json.loads(PAYLOAD.read_text())
    gpt_order = _decode_order(payload["gpt_oss_meta_b64"])
    gemma_order = _decode_order(payload["gemma_4_meta_b64"])
    source_module = _load_attack()
    if len(gpt_order) != 2_000 or len(set(gpt_order)) != 2_000:
        raise RuntimeError("GPT order must contain 2,000 unique recipients")
    if len(gemma_order) != 2_000 or len(set(gemma_order)) != 2_000:
        raise RuntimeError("Gemma order must contain 2,000 unique recipients")
    if set(gpt_order) != set(source_module._GPT_RECIPIENTS):
        raise RuntimeError("GPT recipient set differs from exp021")
    if set(gemma_order) != set(source_module._GEMMA_RECIPIENTS):
        raise RuntimeError("Gemma recipient set differs from exp021")

    gpt_text = "\n".join(gpt_order)
    gemma_text = "\n".join(gemma_order)
    gpt_digest = hashlib.sha256(gpt_text.encode("ascii")).hexdigest()
    gemma_digest = hashlib.sha256(gemma_text.encode("ascii")).hexdigest()
    gpt_bank = base64.b85encode(zlib.compress(gpt_text.encode("ascii"), level=9)).decode("ascii")
    gemma_bank = base64.b64encode(zlib.compress(gemma_text.encode("ascii"), level=9)).decode("ascii")

    attack = SOURCE.read_text()
    attack = _replace_once(
        attack,
        r'\A""".*?"""',
        '"""exp025: exp021の候補集合をr192のN=3平均応答速度順へ並べ替えた1-hop版。\n\n'
        "GPT/Gemmaのプロンプト、2,000候補集合、モデル判定、AttackAlgorithmフローはexp021と同一。\n"
        '候補順だけを、3回すべて正確な候補を優先した平均応答時間の昇順へ変更する。\n"""',
    )
    attack = _replace_once(
        attack,
        r'_GPT_RECIPIENT_BANK_SHA256 = "[0-9a-f]+"',
        f'_GPT_RECIPIENT_BANK_SHA256 = "{gpt_digest}"',
    )
    attack = _replace_once(
        attack,
        r"_GPT_RECIPIENT_BANK_B85 = \(.*?\)\n_GPT_RECIPIENTS_LIST",
        f"_GPT_RECIPIENT_BANK_B85 = {_literal_chunks(gpt_bank)}\n_GPT_RECIPIENTS_LIST",
    )
    attack = _replace_once(
        attack,
        r"_GPT_RECIPIENT_REPLACEMENTS = \{.*?\}\nfor _index, _recipient",
        "_GPT_RECIPIENT_REPLACEMENTS = {}\nfor _index, _recipient",
    )
    attack = _replace_once(
        attack,
        r'_GEMMA_RECIPIENT_BANK_SHA256 = "[0-9a-f]+"',
        f'_GEMMA_RECIPIENT_BANK_SHA256 = "{gemma_digest}"',
    )
    attack = _replace_once(
        attack,
        r"_GEMMA_RECIPIENT_BANK_B64 = \(.*?\)\n+_GEMMA_RECIPIENTS",
        f"_GEMMA_RECIPIENT_BANK_B64 = {_literal_chunks(gemma_bank)}\n\n_GEMMA_RECIPIENTS",
    )

    metadata = {
        "id": "rikitomo0526/ai-agent-security-attack-script-exp025",
        "title": "AI Agent Security - Attack script exp025",
        "code_file": "submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": [],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": ["ai-agent-security-multi-step-tool-attacks"],
        "model_sources": [],
    }
    DESTINATION.mkdir(parents=True, exist_ok=False)
    (DESTINATION / "attack.py").write_text(attack)
    (DESTINATION / "kernel-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(f"created {DESTINATION}; GPT={gpt_digest}; Gemma={gemma_digest}")


if __name__ == "__main__":
    main()
