# Cookie手動エクスポート手順

## 1. Chrome拡張機能のインストール

以下のいずれかをインストールしてください：
- **EditThisCookie**: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
- **Cookie-Editor**: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm

## 2. Keibabookにログイン

1. Chromeで https://s.keibabook.co.jp/ を開く
2. ログイン（既にログイン済みならスキップ）

## 3. Cookieをエクスポート

### EditThisCookieの場合:
1. 拡張機能アイコンをクリック
2. 「Export」ボタンをクリック（クリップボードにコピーされます）
3. メモ帳を開いて貼り付け
4. `c:\GeminiCLI\TEST\keibabook\cookies.json` として保存

### Cookie-Editorの場合:
1. 拡張機能アイコンをクリック
2. 右上の「Export」ボタンをクリック
3. 「JSON」形式を選択
4. コピーしてメモ帳に貼り付け
5. `c:\GeminiCLI\TEST\keibabook\cookies.json` として保存

## 4. スクレイパーを実行

```powershell
cd c:\GeminiCLI\TEST\keibabook
python run_scraper.py
```

## 注意事項

- Cookieには有効期限があります（通常は数週間〜数ヶ月）
- 期限が切れたら、再度エクスポートが必要です
- `cookies.json` は個人情報を含むため、共有しないでください
