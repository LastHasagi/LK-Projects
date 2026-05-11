import asyncio
import json
import os
from pathlib import Path

from datasets import Dataset
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import AnswerRelevancy, ContextPrecision, Faithfulness

from app.features.matching.prompts import SYSTEM_PROMPT, USER_TEMPLATE

DATASET = Path(__file__).parent / "datasets" / "matching_golden.jsonl"


async def _gerar_resposta(llm: ChatOpenAI, sample: dict) -> dict:
    chunks_text = "\n---\n".join(sample["cv_chunks"])
    user_msg = USER_TEMPLATE.format(
        titulo=sample["vaga_titulo"],
        empresa="?",
        localidade="?",
        modalidade="?",
        descricao=sample["vaga_descricao"],
        k=len(sample["cv_chunks"]),
        chunks=chunks_text,
    )
    resp = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ])
    raw = resp.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    parsed = json.loads(raw.strip())
    return parsed


async def _main() -> None:
    if not DATASET.exists():
        raise SystemExit(f"Dataset não encontrado: {DATASET}")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY não definida.")

    samples = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)
    eval_llm = LangchainLLMWrapper(llm)

    rows = []
    for s in samples:
        parsed = await _gerar_resposta(llm, s)
        rows.append({
            "user_input": s["vaga_descricao"],
            "retrieved_contexts": s["cv_chunks"],
            "response": parsed.get("justificativa", ""),
            "reference": s["justificativa_esperada"],
        })

    ds = Dataset.from_list(rows)
    metrics = [
        Faithfulness(llm=eval_llm),
        AnswerRelevancy(llm=eval_llm),
        ContextPrecision(llm=eval_llm),
    ]
    result = evaluate(dataset=ds, metrics=metrics)
    print(result)
    out_path = Path(__file__).parent / "report.md"
    out_path.write_text(
        "# Matching Eval Report\n\n"
        f"Examples: {len(rows)}\n\n"
        f"```\n{result}\n```\n",
        encoding="utf-8",
    )
    print(f"Relatório em {out_path}")


if __name__ == "__main__":
    asyncio.run(_main())
