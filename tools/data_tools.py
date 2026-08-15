from typing import Optional, Literal

from pydantic import BaseModel, Field

from pipeline.data_manager import DataManager
from services.config import MAX_QUERY_RESULT_ROWS


class DataQuery(BaseModel):
    operation: Literal[
        "count",
        "aggregate",
        "list"
    ] = Field(
        description=(
            "Tipo de operação a realizar sobre os dados. "
            "Use count para contar registros, list para listar registros "
            "e aggregate para calcular agregações."
        )
    )

    dataset: str = Field(
        description=(
            "Nome EXATO de um dos datasets retornados por describe_data. "
            "Nunca invente ou altere o nome."
        )
    )

    periodo: Optional[str] = Field(
        default=None,
        description=(
            "Período para filtrar os dados, somente quando o dataset "
            "possuir uma coluna 'periodo'."
        )
    )

    group_by: Optional[str] = Field(
        default=None,
        description=(
            "Nome EXATO da coluna usada para agrupamento. "
            "Deve existir no dataset."
        )
    )

    metric: Optional[str] = Field(
        default=None,
        description=(
            "Nome EXATO da coluna usada como métrica numérica. "
            "Deve existir no dataset."
        )
    )

    aggregation: Optional[
        Literal["sum", "avg", "count", "min", "max"]
    ] = Field(
        default=None,
        description=(
            "Operação matemática aplicada à métrica: "
            "sum, avg, count, min ou max."
        )
    )

    sort: Optional[str] = Field(
        default=None,
        description=(
            "Nome EXATO da coluna pela qual os resultados serão "
            "ordenados."
        )
    )

    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=MAX_QUERY_RESULT_ROWS,
        description=(
            "Número máximo de resultados a retornar. O limite público é "
            f"{MAX_QUERY_RESULT_ROWS}."
        )
    )


def query_data(query: DataQuery, manager: Optional[DataManager] = None):
    """
    Executa uma consulta estruturada nos dados carregados.
    """

    data_manager = manager or DataManager()
    effective_limit = query.limit
    if query.operation in {"list", "aggregate"}:
        effective_limit = min(query.limit or MAX_QUERY_RESULT_ROWS, MAX_QUERY_RESULT_ROWS)

    return data_manager.query(
        operation=query.operation,
        dataset=query.dataset,
        periodo=query.periodo,
        group_by=query.group_by,
        metric=query.metric,
        aggregation=query.aggregation,
        sort=query.sort,
        limit=effective_limit,
    )


def describe_data(manager: Optional[DataManager] = None):
    """
    Retorna os datasets disponíveis e seus metadados,
    incluindo colunas, tipos de dados e amostras.
    """

    return (manager or DataManager()).describe()
