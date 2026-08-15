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


class DatasetUploadResponse(DatasetResponse):
    pass


class DatasetDetailResponse(DatasetResponse):
    pass


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class TableData(BaseModel):
    type: Literal["table"]
    columns: list[str]
    rows: list[dict[str, Any]]


class CountData(BaseModel):
    type: Literal["count"]
    value: int


class QueryResponse(BaseModel):
    answer: str
    data: TableData | CountData | None = None
