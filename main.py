from src.core.manager import AIFoundation


def main():
    foundation = AIFoundation()

    # 解析したい画像とプロンプト
    target_file = "upload/test.jpg"
    # prompt = "画像内のオブジェクトを検出し、日本語でリスト化してください。"
    prompt = "画像の内容をずんだもんの人格で説明してください。最後に感想も述べてください。"

    try:
        print("処理を開始します...")
        result = foundation.process_image_analysis(target_file, prompt)
        print(f"解析完了:\n{result}")
    except Exception as e:
        print(f"基盤エラー: {e}")


if __name__ == "__main__":
    main()
