from fastapi.testclient import TestClient


def _png_bytes() -> bytes:
    """テスト用の最小限の PNG バイト列（1x1 px）。"""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8"
        b"\xff\xff?\x00\x05\xfe\x02\xfe\xa1\x8a\x1d\x10\x00\x00\x00\x00IEND\xaeB`\x82"
    )


async def test_extract_single_success(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.ocr.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/test.png"
    )
    mocker.patch(
        "src.api.ocr._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        return_value="抽出テキスト",
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.save_ocr_result",
        new_callable=mocker.AsyncMock,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("page.png", _png_bytes(), "image/png")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] != ""
    assert data["combined_text"] == "--- PAGE 1 ---\n抽出テキスト"
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][0]["filename"] == "page.png"
    assert data["pages"][0]["text"] == "抽出テキスト"
    assert data["pages"][0]["source_gcs_uri"] == "gs://bucket/test.png"


async def test_extract_with_crop_calls_pillow(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.ocr.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/cropped.png"
    )
    mocker.patch(
        "src.api.ocr._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        return_value="cropped text",
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.save_ocr_result",
        new_callable=mocker.AsyncMock,
    )
    crop_mock = mocker.patch("src.api.ocr._crop_image")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("page.png", _png_bytes(), "image/png")},
            data={"crop_top": "200", "crop_bottom": "100", "crop_left": "80", "crop_right": "80"},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    assert crop_mock.called
    kwargs = crop_mock.call_args.args
    assert kwargs[2] == 200  # top
    assert kwargs[3] == 100  # bottom
    assert kwargs[4] == 80  # left
    assert kwargs[5] == 80  # right


async def test_extract_no_crop_does_not_call_pillow(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.ocr.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/test.png"
    )
    mocker.patch(
        "src.api.ocr._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        return_value="text",
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.save_ocr_result",
        new_callable=mocker.AsyncMock,
    )
    crop_mock = mocker.patch("src.api.ocr._crop_image")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("page.png", _png_bytes(), "image/png")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    crop_mock.assert_not_called()


async def test_extract_batch_success(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.ocr.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        side_effect=["gs://bucket/p1.png", "gs://bucket/p2.png"]
    )
    mocker.patch(
        "src.api.ocr._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        side_effect=["ページ1の本文", "ページ2の本文"],
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.save_ocr_result",
        new_callable=mocker.AsyncMock,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract-batch",
            files=[
                ("files", ("p1.png", _png_bytes(), "image/png")),
                ("files", ("p2.png", _png_bytes(), "image/png")),
            ],
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    data = response.json()
    assert len(data["pages"]) == 2
    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][0]["text"] == "ページ1の本文"
    assert data["pages"][1]["page_number"] == 2
    assert data["pages"][1]["text"] == "ページ2の本文"
    assert "--- PAGE 1 ---\nページ1の本文" in data["combined_text"]
    assert "--- PAGE 2 ---\nページ2の本文" in data["combined_text"]


async def test_extract_invalid_mime(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("note.txt", b"plain text", "text/plain")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 400


async def test_extract_requires_api_key(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("page.png", _png_bytes(), "image/png")},
        )

    assert response.status_code == 403


async def test_extract_gemini_failure(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mock_storage_cls = mocker.patch("src.api.ocr.CloudStorageManager")
    mock_storage_cls.return_value.upload_file_async = mocker.AsyncMock(
        return_value="gs://bucket/test.png"
    )
    mocker.patch(
        "src.api.ocr._ai_core.analyze_file_simple",
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError("Gemini API error"),
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.save_ocr_result",
        new_callable=mocker.AsyncMock,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/ocr/extract",
            files={"file": ("page.png", _png_bytes(), "image/png")},
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 500


async def test_get_ocr_result_success(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.core.ocr_schema import OcrPageResult, OcrResult

    sample = OcrResult(
        id="abc123",
        combined_text="--- PAGE 1 ---\nhello",
        pages=[
            OcrPageResult(
                page_number=1,
                filename="page.png",
                text="hello",
                source_gcs_uri="gs://bucket/page.png",
            )
        ],
    )
    mocker.patch(
        "src.api.ocr.firestore_manager.get_ocr_result",
        new_callable=mocker.AsyncMock,
        return_value=sample,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get(
            "/ocr/extract/abc123",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "abc123"
    assert data["pages"][0]["text"] == "hello"


async def test_get_ocr_result_not_found(mocker):
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")
    mocker.patch(
        "src.api.ocr.firestore_manager.get_ocr_result",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get(
            "/ocr/extract/missing",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 404
