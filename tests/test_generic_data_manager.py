from pipeline.data_manager import DataManager


dm = DataManager()
dm.load()

metadata = dm.describe()

print("\n=== TESTE GENÉRICO ===")

for dataset, info in metadata.items():

    print(f"\nDataset: {dataset}")
    print(f"Linhas: {info['rows']}")

    columns = info["columns"]

    # Teste 1: dataset possui schema
    assert len(columns) > 0

    # Teste 2: list funciona sem conhecer previamente as colunas
    result = dm.query(
        operation="list",
        dataset=dataset,
        limit=3
    )

    assert result["dataset"] == dataset
    assert len(result["result"]) <= 3

    print("✓ list OK")

print("\n=== TODOS OS TESTES PASSARAM ===")