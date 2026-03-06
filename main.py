import os

from dotenv import load_dotenv

from src.core.ai import GeminiCore

# from src.core.storage import CloudStorageManager # 今回は一旦パス指定でテスト

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if PROJECT_ID is None:
    raise ValueError("環境変数 'GOOGLE_CLOUD_PROJECT' が指定されていません")

LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")  # デフォルト値を設定可能


def main():
    # 1. 環境変数の準備
    project_id = PROJECT_ID
    if project_id is None:
        raise ValueError("環境変数 'GOOGLE_CLOUD_PROJECT' が指定されていません")

    location = "us-central1"  # または "asia-northeast1"

    print(f"🚀 AI基盤 起動テスト (Project: {project_id})")

    # 2. クラスのインスタンス化
    try:
        core = GeminiCore(project_id=project_id, location=location)

        # 3. テスト用のプロンプト（JSON形式で返してもらうよう指示）
        prompt = """
        画像の内容を以下のJSON形式で解析してください。
        {
            "summary": "全体の説明",
            "objects": ["検知した物体のリスト"],
            "is_danger": true/false
        }
        """

        # 今回は一旦、GCSなし（テキストのみ）の画像なしルートをテスト
        print("🤖 Geminiに問い合わせ中...")
        result_json = core.generate_json(prompt=prompt)

        print("\n✨ --- 解析結果 ---")
        print(result_json)
        print("------------------\n")
        print("✅ 動作確認完了！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
