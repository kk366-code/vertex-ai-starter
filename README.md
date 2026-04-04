# Gemini Analysis API Starter

`uv` と Google Cloud Vertex AI (Gemini) を利用した AI バックエンドのプロジェクトを素早く、かつベストプラクティスに沿って開始するためのテンプレートとして開発しています。

> [!NOTE]
> **本ドキュメントの構成について**
> このREADMEは、プロジェクトの概要説明だけでなく、**「誰でも迷わずに開発環境を構築できる詳細な手順書」**として整理されています。
> ローカル開発からクラウドデプロイまで、一貫したワークフローを提供します。

## 🚀 特徴

- **Vertex AI (Gemini) 最適化**: `google-genai` を使用
- **モダンなパッケージ管理**: `uv` による高速で再現可能な環境構築
- **テスト・デプロイ自動化**: 自動ビルド・テストパイプラインへの統合をサポート

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

> **⚠️Git Bash をメインで使用する場合**
> Windows のパス（スペースを含む `Cloud SDK` など）が原因でコマンドが認識されないことがあります。以下の設定を必ず行ってください。
>
> ```bash
> # .bashrc にエイリアスを追記
> echo "alias gcloud='gcloud.cmd'" >> ~/.bashrc
>
> # 設定を反映
> source \~/.bashrc
>
>```

---

### 2. Python 環境の紐付け (重要)

`gcloud` は Python 3.10 以上を必要とします。本プロジェクトでは `uv` で管理している Python を使用することを推奨します。

```bash
# uv で Python 3.14 をインストール
uv python install 3.14

# gcloud が使用する Python を指定 (macOS/Linux)
export CLOUDSDK_PYTHON=$(uv python find 3.14)

# Windows (PowerShell) の場合
$env:CLOUDSDK_PYTHON = (uv python find 3.14)
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

### ターミナルから VSCode を開く設定 (`code` コマンド)

ターミナルから直接ファイルやフォルダを開けるように、`code` コマンドをインストールしておくことを推奨します。

1. VSCode を起動し、`Command (⌘) + Shift + P` を押してコマンドパレットを開きます。
2. 「**shell command**」と入力し、「**シェル コマンド: PATH 内に 'code' コマンドをインストールします**」を選択します。
3. 権限の許可を求められたら承認します。

これで、プロジェクトルートで `code .` と打つだけで VSCode が起動するようになります。

### Ruff の設定

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

## 🚀 実行方法 (Usage)

### 1. ローカルでの起動

依存関係の管理には `uv` を使用しています。

```bash
# 依存関係のインストール
uv sync

# サーバーの起動（ポート8000で起動します）
uv run uvicorn src.api.main:app --reload

```

## 開発プロセス

実務的なチーム開発を想定し、以下のワークフローを採用しています。

### ブランチ戦略 (GitHub Flow)

本プロジェクトでは GitHub Flow を採用しています。

1. `main` ブランチから`feat/`, `fix/` などの接頭辞を用いた機能単位のブランチを作成
2. 実装完了後、GitHub 上でプルリクエストを作成
3. セルフレビューを経て `main` ブランチへマージ
4. `main` ブランチは常にデプロイ可能な状態を維持

### 🔄 ブランチ切り替え時の注意点（環境の同期）

別のブランチ（例：feat/ から main）へ切り替えた際、Git はソースコードを戻しますが、.gitignoreに指定されている.venv 内の内容は変更しません。uv add でインストールしたライブラリ等が .venv に残っていると、Mypy で予期しない型エラーが発生することがあります。

ブランチを切り替えた後は、必ず以下のコマンドで環境を同期させてください。

```bash
# 設計図(uv.lock)と実体(.venv)を同期し、不要なパッケージを削除する
uv sync

# もし型エラーが解消されない場合は、仮想環境を再構築してください
rm -rf .venv && uv sync

