from pathlib import Path

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
