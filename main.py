import asyncio

from src.core.ai import GeminiCore
from src.core.config import settings
from src.core.schema import AnalysisResult
from src.core.storage import CloudStorageManager


async def main():

    print(f"🚀 AI基盤 起動テスト (Project: {settings.google_cloud_project})")

    try:
        # 2. クラスのインスタンス化
        core = GeminiCore(
            project_id=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

        # 3. プロンプト（Pydanticを使う場合、JSONの書き方の指示は不要）
        # Geminiはresponse_schemaを見て自動的に構造を理解する
        prompt = (
            "画像（または指示内容）の全体的な要約、検知した物体、"
            "および危険性の有無を判定してください。"
        )

        print("🤖 Geminiに問い合わせ中...")

        # 4. 画像解析用メソッド を呼び出す
        storage = CloudStorageManager()

        # TODO: ここも非同期化する場合は await をつける
        print("📤 画像をアップロード中...")
        gcs_uri = storage.upload_file("upload/test4.jpg")

        # 戻り値は AnalysisResult 型のインスタンスです
        result = await core.analyze_image(
            prompt=prompt,
            gcs_uri=gcs_uri,
            response_schema=AnalysisResult,
        )

        print("\n✨ --- 解析結果 (Pydantic Object) ---")
        # 辞書形式で表示したい場合は .model_dump() を使います
        print(f"説明: {result.description}")
        print(f"物体リスト: {result.objects}")
        print(f"解析の信頼度スコア: {result.confidence_score}")

        print("\n📦 生のデータ構造:")
        print(result.model_dump())
        print("------------------\n")

        print("✅ 構造化データの取得に成功しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    asyncio.run(main())
