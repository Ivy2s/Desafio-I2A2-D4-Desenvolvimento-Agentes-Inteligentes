import json
from pathlib import Path

import pandas as pd


class DataDictionary:
    """Gera metadados de datasets para descoberta por agentes."""

    @staticmethod
    def build(
        datasets: dict[str, pd.DataFrame],
        descriptions: dict[tuple[str, str], str] | None = None,
    ) -> dict:
        dictionary: dict[str, dict] = {}
        descriptions = descriptions or {}

        for name, df in datasets.items():
            dictionary[name] = {
                "rows": int(len(df)),
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample": df.head(3).to_dict(orient="records"),
                "descriptions": {
                    column: descriptions[(name, column)]
                    for column in df.columns
                    if (name, column) in descriptions
                },
            }

        return dictionary

    @staticmethod
    def save(dictionary: dict, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(dictionary, file, ensure_ascii=False, indent=2)
        return str(path)
