from __future__ import annotations

from dataclasses import dataclass

from case_pilot.agents import CaseAgent
from case_pilot.config import Settings, get_settings
from case_pilot.llm import LLMClient
from case_pilot.observability import Tracer
from case_pilot.rag.ingest import build_retriever
from case_pilot.rag.retriever import Retriever
from case_pilot.tools import build_case_tools


@dataclass
class AppState:
    settings: Settings
    retriever: Retriever
    tracer: Tracer
    case_agent: CaseAgent


def build_app_state() -> AppState:
    settings = get_settings()
    retriever = build_retriever()
    llm = LLMClient(api_key=settings.anthropic_api_key, model=settings.model, use_mock=settings.use_mock_llm)
    tracer = Tracer(settings.traces_dir)
    case_agent = CaseAgent(
        llm=llm, tools=build_case_tools(retriever), tracer=tracer, max_steps=settings.max_agent_steps,
    )
    return AppState(settings=settings, retriever=retriever, tracer=tracer, case_agent=case_agent)
