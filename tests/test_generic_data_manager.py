from pathlib import Path

from pipeline.data_manager import DataManager


def test_data_manager_discovers_multiple_datasets_without_fixed_names(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "first.csv").write_text("id\n1\n", encoding="utf-8")
    (data_dir / "second.csv").write_text("label\nA\n", encoding="utf-8")
    manager = DataManager(data_dir=str(data_dir))

    metadata = manager.load()

    assert set(metadata) == {"first", "second"}
    for dataset, info in manager.describe().items():
        assert info["columns"]
        result = manager.query(operation="list", dataset=dataset, limit=3)
        assert result["dataset"] == dataset
        assert len(result["result"]) <= 3
