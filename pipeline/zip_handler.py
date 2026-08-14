from pathlib import Path
from zipfile import ZipFile


class ZipHandler:
    """Extrai arquivos ZIP para um diretório de destino."""

    @staticmethod
    def extract(zip_path: str, output_dir: str) -> list[str]:
        zip_file = Path(zip_path)
        destination = Path(output_dir)

        if not zip_file.exists():
            raise FileNotFoundError(f"Arquivo ZIP nao encontrado: {zip_path}")

        destination.mkdir(parents=True, exist_ok=True)

        extracted_files: list[str] = []
        with ZipFile(zip_file, "r") as archive:
            archive.extractall(destination)
            for member in archive.namelist():
                extracted_files.append(str(destination / member))

        return extracted_files