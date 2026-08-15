from pathlib import Path

import pytest
import pandas as pd

from pipeline.csv_loader import CSVLoader
from pipeline.data_manager import DataManager


def test_csv_loader_normalizes_columns_and_supports_semicolon(tmp_path: Path):
    path = tmp_path / "accented.csv"
    path.write_text("Valor Total;Descrição\n10;Açúcar\n", encoding="utf-8")

    frame = CSVLoader.load_csv(str(path))

    assert list(frame.columns) == ["valor_total", "descricao"]
    assert frame.iloc[0]["descricao"] == "Açúcar"


def test_csv_loader_supports_cp1252_text(tmp_path: Path):
    path = tmp_path / "latin.csv"
    path.write_bytes("nome;cidade\nJoão;São Paulo\n".encode("cp1252"))

    frame = CSVLoader.load_csv(str(path))

    assert frame.iloc[0]["nome"] == "João"
    assert frame.iloc[0]["cidade"] == "São Paulo"


@pytest.mark.parametrize("content", [b"", b"id,nome,valor\n"])
def test_empty_csvs_are_rejected_without_traceback(tmp_path: Path, content: bytes):
    path = tmp_path / "empty.csv"
    path.write_bytes(content)
    manager = DataManager(data_dir=str(tmp_path / "data"))

    with pytest.raises((ValueError, pd.errors.EmptyDataError)):
        manager.load(str(path))


def test_malformed_csv_is_handled_by_the_existing_parser(tmp_path: Path):
    path = tmp_path / "malformed.csv"
    path.write_text("a,b,c\n1,2\n3,4,5,6\n", encoding="utf-8")
    manager = DataManager(data_dir=str(tmp_path / "data"))

    try:
        manager.load(str(path))
    except (ValueError, pd.errors.ParserError):
        return
    assert "malformed" in manager.datasets
