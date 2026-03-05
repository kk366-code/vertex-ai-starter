from src.core.ai import GeminiManager
from src.core.storage import CloudStorageManager


def run_pipeline(file_path, prompt):
    """
    一連の処理（アップロード → 解析）を行うコア・ロジック
    """
    storage = CloudStorageManager()
    ai = GeminiManager()

    # 1. アップロード
    gcs_uri = storage.upload_file(file_path)
    # 2. 解析
    result = ai.analyze_media(gcs_uri, prompt)
    return result


def main():
    """
    開発中の動作確認や、CLIとして使うための実行用関数
    """
    print("🚀 AI Pipeline Start")

    # 動作確認用のサンプル
    target = "upload/test.png"
    prompt = "画像の内容を日本語で説明してください。"

    try:
        response = run_pipeline(target, prompt)
        print(f"✅ Result: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
