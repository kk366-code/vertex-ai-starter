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
