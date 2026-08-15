from pathlib import Path

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
