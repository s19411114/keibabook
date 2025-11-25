# Opus & Haiku Handover — KeibaBook Scraper

## 目的
Opus と Haiku 向けの作業引継ぎファイルです。現状の問題、これまでに実施した修正、再現手順、優先度の高い問題、テスト/計測コマンド、および期待する成果を含みます。

---

## 現状サマリ（短く）
- 問題: 1レースのスクレイプが極端に遅く（数時間に達する）なるケースがあり、4+時間の報告あり
- 修正済み: 429バックオフの上限短縮、RateLimiter のレンジ調整（1–2秒）、Docker イメージ改善、会場名の正規化、テスト修正。
- 検証済み: 主要ユニットテスト 24 件パス（`pytest` 非スローグループ）。
- 未解決: 実行環境（Docker vs ホスト）ごとのパフォーマンス差、run_pedigree の長時間処理、429 頻度と並列制御の最適化。

---

## 重要アーティファクト（すぐ見るもの）
- `issues/PERFORMANCE_ANALYSIS.md` — 詳細分析
- `issues/HANDOVER_TASKS.md` — 大きな改善タスク
- `issues/claudeopus_bundle.md`、`issues/claudeopus_request.md` — もともとの review bundle
- `issues/attachments/keibabook_sample_logs.zip` — サンプルログ
- 新規: `issues/OPUS_HAIKU_HANDOVER.md`（このファイル）

---

## 再現手順（ホスト）
1. 仮想環境を有効化（WSL かローカル Python）
2. 依存パッケージをインストール（project root）:

```powershell
python -m pip install -r requirements.txt
```

3. 1レース（浦和 9R）を測定付きで実行:

```powershell
$env:PYTHONPATH='C:\GeminiCLI\TEST\keibabook';
Measure-Command { C:/path/to/python.exe scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files }
```

- 実行結果: `data/` に JSON が書かれる。perf ログは CONSOLE に出る（`--perf`）。
- デバッグ HTML/JSON を含めたい場合は `--skip-debug-files` を外す。

---

## 再現手順（Docker）
1. Docker イメージのビルド（Playwright 公式イメージベースに修正済み）:

```powershell
docker-compose build --no-cache app
```

2. Docker での実行:

```powershell
docker-compose run --rm app python scripts/run_single_race.py --venue 浦和 --race 9 --perf --skip-dup --full --skip-debug-files
```

- 実行する際に `--skip-debug-files` を外すと `debug_page_<race_key>.html` や `debug_fetches_<race_key>.json` が出るため、これらを ZIP にして添付してください。

---

## 必要なログ/アーティファクト（実行時に必ず集める）
- `debug_fetches_<race_key>.json`  — すべてのフェッチのタイムスタンプ、HTTP ステータス、goto_ms, content_ms
- `debug_page_<race_key>.html` — 最後に取得したページ HTML
- `data/<race_id>/*` — 出力 JSON
- Docker の `docker logs` および `docker stats`（もし Docker で実行した場合）
- `settings.yml` の実行時値

---

## 優先タスク（Opus と Haiku 向け）
1. まず**再現**: ホスト / Docker 両方で 1 レースの実行を行い、それぞれの所要時間と `debug_fetches` を比較（優先）
2. 429 分析: `debug_fetches` で 429 の発生頻度と対象 URL（pedigree, point, horse detail 等）を特定。429 が多いなら、手短に次の方針のうちどれが良いか検討してください:
   - 同一ドメインの 1-2 秒待機を維持、並列数を下げる
   - リトライ回数を減らし、バックオフ最大を 10-30 秒に留める
3. `run_pedigree.py` を `aiohttp` ベースで並列化（CONCURRENCY=3 推奨）
4. Docker での I/O と mount の最適化（`:delegated`、`/app/data` を docker volume に）
5. RateLimiter のテスト（`pytest` に `tests/test_rate_limiter.py` を追加する）

---

## 実行中に確認してほしいこと
- どの URL で最も時間を消費しているか（goto_ms で判定）
- 429 が発生している場合は直近 N 件で 429 のパターンを示す
- ブラウザ起動の時間（Playwright ブラウザの launch 時間）
- CPU / メモリの利用状況（Docker の場合 `docker stats`）

---

## 受け入れ基準（完了の定義）
- ホストと Docker の指標（1レースの時間）が 2 倍以内（許容）であり、かつ 1 レースが 2 分以内に完了すること（通常ケース）
- 429 の頻発が無くなり、RateLimiter とリトライの設定が安定していること
- `run_pedigree` 処理の大幅な時間削減（例えば 100 URL を 5 分以下）

---

## 追加の注意点
- Playwright の headless か headful は挙動に影響する（headless の方が若干高速）
- ログイン（`KeibaBookLogin`）はクッキーを保存し再利用しているため、Cookie の検証を忘れずに
- テストは `pytest -k 'not slow'` で事前チェックをする

---

## 連絡先 / 実施履歴
- ブランチ: `fix/scraper-normalization-perf-debug`
- 最終コミット: 最新のコミットを参照（リモートに push 済み）
- まず再現とログ収集 → 429 分析 → 非同期化・並列制御の調整 の順で対応してください。

---

必要なら私が続けて Docker とホストでの比較実行や `run_pedigree` の非同期化を行います。どれから着手しますか？
