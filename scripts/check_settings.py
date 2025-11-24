from src.utils.config import load_settings
cfg = load_settings()
print('LOGIN_ID=', cfg.get('login_id'))
print('LOGIN_PASSWORD_PRESENT=', bool(cfg.get('login_password')))
