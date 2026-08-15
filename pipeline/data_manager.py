from pathlib import Path
import csv
from typing import Optional

import pandas as pd

from pipeline.csv_loader import CSVLoader
from pipeline.data_dictionary import DataDictionary
from pipeline.validator import DataValidator
from pipeline.zip_handler import ZipHandler


class DataManager:
    """Gerencia os datasets carregados e executa consultas."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.datasets: dict[str, pd.DataFrame] = {}
        self.dictionary: dict = {}
        self.provided_descriptions: dict[tuple[str, str], str] = {}

    def load(self, source_path: Optional[str] = None):
        if source_path:
            path = Path(source_path)

            if path.suffix.lower() == ".zip":
                ZipHandler.extract(str(path), str(self.data_dir))
                self.datasets = CSVLoader.load_directory(str(self.data_dir))

            elif path.suffix.lower() == ".csv":
                self.datasets = {
                    path.stem.lower(): CSVLoader.load_csv(str(path))
                }

            elif path.is_dir():
                self.datasets = CSVLoader.load_directory(str(path))

            else:
                raise ValueError(
                    f"Formato de origem nao suportado: {source_path}"
                )

        else:
            self.datasets = CSVLoader.load_directory(str(self.data_dir))

        DataValidator.validate_datasets(self.datasets)
        self.provided_descriptions = self._load_provided_dictionary()
        self.dictionary = DataDictionary.build(self.datasets, self.provided_descriptions)

        return self.datasets

    def _load_provided_dictionary(self) -> dict[tuple[str, str], str]:
        """Lê o dicionário opcional fornecido no ZIP sem tratá-lo como dataset."""
        candidates = [
            path
            for path in self.data_dir.rglob("*.csv")
            if path.stem.lower() in CSVLoader.DICTIONARY_FILENAMES
        ]
        if not candidates:
            return {}

        descriptions: dict[tuple[str, str], str] = {}
        with candidates[0].open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            required = {"arquivo", "coluna", "descricao"}
            if not reader.fieldnames or not required.issubset(
                {field.strip().lower() for field in reader.fieldnames}
            ):
                raise ValueError(
                    "O dicionário deve conter as colunas arquivo, coluna e descricao"
                )
            fields = {field.strip().lower(): field for field in reader.fieldnames}
            for row in reader:
                dataset = Path(row[fields["arquivo"]].strip()).stem.lower()
                column = row[fields["coluna"]].strip()
                description = row[fields["descricao"]].strip()
                if dataset and column and description:
                    descriptions[(dataset, column)] = description
        return descriptions

    def describe(self) -> dict:
        """Retorna metadata dos datasets disponíveis."""

        if not self.dictionary:
            self.load()

        return self.dictionary

    def query(
        self,
        operation: str,
        dataset: str,
        periodo: Optional[str] = None,
        group_by: Optional[str] = None,
        metric: Optional[str] = None,
        aggregation: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        if not self.datasets:
            self.load()

        if dataset not in self.datasets:
            raise ValueError(
                f"Dataset '{dataset}' nao encontrado. "
                f"Datasets disponiveis: {list(self.datasets.keys())}"
            )

        df = self.datasets[dataset].copy()

        # ---------------------------------------------------------
        # FILTRO POR PERIODO
        # ---------------------------------------------------------

        if periodo:
            if "periodo" not in df.columns:
                raise ValueError(
                    f"O dataset '{dataset}' nao possui a coluna 'periodo'. "
                    f"Colunas disponiveis: {list(df.columns)}"
                )

            df = df[df["periodo"].astype(str) == str(periodo)]

        normalized_operation = operation.lower().strip()

        # ---------------------------------------------------------
        # COUNT
        # ---------------------------------------------------------

        if normalized_operation in {"count", "contagem"}:
            return {
                "dataset": dataset,
                "operation": "count",
                "result": int(len(df)),
            }

        # ---------------------------------------------------------
        # LIST
        # ---------------------------------------------------------

        if normalized_operation in {"list", "listar"}:
            effective_limit = limit if limit else 20
            rows = df.head(effective_limit).to_dict(
                orient="records"
            )

            return {
                "dataset": dataset,
                "operation": "list",
                "result": rows,
                "truncated": len(df) > len(rows),
                "returned_rows": len(rows),
            }

        # ---------------------------------------------------------
        # AGGREGATE
        # ---------------------------------------------------------

        if normalized_operation in {
            "aggregate",
            "agregacao",
            "groupby",
            "agrupamento",
        }:

            if not group_by:
                raise ValueError(
                    "Para agregacao informe 'group_by'."
                )

            if not metric:
                raise ValueError(
                    "Para agregacao informe 'metric'."
                )

            if not aggregation:
                raise ValueError(
                    "Para agregacao informe 'aggregation'."
                )

            if group_by not in df.columns:
                raise ValueError(
                    f"Coluna group_by '{group_by}' nao encontrada "
                    f"no dataset '{dataset}'. "
                    f"Colunas disponiveis: {list(df.columns)}"
                )

            if metric not in df.columns:
                raise ValueError(
                    f"Coluna metric '{metric}' nao encontrada "
                    f"no dataset '{dataset}'. "
                    f"Colunas disponiveis: {list(df.columns)}"
                )

            # Converte metric para numerico
            metric_values = pd.to_numeric(
                df[metric],
                errors="coerce"
            )

            df["_metric"] = metric_values

            aggregation_map = {
                "avg": "mean",
                "sum": "sum",
                "count": "count",
                "min": "min",
                "max": "max",
            }

            aggregation = aggregation_map.get(
                aggregation.lower(),
                aggregation.lower()
            )

            grouped = (
                df.groupby(
                    group_by,
                    dropna=False
                )["_metric"]
                .agg(aggregation)
                .reset_index()
                .rename(
                    columns={
                        "_metric": metric
                    }
                )
            )

            # -----------------------------------------------------
            # ORDENAÇÃO
            # -----------------------------------------------------

            if sort:
                if sort not in grouped.columns:
                    raise ValueError(
                        f"Coluna de ordenacao '{sort}' nao encontrada "
                        f"no resultado. "
                        f"Colunas disponiveis: {list(grouped.columns)}"
                    )

                grouped = grouped.sort_values(
                    by=sort,
                    ascending=False
                )

            # -----------------------------------------------------
            # LIMIT
            # -----------------------------------------------------

            total_rows = len(grouped)
            if limit:
                grouped = grouped.head(limit)

            return {
                "dataset": dataset,
                "operation": "aggregate",
                "result": grouped.to_dict(
                    orient="records"
                ),
                "truncated": total_rows > len(grouped),
                "returned_rows": len(grouped),
            }

        # ---------------------------------------------------------
        # OPERAÇÃO INVÁLIDA
        # ---------------------------------------------------------

        raise ValueError(
            f"Operacao '{operation}' nao suportada. "
            f"Operacoes disponiveis: count, list, aggregate."
        )
