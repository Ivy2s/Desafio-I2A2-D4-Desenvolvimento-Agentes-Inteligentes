from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from api.schemas.datasets import DatasetResponse, QueryRequest, QueryResponse
from services.exceptions import (
    AIUnavailableError,
    AgentExecutionError,
    DatasetNotFoundError,
    InvalidDatasetError,
    UnsupportedFileError,
)

router = APIRouter(prefix="/api/datasets")


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(request: Request, file: UploadFile = File(...)) -> DatasetResponse:
    try:
        session = await request.app.state.dataset_service.upload(file)
        return request.app.state.dataset_service.metadata(session)
    except UnsupportedFileError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    except InvalidDatasetError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Erro interno ao processar o dataset") from error


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(request: Request, dataset_id: UUID) -> DatasetResponse:
    try:
        session = request.app.state.registry.get(dataset_id)
        return request.app.state.dataset_service.metadata(session)
    except DatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Dataset não encontrado") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Erro interno ao ler o dataset") from error


@router.post("/{dataset_id}/query", response_model=QueryResponse)
def query_dataset(
    request: Request,
    dataset_id: UUID,
    payload: QueryRequest,
) -> QueryResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="A pergunta não pode ser vazia")
    try:
        result = request.app.state.query_service.query(dataset_id, payload.question.strip())
        return QueryResponse(answer=result.answer, data=result.data)
    except DatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Dataset não encontrado") from error
    except AIUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentExecutionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
