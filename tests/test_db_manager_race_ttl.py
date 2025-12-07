import os
from src.utils.db_manager import CSVDBManager
from datetime import datetime, timedelta

def test_is_race_fetched_ttl(tmp_path):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    db = CSVDBManager(db_dir=str(db_dir))
    race_id = '202501010101'
    # Log a shutuba url for this race
    db.log_url(f"https://example/{race_id}", race_id, 'shutuba', 'success')
    # Should be fetched with default (no ttl)
    assert db.is_race_fetched(race_id) is True
    # Now test TTL: pass a small TTL (1 second) and simulate older fetched_at
    # Manually update CSV log to set an old fetched_at
    import pandas as pd
    df = pd.read_csv(db.url_log_path, encoding='utf-8-sig')
    df.loc[0, 'fetched_at'] = (datetime.now() - timedelta(days=10)).isoformat()
    df.to_csv(db.url_log_path, index=False, encoding='utf-8-sig')
    # With TTL=3600s (1hr), should be False
    assert db.is_race_fetched(race_id, max_age_seconds=3600) is False
    # With a very large TTL, should be True
    assert db.is_race_fetched(race_id, max_age_seconds=3600*24*365) is True
