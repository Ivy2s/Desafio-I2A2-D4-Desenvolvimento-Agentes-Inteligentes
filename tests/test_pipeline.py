from pipeline.data_manager import DataManager


def main():
    manager = DataManager()

    manager.load("/Users/jheni/Desktop/Desafio-I2A2-D4-Desenvolvimento-Agentes-Inteligentes/data/202401_NFs.zip")

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