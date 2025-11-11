import os
import yaml

def load_settings(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'settings.yml')
        path = os.path.abspath(path)
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    return cfg
