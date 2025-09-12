import json
from pathlib import Path
import shutil

path = Path("movies-data.json")
backup = Path("movies-data.json.bak")

# Резервная копия
shutil.copy2(path, backup)

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

changed = 0
for m in data.get("movies", []):
    if not isinstance(m, dict):
        continue
    id_val = str(m.get("id", "")).lower()
    title_val = str(m.get("title", "")).lower()
    if "multfilm" in id_val or "multfilm" in title_val:
        if m.get("category") == "filmy":
            m["category"] = "multfilmy"
            changed += 1

with path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Updated entries: {changed}. Backup saved to {backup}")
