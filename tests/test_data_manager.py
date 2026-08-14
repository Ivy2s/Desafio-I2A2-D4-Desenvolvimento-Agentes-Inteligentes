from pipeline.data_manager import DataManager


dm = DataManager()
dm.load()

print("\n=== DATASETS DISPONÍVEIS ===")
metadata = dm.describe()

for dataset, info in metadata.items():
    print(f"\nDataset: {dataset}")
    print(f"Linhas: {info['rows']}")
    print(f"Colunas: {info['columns']}")


print("\n=== TESTE DE QUERY ===")

dataset = list(metadata.keys())[0]

columns = metadata[dataset]["columns"]

print(f"Dataset selecionado: {dataset}")
print(f"Primeira coluna disponível: {columns[0]}")


result = dm.query(
    operation="list",
    dataset=dataset,
    limit=5
)

print("\nResultado:")
print(result)