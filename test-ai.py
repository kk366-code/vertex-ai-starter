import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # デフォルト値を設定可能

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
    http_options={'api_version': 'v1'}
)

print(f"--- 接続情報 ---")
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash", # バージョンが古いと動かない
        contents="こんにちは！Vertex AIを使ってみます。応答をください！"
    )
    print("--- 実行結果 ---")
    print(response.text)
except Exception as e:
    print(f"エラーが発生しました:\n{e}")
