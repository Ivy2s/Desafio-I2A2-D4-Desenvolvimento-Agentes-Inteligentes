from pathlib import Path

from services.query_service import QueryService
from services.session_registry import SessionRegistry


def main():
    registry = SessionRegistry(".runtime/manual-agent")
    session = registry.create()
    try:
        zip_path = Path(__file__).resolve().parents[1] / "data" / "202401_NFs.zip"
        session.manager.load(str(zip_path))
        registry.register(session)
        result = QueryService(registry).query(
            session.dataset_id,
            "Quais são os 5 fornecedores com maior valor total?",
        )
        print(result.answer)
        print(result.data)
    finally:
        registry.discard(session)


if __name__ == "__main__":
    main()
