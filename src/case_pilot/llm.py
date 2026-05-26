from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int
    raw: Any = None


_PRICING = {
    "claude-opus-4-7": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (0.80, 4.0),
}


def estimate_cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    for key, (pin, pout) in _PRICING.items():
        if model.startswith(key):
            return (in_tokens / 1_000_000) * pin + (out_tokens / 1_000_000) * pout
    return (in_tokens / 1_000_000) * 3.0 + (out_tokens / 1_000_000) * 15.0


class LLMClient:
    """Anthropic client with mock-mode fallback. Same shape as the Site
    Copilot client so swapping to Azure OpenAI or Bedrock is a constructor
    change, not a refactor."""

    def __init__(self, *, api_key: str | None, model: str, use_mock: bool = False):
        self.model = model
        self.use_mock = use_mock or os.environ.get("CASE_PILOT_USE_MOCK_LLM") == "1"
        self._client: Anthropic | None = None
        if not self.use_mock and not api_key:
            print(
                "[case-pilot] WARNING: ANTHROPIC_API_KEY not set; falling back to mock mode. "
                "Set the key for live Claude responses.",
                flush=True,
            )
            self.use_mock = True
        if not self.use_mock:
            self._client = Anthropic(api_key=api_key)

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if self.use_mock:
            return self._mock_complete(system=system, messages=messages, tools=tools)

        assert self._client is not None
        kwargs: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        resp = self._client.messages.create(**kwargs)
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "input": block.input})

        return LLMResponse(
            text="\n".join(text_parts).strip(),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason or "",
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            raw=resp,
        )

    def _mock_complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> LLMResponse:
        # If we have tools and haven't used one yet, call retrieve first.
        already_used_tool = any(
            isinstance(msg.get("content"), list)
            and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in msg["content"])
            for msg in messages
        )
        if tools and not already_used_tool:
            return LLMResponse(
                text="",
                tool_calls=[{
                    "id": "toolu_mock_retrieve",
                    "name": "retrieve",
                    "input": {"query": "BlackArmor pedicle screw indications oncology", "k": 6},
                }],
                stop_reason="tool_use",
                input_tokens=420,
                output_tokens=18,
            )

        draft = {
            "case_summary": (
                "55F with T8 metastatic breast carcinoma involving the posterior vertebral elements. "
                "Indication for posterior instrumented fusion T6-T10 with planned post-op radiation. "
                "(Mock response.)"
            ),
            "indications_check": [
                {"item": "Posterior spinal fixation, T1-S1", "ok": True,
                 "source": "indications:blackarmor_pedicle_screws_ifu"},
                {"item": "Oncology with post-op radiation/imaging needs", "ok": True,
                 "source": "indications:blackarmor_pedicle_screws_ifu"},
            ],
            "recommended_configuration": {
                "construct": "T6-T10 posterior instrumented fusion",
                "screws": "BlackArmor pedicle screws 6.0 x 45 mm (T6-T10, bilateral, 10 screws)",
                "rods": "BlackArmor CFR-PEEK rods, 5.5 mm, length pending intraop measurement",
                "rationale": "Radiolucent construct preserves post-op imaging quality for tumor surveillance and radiation planning.",
            },
            "imaging_benefit": "high — patient has post-op radiation planned at 4 weeks; titanium artifact would significantly degrade MR/CT image quality.",
            "compliance_flags": [
                {"category": "MDR/FDA", "status": "ok",
                 "note": "Indication matches IFU; no off-label use."},
            ],
            "open_questions": [
                "Confirm bone quality (T-score) — if severe osteoporosis, consider cement augmentation.",
                "Verify levels with intraop fluoroscopy and surgeon's preop plan.",
            ],
            "needs_clinical_specialist_review": False,
        }
        return LLMResponse(
            text=json.dumps(draft, indent=2),
            tool_calls=[],
            stop_reason="end_turn",
            input_tokens=1100,
            output_tokens=240,
        )
