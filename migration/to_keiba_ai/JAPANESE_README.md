# keiba-ai への移管: 簡潔ガイド（日本語）

このフォルダは、keibabook から keiba-ai に移管することを提案するコード／スクリプト群をまとめた一時的な収集場所です。移管の流れを円滑にするため、複数ファイルを機能別に整理し、移管対象と理由を残してあります。

目的:
- Netkeiba の過去データ収集、トラックバイアス計算、ペディグリー収集などの重い・長期的バッチ処理は keiba-ai に移管します。

移管済 / 移管対象（main から移動済み / 仮置き済み）:

- `src/scrapers/netkeiba_result.py` (結果ページスクレイパー)  -> migration/to_keiba_ai/src/scrapers/netkeiba_result.py
- `src/scrapers/netkeiba_db_scraper.py` (Netkeiba DB バッチ) -> migration/to_keiba_ai/src/scrapers/netkeiba_db_scraper.py
- `src/utils/track_bias.py` (トラックバイアス分析) -> migration/to_keiba_ai/src/utils/track_bias.py
- `run_pedigree.py`, `run_pedigree_safe.py`, `pedigree_queue.json`, `pedigree_store/` -> migration/to_keiba_ai/root-files/

注: 上記ファイルは main から削除/無効化して移行フォルダにまとめられています。将来的に keiba-ai に取り込まれ次第、keibabook は `src/adapters/keiba_ai_adapter.py` 経由でデータを取得する方針です。
- keibabook は 1 レース分の JSON 抽出と keibabook 固有フィールド（レース後コメント、調教等）に限定します。

移管作業の注意点:
- まずローカルで機能ごとに分離してテストする（keiba-ai 側のコードはいじらない）
- 小さなモジュールに分割した上でフォルダ（例: `netkeiba_calendar`, `netkeiba_archive`, `track_bias` など）にまとめる
- そのまま keiba-ai に移す（keiba-ai 側で利用できるもののみを取り入れてもらう）
- 移管後は keibabook に `keiba_ai_adapter` を置き、keiba-ai の API/データを参照する

簡単なフェーズ:
1. ローカルで分離・整理（このフォルダにまとめる）
2. keiba-ai 側に PR 提案（機能まとまりごと）
3. keiba-ai が取り込んだら、keibabook の該当箇所を API 呼び出しに差し替え

バックアップ: 移管前に一時的なバックアップを作成してください（`scripts/backup_repo.sh` を作成済み）。

問い合わせ先: リポジトリ管理者
