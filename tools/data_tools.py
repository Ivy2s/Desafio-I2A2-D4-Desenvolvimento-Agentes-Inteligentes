from typing import Optional

from pydantic import BaseModel


class DataQuery(BaseModel):
    operation: str
    dataset: str
    periodo: Optional[str] = None
    group_by: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None


def query_data(query: DataQuery):
    """
    Executa uma consulta estruturada nos dados.

    Esta implementação é temporária.
    Será substituída pela integração com o DataManager
    desenvolvido pelo responsável pelo Pipeline.
    """

    raise NotImplementedError(
        "DataManager ainda não integrado."
    )


def describe_data():
    """
    Retorna informações sobre os datasets disponíveis.

    Implementação temporária.
    """
    
    raise NotImplementedError(
        "DataManager ainda não integrado."
    )