#!/usr/bin/env python3
"""
Open a headful Playwright browser and load cookies from cookies.json.
Keep the browser open for manual inspection.
"""
import json
import os
import sys
from pathlib import Path
from typing import List

try:
    from playwright.sync_api import sync_playwright
except Exception:
    print('playwright not installed or not configured. Install with `pip install playwright` and run `playwright install`')
    sys.exit(2)

COOKIE_FILE = os.environ.get('COOKIE_FILE', 'cookies.json')
DEFAULT_URL = 'https://s.keibabook.co.jp/'


def load_cookies(file_path: str) -> List[dict]:
    p = Path(file_path)
    if not p.exists():
        return []
    try:
        with open(p, 'r', encoding='utf-8') as f:
            c = json.load(f)
            return c
    except Exception as e:
        print('Error loading cookies:', e)
        return []


def convert_cookie(cookie: dict, default_url: str = DEFAULT_URL) -> dict:
    # Playwright expects cookie dict elements: name, value, url|domain/path, expires (optional), httpOnly, secure, sameSite
    c = dict(
        name=cookie.get('name'),
        value=cookie.get('value'),
        path=cookie.get('path', '/'),
        domain=cookie.get('domain'),
        httpOnly=cookie.get('httpOnly', False),
        secure=cookie.get('secure', False),
    )
    if cookie.get('expires'):
        try:
            c['expires'] = int(cookie.get('expires'))
        except Exception:
            pass
    # Add url to make it work with add_cookies
    dom = cookie.get('domain')
    if dom:
        dom = dom.lstrip('.')
        c['url'] = f'https://{dom}'
    else:
        c['url'] = default_url
    if cookie.get('sameSite'):
        # convert capitalization if necessary
        c['sameSite'] = cookie.get('sameSite')
    return c


if __name__ == '__main__':
    cookies = load_cookies(COOKIE_FILE)
    print(f'Loaded {len(cookies)} cookies from {COOKIE_FILE}')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        if cookies:
            converted = [convert_cookie(c) for c in cookies]
            try:
                context.add_cookies(converted)
            except Exception as e:
                print('Warning: failed to add cookies to context:', e)
        page = context.new_page()
        try:
            page.goto(DEFAULT_URL, wait_until='networkidle')
        except Exception as e:
            print('Navigation error:', e)

        # Check cookies in context
        ctx_cookies = context.cookies()
        tk = [c for c in ctx_cookies if c.get('name') == 'tk']
        if tk:
            print('tk cookie present; likely logged in.')
        else:
            print('tk cookie not present; page will be open for manual login.')

        print('Browser opened. Perform manual actions; press Enter here when you want to close the browser.')
        try:
            input()
        except KeyboardInterrupt:
            pass

        # Optionally save cookies back (so updated cookies are persisted)
        try:
            new_cookies = context.cookies()
            with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_cookies, f, ensure_ascii=False, indent=2)
            print(f'Saved {len(new_cookies)} cookies to {COOKIE_FILE}')
        except Exception as e:
            print('Failed to save cookies:', e)

        context.close()
        browser.close()
