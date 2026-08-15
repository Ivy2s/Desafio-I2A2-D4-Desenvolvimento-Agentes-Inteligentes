from pathlib import Path
from zipfile import ZipFile

from pipeline.data_manager import DataManager


def test_pipeline_loads_zip_and_queries_without_machine_paths(tmp_path: Path):
    zip_path = tmp_path / "dataset.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("items.csv", "id,value\n1,10\n2,20\n")

    manager = DataManager(data_dir=str(tmp_path / "runtime"))
    manager.load(str(zip_path))

    assert manager.query(operation="count", dataset="items")["result"] == 2
    assert manager.query(operation="aggregate", dataset="items", group_by="id", metric="value", aggregation="sum")["result"]
