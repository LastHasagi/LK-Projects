from contextlib import asynccontextmanager
from typing import Annotated, TypedDict

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    trim_messages,
)
from app.core.llm.models import Role
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.postgres.aio import AsyncPostgresStore

from app.core.config import get_settings
from app.core.llm.client import get_llm
from app.core.logging import get_logger
from app.features.agente.long_term_memory import list_all_facts
from app.features.agente.prompts import SYSTEM_PROMPT
from app.features.agente.tools import AGENT_TOOLS

log = get_logger(__name__)

_graph_state: dict = {}

SUMMARY_THRESHOLD = 30
KEEP_LAST = 15
TRIM_MAX_TOKENS = 8000


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str


def _pg_dsn() -> str:
    raw = get_settings().database_url
    return raw.replace("postgresql+asyncpg://", "postgresql://")


def _format_for_summary(m: BaseMessage) -> str:
    role = m.__class__.__name__.replace("Message", "").lower()
    content = m.content if isinstance(m.content, str) else str(m.content)
    return f"[{role}] {content[:1500]}"


async def _summarizer_node(state: AgentState) -> dict:
    msgs = state["messages"]
    if len(msgs) <= SUMMARY_THRESHOLD:
        return {}
    older = msgs[:-KEEP_LAST]
    if not older:
        return {}

    transcript = "\n".join(_format_for_summary(m) for m in older)
    prior = state.get("summary") or ""
    instr = (
        "Resuma os fatos relevantes da conversa em até 500 tokens. "
        "Foque em: vagas discutidas (empresa+cargo+status), candidaturas em andamento, "
        "preferências/dados do usuário (nome, pretensão salarial, modalidade), "
        "ações pendentes. Português, denso, sem floreios."
    )
    user_payload = (
        (f"Resumo anterior:\n{prior}\n\n" if prior else "")
        + f"Mensagens antigas:\n{transcript}"
    )
    fast = get_llm("FAST")
    resp = await fast.ainvoke(
        [SystemMessage(content=instr), HumanMessage(content=user_payload)]
    )
    new_summary = (
        resp.content if isinstance(resp.content, str) else str(resp.content)
    ).strip()

    removes = [RemoveMessage(id=m.id) for m in older if getattr(m, "id", None)]
    log.info(
        "agent_summary_compaction",
        removed=len(removes),
        kept=KEEP_LAST,
        summary_len=len(new_summary),
    )
    return {"messages": removes, "summary": new_summary}


def _route_after_start(state: AgentState) -> str:
    return "summarizer" if len(state["messages"]) > SUMMARY_THRESHOLD else "agent"


_llm_with_tools_cache: dict[str, object] = {}


def _get_llm_with_tools(role: Role):
    cached = _llm_with_tools_cache.get(role)
    if cached is not None:
        return cached
    bound = get_llm(role).bind_tools(AGENT_TOOLS)
    _llm_with_tools_cache[role] = bound
    return bound


async def _facts_block() -> str:
    store = _graph_state.get("store")
    if store is None:
        return ""
    try:
        facts = await list_all_facts(store)
    except Exception as e:
        log.warning("facts_fetch_failed", error=str(e))
        return ""
    if not facts:
        return ""
    lines = [
        f"- ({f['categoria']}) {f['fato']}"
        for f in facts
        if f.get("fato")
    ]
    if not lines:
        return ""
    return "Fatos persistidos do usuário (use livremente — NÃO chame buscar_fatos_relevantes):\n" + "\n".join(lines)


_SMART_KEYWORDS = (
    "gupy.io",
    "linkedin.com/jobs",
    "rejeitei",
    "reformul",
    "ajusta",
    "ajuste",
    "muda o tom",
    "muda a abordagem",
    "rewrite",
    "redige",
    "estado: revisão de rascunho",
    "rascunho",
    "card",
    "candidatura",
    "manda os",
    "envia os",
    "envia o card",
    "manda o card",
)
_SMART_LEN_THRESHOLD = 300


def _select_role(messages: list[BaseMessage]) -> Role:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            raw = m.content if isinstance(m.content, str) else str(m.content)
            text = raw.strip()
            if len(text) >= _SMART_LEN_THRESHOLD:
                return "SMART"
            lower = text.lower()
            if any(kw in lower for kw in _SMART_KEYWORDS):
                return "SMART"
            return "FAST"
    return "FAST"


async def _agent_node(state: AgentState) -> dict:
    role: Role = _select_role(state["messages"])
    llm = _get_llm_with_tools(role)
    history = trim_messages(
        state["messages"],
        max_tokens=TRIM_MAX_TOKENS,
        strategy="last",
        token_counter=llm,
        include_system=False,
        start_on="human",
        end_on=("human", "tool"),
        allow_partial=False,
    )
    system_msgs: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    summary = state.get("summary")
    extra_context_parts: list[str] = []
    if summary:
        extra_context_parts.append(f"Resumo da conversa anterior:\n{summary}")
    facts_block = await _facts_block()
    if facts_block:
        extra_context_parts.append(facts_block)
    if extra_context_parts:
        system_msgs.append(SystemMessage(content="\n\n".join(extra_context_parts)))
    resp = await llm.ainvoke([*system_msgs, *history])
    usage = getattr(resp, "usage_metadata", None) or {}
    log.info(
        "agent_step",
        role=role,
        history_len=len(history),
        has_summary=bool(summary),
        tool_calls=[tc.get("name") for tc in (getattr(resp, "tool_calls", []) or [])],
        text_len=len(resp.content) if isinstance(resp.content, str) else -1,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=usage.get("total_tokens"),
    )
    return {"messages": [resp]}


def _build_graph_unchecked():
    g = StateGraph(AgentState)
    g.add_node("summarizer", _summarizer_node)
    g.add_node("agent", _agent_node)
    g.add_node("tools", ToolNode(AGENT_TOOLS))
    g.add_conditional_edges(
        START, _route_after_start, {"summarizer": "summarizer", "agent": "agent"}
    )
    g.add_edge("summarizer", "agent")
    g.add_conditional_edges(
        "agent", tools_condition, {"tools": "tools", "__end__": "__end__"}
    )
    g.add_edge("tools", "agent")
    return g


@asynccontextmanager
async def graph_lifespan():
    settings = get_settings()
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key,
    )
    async with (
        AsyncPostgresSaver.from_conn_string(_pg_dsn()) as saver,
        AsyncPostgresStore.from_conn_string(
            _pg_dsn(),
            index={"dims": 1536, "embed": embeddings, "fields": ["fato"]},
        ) as store,
    ):
        await saver.setup()
        await store.setup()
        _graph_state["graph"] = _build_graph_unchecked().compile(
            checkpointer=saver, store=store
        )
        _graph_state["store"] = store
        try:
            yield
        finally:
            _graph_state.pop("graph", None)
            _graph_state.pop("store", None)
            _llm_with_tools_cache.clear()


def get_graph():
    g = _graph_state.get("graph")
    if g is None:
        raise RuntimeError("Graph not initialized — graph_lifespan() must wrap usage.")
    return g
