import argparse, json, os, sys

def main():
    p = argparse.ArgumentParser(description="Pretty/minify JSON")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pretty", action="store_true", help="Сделать читаемый JSON")
    g.add_argument("--minify", action="store_true", help="Сжать JSON в одну строку")
    p.add_argument("--in", dest="inp", required=True, help="Путь к исходному JSON")
    p.add_argument("--out", dest="out", help="Путь к выходному JSON")
    p.add_argument("--indent", type=int, default=2, help="Отступ для --pretty (по умолчанию 2)")
    args = p.parse_args()

    src = args.inp
    if not args.out:
        base, ext = os.path.splitext(src)
        args.out = f"{base}.pretty{ext}" if args.pretty else f"{base}.min{ext}"

    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.pretty:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=args.indent)
            f.write("\n")
    else:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")

if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        try:
            sys.stderr.close()
        except Exception:
            pass

# python .\json_format_minify.py --pretty --in ".\movies-data-without-pop.json" --out ".\movies-data-without-pop.pretty.json"
# python .\json_format_minify.py --minify --in ".\movies-data-without-pop.json" --out ".\movies-data-without-pop.min.json"