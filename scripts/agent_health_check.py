#!/usr/bin/env python3
"""
Agent health check script
- Verifies environment, key dependencies, cookie presence and minimal server checks
- Outputs JSON summary
"""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from datetime import datetime

RESULT = {
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'ok': True,
    'checks': {}
}

PROJECT_ROOT = Path(__file__).parent.parent
COOKIE_FILE = PROJECT_ROOT / 'cookies.json'


def check_python_version():
    v = sys.version_info
    return {'ok': v.major == 3 and v.minor >= 12, 'value': f'{v.major}.{v.minor}.{v.micro}'}


def check_venv():
    # heuristic: .venv directory exists and sys.prefix includes it
    venv_dir = PROJECT_ROOT / '.venv'
    active_venv = '.venv' in sys.prefix or os.environ.get('VIRTUAL_ENV')
    return {'ok': venv_dir.exists() and active_venv, 'venv_dir_exists': venv_dir.exists(), 'active_venv_prefix': sys.prefix}


def check_dependency(module_name):
    try:
        __import__(module_name)
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1.0)
        s.connect((host, port))
        s.close()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def check_cookies_tk():
    if not COOKIE_FILE.exists():
        return {'ok': False, 'reason': 'not_found'}
    try:
        cookies = json.load(open(COOKIE_FILE, 'r', encoding='utf-8'))
        tk = [c for c in cookies if c.get('name') == 'tk']
        if tk:
            return {'ok': True, 'tk_count': len(tk)}
        else:
            return {'ok': False, 'reason': 'tk_not_found', 'cookies_count': len(cookies)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def main():
    # Python version
    RESULT['checks']['python_version'] = check_python_version()

    # venv
    RESULT['checks']['venv'] = check_venv()

    # dependencies
    for mod in ('playwright', 'nicegui'):
        RESULT['checks'][f'module_{mod}'] = check_dependency(mod)

    # servers
    RESULT['checks']['nicegui_port'] = check_port('127.0.0.1', 8080)

    # cookie
    RESULT['checks']['cookies_tk'] = check_cookies_tk()

    # run smoke command for `scripts/test_login.py` existence
    test_login_path = PROJECT_ROOT / 'scripts' / 'test_login.py'
    RESULT['checks']['test_login_exists'] = {'ok': test_login_path.exists(), 'path': str(test_login_path)}

    # overall
    RESULT['ok'] = all(check.get('ok', False) for check in RESULT['checks'].values())

    print(json.dumps(RESULT, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
