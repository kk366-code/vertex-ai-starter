`uv` を使用して、Google Cloud Vertex AI (Gemini) を利用するためのスタータープロジェクトです。

## 🚀 特徴

- **最新のSDK**: `google-genai` を使用
- **モダンなパッケージ管理**: `uv` による高速で再現可能な環境構築
- **環境変数の分離**: `python-dotenv` による安全な設定管理

## 🛠 セットアップ

### 1. 準備
- Google Cloud プロジェクトの作成
- Vertex AI API の有効化
- 支払い情報の紐付け

### 2. 環境構築


## 🛠 Google Cloud CLI (gcloud) の導入

プロジェクトを操作するために Google Cloud CLI のインストールが必要です。OSごとの手順に従ってください。

### 1. インストール

#### 🍎 macOS

Homebrewを使用するか、インタラクティブなスクリプトでインストールします。

```bash
# Homebrewを使用する場合
brew install --cask google-cloud-sdk

# または インストールスクリプトを使用する場合
curl https://sdk.cloud.google.com | bash
```

#### 🐧 Linux

多くのディストリビューションで以下のスクリプトが動作します。

```bash
curl https://sdk.cloud.google.com | bash
```

#### 🪟 Windows

1. [Google Cloud CLI インストーラ](https://www.google.com/search?q=https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe) をダウンロードして実行します。
2. インストール完了後、**Google Cloud SDK Shell** を管理者権限で起動します。

---

### 2. Python 環境の紐付け (重要)

`gcloud` は Python 3.10 以上を必要とします。本プロジェクトでは `uv` で管理している Python を使用することを推奨します。

```bash
# uv で Python 3.12 をインストール
uv python install 3.12

# gcloud が使用する Python を指定 (macOS/Linux)
export CLOUDSDK_PYTHON=$(uv python find 3.12)

# Windows (PowerShell) の場合
$env:CLOUDSDK_PYTHON = (uv python find 3.12)
```

> [!TIP]
> ターミナルを再起動しても有効にするために、macOS/Linux の場合は `~/.zshrc` や `~/.bashrc` に上記 `export` 文を追記してください。

---

### 3. 初期設定と認証

インストールが完了したら、以下のコマンドで Google アカウントとの連携を行います。

```bash
# 1. 基本設定（ブラウザが開くのでログインしてプロジェクトを選択）
gcloud init

# 2. アプリケーション実行用認証 (ADC) の設定
# これにより Python SDK (google-genai) が自動的に認証情報を参照できるようになります
gcloud auth application-default login
```


### 4. 接続確認

正しく設定されたか確認します。

```bash
gcloud --version
```


### 5. 環境変数の設定

プロジェクトを実行するために、環境変数の設定が必要です。テンプレートをコピーして `.env` ファイルを作成してください。

```bash
# テンプレートをコピー
cp .env.example .env
```

作成した `.env` をエディタで開き、以下の項目を各自の環境に合わせて編集してください。

| 変数名 | 説明 | 設定例 |
| --- | --- | --- |
| `GOOGLE_CLOUD_PROJECT` | 使用するプロジェクトID | `your-project-id-123` |
| `GOOGLE_CLOUD_LOCATION` | Vertex AIのリソース場所 | `asia-northeast1` |

---

### 💡 次のステップ

認証が完了したら、プロジェクトの依存関係を同期してください。

```bash
# リポジトリのクローン（またはダウンロード）
# uvによるパッケージインストール
uv sync
```

## データ基盤 (Google Cloud Storage)
本プロジェクトでは、Vertex AI での学習効率とコスト最適化を両立するため、以下の GCS 構成を採用しています。
- クラス: Standard
  - Vertex AI による頻繁なデータ読み込み（モデル訓練・推論）が発生するため、取り出し料金のない Standard を選択。

- Hierarchical Namespace (HNS): 有効
  - 大規模なデータセットの管理を想定し、ファイルシステムに近い階層構造を有効化。これにより、AI/ML パイプラインにおけるフォルダのリネームや一覧表示のパフォーマンスを最適化しています。

### セキュリティ設計
- 公開アクセスの防止: オン
  - 機密性の高い学習データやAPIキーの流出を防ぐため、インターネットからの直接アクセスを完全に遮断しています。

- アクセス制御: Uniform（均一性）
  - Hierarchical Namespace との互換性を保ちつつ、IAM（Identity and Access Management）による一元的な権限管理を行い、最小権限の原則（Least Privilege）を適用しています。


## 🛠 開発環境の設定 (VSCode)

本プロジェクトでは `Ruff` を使用したコードの自動整形を推奨しています。以下の設定を行うことで、保存時に自動でインポート順の整理とコードフォーマットが行われます。

1. **拡張機能のインストール**:
   - [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) 拡張機能をインストールします。

2. **VSCode 設定の適用**:
   プロジェクト直下の `.vscode/settings.json` に以下の設定を追加してください（リポジトリに含まれている場合は不要です）。

  ```json
   {
     "[python]": {
       "editor.defaultFormatter": "charliermarsh.ruff",
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
         "source.organizeImports.ruff": "explicit",
         "source.fixAll.ruff": "explicit"
       }
     }
   }
  ```


## 開発プロセス

実務的なチーム開発を想定し、以下のワークフローを採用しています。

### ブランチ戦略 (GitHub Flow)
本プロジェクトでは GitHub Flow を採用しています。
1. `main` ブランチから`feat/`, `fix/` などの接頭辞を用いた機能単位のブランチを作成
2. 実装完了後、GitHub 上でプルリクエストを作成
3. セルフレビューを経て `main` ブランチへマージ
4. `main` ブランチは常にデプロイ可能な状態を維持

### 💡 開発効率化：AIによるコミットメッセージ生成 (`gdc`)

本プロジェクトでは、`git diff` を解析して AI に適切なコミットメッセージを提案させるためのカスタムコマンド `gdc` (Git Diff Copy) の導入を推奨しています。

#### 設定方法

`~/.bashrc` (Git Bash) または `$PROFILE` (PowerShell) に以下の関数を追記してください。



<details>
<summary>Git Bash (.bashrc) 用の設定</summary>

```bash
# ホームディレクトリへ移動
cd ~

# 設定ファイル（.bashrc）の作成
touch .bashrc

# Git Bash起動時に .bashrc を読み込むための設定 (.bash_profile)
touch .bash_profile
echo "if [ -f ~/.bashrc ]; then . ~/.bashrc; fi" >> .bash_profile
```

```bash
function gdc() {
  if [ -z "$(git diff --cached)" ]; then
    echo "No staged changes found. Please 'git add' files first."
    return 1
  fi

  (
    echo "以下の git diff から、コミットメッセージの候補を3つ提案してください。"
    echo "【制約条件】"
    echo "- 各候補はそのままターミナルで実行できるよう git commit -m \"[メッセージ]\" の形式で出力してください。"
    echo "- メッセージ自体は英語（English）で作成してください。"
    echo "- GitHub Flow / Conventional Commits 形式（feat:, fix: 等）を使用してください。"
    echo "- 各候補の後に、なぜそのメッセージを選んだのかの解説を「日本語」で添えてください。"
    echo "- コミットメッセージ以外の解説や説明はすべて「日本語」で行ってください。"
    echo "---"
    git diff --cached
  ) | powershell.exe -NoProfile -Command "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; [Console]::In.ReadToEnd() | Set-Clipboard"
  echo "Prompt with 'git commit -m' copied to clipboard!"
}
```



</details>

<details>
<summary>PowerShell 用の設定</summary>

```powershell
function gdc {
    $diff = git diff --cached
    if (-not $diff) {
        Write-Host "No staged changes found." -ForegroundColor Yellow
        return
    }
    $prompt = @"
以下の git diff から、コミットメッセージの候補を3つ提案してください。
【制約条件】
- 各候補はそのままターミナルで実行できるよう git commit -m "[メッセージ]" の形式で出力してください。
- メッセージ自体は英語（English）で作成してください。
- GitHub Flow / Conventional Commits 形式（feat:, fix: 等）を使用してください。
- 各候補の後に、なぜそのメッセージを選んだのかの解説を「日本語」で添えてください。
- コミットメッセージ以外の解説や説明はすべて「日本語」で行ってください。
---
"@
    ($prompt + "`n" + $diff) | Set-Clipboard
    Write-Host "Prompt with 'git commit -m' copied to clipboard!" -ForegroundColor Green
}

