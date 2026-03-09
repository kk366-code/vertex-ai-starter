from core.ai import GeminiCore
from core.schema import AnalysisResult


def test_analyze_text_success(mocker):
    # 1. GeminiCoreのインスタンスを作成
    # (Clientの初期化でエラーが出ないよう、プロジェクトID等は適当に渡す)
    core = GeminiCore(project_id="test-project", location="asia-northeast1")

    # 2. 期待するレスポンス（モック）を作成
    mock_response = mocker.MagicMock()
    mock_response.text = (
        '{"success": true, "description": "テスト成功", '
        '"objects": ["test"], "confidence_score": 0.9}'
    )

    # 3. インスタンスのメソッドを直接モックに差し替える (狙い撃ち)
    # 文字列でのパッチではなく、オブジェクトの属性を直接書き換えます
    mock_method = mocker.patch.object(
        core.client.models, "generate_content", return_value=mock_response
    )

    # 4. テスト実行
    result = core.analyze_text(prompt="こんにちは", response_schema=AnalysisResult)

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
