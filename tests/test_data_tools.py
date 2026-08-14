from tools.data_tools import DataQuery, query_data, describe_data


print("=== DATASETS ===")
print(describe_data().keys())


print("\n=== QUERY ===")

query = DataQuery(
    operation="aggregate",
    dataset="202401_nfs_itens",
    group_by="razao_social_emitente",
    metric="valor_total",
    aggregation="sum",
    sort="valor_total",
    limit=5,
)

result = query_data(query)

print(result)