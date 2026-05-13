from contextlib import asynccontextmanager
from typing import Annotated, TypedDict

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    trim_messages,
)
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.postgres.aio import AsyncPostgresStore

from app.core.config import get_settings
from app.core.llm.client import get_llm
from app.core.logging import get_logger
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


async def _agent_node(state: AgentState) -> dict:
    llm = get_llm("SMART").bind_tools(AGENT_TOOLS)
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
    if summary:
        system_msgs.append(
            SystemMessage(content=f"Resumo da conversa anterior:\n{summary}")
        )
    resp = await llm.ainvoke([*system_msgs, *history])
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
        try:
            yield
        finally:
            _graph_state.pop("graph", None)


def get_graph():
    g = _graph_state.get("graph")
    if g is None:
        raise RuntimeError("Graph not initialized — graph_lifespan() must wrap usage.")
    return g