```

</details>

<details>
<summary>macOS (zsh / bash) 用の設定</summary>

macOSでは `pbcopy` コマンドを使用してクリップボードに送ります。

```bash
function gdc() {
  if [ -z "$(git diff --cached)" ]; then
    echo "No staged changes found. Please 'git add' files first."
    return 1
  fi

  (
    echo "以下の git diff から、コミットメッセージの候補を3つ提案してください。"
    echo "【制約条件】"
    echo "- 各候補はそのままターミナルで実行できるよう git commit -m \"[メッセージ]\" の形式で出力してください。"
    echo "- メッセージ自体は英語（English）で作成してください。"
    echo "- GitHub Flow / Conventional Commits 形式（feat:, fix: 等）を使用してください。"
    echo "- 各候補の後に、なぜそのメッセージを選んだのかの解説を「日本語」で添えてください。"
    echo "- コミットメッセージ以外の解説や説明はすべて「日本語」で行ってください。"
    echo "---"
    git diff --cached
  ) | pbcopy
  echo "Prompt with 'git commit -m' copied to clipboard!"
}

```

</details>


#### 使い方

1. `git add .` で変更をステージング。
2. ターミナルで `gdc` を実行。
3. ブラウザで Gemini 等に貼り付け。
4. 提案された `git commit -m "..."` をコピーしてターミナルで実行。

### ディレクトリ構成 (Modular Design)

将来的な機能拡張（動画解析、BI連携など）に柔軟に対応できるよう、役割ごとにディレクトリを分離しています。

- `src/core/`: 外部サービス（Gemini, GCS）との接続・認証を担うコア基盤
- `src/schemas/`: AIのレスポンス（JSON）の型定義（予定）
- `src/processors/`: 動画のチャンク化などメディア処理ロジック（予定）
- `upload/`: 処理対象メディアの一時保管ディレクトリ（`.gitignore` 対象）
