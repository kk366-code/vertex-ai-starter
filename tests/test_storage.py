from typing import cast
from unittest.mock import MagicMock

import pytest

from src.core.storage import CloudStorageManager


def test_upload_file_sync(mocker):
    # GCSクライアントをモック (パッチは当てるが、変数は使わない)
    _ = mocker.patch("google.cloud.storage.Client")
    manager = CloudStorageManager()
    manager.bucket_name = "test-bucket"

    # 期待する戻り値を設定
    expected_uri = "gs://test-bucket/test.png"

    # patch.object の戻り値を MagicMock としてキャスト
    mock_logic = cast(
        MagicMock,
        mocker.patch.object(manager, "_upload_logic", return_value=expected_uri),
    )

    # 実行
    result = manager.upload_file("upload/test.png")

    assert result == expected_uri
    # manager._upload_logic.assert_called_once_with("upload/test.png", "test.png")
    mock_logic.assert_called_once_with("upload/test.png", "test.png")


@pytest.mark.asyncio
async def test_upload_file_async(mocker):
    # CloudStorageManager() で本物ではなくモックが起動するようにする
    _ = mocker.patch("google.cloud.storage.Client")
    manager = CloudStorageManager()
    manager.bucket_name = "test-bucket"

    expected_uri = "gs://test-bucket/async-test.png"

    # _upload_logic がスレッドプール内で呼ばれることを検証
    # ここでは実際のアップロードは行わず、モックが値を返すように設定
    # mock_logic = mocker.patch.object(manager, "_upload_logic", return_value=expected_uri)

    mock_logic = cast(
        MagicMock,  # _upload_logic自体は同期関数として呼ばれるのでMagicMock
        mocker.patch.object(manager, "_upload_logic", return_value=expected_uri),
    )

    # 実行
    result = await manager.upload_file_async("upload/async-test.png")

    assert result == expected_uri
    mock_logic.assert_called_once()
