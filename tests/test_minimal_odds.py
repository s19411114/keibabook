import datetime
import json
from src.scrapers.odds_fetcher import OddsFetcher
from scripts.cli_minimal_odds import compare_snapshots


def test_compare_snapshots_simple():
    prev = {'horses': [{'horse_num': '1', 'win_odds': '2.0'}, {'horse_num': '2', 'win_odds': '4.0'}]}
    cur = {'horses': [{'horse_num': '1', 'win_odds': '3.0'}, {'horse_num': '2', 'win_odds': '2.0'}]}
    changes = compare_snapshots(prev, cur)
    assert isinstance(changes, dict)
    assert '1' in changes
    assert '2' in changes
    # 1: from 2.0 to 3.0 = +50%
    assert changes['1'] == 50.0
    # 2: from 4.0 to 2.0 = -50%
    assert changes['2'] == -50.0
