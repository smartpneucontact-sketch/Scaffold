from __future__ import annotations

import json
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from case_pilot.api.deps import AppState, build_app_state
from case_pilot.notifications import diagnostic_status, maybe_notify_visitor, send_test_email

_STATIC_DIR = Path(__file__).resolve().parent.parent / "ui" / "static"
_SAMPLES_DIR = Path("data/samples")


class CasePayload(BaseModel):
    case_id: str
    submitted_by: str | None = None
    date: str | None = None
    site: str | None = None
    description: str = Field(..., description="Free-text surgical case description")


class AgentResponse(BaseModel):
    run_id: str
    parsed: dict[str, Any] | None
    final_text: str
    steps: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_invocations: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_state = build_app_state()
    yield


app = FastAPI(
    title="Case Pilot",
    version="0.1.0",
    description=(
        "AI-assisted surgical case intake and radiolucent implant configuration. "
        "Portfolio demo for icotec medical (Digitalization & AI Professional)."
    ),
    lifespan=lifespan,
)


@app.middleware("http")
async def site_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and request.url.path == "/":
        try:
            await maybe_notify_visitor(request, request.url.path)
        except Exception as e:
            print(f"[case-pilot] visitor notify error: {e}", flush=True)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _state(request: Request) -> AppState:
    return request.app.state.app_state


@app.get("/healthz")
def healthz(request: Request) -> dict[str, Any]:
    s = _state(request)
    return {
        "status": "ok",
        "model": s.settings.model,
        "corpus_chunks": s.retriever.size(),
        "use_mock_llm": s.case_agent.llm.use_mock,
    }


@app.get("/api", include_in_schema=False)
def api_info(request: Request) -> dict[str, Any]:
    s = _state(request)
    return {
        "service": "Case Pilot",
        "version": "0.1.0",
        "description": "AI-assisted surgical case intake and radiolucent implant configuration for icotec medical.",
        "endpoints": {
            "GET /": "HTML UI",
            "POST /agents/case/intake": "Triage a surgical case description",
            "GET /healthz": "Liveness + model status",
            "GET /api/samples/cases": "Sample surgical cases",
        },
        "mode": "MOCK" if s.case_agent.llm.use_mock else f"LIVE ({s.settings.model})",
    }


@app.get("/api/samples/cases", include_in_schema=False)
def sample_cases() -> list[dict[str, Any]]:
    p = _SAMPLES_DIR / "case_inbox.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/notify/diag", include_in_schema=False)
def notify_diag() -> dict[str, Any]:
    return diagnostic_status()


@app.post("/api/notify/test", include_in_schema=False)
async def notify_test() -> dict[str, Any]:
    return await send_test_email()


@app.post("/agents/case/intake", response_model=AgentResponse)
def case_intake(payload: CasePayload, request: Request) -> AgentResponse:
    s = _state(request)
    try:
        result = s.case_agent.run_case(payload.model_dump())
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[case-pilot] case intake failed: {type(e).__name__}: {e}\n{tb}", flush=True)
        raise HTTPException(
            status_code=500,
            detail={"error": type(e).__name__, "message": str(e), "agent": "case_intake"},
        )
    return AgentResponse(
        run_id=result.run_id,
        parsed=result.parsed,
        final_text=result.final_text,
        steps=result.steps,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=round(result.cost_usd, 6),
        tool_invocations=result.tool_invocations,
    )


if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")
