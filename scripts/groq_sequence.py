"""Run the controlled four-query sequence in one process through QueryService."""

import json
import logging
import os
from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["AI_PROVIDER"] = "groq"
os.environ["GROQ_MODEL"] = "openai/gpt-oss-20b"

from services.query_service import QueryService  # noqa: E402
from services.session_registry import SessionRegistry  # noqa: E402


QUESTIONS = (
    "Qual produto apresentou o maior volume comprado?",
    "Qual foi o total gasto no período?",
    "Quais foram os cinco maiores fornecedores?",
    "Qual foi o valor médio por item comprado?",
)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    source = Path("data/202401_NFs_Itens.csv")
    with tempfile.TemporaryDirectory(prefix="groq-sequence-") as root:
        registry = SessionRegistry(root)
        session = registry.create()
        session.manager.load(str(source))
        registry.register(session)
        service = QueryService(registry)
        report = []
        for index, question in enumerate(QUESTIONS, start=1):
            try:
                result = service.query(session.dataset_id, question)
                report.append(
                    {
                        "query": index,
                        "question": question,
                        "status": "success",
                        "answer": result.answer,
                        "telemetry": result.telemetry,
                    }
                )
            except Exception as error:
                report.append(
                    {
                        "query": index,
                        "question": question,
                        "status": "error",
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "details": error.details() if hasattr(error, "details") else None,
                    }
                )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if all(item["status"] == "success" for item in report) else 1


if __name__ == "__main__":
    sys.exit(main())
