# pretty_serials.py
import json

src = "serials.json"
dst = "serials.pretty.json"

with open(src, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(dst, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Готово: {dst}")