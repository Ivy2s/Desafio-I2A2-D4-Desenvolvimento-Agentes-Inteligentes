from pathlib import Path
from typing import Any
from uuid import UUID
from zipfile import BadZipFile

from fastapi import UploadFile

from pipeline.data_manager import DataManager
from services.exceptions import InvalidDatasetError, UnsupportedFileError
from services.session_registry import DatasetSession, SessionRegistry


class DatasetService:
    def __init__(self, registry: SessionRegistry):
        self.registry = registry

    async def upload(self, file: UploadFile) -> DatasetSession:
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in {".zip", ".csv"}:
            raise UnsupportedFileError("Apenas arquivos .zip ou .csv são aceitos")

        session = self.registry.create()
        upload_path = session.root_dir / filename.replace("/", "_").replace("\\", "_")
        try:
            with upload_path.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    output.write(chunk)
            session.manager.load(str(upload_path))
            if not session.manager.datasets:
                raise InvalidDatasetError("Nenhum CSV encontrado no arquivo")
            return session
        except (BadZipFile, OSError, ValueError) as error:
            self.registry.remove(session.dataset_id)
            raise InvalidDatasetError(f"Não foi possível processar o dataset: {error}") from error
        finally:
            await file.close()

    @staticmethod
    def metadata(session: DatasetSession) -> dict[str, Any]:
        dictionary = session.manager.describe()
        datasets = [
            {
                "name": name,
                "rows": info["rows"],
                "columns": info["columns"],
                "dtypes": info["dtypes"],
                "sample": info["sample"],
            }
            for name, info in dictionary.items()
        ]
        return {
            "datasetId": str(session.dataset_id),
            "status": "ready",
            "createdAt": session.created_at,
            "summary": {
                "files": len(datasets),
                "rows": sum(item["rows"] for item in datasets),
                "columns": sum(len(item["columns"]) for item in datasets),
            },
            "datasets": datasets,
        }
