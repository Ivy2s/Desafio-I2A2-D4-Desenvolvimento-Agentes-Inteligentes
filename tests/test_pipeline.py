from pipeline.data_manager import DataManager
from pathlib import Path


def main():
    manager = DataManager()

    zip_path = Path(__file__).resolve().parents[1] / "data" / "202401_NFs.zip"
    manager.load(str(zip_path))

    print("\n=== DATASETS ===")
    print(manager.datasets.keys())

    print("\n=== DESCRIÇÃO ===")
    print(manager.describe())

    print("\n=== CONSULTA ===")

    result = manager.query(
        operation="count",
        dataset="202401_nfs_itens"
    )

    print(result)

    print("\n=== RANKING ===")

    result = manager.query(
        operation="aggregate",
        dataset="202401_nfs_itens",
        group_by="razao_social_emitente",
        metric="valor_total",
        aggregation="sum",
        sort="valor_total",
        limit=5
    )

    print(result)


if __name__ == "__main__":
    main()
