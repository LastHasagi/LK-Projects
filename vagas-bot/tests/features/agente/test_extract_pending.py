from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.core.pending_email import EMAIL_CONFIRM_PENDING_PREFIX
from app.features.agente.email_handlers import (
    extract_pending_email_uuid_from_messages,
)


def test_returns_uid_when_tool_ran_in_current_turn():
    msgs = [
        HumanMessage(content="vaga..."),
        AIMessage(content=""),
        ToolMessage(content=f"{EMAIL_CONFIRM_PENDING_PREFIX}abc123", tool_call_id="t1"),
        AIMessage(content="rascunho pronto"),
    ]
    assert extract_pending_email_uuid_from_messages(msgs) == "abc123"


def test_ignores_uid_from_previous_turn():
    msgs = [
        HumanMessage(content="vaga antiga"),
        AIMessage(content=""),
        ToolMessage(content=f"{EMAIL_CONFIRM_PENDING_PREFIX}OLD_UID", tool_call_id="t1"),
        AIMessage(content="ok"),
        HumanMessage(content="me mostra outras vagas"),
        AIMessage(content="aqui"),
    ]
    assert extract_pending_email_uuid_from_messages(msgs) is None


def test_returns_none_when_no_tool_call():
    msgs = [
        HumanMessage(content="oi"),
        AIMessage(content="oi"),
    ]
    assert extract_pending_email_uuid_from_messages(msgs) is None
