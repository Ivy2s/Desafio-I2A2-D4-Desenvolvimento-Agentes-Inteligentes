from pathlib import Path

import pytest

from pipeline.data_manager import DataManager


def test_data_manager_loads_and_lists_a_relative_csv(tmp_path: Path):
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))

    manager.load(str(csv_path))
    metadata = manager.describe()
    result = manager.query(operation="list", dataset="records", limit=5)

    assert metadata["records"]["rows"] == 2
    assert metadata["records"]["columns"] == ["id", "name"]
    assert result["dataset"] == "records"
    assert len(result["result"]) == 2


def test_list_sorts_numeric_values_before_applying_limit(tmp_path: Path):
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("id,value\nA,9\nB,100\nC,20\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    result = manager.query(
        operation="list",
        dataset="records",
        sort="value",
        sort_direction="desc",
        limit=2,
    )

    assert [row["id"] for row in result["result"]] == ["B", "C"]


def test_list_sorts_text_case_insensitively(tmp_path: Path):
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("name\nzulu\nAlpha\nbeta\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    result = manager.query(
        operation="list",
        dataset="records",
        sort="name",
        sort_direction="asc",
    )

    assert [row["name"] for row in result["result"]] == ["Alpha", "beta", "zulu"]


def test_list_rejects_unknown_sort_column(tmp_path: Path):
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("id,value\nA,9\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))
    manager.load(str(csv_path))

    with pytest.raises(ValueError, match="Coluna de ordenacao"):
        manager.query(operation="list", dataset="records", sort="missing")
