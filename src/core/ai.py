import os

from dotenv import load_dotenv
from google.genai import Client, types

load_dotenv()


class GeminiCore:
    def __init__(self, project_id: str, location: str):
        # 設定が不足している場合はエラーを出して終了
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT が設定されていません。")

        self.client = Client(vertexai=True, project=project_id, location=location)
        self.model_id = "gemini-2.5-flash"

    def generate_json(
        self,
        prompt: str,
        gcs_uri: str | None = None,
        mime_type: str = "image/png",
    ) -> str:
        """GCSメディアを含めたJSON推論を実行"""
        contents: list[str | types.Part] = [prompt]

        # --- メディアがない場合は、テキストのみで処理 ---
        if gcs_uri is None:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )

            # response.textはNoneを返す可能性があるため、ここでNoneチェック
            if response.text is None:
                raise ValueError("Geminiからのレスポンス(text)がNoneでした。")

            return response.text

        # --- メディアがある場合の処理 ---
        media_part = types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type)
        contents.append(media_part)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,  # 汎用基盤として再現性を高めるため低めに設定
        )

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config,
        )

        # Noneチェック
        if response.text is None:
            raise ValueError("Geminiからのレスポンス(text)がNoneでした。")

        return response.text


class GeminiManager:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")

        # vertexai=True を指定することで Vertex AI バックエンドを使用
        self.client = Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )
        self.model_id = "gemini-2.5-flash"

    def analyze_media(self, gcs_uri, prompt, mime_type="image/png"):
        """
        GCS上のメディアを解析する
        """
        # GCSの情報をPartとして作成
        media_part = types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type)

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, media_part],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        return response.text


if __name__ == "__main__":
    ai = GeminiManager()
    bucket = os.getenv("GCS_BUCKET_NAME")
    test_uri = f"gs://{bucket}/test.png"

    test_prompt = "この画像の内容を「日本語」で詳細に説明してください。キーは 'description' と 'objects' にしたJSON形式で返してください。"

    try:
        result = ai.analyze_media(test_uri, test_prompt)
        print(f"AI Response:\n{result}")
    except Exception as e:
        print(f"エラーが発生しました:\n{e}")
