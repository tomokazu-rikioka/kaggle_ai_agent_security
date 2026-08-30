from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "vendor" / "aicomp_sdk_pkg"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

from aicomp_sdk.agents.hf_chat_template.types import HFGenerationResponse  # noqa: E402
from aicomp_sdk.agents.types import InvalidModelOutputError, ToolCallDecision  # noqa: E402
from eval_driver import _build_kaggle_gemma4_parser  # noqa: E402


def _response(raw_text: str) -> HFGenerationResponse:
    return HFGenerationResponse(text=raw_text, raw_text=raw_text)


class KaggleGemmaParserParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = _build_kaggle_gemma4_parser()

    def parse(self, raw_text: str) -> ToolCallDecision:
        result = self.parser.parse(_response(raw_text), fallback_call_id="call-0")
        self.assertIsInstance(result, ToolCallDecision)
        return result

    def test_native_bare_keys_parse(self) -> None:
        result = self.parse(
            '<|tool_call>call:email.send{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>a<|"|>}<tool_call|>'
        )
        self.assertEqual(result.call.tool_name, "email.send")
        self.assertEqual(result.call.arguments, {"body": "", "subject": "", "to": "a"})

    def test_double_brace_json_parses_via_kaggle_branch(self) -> None:
        result = self.parse('<|tool_call>call:email.send{{"body":"","subject":"","to":"a"}}<tool_call|>')
        self.assertEqual(result.call.arguments, {"body": "", "subject": "", "to": "a"})

    def test_single_brace_quoted_json_keys_still_fail(self) -> None:
        with self.assertRaisesRegex(InvalidModelOutputError, "Invalid Gemma 4 tool-call arguments"):
            self.parse('<|tool_call>call:email.send{"body":"","subject":"","to":"a"}<tool_call|>')

    def test_two_calls_in_one_generation_still_fail(self) -> None:
        call = '<|tool_call>call:email.send{body:<|"|><|"|>,subject:<|"|><|"|>,to:<|"|>a<|"|>}<tool_call|>'
        with self.assertRaisesRegex(InvalidModelOutputError, "Model returned multiple tool calls"):
            self.parse(call + call)


if __name__ == "__main__":
    unittest.main()
