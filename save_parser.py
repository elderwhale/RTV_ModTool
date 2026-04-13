
import re

def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _extract_value(text, key):
    pattern = rf"^{re.escape(key)}\s*=\s*(.+)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return None
    raw = match.group(1).strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw == "true":
        return True
    if raw == "false":
        return False
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw

def parse_player_tres(path, logger=print):
    text = _read_text(path)
    keys = ["health","energy","hydration","temperature","mental","dehydration","bleeding","fracture","burn","frostbite","rupture","insanity"]
    data = {key: _extract_value(text, key) for key in keys}
    logger(f"Parsed player fields from {path}: {data}")
    return data

def parse_world_tres(path, logger=print):
    text = _read_text(path)
    keys = ["difficulty","season","day","time","weather","weatherTime","shelters"]
    data = {key: _extract_value(text, key) for key in keys}
    logger(f"Parsed world fields from {path}: {data}")
    return data