```


### 💡 開発効率化：AIによるコミットメッセージ生成 (`gdc`)

本プロジェクトでは、`git diff` を解析して AI に適切なコミットメッセージを提案させるためのカスタムコマンド `gdc` (Git Diff Copy) の導入を推奨しています。

**なぜこの方法を採用するのか：**

- **完全無料**: `aicommits` 等のツールとは異なり、有料の API キー（OpenAI API 等）を取得する必要がありません。
- **ブラウザ活用**: `git diff` とプロンプトを1コマンドでコピーし、普段お使いの ChatGPT や Gemini、Claude のブラウザ版に貼り付けるだけで最適なメッセージが得られます。
- **高精度**: 最新の LLM ブラウザ版を利用することで、常に賢いモデルの提案を受けることができます。

#### 設定方法

<details>
<summary>macOS (zsh / bash) 用の設定</summary>

macOSでは `pbcopy` コマンドを使用してクリップボードに送ります。

1. 設定ファイルを開く

```bash
# zsh の場合
code ~/.zshrc

# bash の場合 (古いOSや明示的に変更している場合)
code ~/.bashrc
```

1. 以下の関数を設定ファイルに追記

```bash
function gdc() {
  # 1. ステージングされている差分があるか確認
  local diff=$(git diff --cached)

  if [ -z "$diff" ]; then
    echo "❌ No staged changes found."
    echo "先に 'git add' を実行して、コミットしたいファイルを選択してください。"
    return 1
  fi

  (
    echo "以下の git diff から、コミットメッセージの候補を3つ提案してください。"
    echo "【制約条件】"
    echo "- 1行のタイトルのみで書いてください。詳細（Body）は不要です。Bodyの提案も不要です。"
    echo "- コピペしやすいように、コマンドはコードブロック形式で出力してください。"
    echo "- 各候補はそのままターミナルで実行できるよう git commit -m \"[メッセージ]\" の形式で出力してください。"
    echo "- メッセージ自体は英語（English）で作成してください。"
    echo "- GitHub Flow / Conventional Commits 形式（feat:, fix: 等）を使用してください。"
    echo "- 各候補の後に、なぜそのメッセージを選んだのかの解説を「日本語」で添えてください。"
    echo "- コミットメッセージ以外の解説や説明はすべて「日本語」で行ってください。"
    echo "---"
    echo "$diff"
  ) | pbcopy
  echo "Prompt with 'git commit -m' copied to clipboard!"
}

```

1. 設定を反映

```bash
source ~/.zshrc  # zsh の場合
# または source ~/.bashrc
```

</details>

<details>
<summary>Git Bash (.bashrc) 用の設定</summary>

1. 設定ファイルの作成

```bash
# ホームディレクトリへ移動
cd ~

# 設定ファイル（.bashrc）の作成
touch .bashrc

