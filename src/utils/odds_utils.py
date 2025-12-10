from typing import Dict


def compare_snapshots(prev: Dict, current: Dict) -> Dict:
    """
    Simple percent change per horse_num for win odds only (if present).
    Returns a dict: { horse_num: percent_change }
    """
    changes = {}
    prev_h = {str(h.get('horse_num')): float(h.get('win_odds')) if h.get('win_odds') else None for h in prev.get('horses', [])}
    cur_h = {str(h.get('horse_num')): float(h.get('win_odds')) if h.get('win_odds') else None for h in current.get('horses', [])}
    for k, v in cur_h.items():
        if k in prev_h and prev_h[k] and v:
            try:
                pct = (v - prev_h[k]) / prev_h[k] * 100.0
                changes[k] = round(pct, 2)
            except Exception:
                changes[k] = None
    return changes
