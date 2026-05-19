# FRONTEND.md - UI / Template Guide

## 🎨 Stack

- **テンプレートエンジン**: Jinja2（`src/api/templates/`）
- **CSS**: Tailwind CSS（CDN）
- **インタラクション**: htmx（フォーム送信・部分更新）

## 📄 新しい画面を追加する手順

1. `src/api/templates/<feature>.html` を作成
   - 既存の `search.html` や `agent.html` をベースにする
2. `src/api/main.py` にGETルートを追加

   ```python
   @app.get("/<feature>", response_class=HTMLResponse)
   async def <feature>(request: Request):
       return templates.TemplateResponse("<feature>.html", {"request": request})
   ```

3. APIとの通信には htmx を使い、レスポンスはHTML断片で返す

## 🖊 HTML Formatting

- `.prettierrc` に基づき整形すること
- コマンド: `npx prettier --write src/api/templates/`

## ⚠️ Safari WebKit Known Pitfalls

### `white-space: pre-wrap` は Tailwind クラスではなくインラインスタイルで指定する

Tailwind Play CDN は JavaScript でページの静的 HTML をスキャンして CSS を生成するため、`innerHTML` で動的に追加した要素のクラスが CSS 生成対象にならない場合がある。Safari WebKit は CSS が未適用の場合に改行を無視するため、改行を保持したいテキスト表示には必ずインラインスタイルを使うこと。

```html
<!-- NG: innerHTML で動的生成した要素に Tailwind クラス -->
<div class="whitespace-pre-wrap">...</div>

<!-- OK: インラインスタイルで直接指定 -->
<div style="white-space: pre-wrap;">...</div>
```

### detached な table 要素に `innerHTML` で子要素を設定しない

Safari WebKit では、DOM に挿入する前の `<tr>` 要素に `innerHTML` で `<td>` を設定すると失敗するケースがある。`createElement` + `textContent` + `appendChild` で構築すること。

```javascript
// NG: detached <tr> への innerHTML
const tr = document.createElement("tr");
tr.innerHTML = `<td>${value}</td>`;

// OK: DOM API で構築
const tr = document.createElement("tr");
const td = document.createElement("td");
td.textContent = value;
tr.appendChild(td);
```

### `fetch` のエラーハンドリングで `finally` に注意

`finally` ブロックで `setLoading(false)` などを呼ぶ場合、`catch` でセットしたエラー表示を上書きしないよう注意する。エラーボックスを隠す処理はリクエスト開始時（`isLoading === true`）のみ行うこと。

```javascript
function setLoading(isLoading) {
  // ...
  if (isLoading) {
    document.getElementById("error-box").classList.add("hidden"); // 開始時のみ隠す
  }
}
```
