from io import BytesIO
from pathlib import Path
import stat
from types import SimpleNamespace
from uuid import UUID
from zipfile import ZipFile, ZipInfo

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from api.main import create_app
from services.query_service import QueryResult
from services.exceptions import ProviderRateLimitError, UnknownToolError


CSV = b"name,value\nalpha,10\nbeta,20\n"


def client_for(tmp_path):
    return TestClient(create_app(str(tmp_path / "datasets")))


def upload(client, filename="data.csv", content=CSV):
    response = client.post(
        "/api/datasets",
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()


def zip_bytes(*entries):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return buffer.getvalue()


def test_health_does_not_require_ai_key(tmp_path):
    response = client_for(tmp_path).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_csv_and_metadata(tmp_path):
    client = client_for(tmp_path)
    payload = upload(client)

    assert payload["status"] == "ready"
    assert payload["summary"] == {"files": 1, "rows": 2, "columns": 2}
    dataset_id = payload["datasetId"]
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    assert response.json()["datasets"][0]["name"] == "data"
    assert response.json() == payload
    assert response.json()["datasets"][0]["columns"] == [
        {"name": "name", "type": "string"},
        {"name": "value", "type": "string"},
    ]


def test_upload_zip_with_nested_csv(tmp_path):
    client = client_for(tmp_path)
    content = zip_bytes(("nested/data.csv", CSV), ("notes.txt", b"ignored"))
    payload = upload(client, "bundle.zip", content)
    assert payload["summary"]["files"] == 1
    assert payload["datasets"][0]["name"] == "data"


def test_upload_zip_processes_data_dictionary_without_counting_it(tmp_path):
    client = client_for(tmp_path)
    content = zip_bytes(
        ("compras/compras.csv", b"fornecedor,valor\nAlfa,10\n"),
        ("dicionario.csv", b"arquivo,coluna,descricao\ncompras.csv,valor,Valor total\n"),
    )
    payload = upload(client, "bundle.zip", content)

    assert payload["summary"] == {"files": 1, "rows": 1, "columns": 2}


def test_upload_rejects_corrupt_or_empty_zip(tmp_path):
    client = client_for(tmp_path)
    corrupt = client.post(
        "/api/datasets",
        files={"file": ("broken.zip", b"not a zip", "application/zip")},
    )
    empty = client.post(
        "/api/datasets",
        files={"file": ("empty.zip", zip_bytes(("notes.txt", b"ignored")), "application/zip")},
    )
    assert corrupt.status_code == 400
    assert empty.status_code == 400


def test_zip_path_traversal_is_rejected(tmp_path):
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    content = zip_bytes(("../outside.csv", CSV))
    response = client.post(
        "/api/datasets",
        files={"file": ("unsafe.zip", content, "application/zip")},
    )
    assert response.status_code == 400
    assert not (tmp_path / "outside.csv").exists()
    assert list((tmp_path / "datasets").iterdir()) == []
    assert list(app.state.registry) == []


def test_zip_absolute_windows_path_is_rejected(tmp_path):
    client = client_for(tmp_path)
    content = zip_bytes((r"C:\Windows\evil.csv", CSV))
    response = client.post(
        "/api/datasets",
        files={"file": ("unsafe.zip", content, "application/zip")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsafe_zip_entry"


def test_zip_absolute_unix_path_is_rejected(tmp_path):
    response = client_for(tmp_path).post(
        "/api/datasets",
        files={"file": ("unsafe.zip", zip_bytes(("/tmp/evil.csv", CSV)), "application/zip")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsafe_zip_entry"


def test_zip_symlink_is_rejected(tmp_path):
    buffer = BytesIO()
    info = ZipInfo("linked.csv")
    info.external_attr = stat.S_IFLNK << 16
    with ZipFile(buffer, "w") as archive:
        archive.writestr(info, "../../outside.csv")

    response = client_for(tmp_path).post(
        "/api/datasets",
        files={"file": ("symlink.zip", buffer.getvalue(), "application/zip")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsafe_zip_entry"


def test_upload_rejects_unsupported_format(tmp_path):
    response = client_for(tmp_path).post(
        "/api/datasets",
        files={"file": ("notes.txt", b"text", "text/plain")},
    )
    assert response.status_code == 415


def test_uploads_are_isolated(tmp_path):
    client = client_for(tmp_path)
    first = upload(client)
    second = upload(client, "other.csv", b"other,total\none,3\n")
    assert first["datasetId"] != second["datasetId"]
    assert client.get(f"/api/datasets/{first['datasetId']}").json()["datasets"][0]["name"] == "data"
    assert client.get(f"/api/datasets/{second['datasetId']}").json()["datasets"][0]["name"] == "other"


def test_uploads_keep_managers_and_directories_isolated(tmp_path):
    legacy_data = Path(__file__).resolve().parents[1] / "data"
    legacy_before = {path.name for path in legacy_data.iterdir()}
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    first = upload(client, "a.csv", b"name,value\nAlice,1\n")
    second = upload(client, "b.csv", b"product,total\nMouse,100\n")

    first_session = app.state.registry.get(UUID(first["datasetId"]))
    second_session = app.state.registry.get(UUID(second["datasetId"]))
    assert first_session.root_dir != second_session.root_dir
    assert first_session.manager is not second_session.manager
    assert set(first_session.manager.datasets) == {"a"}
    assert set(second_session.manager.datasets) == {"b"}
    assert not (first_session.root_dir / "data" / "b.csv").exists()
    assert not (second_session.root_dir / "data" / "a.csv").exists()
    assert {path.name for path in legacy_data.iterdir()} == legacy_before


def test_two_zips_with_same_internal_basename_are_isolated(tmp_path):
    client = client_for(tmp_path)
    first = upload(client, "first.zip", zip_bytes(("A/data.csv", CSV)))
    second = upload(client, "second.zip", zip_bytes(("B/data.csv", CSV)))
    assert first["datasetId"] != second["datasetId"]
    assert first["datasets"][0]["name"] == "data"
    assert second["datasets"][0]["name"] == "data"


def test_duplicate_csv_basenames_in_one_zip_are_rejected(tmp_path):
    response = client_for(tmp_path).post(
        "/api/datasets",
        files={
            "file": (
                "collision.zip",
                zip_bytes(("a/data.csv", CSV), ("b/data.csv", CSV)),
                "application/zip",
            )
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "dataset_load_failed"
    assert list((tmp_path / "datasets").iterdir()) == []


def test_upload_limit_cleans_session(tmp_path, monkeypatch):
    import services.dataset_service as dataset_service

    monkeypatch.setattr(dataset_service, "MAX_UPLOAD_BYTES", 4)
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    response = client.post(
        "/api/datasets",
        files={"file": ("large.csv", b"name,value\n", "text/csv")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"
    assert list((tmp_path / "datasets").iterdir()) == []
    assert list(app.state.registry) == []


def test_zip_member_limit_cleans_session(tmp_path, monkeypatch):
    import services.dataset_service as dataset_service

    monkeypatch.setattr(dataset_service, "MAX_ZIP_MEMBERS", 1)
    content = zip_bytes(("one.csv", CSV), ("two.csv", CSV))
    app = create_app(str(tmp_path / "datasets"))
    response = TestClient(app).post(
        "/api/datasets",
        files={"file": ("many.zip", content, "application/zip")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "zip_limit_exceeded"
    assert list((tmp_path / "datasets").iterdir()) == []
    assert list(app.state.registry) == []


def test_missing_dataset_returns_404(tmp_path):
    response = client_for(tmp_path).get("/api/datasets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "dataset_not_found"


def test_query_without_ai_key_returns_controlled_error(tmp_path, monkeypatch):
    import services.query_service as query_service

    monkeypatch.setattr(query_service, "is_ai_configured", lambda: False)
    client = client_for(tmp_path)
    dataset_id = upload(client)["datasetId"]
    response = client.post(
        f"/api/datasets/{dataset_id}/query",
        json={"question": "quantos registros existem?"},
    )
    assert response.status_code == 503


def test_query_uses_structured_application_result(tmp_path):
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    dataset_id = upload(client)["datasetId"]
    app.state.query_service = SimpleNamespace(
        query=lambda received_id, question: QueryResult(
            answer=f"Resposta para {question}",
            data={
                "type": "table",
                "columns": ["name"],
                "rows": [{"name": "alpha"}],
                "truncated": False,
                "returnedRows": 1,
            },
        )
    )
    response = client.post(
        f"/api/datasets/{dataset_id}/query",
        json={"question": "liste os registros"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["type"] == "table"


def test_query_orchestration_error_has_stable_code(tmp_path):
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    dataset_id = upload(client)["datasetId"]

    app.state.query_service = SimpleNamespace(
        query=lambda received_id, question: (_ for _ in ()).throw(
            UnknownToolError("Ferramenta desconhecida")
        )
    )
    response = client.post(
        f"/api/datasets/{dataset_id}/query",
        json={"question": "consulta"},
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "unknown_tool"


def test_query_rate_limit_preserves_provider_details(tmp_path):
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    dataset_id = upload(client)["datasetId"]
    app.state.query_service = SimpleNamespace(
        query=lambda received_id, question: (_ for _ in ()).throw(
            ProviderRateLimitError(
                "Limite temporário do provedor atingido.",
                provider="groq",
                retry_after_seconds=4,
                metadata={"remaining_tokens": "0"},
            )
        )
    )

    response = client.post(
        f"/api/datasets/{dataset_id}/query",
        json={"question": "consulta"},
    )

    assert response.status_code == 429
    assert response.json()["error"] == {
        "code": "provider_rate_limit",
        "message": "Limite temporário do provedor atingido.",
        "details": {
            "provider": "groq",
            "retryable": True,
            "retry_after_seconds": 4,
            "remaining_tokens": "0",
        },
    }


def test_query_count_response_is_typed(tmp_path):
    app = create_app(str(tmp_path / "datasets"))
    client = TestClient(app)
    dataset_id = upload(client)["datasetId"]
    app.state.query_service = SimpleNamespace(
        query=lambda received_id, question: QueryResult(
            answer="Foram encontrados 2 registros.",
            data={"type": "count", "value": 2},
        )
    )
    response = client.post(
        f"/api/datasets/{dataset_id}/query",
        json={"question": "quantos?"},
    )
    assert response.status_code == 200
    assert response.json()["data"] == {"type": "count", "value": 2}


def test_openapi_exposes_contract_schemas(tmp_path):
    spec = client_for(tmp_path).get("/openapi.json").json()
    schemas = spec["components"]["schemas"]
    assert {"HealthResponse", "ErrorResponse", "TableData", "CountData"} <= set(schemas)
    assert "/api/datasets/{dataset_id}/query" in spec["paths"]
    query_schema = schemas["QueryResponse"]["properties"]["data"]
    assert "anyOf" in query_schema


def test_json_boundary_normalizes_non_standard_scalars():
    from services.json_safe import to_json_safe

    value = to_json_safe({
        "integer": np.int64(3),
        "float": np.float64(1.5),
        "nan": np.nan,
        "infinity": np.inf,
        "missing": pd.NA,
        "timestamp": pd.Timestamp("2026-08-14T21:00:00Z"),
    })
    assert value == {
        "integer": 3,
        "float": 1.5,
        "nan": None,
        "infinity": None,
        "missing": None,
        "timestamp": "2026-08-14T21:00:00+00:00",
    }


def test_query_rejects_blank_question(tmp_path):
    client = client_for(tmp_path)
    dataset_id = upload(client)["datasetId"]
    response = client.post(f"/api/datasets/{dataset_id}/query", json={"question": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
