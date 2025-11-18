import os
import json
from typing import List

CONFIG_ENV_PATH = os.path.join(os.path.dirname(__file__), 'config.env')

def _parse_env_file(path: str) -> dict:
    data = {}
    if not os.path.exists(path):
        return data
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                # strip surrounding quotes if present
                val = val.strip().strip('"').strip("'")
                data[key] = val
    except Exception:
        # Fail soft; caller may still use env vars
        pass
    return data

def get_gemini_keys() -> List[str]:
    """Return list of Gemini API keys.
    Order matters; first key is the primary unless rotation is used in a script.

    Source priority:
    1) config.env GEMINI_API_KEYS
    2) Process environment GEMINI_API_KEYS

    Accepted formats:
    - Comma-separated string: key1,key2,key3
    - JSON array: ["key1", "key2"]
    """
    env_file = _parse_env_file(CONFIG_ENV_PATH)
    raw = env_file.get('GEMINI_API_KEYS', '')
    if not raw:
        raw = os.getenv('GEMINI_API_KEYS', '')
    keys: List[str] = []
    if raw:
        s = raw.strip()
        if s.startswith('['):
            try:
                arr = json.loads(s)
                if isinstance(arr, list):
                    keys = [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                # fall back to comma split
                keys = [p.strip() for p in s.split(',') if p.strip()]
        else:
            keys = [p.strip() for p in s.split(',') if p.strip()]
    if not keys:
        raise RuntimeError('GEMINI_API_KEYS are not configured. Set in config.env or environment')
    return keys
