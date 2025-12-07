import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from src.utils.db_manager import CSVDBManager


def test_is_url_fetched_with_ttl(tmp_path):
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)

    manager = CSVDBManager(db_dir=str(db_dir))
    url = "https://example.com/test"
    # Log URL now
    manager.log_url(url, "race1", "test", status="success")

    # Should be fetched without TTL
    assert manager.is_url_fetched(url) is True
    # Should be fetched with TTL longer than 0
    assert manager.is_url_fetched(url, max_age_seconds=60) is True

    # Now modify CSV to make fetched_at be 2 hours ago
    df = pd.read_csv(manager.url_log_path, encoding='utf-8-sig')
    old_time = (datetime.now() - timedelta(hours=2)).isoformat()
    df.loc[df['url'] == url, 'fetched_at'] = old_time
    df.to_csv(manager.url_log_path, index=False, encoding='utf-8-sig')

    # TTL 1 hour -> should be False
    assert manager.is_url_fetched(url, max_age_seconds=3600) is False
    # TTL 3 hours -> should be True
    assert manager.is_url_fetched(url, max_age_seconds=3600*3) is True
