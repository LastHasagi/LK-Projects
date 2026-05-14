from app.features.agente.tools import (
    AGENT_TOOLS,
    _validate_fato,
)


def test_enviar_candidatura_por_email_not_exposed_to_agent():
    """Garantia de que envio direto não está disponível para o LLM.
    Único caminho é via preparar_envio_email_confirmacao + botão Aprovar."""
    tool_names = {t.name for t in AGENT_TOOLS}
    assert "enviar_candidatura_por_email" not in tool_names
    assert "preparar_envio_email_confirmacao" in tool_names


def test_validate_fato_rejects_composite():
    err = _validate_fato(
        "pretensão R$ 13.000 CLT e R$ 17.000 PJ", "compensacao_disponibilidade"
    )
    assert err is not None
    assert "composto" in err.lower()


def test_validate_fato_rejects_compensacao_without_signal():
    err = _validate_fato("gosto de café", "compensacao_disponibilidade")
    assert err is not None


def test_validate_fato_accepts_compensacao_with_value():
    assert _validate_fato("pretensão R$ 13.000 PJ", "compensacao_disponibilidade") is None


def test_validate_fato_accepts_modalidade_only():
    assert _validate_fato("modalidade preferida remoto", "compensacao_disponibilidade") is None


def test_validate_fato_accepts_candidato_simple():
    assert _validate_fato("nome completo Rodrigo Graça", "candidato") is None


def test_agent_tools_contains_expected_set():
    names = {t.name for t in AGENT_TOOLS}
    expected = {
        "buscar_vagas_semantica",
        "explicar_fit",
        "listar_candidaturas_em_andamento",
        "iniciar_busca_vagas",
        "extrair_emails_do_texto",
        "preparar_envio_email_confirmacao",
        "candidatar_a_vaga",
        "traduzir_cv_para_idioma",
        "salvar_fato_usuario",
    }
    assert names == expected
