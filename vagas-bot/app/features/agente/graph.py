from contextlib import asynccontextmanager

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import get_settings
from app.core.llm.client import get_llm
from app.features.agente.prompts import SYSTEM_PROMPT
from app.features.agente.tools import AGENT_TOOLS

_graph_state: dict = {}


def _pg_dsn() -> str:
    raw = get_settings().database_url
    return raw.replace("postgresql+asyncpg://", "postgresql://")


async def _agent_node(state: MessagesState):
    llm = get_llm("FAST").bind_tools(AGENT_TOOLS)
    msgs = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    resp = await llm.ainvoke(msgs)
    return {"messages": [resp]}


def _build_graph_unchecked():
    g = StateGraph(MessagesState)
    g.add_node("agent", _agent_node)
    g.add_node("tools", ToolNode(AGENT_TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "__end__"})
    g.add_edge("tools", "agent")
    return g


@asynccontextmanager
async def graph_lifespan():
    async with AsyncPostgresSaver.from_conn_string(_pg_dsn()) as saver:
        await saver.setup()
        _graph_state["graph"] = _build_graph_unchecked().compile(checkpointer=saver)
        try:
            yield
        finally:
            _graph_state.pop("graph", None)


def get_graph():
    g = _graph_state.get("graph")
    if g is None:
        raise RuntimeError("Graph not initialized — graph_lifespan() must wrap usage.")
    return g
