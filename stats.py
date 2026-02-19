import json
import os

STATS_FILE = "stats.json"

def _load():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_view(toy_id):
    data = _load()
    if toy_id not in data:
        data[toy_id] = {"views": 0, "clicks": 0}
    data[toy_id]["views"] += 1
    _save(data)

def add_click(toy_id):
    data = _load()
    if toy_id not in data:
        data[toy_id] = {"views": 0, "clicks": 0}
    data[toy_id]["clicks"] += 1
    _save(data)
