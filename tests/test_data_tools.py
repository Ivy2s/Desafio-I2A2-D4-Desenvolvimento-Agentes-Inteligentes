from pathlib import Path

import pytest

from tools.data_tools import DataQuery, describe_data, query_data
from pipeline.data_manager import DataManager


def test_data_tools_use_the_provided_manager(tmp_path: Path):
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("name,value\nAlice,10\nBob,20\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    assert list(describe_data(manager)) == ["records"]
    result = query_data(
        DataQuery(operation="aggregate", dataset="records", group_by="name", metric="value", aggregation="sum"),
        manager,
    )
    assert result["dataset"] == "records"
    assert len(result["result"]) == 2


def test_data_query_normalizes_numeric_string_limit():
    query = DataQuery(operation="list", dataset="records", limit="1")

    assert query.limit == 1


def test_data_query_normalizes_natural_language_aggregations():
    query = DataQuery(
        operation="agregação",
        dataset="records",
        group_by="name",
        metric="value",
        aggregation="soma",
    )

    assert query.operation == "aggregate"
    assert query.aggregation == "sum"


def test_data_query_normalizes_maximum_alias():
    query = DataQuery(
        operation="aggregate",
        dataset="records",
        group_by="name",
        metric="value",
        aggregation="maior",
    )

    assert query.aggregation == "max"


@pytest.fixture
def ranking_manager(tmp_path: Path) -> DataManager:
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "supplier,value\n"
        "A,100\n"
        "A,50\n"
        "B,200\n"
        "C,75\n"
        "D,25\n"
        "E,10\n"
        "F,5\n"
        "G,1\n"
        "H,2\n"
        "I,3\n"
        "J,4\n",
        encoding="utf-8",
    )
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))
    return manager


@pytest.mark.parametrize("limit", [1, 3, 5, 10])
def test_ranking_applies_limit_after_aggregation(
    ranking_manager: DataManager, limit: int
):
    result = query_data(
        DataQuery(
            operation="aggregate",
            dataset="sales",
            group_by="supplier",
            metric="value",
            aggregation="sum",
            sort="value",
            limit=limit,
        ),
        ranking_manager,
    )

    assert len(result["result"]) == limit
    assert result["returned_rows"] == limit
    assert [row["supplier"] for row in result["result"]] == [
        "B", "A", "C", "D", "E", "F", "J", "I", "H", "G"
    ][:limit]


def test_ranking_supports_ascending_order(ranking_manager: DataManager):
    result = query_data(
        DataQuery(
            operation="aggregate",
            dataset="sales",
            group_by="supplier",
            metric="value",
            aggregation="sum",
            sort="value",
            sort_direction="asc",
            limit=3,
        ),
        ranking_manager,
    )

    assert [(row["supplier"], row["value"]) for row in result["result"]] == [
        ("G", 1.0),
        ("H", 2.0),
        ("I", 3.0),
    ]


def test_ranking_returns_fewer_rows_when_dataset_has_fewer_groups(
    ranking_manager: DataManager,
):
    result = query_data(
        DataQuery(
            operation="aggregate",
            dataset="sales",
            group_by="supplier",
            metric="value",
            aggregation="sum",
            sort="value",
            limit=100,
        ),
        ranking_manager,
    )

    assert len(result["result"]) == 10
    assert result["truncated"] is False


def test_executor_rejects_invalid_limit(ranking_manager: DataManager):
    with pytest.raises(ValueError, match="inteiro positivo"):
        ranking_manager.query(
            operation="aggregate",
            dataset="sales",
            group_by="supplier",
            metric="value",
            aggregation="sum",
            sort="value",
            limit=0,
        )


def test_maximum_value_ranking_orders_by_metric_not_group_name(
    ranking_manager: DataManager,
):
    result = ranking_manager.query(
        operation="aggregate",
        dataset="sales",
        group_by="supplier",
        metric="value",
        aggregation="max",
        sort="supplier",
        sort_direction="asc",
        limit=1,
    )

    assert result["result"] == [{"supplier": "B", "value": 200.0}]


def test_aggregate_rejects_a_metric_with_no_numeric_values(tmp_path: Path):
    csv_path = tmp_path / "invalid-values.csv"
    csv_path.write_text("supplier,value\nA,not-a-number\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    with pytest.raises(ValueError, match="valores numéricos válidos"):
        manager.query(
            operation="aggregate",
            dataset="invalid-values",
            group_by="supplier",
            metric="value",
            aggregation="max",
            limit=1,
        )


def test_aggregate_parses_brazilian_decimal_values(tmp_path: Path):
    csv_path = tmp_path / "brazilian-values.csv"
    # The CSV uses a semicolon so the decimal comma remains part of the value.
    csv_path.write_text(
        "supplier;value\nA;4.603,42\nB;10.000,00\n",
        encoding="utf-8",
    )
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    result = manager.query(
        operation="aggregate",
        dataset="brazilian-values",
        group_by="supplier",
        metric="value",
        aggregation="max",
        sort="value",
        limit=1,
    )

    assert result["result"] == [{"supplier": "B", "value": 10000.0}]


@pytest.mark.parametrize("invalid_limit", [0, -1, "not-a-number", 1001])
def test_ranking_rejects_invalid_or_excessive_limit(invalid_limit):
    with pytest.raises((ValueError, TypeError)):
        DataQuery(operation="aggregate", dataset="sales", limit=invalid_limit)
