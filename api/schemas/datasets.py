from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    files: int
    rows: int
    columns: int


class DatasetMetadata(BaseModel):
    name: str
    rows: int
    columns: list[str]
    dtypes: dict[str, str]
    sample: list[dict[str, Any]]


class DatasetResponse(BaseModel):
    datasetId: UUID
    status: Literal["ready"]
    createdAt: datetime
    summary: DatasetSummary
    datasets: list[DatasetMetadata]


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class QueryResponse(BaseModel):
    answer: str
    data: dict[str, Any] | None = None
