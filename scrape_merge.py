#!/usr/bin/env python3
import json
from pathlib import Path

# --- モックデータ（実運用時はここをスクレイピング結果で置換） ---
race = {
  "race_id": "202503060201",
  "race_name": "第1回福島競馬 第1日目 1R",
  "race_grade": "サラ系3歳未勝利",
  "distance": "ダート1700m",
  "date": "2025-03-06",
  "horses": [
    {"horse_num": "1", "horse_name": "馬名1", "jockey": "騎手1", "weight": "55", "odds": "12.5", "horse_name_link": "/db/uma/dummy_link"}
  ]
}
past_results_map = {
  "1": [
    {"date": "2025-10-20", "venue": "東京", "race_num": "1", "finish_position": "1着", "time": "1:35.0", "jockey": "ルメール", "weight": "55"}
  ]
}
pedigree_map = {
  "1": {"father": "ドレフォン", "mother": "セイウンアワード", "mothers_father": "タニノギムレット"}
}
training_map = {
  "1": [{"date":"2025-11-05","location":"美浦南Ｗ","time":"68.9-53.5-38.6-11.9","evaluation":"馬ナリ余力"}]
}
stable_comment_map = {"1": "まだ素質だけで走っている感じ。使いつつ良くなってくれば。"}
previous_race_comment_map = {"1": "スタートで後手を踏んだのが全て。力負けではない。"}

# --- マージロジック（出馬表優先、血統は補完、調教は追加、履歴は保持） ---
def absolutize(url):
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    base = "https://s.keibabook.co.jp"
    if url.startswith("/"):
        return base + url
    return base + "/" + url

all_nums = set()
all_nums.update(h["horse_num"] for h in race.get("horses", []))
all_nums.update(pedigree_map.keys())
all_nums.update(training_map.keys())
all_nums.update(past_results_map.keys())

horses_out = []
for num in sorted(all_nums, key=lambda x: int(x) if str(x).isdigit() else x):
    horse_from_race = next((h for h in race.get("horses", []) if h.get("horse_num")==num), None)
    entry = {"_flags": []}
    if horse_from_race:
        entry["horse_num"] = horse_from_race.get("horse_num")
        entry["horse_name"] = horse_from_race.get("horse_name")
        entry["jockey"] = horse_from_race.get("jockey")
        entry["weight"] = horse_from_race.get("weight")
        entry["odds"] = horse_from_race.get("odds")
        entry["detail_url"] = absolutize(horse_from_race.get("horse_name_link"))
    else:
        entry["horse_num"] = num
        entry["_flags"].append("no_entry_in_shutuba")
    if pedigree_map.get(num):
        for k,v in pedigree_map[num].items():
            if k not in entry or not entry.get(k):
                entry[k]=v
    entry["past_results"] = past_results_map.get(num, [])
    entry["training"] = sorted(training_map.get(num, []), key=lambda r: r.get("date") or "", reverse=True)
    if stable_comment_map.get(num):
        entry["stable_comment"] = stable_comment_map[num]
    if previous_race_comment_map.get(num):
        entry["previous_race_comment"] = previous_race_comment_map[num]
    if not entry.get("horse_name"):
        entry["_flags"].append("missing_horse_name")
    if not entry.get("detail_url"):
        entry["_flags"].append("missing_detail_url")
    horses_out.append(entry)

merged = {
  "race_id": race.get("race_id"),
  "race_name": race.get("race_name"),
  "race_grade": race.get("race_grade"),
  "distance": race.get("distance"),
  "date": race.get("date"),
  "horses": horses_out
}

out_path = Path("output.json")
out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
print(f"wrote {out_path.resolve()}")
