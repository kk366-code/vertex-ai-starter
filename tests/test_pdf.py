from fastapi.testclient import TestClient


async def test_extract_text_success(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.pdf.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/test.pdf"
    )
    mocker.patch(
        "src.api.pdf._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        return_value="extracted text",
    )
    mocker.patch(
        "src.api.pdf.firestore_manager.save_pdf_text",
        new_callable=mocker.AsyncMock,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/pdf/extract-text",
            files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "extracted text"
    assert data["source_gcs_uri"] == "gs://bucket/test.pdf"
    assert data["id"] != ""


async def test_extract_text_invalid_mime(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/pdf/extract-text",
            files={"file": ("test.txt", b"plain text", "text/plain")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 400


async def test_extract_text_gemini_failure(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.pdf.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/test.pdf"
    )
    mocker.patch(
        "src.api.pdf._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError("API error"),
    )
    mocker.patch(
        "src.api.pdf.firestore_manager.save_pdf_text",
        new_callable=mocker.AsyncMock,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/pdf/extract-text",
            files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 500
