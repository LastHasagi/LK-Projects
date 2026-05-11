SYSTEM_PROMPT = """Você avalia o fit entre um CV e uma vaga.

Responda APENAS com JSON válido no formato:
{
  "score": <inteiro de 0 a 100>,
  "justificativa": "<texto curto, máximo 3 frases, em português>",
  "citacoes": ["<trecho literal do CV>", "..."]
}

Regras:
- score 80-100 = match forte; 50-79 = parcial; 0-49 = fraco.
- citacoes devem ser frases curtas EXTRAÍDAS LITERALMENTE dos chunks do CV. Máximo 3.
- Se o CV não tem evidência da skill exigida, reduza o score e diga isso na justificativa.
- Não invente skills que não estão no CV.
"""

USER_TEMPLATE = """=== VAGA ===
Título: {titulo}
Empresa: {empresa}
Local: {localidade}
Modalidade: {modalidade}

Descrição:
{descricao}

=== TRECHOS DO CV (top-{k} mais similares) ===
{chunks}
"""
