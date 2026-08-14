from pathlib import Path
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
        self.dictionary = DataDictionary.build(self.datasets)

        return self.datasets

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
            rows = df.head(limit if limit else 20).to_dict(
                orient="records"
            )

            return {
                "dataset": dataset,
                "operation": "list",
                "result": rows,
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

            if limit:
                grouped = grouped.head(limit)

            return {
                "dataset": dataset,
                "operation": "aggregate",
                "result": grouped.to_dict(
                    orient="records"
                ),
            }

        # ---------------------------------------------------------
        # OPERAÇÃO INVÁLIDA
        # ---------------------------------------------------------

        raise ValueError(
            f"Operacao '{operation}' nao suportada. "
            f"Operacoes disponiveis: count, list, aggregate."
        )