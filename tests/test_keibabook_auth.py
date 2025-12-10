import json
import os
import time
from pathlib import Path

from src.utils.keibabook_auth import KeibaBookAuth


def test_is_cookie_valid_absent(tmp_path):
    nonexist = tmp_path / 'no_cookies.json'
    valid, msg = KeibaBookAuth.is_cookie_valid(str(nonexist))
    assert valid is False
    assert '存在しません' in msg


def test_is_cookie_valid_expired(tmp_path):
    cookie_path = tmp_path / 'cookies.json'
    now = int(time.time())
    expired_cookie = [{'name': 'tk', 'value': 'x', 'expires': now - 3600}]
    with open(cookie_path, 'w', encoding='utf-8') as f:
        json.dump(expired_cookie, f)
    valid, msg = KeibaBookAuth.is_cookie_valid(str(cookie_path))
    assert valid is False
    assert '期限切れ' in msg


def test_is_cookie_valid_ok(tmp_path):
    cookie_path = tmp_path / 'cookies.json'
    now = int(time.time())
    future_cookie = [{'name': 'tk', 'value': 'x', 'expires': now + 86400 * 5}]
    with open(cookie_path, 'w', encoding='utf-8') as f:
        json.dump(future_cookie, f)
    valid, msg = KeibaBookAuth.is_cookie_valid(str(cookie_path))
    assert valid is True
    assert '残り' in msg
