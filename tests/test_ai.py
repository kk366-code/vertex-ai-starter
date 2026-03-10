import pytest
from pydantic import ValidationError

from core.ai import GeminiCore
from core.schema import AnalysisResult


async def test_analyze_text_success(mocker):
    # 1. GeminiCoreのインスタンスを作成
    # (実際にはAPIを叩きにいかないので、、プロジェクトID等は適当に渡す)
    core = GeminiCore(project_id="test-project", location="asia-northeast1")

    # 2. 期待するレスポンス（モック）を作成
    mock_response = mocker.MagicMock()
    mock_response.text = (
        '{"success": true, "description": "テスト成功", '
        '"objects": ["test"], "confidence_score": 0.9}'
    )

    # 3. インスタンスのメソッドを直接モックに差し替え
    # 文字列でのパッチではなく、オブジェクトの属性を直接書き換える
    # (ここではGoogleのサーバーへリクエストを送る関数を、
    # 手順2で作った「偽の回答を返すだけの関数」に置き換えている)
    # mock_method = mocker.patch.object(
    #     core.client.models, "generate_content", return_value=mock_response
    # )
    mock_method = mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        return_value=mock_response,
    )

    # 4. テスト実行
    result = await core.analyze_text(prompt="こんにちは", response_schema=AnalysisResult)

    # 5. 検証

    # 型の検証 (Type Check):
    # 戻り値(result)がAnalysisResult クラス（Pydanticモデル）のインスタンスであることを確認
    assert isinstance(result, AnalysisResult)

    # 状態の検証 (Boolean Check):
    # モックのsuccessフィールドの値が期待通りであるかを確認
    assert result.success is True

    # 内容の包含検証 (String Membership Check):
    # descriptionフィールドに期待した文字列が含まれているかを確認
    assert "テスト成功" in result.description

    # データの同一性検証 (List Equality Check):
    # objectsフィールドのリストが期待通りであるかを確認
    assert result.objects == ["test"]

    # メソッドが呼ばれたかどうかも確認できる
    mock_method.assert_called_once()


# AIがデタラメなJSONを返した場合のテスト ---
async def test_analyze_text_validation_error(mocker):
    core = GeminiCore(project_id="test-project", location="asia-northeast1")

    # 必須フィールドである 'success' が欠けている不正なレスポンス
    mock_response = mocker.MagicMock()
    mock_response.text = '{"description": "失敗するはず", "objects": []}'

    # mocker.patch.object(core.client.models, "generate_content", return_value=mock_response)
    mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        return_value=mock_response,
    )
    # PydanticのValidationErrorが発生することを期待する
    with pytest.raises(ValidationError):
        await core.analyze_text(prompt="テスト", response_schema=AnalysisResult)


# API自体が例外を投げた場合のテスト ---
async def test_analyze_text_api_failure(mocker):
    core = GeminiCore(project_id="test-project", location="asia-northeast1")

    # generate_content自体が例外（エラー）を投げるように設定
    mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        side_effect=Exception("API Error"),
    )
    # プログラムが例外をキャッチせず、適切に上に投げるかを確認
    with pytest.raises(Exception) as excinfo:
        await core.analyze_text(prompt="テスト", response_schema=AnalysisResult)

    assert "API Error" in str(excinfo.value)
