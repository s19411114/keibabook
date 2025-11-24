import os
import yaml

def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return value


def load_settings(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'settings.yml')
        path = os.path.abspath(path)
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}

    # Override with environment variables when provided (safer for credentials)
    # Priority: ENV variables > settings.yml
    env_login_id = os.environ.get('LOGIN_ID') or os.environ.get('KEIBABOOK_LOGIN_ID')
    env_login_password = os.environ.get('LOGIN_PASSWORD') or os.environ.get('KEIBABOOK_LOGIN_PASSWORD')
    env_cookie_file = os.environ.get('COOKIE_FILE') or os.environ.get('COOKIES_FILE')
    env_playwright_headless = os.environ.get('PLAYWRIGHT_HEADLESS')

    if env_login_id:
        cfg['login_id'] = env_login_id
    if env_login_password:
        cfg['login_password'] = env_login_password
    if env_cookie_file:
        cfg['cookie_file'] = env_cookie_file
    if env_playwright_headless is not None:
        cfg['playwright_headless'] = _coerce_bool(env_playwright_headless)
    return cfg
