# SKILL.md - Implementation Patterns

## 🐍 Modern Python Best Practices (2026)

AIがコードを生成・修正する際は、以下の2026年3月時点の最新プラクティスを遵守してください。

- **Python Version**: Python 3.14+ の機能を優先的に使用します。
- **Type Annotations**: `Optional` や `Union` は使用せず、常に `|` (Pipe syntax) を使用してください（例: `str | None`, `int | float`）。
- **Native Types**: `list[]`, `dict[]`, `tuple[]` などの組み込みジェネリクスを直接使用します。
- **Strict Linting**: 常に `ruff` の最新ルール（特に `UP` カテゴリ）に従い、レガシーな構文（例: `.format()`）を排除し、`f-strings` を使用してください。
- **Dependency Management**: パッケージ管理には `uv` を使用し、実行時は `uv run` を前提とします。

## 🤖 Vertex AI (google-genai) Implementation

Geminiを使用して構造化データを取得する場合は、以下の定石に従ってください。

1. **Define Schema**: Pydanticの `BaseModel` を定義し、各フィールドに詳細な `Field(description=...)` を記述します。
2. **Config Settings**: `response_mime_type="application/json"` と `response_schema` を設定します。
3. **Validation**: レスポンスは `model_validate_json()` を使用してパースし、型安全なオブジェクトとして返します。

```python
# Implementation Pattern
async def analyze(prompt: str, schema: type[T]) -> T:
    config = genai.types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.1
    )
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[prompt], 
        config=config
    )
    return schema.model_validate_json(response.text)

```

## ☁️ Google Cloud Storage (GCS) Operations

- **Upload First**: AI解析の前に `CloudStorageManager` を使用してファイルをアップロードします。
- **URI Passing**: Geminiにはローカルパスではなく、必ず `gs://` 形式のURIを渡してください。
- **Mime-types**: デフォルトは `image/png` ですが、`image/jpeg` も適切にサポートしてください。

## 🧪 Testing Strategy (Async Mocking)

Gemini APIのテストには、`pytest-mock` を使用した以下のパターンを採用します。

- **Mock Target**: `core.client.aio.models` の `generate_content` をモックします。
- **Async Setup**: `new_callable=mocker.AsyncMock` を指定して、非同期呼び出しを正しくシミュレートします。

```python
mock_method = mocker.patch.object(
    core.client.aio.models,
    "generate_content",
    new_callable=mocker.AsyncMock,
    return_value=mock_response
)

```

## ⚠️ Known Pitfalls & Safety

- **Project ID Validation**: 実行前に必ず `.env` から `GOOGLE_CLOUD_PROJECT` が正しく読み込まれているかチェックしてください。
- **Error Handling**: 解析不能な場合（画像が壊れている等）は、例外を投げるのではなく、スキーマの `success=False` フィールドを使用して正常に応答を返してください。
- **Text Encoding**: 特にWindows環境での実行を考慮し、ファイル操作やログ出力時は常に `UTF-8` を明示してください。

## 🐍 Python / FastAPI

### Safe Temporary File Handling

- **Automatic Cleanup with tempfile**:
  `tempfile` モジュールを活用することで、ディスク容量の圧迫や予期せぬファイルの残留を防ぎます。

  ```python
  # 推奨されるパターン
  with tempfile.TemporaryDirectory(dir=Path("upload")) as tmp_dir:
      local_path = Path(tmp_dir) / file.filename
      # 処理を実行...
  # スコープを抜けると tmp_dir とその中身は自動で物理削除される

  ```

### FastAPI Modern Patterns (2026)

- **Annotated Type Hints**:
FastAPI の各コンポーネント定義には `Annotated` を標準採用します。これにより、メタデータと型定義を分離し、可読性を高めます。
- `prompt: Annotated[str, Form()]`
- `file: Annotated[UploadFile, File()]`
- `api_key: Annotated[str, Security(verify_api_key)]`

#### Efficient File Handling with shutil

- **shutil.copyfileobj**: アップロードされた `UploadFile` ストリームをローカルファイルに効率的に書き出すために使用。

- **Memory Efficiency**: 大容量ファイルを扱う際、メモリ（RAM）を消費しすぎないようにストリームベースのコピーを徹底する。
