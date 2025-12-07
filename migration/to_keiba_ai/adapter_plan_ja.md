# keiba-ai Adapter 計画（日本語）

目的: keiba-ai に移管された履歴データやバッチ処理を keibabook が利用できるようにするための簡易アダプタ案。

1. 役割
- keibabook は per-race JSON の生成を行い、必要な過去データ（track_bias、past_results、peds など）は keiba-ai に問い合わせて取得する。

2. 提案 API（仮想）
- GET /history/race/{race_id} → 過去レース情報（最小: results, payouts, date, course, passing, last_3f）
- GET /history/horse/{horse_id} → 馬の履歴
- GET /analytics/track_bias/{race_id} → 当該レースの track_bias

3. keibabook 側の Adapter 実装 (例)
- `src/adapters/keiba_ai_adapter.py`:
  - `get_race_history(race_id)`
  - `get_horse_history(horse_id)`
  - `get_track_bias(race_id)`
  - fallback: keiba-ai が応答しない場合、ローカルのスクレーパーを一時的に実行

4. 実装フロー（最短）
- `migration/to_keiba_ai/` にあるコードをローカルでモジュール化
- keiba-ai 側 PR 後、keibabook に `keiba_ai_adapter.py` を追加
- `cli_prepare_now.py` などを adapter を利用するように置換
- テスト: `tests/test_adapter.py` を作成し、keiba-ai のモックレスポンスで動作確認

5. 低リスクな段階的移行
- 初期段階: adapter は keiba-ai への HTTP 呼び出しではなく、ローカルの `migration/to_keiba_ai` にあるコードを呼ぶようにして互換性を確認
- その後、keiba-ai のエンドポイントが用意できたら、adapter を本番の API に差し替え

