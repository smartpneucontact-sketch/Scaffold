from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from case_pilot.rag.retriever import Retriever


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., Any]

    def to_anthropic(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


class ToolRegistry:
    def __init__(self, tools: list[ToolSpec] | None = None):
        self._tools: dict[str, ToolSpec] = {}
        for t in tools or []:
            self.register(t)

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def to_anthropic(self) -> list[dict[str, Any]]:
        return [t.to_anthropic() for t in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            return {"error": f"unknown tool: {name}"}
        try:
            return self._tools[name].fn(**arguments)
        except TypeError as e:
            return {"error": f"bad arguments for {name}: {e}"}
        except Exception as e:  # pragma: no cover
            return {"error": f"{name} raised: {type(e).__name__}: {e}"}


def _make_retrieve_tool(retriever: Retriever) -> ToolSpec:
    def retrieve(query: str, k: int = 6, source_type: str | None = None) -> dict[str, Any]:
        filters = {"source_type": source_type} if source_type else None
        results = retriever.search(query, k=k, filters=filters)
        return {
            "results": [
                {
                    "chunk_id": r.chunk.chunk_id,
                    "source_type": r.chunk.source_type,
                    "source_id": r.chunk.source_id,
                    "section": r.chunk.section,
                    "score": round(r.score, 3),
                    "text": r.chunk.text,
                }
                for r in results
            ],
            "count": len(results),
        }

    return ToolSpec(
        name="retrieve",
        description=(
            "Search the icotec product and compliance corpus (specs, indications-for-use, surgical "
            "technique guides, prior cases, regulatory documents) for context relevant to a surgical "
            "case. Always call this BEFORE drafting case recommendations. Returns chunks with their "
            "source so you can cite each claim precisely."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language search query."},
                "k": {"type": "integer", "default": 6, "description": "Max results (1-12)."},
                "source_type": {
                    "type": "string",
                    "enum": ["spec", "indications", "surgical_technique", "case", "compliance"],
                    "description": "Optional filter to one source type.",
                },
            },
            "required": ["query"],
        },
        fn=retrieve,
    )


def _check_imaging_benefit() -> ToolSpec:
    """Heuristic: rate the imaging-benefit of using radiolucent implants for a case."""
    def check_imaging_benefit(
        oncology: bool = False,
        post_op_radiation: bool = False,
        post_op_mri_planned: bool = False,
        pediatric: bool = False,
    ) -> dict[str, Any]:
        score = 0
        if oncology:
            score += 2
        if post_op_radiation:
            score += 2
        if post_op_mri_planned:
            score += 1
        if pediatric:
            score += 1
        if score >= 3:
            band = "high"
        elif score >= 1:
            band = "medium"
        else:
            band = "low"
        return {
            "benefit_band": band,
            "score": score,
            "rationale": (
                f"oncology={oncology}, post_op_radiation={post_op_radiation}, "
                f"post_op_mri_planned={post_op_mri_planned}, pediatric={pediatric}"
            ),
        }

    return ToolSpec(
        name="check_imaging_benefit",
        description=(
            "Rate the imaging benefit of selecting radiolucent BlackArmor implants over a "
            "titanium alternative for this case. High benefit cases are the strongest "
            "indications for icotec's products."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "oncology": {"type": "boolean", "default": False},
                "post_op_radiation": {"type": "boolean", "default": False},
                "post_op_mri_planned": {"type": "boolean", "default": False},
                "pediatric": {"type": "boolean", "default": False},
            },
            "required": [],
        },
        fn=check_imaging_benefit,
    )


def _classify_complexity() -> ToolSpec:
    def classify_case_complexity(
        levels: int = 1,
        revision: bool = False,
        osteoporosis: bool = False,
        deformity: bool = False,
    ) -> dict[str, Any]:
        score = 0
        score += max(0, levels - 1)
        if revision:
            score += 2
        if osteoporosis:
            score += 1
        if deformity:
            score += 2
        if score >= 4:
            band = "high"
        elif score >= 2:
            band = "medium"
        else:
            band = "low"
        return {
            "complexity_band": band,
            "score": score,
            "rationale": (
                f"levels={levels}, revision={revision}, osteoporosis={osteoporosis}, deformity={deformity}"
            ),
        }

    return ToolSpec(
        name="classify_case_complexity",
        description="Classify surgical case complexity from level count, revision status, bone quality, and deformity.",
        input_schema={
            "type": "object",
            "properties": {
                "levels": {"type": "integer", "default": 1, "description": "Number of spinal levels instrumented."},
                "revision": {"type": "boolean", "default": False},
                "osteoporosis": {"type": "boolean", "default": False},
                "deformity": {"type": "boolean", "default": False},
            },
            "required": [],
        },
        fn=classify_case_complexity,
    )


def build_case_tools(retriever: Retriever) -> ToolRegistry:
    return ToolRegistry(tools=[
        _make_retrieve_tool(retriever),
        _check_imaging_benefit(),
        _classify_complexity(),
    ])
