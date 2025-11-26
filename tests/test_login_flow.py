import asyncio
import json
import os
from unittest.mock import AsyncMock, patch
import pytest

from src.utils.login import KeibaBookLogin


@pytest.mark.asyncio
async def test_load_cookies_to_context(tmp_path):
    cookie_file = tmp_path / 'cookies.json'
    cookies = [{"name": "sessionid", "value": "abc", "domain": "s.keibabook.co.jp"}]
    cookie_file.write_text(json.dumps(cookies), encoding='utf-8')

    # Create a dummy context with an async add_cookies method
    context = AsyncMock()
    context.add_cookies = AsyncMock()

    loaded = await KeibaBookLogin.load_cookies_to_context(context, str(cookie_file))
    assert loaded is True
    context.add_cookies.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_logged_in_uses_cookies(tmp_path):
    cookie_file = tmp_path / 'cookies.json'
    cookies = [{"name": "sessionid", "value": "abc", "domain": "s.keibabook.co.jp"}]
    cookie_file.write_text(json.dumps(cookies), encoding='utf-8')

    # Setup context and page
    page = AsyncMock()
    # Simulate that after loading cookies, navigation does not redirect to login
    async def goto(url, **kwargs):
        page.url = "https://s.keibabook.co.jp/dashboard"
        return None
    page.goto = goto

    context = AsyncMock()
    context.add_cookies = AsyncMock()
    context.new_page = AsyncMock(return_value=page)

    # Patch KeibaBookLogin.login to ensure it's not called
    with patch('src.utils.login.KeibaBookLogin.login', new=AsyncMock()) as login_mock:
        result = await KeibaBookLogin.ensure_logged_in(context, login_id='u', password='p', cookie_file=str(cookie_file), save_cookies=False)
        assert result is True
        login_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_logged_in_falls_back_to_login(tmp_path):
    cookie_file = tmp_path / 'cookies.json'
    cookies = [{"name": "sessionid", "value": "abc", "domain": "s.keibabook.co.jp"}]
    cookie_file.write_text(json.dumps(cookies), encoding='utf-8')

    # Setup page that will indicate we're not logged in
    page = AsyncMock()
    async def goto(url, **kwargs):
        page.url = "https://s.keibabook.co.jp/login/login"
        return None
    page.goto = goto

    context = AsyncMock()
    context.add_cookies = AsyncMock()
    context.new_page = AsyncMock(return_value=page)

    with patch('src.utils.login.KeibaBookLogin.login', new=AsyncMock(return_value=True)) as login_mock:
        result = await KeibaBookLogin.ensure_logged_in(context, login_id='u', password='p', cookie_file=str(cookie_file), save_cookies=False)
        assert result is True
        login_mock.assert_awaited_once()


def test_cookie_file_expiry(tmp_path):
    # expired cookie
    import time
    expired_cookie = [{"name": "sessionid", "value": "a", "domain": "s.keibabook.co.jp", "expires": int(time.time()) - 10}]
    f = tmp_path / 'cookies.json'
    f.write_text(json.dumps(expired_cookie), encoding='utf-8')
    assert KeibaBookLogin.cookie_file_expired(str(f)) is True


def test_cookie_file_not_expired(tmp_path):
    import time
    valid_cookie = [{"name": "sessionid", "value": "a", "domain": "s.keibabook.co.jp", "expires": int(time.time()) + 3600}]
    f = tmp_path / 'cookies.json'
    f.write_text(json.dumps(valid_cookie), encoding='utf-8')
    assert KeibaBookLogin.cookie_file_expired(str(f)) is False
