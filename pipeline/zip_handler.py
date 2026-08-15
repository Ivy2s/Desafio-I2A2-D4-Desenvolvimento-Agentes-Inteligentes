from pathlib import Path
from zipfile import ZipFile


class ZipHandler:
    """Extrai arquivos ZIP para um diretório de destino com segurança."""

    @staticmethod
    def extract(zip_path: str, output_dir: str) -> list[str]:
        zip_file = Path(zip_path)
        destination = Path(output_dir)

        if not zip_file.exists():
            raise FileNotFoundError(f"Arquivo ZIP nao encontrado: {zip_path}")

        destination.mkdir(parents=True, exist_ok=True)

        extracted_files: list[str] = []
        with ZipFile(zip_file, "r") as archive:
            for member in archive.infolist():
                normalized_name = member.filename.replace("\\", "/")
                member_path = Path(normalized_name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError(
                        f"Entrada ZIP insegura: {member.filename}"
                    )

                target = (destination / member_path).resolve()
                destination_root = destination.resolve()
                if target != destination_root and destination_root not in target.parents:
                    raise ValueError(
                        f"Entrada ZIP fora do diretório reservado: {member.filename}"
                    )

                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("wb") as output:
                    output.write(source.read())
                extracted_files.append(str(target))

        return extracted_files
