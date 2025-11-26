import json
from pathlib import Path
from typing import Any


def save_per_race_json(output_dir: Path, race_id: str, race_key: str, data: Any) -> Path:
    """Save race data as a single per-race JSON file in `output_dir/<race_id>/<race_key>_1R.json`.

    Returns the saved Path.
    """
    dir_path = Path(output_dir) / str(race_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{race_key}_1R.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path


def save_race_summary_json(output_dir: Path, race_id: str, race_key: str, data: Any) -> Path:
    """Save a compact summary JSON for the race with selected fields.

    Returns the saved Path.
    """
    dir_path = Path(output_dir) / str(race_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    summary = {
        'race_id': race_id,
        'race_key': race_key,
        'race_name': data.get('race_name'),
        'race_grade': data.get('race_grade'),
        'distance': data.get('distance'),
        'point_info': data.get('point_info', {}),
        'horses': []
    }
    for h in data.get('horses', []):
        horse_summary = {
            'horse_num': h.get('horse_num'),
            'horse_name': h.get('horse_name'),
            'prediction_mark': h.get('prediction_mark'),
            'current_odds': h.get('current_odds'),
            'training': h.get('training_data', {}),
            'stable_comment': h.get('stable_comment', ''),
            'previous_race_comment': h.get('previous_race_comment', ''),
            'past_results': h.get('past_results', []),
            'pedigree_summary': {
                'father': h.get('pedigree_data', {}).get('father'),
                'mother': h.get('pedigree_data', {}).get('mother')
            }
        }
        summary['horses'].append(horse_summary)

    file_path = dir_path / f"{race_key}_summary.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return file_path