# Git Bash起動時に .bashrc を読み込むための設定 (.bash_profile)
touch .bash_profile
echo "if [ -f ~/.bashrc ]; then . ~/.bashrc; fi" >> .bash_profile
```

1. 関数の作成

`~/.bashrc` (Git Bash) に以下の関数を追記してください。

```bash
function gdc() {
  if [ -z "$(git diff --cached)" ]; then
    echo "No staged changes found. Please 'git add' files first."
    return 1
  fi

  (
    echo "以下の git diff から、コミットメッセージの候補を3つ提案してください。"
    echo "【制約条件】"
    echo "- 1行のタイトルのみで書いてください。詳細（Body）は不要です。Bodyの提案も不要です。"
    echo "- 各候補はそのままターミナルで実行できるよう git commit -m \"[メッセージ]\" の形式で出力してください。"
    echo "- コピペしやすいように、コマンドはコードブロック形式で出力してください。"
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

1. 設定の有効化

```bash
# 有効化する
source ~/.bashrc
```

</details>

<details>
<summary>PowerShell 用の設定</summary>

`$PROFILE` (PowerShell) に以下の関数を追記します。

```powershell
function gdc {
    # PowerShellが外部コマンド（git）から受け取るエンコーディングをUTF-8に設定
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    # 出力のエンコーディングを UTF8 に一時的に固定（Gitの日本語出力を正しく受け取るため）
    $OutputEncoding = [System.Text.Encoding]::UTF8

    $diff = git diff --cached
    if (-not $diff) {
        Write-Host "No staged changes found." -ForegroundColor Yellow
        return
    }
    $prompt = @"
以下の git diff から、コミットメッセージの候補を3つ提案してください。
【制約条件】
- 1行のタイトルのみで書いてください。詳細（Body）は不要です。Bodyの提案も不要です。
- コピペしやすいように、コマンドはコードブロック形式で出力してください。
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

### 手順

1. 設定ファイルの作成と編集

PowerShellを開き、以下のコマンドを順番に実行して設定ファイルを準備します。

```bash
# 1. 設定ファイルのパスを確認
$PROFILE

# 2. ファイルが存在しない場合は作成（フォルダごと強制作成）
if (!(Test-Path $PROFILE)) {
    New-Item -Type File -Path $PROFILE -Force
}

# 3. VS Code で設定ファイルを開く
code $PROFILE

```

1. 関数の追記と保存（重要：文字コード）

開いたファイルに、先ほどの function gdc { ... } を貼り付けます。

> ⚠️
> **重要：保存時の文字コードについて**
>
> PowerShellで日本語を正しく扱うため、VS Code の右下にあるエンコーディング設定から **UTF-8 with BOM** を選択して保存してください。

1. 設定の反映

保存後、以下のコマンドを打つか PowerShell を再起動すれば gdc が有効になります。

```bash
# $PROFILE を UTF-8 with BOM で保存しなおしたときなども以下を実行
. $PROFILE

```

</details>

#### 使い方

1. `git add .` で変更をステージング。
2. ターミナルで `gdc` を実行。
3. ブラウザで Gemini 等に貼り付け。
4. 提案された `git commit -m "..."` をコピーしてターミナルで実行。

### 💡 開発効率化：AIへのコンテキスト共有 (`axc`)

AIアシスタントとの新しいチャットを開始する際、プロジェクトの全コードと規約（`CLAUDE.md`, `SKILL.md`）を瞬時に共有するためのコマンド `axc` (AI Context Copy) の導入を推奨します。

#### 必要なランタイムのインストール

- **Node.js (LTS推奨)**: AIコンテキスト生成ツール (`repomix`) の実行に必要です。
- [Node.js 公式サイト](https://nodejs.org/) からインストールするか、パッケージマネージャー（`brew`, `nvm`, `fnm` 等）を使用してください。

<details>
<summary>macOS (zsh) 用の設定</summary>

`~/.zshrc` に以下の関数を追記してください（`pbcopy` を使用）。

```bash
function axc() {
  echo "🔄 Generating codebase context..."
  (
    echo "このプロジェクトのコードベースを渡します。特に CLAUDE.md にあるプロジェクト構造と、SKILL.md にある実装パターン（Python 3.14+, Pydantic, Vertex AIの非同期処理など）を厳守してください。これ以降、新しいコードの提案や修正はすべてこれらの規約に従ってください。"
    echo "---"
    npx repomix --stdout
  ) | pbcopy
  echo "✅ Codebase and prompt copied to clipboard!"
}

function axp() {
  local agent_name=$1
  local agent_file="agents/${agent_name}.md"
  local output_file="repomix-context.xml"

  # 以前の残骸（repomix-context.xml）があれば掃除
  rm -f "$output_file"

  echo "🔄 Packing codebase for Gemini... (Agent: ${agent_name:-None})"

  {
    # AIエンジニアとしてのアイデンティティと指示を最上部に配置
    echo "<agent_context>"
    if [ -n "$agent_name" ] && [ -f "$agent_file" ]; then
      cat "$agent_file"
      echo -e "\n---\n"
    fi
    echo "このプロジェクトのコードベースを渡します。特に CLAUDE.md の構造と SKILL.md の実装パターンを厳守してください。"
    echo "</agent_context>"
    
    # Repomixを実行して標準出力を結合
    npx repomix --style xml --compress --remove-comments --remove-empty-lines --output -
  } > "$output_file"

  if [ -s "$output_file" ]; then
    echo "✅ Success! Please upload '$output_file' to Gemini."
    # Macの場合、Finderでファイルを選択状態にするとさらに便利
    # open -R "$output_file"
  else
    echo "❌ Error: Failed to generate $output_file"
  fi
}
```

</details>

<details>
<summary>Git Bash (.bashrc) 用の設定</summary>

`~/.bashrc` に以下の関数を追記してください。

```bash
function axc() {
  echo "🔄 Generating codebase context..."
  (
    echo "このプロジェクトのコードベースを渡します。特に CLAUDE.md にあるプロジェクト構造と、SKILL.md にある実装パターン（Python 3.14+, Pydantic, Vertex AIの非同期処理など）を厳守してください。これ以降、新しいコードの提案や修正はすべてこれらの規約に従ってください。"
    echo "---"
    npx repomix --stdout
  ) | powershell.exe -NoProfile -Command "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; [Console]::In.ReadToEnd() | Set-Clipboard"
  echo "✅ Codebase and prompt copied to clipboard!"
}

```

</details>

<details>
<summary>PowerShell 用の設定</summary>

`$PROFILE` に以下の関数を追記してください。

```powershell
function axc {
    # エンコーディング設定
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    
    Write-Host "🔄 Generating codebase context with npx repomix..." -ForegroundColor Cyan
    $prompt = @"
このプロジェクトのコードベースを渡します。特に CLAUDE.md にあるプロジェクト構造と、SKILL.md にある実装パターン（Python 3.14+, Pydantic, Vertex AIの非同期処理など）を厳守してください。これ以降、新しいコードの提案や修正はすべてこれらの規約に従ってください。
---
"@
    # repomixを実行して出力を取得
    $repoContent = npx repomix --stdout
    ($prompt + "`n" + $repoContent) | Set-Clipboard
    Write-Host "✅ Codebase and prompt copied to clipboard!" -ForegroundColor Green
}

```

> ⚠️
> 保存時は **UTF-8 with BOM** で保存してください。

</details>

#### 使い方

1. ターミナルで `axc` を実行。
2. AI（ChatGPT, Claude, Gemini等）のチャット欄に貼り付け。
3. これだけで、AIは最新のコードとプロジェクト固有のルールを完全に把握した状態で回答を開始します。

### 💡 開発効率化：AIへのコンテキスト共有 (`axp`)

AIアシスタントとの新しいチャットを開始する際、プロジェクトの全コードと規約（`CLAUDE.md`, `SKILL.md`）、さらに特定の **エージェント指示書** をパッケージ化して共有するためのコマンド `axp` (AI Context Pack) の導入を推奨します。

クリップボードの容量制限（トークン制限）を回避し、Geminiのファイルアップロード機能を最大限に活用します。

#### 必要なランタイムのインストール

- **Node.js (LTS推奨)**: AIコンテキスト生成ツール (`repomix`) の実行に必要です。
- [Node.js 公式サイト](https://nodejs.org/) からインストールしてください。

<details>

<summary>macOS (zsh) / Git Bash (.bashrc) 用の設定</summary>
`~/.zshrc`（Mac）または `~/.bashrc`（Git Bash）に以下の関数を追記してください。

1. 設定ファイルを開く

    ```bash
    # zsh の場合
    code ~/.zshrc

    # bash の場合 (古いOSや明示的に変更している場合)
    code ~/.bashrc
    ```

1. 以下のコードを追記

    ```bash
    function axp() {
      local agent_name=$1
      local agent_file="agents/${agent_name}.md"
      local output_file="repomix-context.xml"

      # 以前のファイルを掃除
      [ -f "$output_file" ] && rm "$output_file"

      echo "🔄 Packing codebase for Gemini... (Agent: ${agent_name:-None})"

      {
        echo "<agent_context>"
        if [ -n "$agent_name" ] && [ -f "$agent_file" ]; then
          cat "$agent_file"
          echo -e "\n---\n"
        fi
        echo "このプロジェクトのコードベースを渡します。特に CLAUDE.md の構造と SKILL.md の実装パターンを厳守してください。"
        echo "</agent_context>"
        
        # Repomixを実行して標準出力を結合
        npx repomix --style xml --compress --remove-comments --remove-empty-lines --output -
      } > "$output_file"

      if [ -s "$output_file" ]; then
        echo "✅ Success! Please upload '$output_file' to Gemini."
        # エクスプローラー/Finderでファイルを選択状態にする
        if [[ "$OSTYPE" == "darwin"* ]]; then
          open -R "$output_file"
        else
          explorer.exe /select,$(cygpath -w "$output_file")
        fi
      else
        echo "❌ Error: Failed to generate $output_file"
        return 1
      fi
    }
    ```

1. 設定の有効化

    ```bash
    # zshの場合
    source ~/.zshrc

    # bashの場合
    source ~/.bashrc

    ```

</details>

<details>

<summary>WSL (zsh / bash) 用の設定</summary>

WSLのターミナル（Ubuntu等）で ~/.zshrc または ~/.bashrc に追記してください。

1. WSL上で設定ファイルを開く：

    ```bash
    code ~/.zshrc  # もしくは ~/.bashrc
    ```

1. 以下のコードを末尾に貼り付けて保存。

    ```bash
    function axp() {
      local agent_name=$1
      local agent_file="agents/${agent_name}.md"
      local output_file="repomix-context.xml"

      # 以前の残骸を掃除
      [ -f "$output_file" ] && rm "$output_file"

      echo "🔄 Packing codebase for Gemini... (Agent: ${agent_name:-None})"

      {
        echo "<agent_context>"
        if [ -n "$agent_name" ] && [ -f "$agent_file" ]; then
          cat "$agent_file"
          echo -e "\n---\n"
        fi
        echo "このプロジェクトのコードベースを渡します。特に CLAUDE.md の構造と SKILL.md の実装パターンを厳守してください。"
        echo "</agent_context>"
        
        # Repomixを実行して標準出力を結合
        npx repomix --style xml --compress --remove-comments --remove-empty-lines --output -
      } > "$output_file"

      if [ -s "$output_file" ]; then
        echo "✅ Success! Please upload '$output_file' to Gemini."
        
        # WSLからWindowsのエクスプローラーを起動し、ファイルをハイライトする
        # wslpath -w でLinuxパスをWindowsパスへ変換して explorer.exe に渡します
        powershell.exe -c "explorer.exe /select,$(wslpath -w "$output_file")"
      else
        echo "❌ Error: Failed to generate $output_file"
        return 1
      fi
    }

    ```

1. 設定を反映：

    ```bash
    source ~/.zshrc  # もしくは ~/.bashrc

</details>

<details>
<summary>PowerShell 用の設定</summary>

1. $PROFILE を開きます。

    ```powershell
    code $PROFILE

    ```

1. `$PROFILE` に以下の関数を追記してください。

    ```powershell
    function axp {
        param (
            [string]$AgentName
        )

        $agentFile = "agents/${AgentName}.md"
        $outputFile = "repomix-context.xml"

        # 以前の残骸を削除
        if (Test-Path $outputFile) { Remove-Item $outputFile }

        Write-Host "🔄 Packing codebase for Gemini... (Agent: $(if ($AgentName) { $AgentName } else { 'None' }))" -ForegroundColor Cyan

        try {
            # 文字化け防止のため、出力をUTF8に強制設定
            $OutputEncoding = [System.Text.Encoding]::UTF8

            # 文字化け防止のため、外部コマンドからPowerShellが受け取る文字コードの設定
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            
            # 1. エージェント情報の構築
            $header = "`n<agent_context>`n"
            $footer = "このプロジェクトのコードベースを渡します。特に CLAUDE.md の構造と SKILL.md の実装パターンを厳守してください。`n</agent_context>`n"
            
            # ヘッダーを新規作成 (BOMなしUTF8)
            [System.IO.File]::WriteAllLines((Join-Path $PWD $outputFile), $header, (New-Object System.Text.UTF8Encoding $false))

            # エージェントファイルがあれば追記
            if ($AgentName -and (Test-Path $agentFile)) {
                $agentContent = Get-Content -Raw -Encoding UTF8 $agentFile
                $agentContent += "`n---`n"
                Add-Content -Path $outputFile -Value $agentContent -Encoding UTF8
            }

            # フッターを追記
            Add-Content -Path $outputFile -Value $footer -Encoding UTF8

            # 2. Repomixの結果を追記 (パイプラインの文字化けを防ぐため一度変数に受ける)
            $repoOutput = npx repomix --style xml --compress --remove-comments --remove-empty-lines --output -
            Add-Content -Path $outputFile -Value $repoOutput -Encoding UTF8

            # 完了チェック
            if ((Get-Item $outputFile).Length -gt 0) {
                Write-Host "✅ Success! Please upload '$outputFile' to Gemini." -ForegroundColor Green
                Start-Process explorer.exe "/select,$outputFile"
            }
        }
        catch {
            Write-Host "❌ Error: Failed to generate $outputFile" -ForegroundColor Red
            Write-Error $_
        }
    }
    ```

1. 設定の有効化

    ```powershell
    . $PROFILE

    ```

> ⚠️ ps1ファイルの保存時は **UTF-8 with BOM** で保存してください。

</details>

#### 使い方

1. **エージェントの指定なし（基本）**

    ```bash
    axp
    ```

    `repomix-context.xml` が生成されます。

2. **特定のエージェント（役割）を指定する場合**
    `agents/architect.md` などを用意している場合：

    ```bash
    axp architect
    ```

    指示書の指示が最優先される形でパッケージ化されます。

3. **Geminiへアップロード**
    コマンド実行後に自動で開くエクスプローラーから、`repomix-context.xml` を Gemini のチャット欄にドラッグ＆ドロップしてください。

### ディレクトリ構成

将来的な機能拡張（動画解析、BI連携など）に柔軟に対応できるよう、役割ごとにディレクトリを分離しています。

- `src/core/`: 外部サービス（Gemini, GCS）との接続・認証を担うコア基盤
- `src/schemas/`: AIのレスポンス（JSON）の型定義（予定）
- `src/processors/`: 動画のチャンク化などメディア処理ロジック（予定）
- `upload/`: 処理対象メディアの一時保管ディレクトリ（`.gitignore` 対象）

## 🛡️ セキュリティへの取り組み

本プロジェクトでは、機密情報の漏洩を未然に防ぐため、以下の対策を講じています。

### Gitleaks によるシークレットスキャン

リポジトリのコミット履歴やソースコード内に、APIキーやパスワードなどの秘密情報が混入していないかを確認するため、`gitleaks` を導入しています。

- **実行コマンド**:

  ```bash
  gitleaks detect --verbose

  ```

- **Git Pre-commit Hook**:
`pre-commit` フレームワークを利用し、ローカルでのコミット時に自動的にスキャンを実行します。
APIキーや認証情報がコードに含まれている場合、コミットが自動的にブロックされます。

#### 設定の有効化方法

開発に参加する場合は、以下のコマンドでフックを有効にしてください。

```bash
uv run pre-commit install

```

## 🚀 デプロイ (Google Cloud Run)

本プロジェクトは、スケーラビリティとコスト効率を両立するため、Google Cloud Run（サーバーレス）へのデプロイを前提としています。

### 🏗️ インフラ構成

- **Runtime**: Python 3.14 (Docker)
- **Deployment**: Google Cloud Run
- **CI/CD**: GitHub + Cloud Build (推奨)
- **AI Backend**: Vertex AI (Gemini 2.5 Flash)

### 1. APIの有効化

プロジェクトを初めて使用する場合は。以下のコマンドを実行して、必要なサービスを有効化してください。

```bash
gcloud services enable run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       aiplatform.googleapis.com

```

### 2. IAM権限の設定

Cloud Run から Vertex AI を呼び出すために、実行サービスアカウントに権限を付与します。

#### 🐧 Linux / macOS (bash, zsh)

```bash
# プロジェクト情報の取得
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Vertex AI ユーザー権限の付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"

# GCS 操作権限の付与（画像解析を利用する場合）
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectUser"

```

#### 🪟 Windows (PowerShell)

```powershell
# プロジェクト情報の取得
$PROJECT_ID = gcloud config get-value project
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format='value(projectNumber)'
$SERVICE_ACCOUNT = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# 権限の付与
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/storage.objectUser"

```

---

### 3. デプロイの実行

uv を使用した Docker ビルドを行い、Cloud Run へデプロイします。
初回デプロイ時は、サービス名 と バケット名 を任意のものに書き換えて実行してください。

#### 🐧 Linux / macOS (bash, zsh) の場合

```bash
SERVICE_NAME=サービス名 # 変更してください
BUCKET_NAME=バケット名  # 変更してください

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project), \ GOOGLE_CLOUD_LOCATION=asia-northeast1, \
    GCS_BUCKET_NAME=$BUCKET_NAME

```

#### 🪟 PowerShell の場合

```powershell
# 設定変数
$PROJECT_ID = gcloud config get-value project
$SERVICE_NAME = "サービス名"
$BUCKET_NAME = "バケット名"

# デプロイ実行
gcloud run deploy $SERVICE_NAME `
    --source . `
    --region asia-northeast1 `
    --allow-unauthenticated `
    --set-env-vars `
"GOOGLE_CLOUD_PROJECT=$PROJECT_ID,`
GOOGLE_CLOUD_LOCATION=asia-northeast1,`
GCS_BUCKET_NAME=$BUCKET_NAME"

```

#### 🟦 Git Bash (Windows) の場合

Windows の Git Bash を使用している場合、パス内のスペースに起因するエラーを防ぐため、以下の手順で実行してください。

```bash
# 1. 変数の設定（サービス名とバケット名を書き換えてください）
SERVICE_NAME="サービス名"
BUCKET_NAME="バケット名"
PROJECT_ID=$(gcloud config get-value project)

# 2. デプロイの実行
# ※改行時のバックスラッシュ（\）の後にスペースが入らないよう注意してください
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=asia-northeast1,GCS_BUCKET_NAME=$BUCKET_NAME

```

### ⚠️ デプロイ時の注意点 (BuildKit)

 ~~Google Cloud Build で `uv` のキャッシュマウント機能を利用するため、ビルド時に **BuildKit** を有効にする必要があります。デプロイコマンドを実行する際は、必ず `--set-build-env-vars DOCKER_BUILDKIT=1` フラグを含めてください。~~

当初は uv のキャッシュマウント機能（BuildKit）を利用してビルド時間の短縮を図っていましたが、Cloud Build 環境での互換性を重視し、現在は標準的なマルチステージビルド構成を採用しています。これにより、特定のビルド環境に依存せず、安定したデプロイが可能です。

### 新しいPCでデプロイする場合

```bash
# 1. ブラウザが起動するので、前回と同じアカウントでログイン
gcloud auth login

# 2. プロジェクト一覧を確認し、対象のプロジェクトIDをコピー
gcloud projects list

# 3. デプロイ先のプロジェクトを固定
gcloud config set project [YOUR_PROJECT_ID]

# 上記「3. デプロイの実行」へ
    
```

### APIキーを設定してデプロイ

既存の設定を維持したまま、特定の環境変数を更新するには --update-env-vars を使用します。

**🐧 bash/zsh:**

```bash
# = の後に不要なスペースなどが入らないように注意
gcloud run services update $SERVICE_NAME \
    --region asia-northeast1 \
    --update-env-vars INTERNAL_API_KEY=設定したいAPIキー

```

**🪟 PowerShell:**

```powershell
gcloud run services update $SERVICE_NAME `
    --region asia-northeast1 `
    --update-env-vars INTERNAL_API_KEY=設定したいAPIキー

```

### デプロイ済みコンテナの設定を一部だけ変更する

**🐧 bash/zsh:**

```bash
gcloud run services update $SERVICE_NAME \
    --region asia-northeast1 \
    --max-instances 1 \
    --min-instances 0

```

**🪟 PowerShell:**

```bash
gcloud run services update $SERVICE_NAME `
    --region asia-northeast1 `
    --max-instances 1 `
    --min-instances 0

```

### 📈 運用の工夫（スケーリングとコスト最適化）

本プロジェクトでは Google Cloud Run のサーバーレス特性を活かし、以下の運用ルールを適用しています。

- **コスト最適化**: 通常時は `min-instances: 0` に設定し、リクエストがない時間帯の課金をゼロに抑えています。
- **ユーザー体験の向上**: コールドスタートによる遅延を防止したい場合、以下のコマンドでインスタンスを常時起動（`min-instances: 1`）させることができます。

```bash
# インスタンスをウォームアップ状態にするコマンド
gcloud run services update gemini-analysis-api --min-instances 1 --region asia-northeast1

```
