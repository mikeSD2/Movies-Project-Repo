import os
import re
import json
import time
import argparse
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Tuple

# ------------- Utils -------------

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def normalize_url(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    u = u.strip()
    if u.startswith('//'):
        return 'https:' + u
    return u

def guess_ext_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    return ext if ext in {'.jpg', '.jpeg', '.png', '.webp', '.gif'} else '.jpg'

def slugify(text: str) -> str:
    text = text or ''
    text = text.strip()
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    text = re.sub(r'-{2,}', '-', text)
    return text or 'untitled'

def build_filename(item: Dict, ext: str) -> str:
    kp = str(item.get('kinopoiskId') or 'nokp')
    title = item.get('title') or 'untitled'
    slug = slugify(title)[:80]
    base = f"{kp}-{slug}"
    base = re.sub(r'[^a-zA-Z0-9._-]+', '-', base).strip('-')
    base = re.sub(r'-{2,}', '-', base)
    return (base or 'image') + ext

def request_with_headers(url: str):
    return urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'ru,en;q=0.9'
        }
    )

# ------------- Worker -------------

def download_one(idx: int, item: Dict, images_dir: str, timeout: float) -> Tuple[int, Dict, str]:
    """
    Returns: (idx, updated_item, status)
    status: 'downloaded' | 'reused' | 'local' | 'no_image' | 'error'
    """
    img = item.get('image')
    url = normalize_url(img)

    if not url or not str(url).strip():
        return idx, item, 'no_image'  # нет картинки — будем выкидывать из выхода

    if not (url.startswith('http://') or url.startswith('https://')):
        # уже локальный/относительный путь — оставляем
        return idx, item, 'local'

    ext = guess_ext_from_url(url)
    fname = build_filename(item, ext)
    rel_path = os.path.join('uploads', 'images', fname).replace('\\', '/')
    abs_path = os.path.join(images_dir, fname)

    if os.path.exists(abs_path):
        item['image'] = rel_path
        return idx, item, 'reused'

    try:
        req = request_with_headers(url)
        if timeout and timeout > 0:
            with urllib.request.urlopen(req, timeout=timeout) as r, open(abs_path, 'wb') as f:
                f.write(r.read())
        else:
            with urllib.request.urlopen(req) as r, open(abs_path, 'wb') as f:
                f.write(r.read())
        item['image'] = rel_path
        return idx, item, 'downloaded'
    except Exception:
        return idx, item, 'error'

# ------------- Main -------------

def process_ndjson(src_path: str, dst_path: str, images_dir: str, workers: int, timeout: float, verbose: bool, log_every: int):
    ensure_dir(images_dir)

    # 1) Load all items to preserve input order on output
    items: List[Dict] = []
    with open(src_path, 'r', encoding='utf-8') as src:
        for line in src:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception:
                continue

    total = len(items)
    to_download = 0
    for it in items:
        u = normalize_url(it.get('image'))
        if u and (u.startswith('http://') or u.startswith('https://')):
            to_download += 1

    print(f"Items: {total}, images to fetch: {to_download}, workers: {workers}, timeout: {timeout if timeout else 'none'}")

    t0 = time.time()
    results: List[Optional[Tuple[int, Dict, str]]] = [None] * total

    downloaded = reused = skipped = errors = 0
    done = 0
    local = 0
    dropped_no_image = 0

    # 2) Parallel downloads
    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = []
        for idx, item in enumerate(items):
            futures.append(exe.submit(download_one, idx, item, images_dir, timeout))

        for fut in as_completed(futures):
            idx, upd, status = fut.result()
            results[idx] = (idx, upd, status)
            done += 1
            if status == 'downloaded':
                downloaded += 1
            elif status == 'reused':
                reused += 1
            elif status == 'local':
                local += 1
            elif status == 'no_image':
                dropped_no_image += 1
            else:
                errors += 1

            if verbose or (done % log_every == 0):
                print(f"[{done}/{total}] downloaded:{downloaded} reused:{reused} local:{local} dropped_no_image:{dropped_no_image} errors:{errors}")

    # 3) Write output in original order
    wrote = 0
    with open(dst_path, 'w', encoding='utf-8') as dst:
        for tup in results:
            if tup is None:
                continue
            _, obj, status = tup
            if status == 'no_image':
                continue  # выкидываем записи без картинки
            dst.write(json.dumps(obj, ensure_ascii=False) + '\n')
            wrote += 1

    dt = time.time() - t0
    print(f"Done in {dt:.1f}s. Wrote: {wrote}. downloaded:{downloaded} reused:{reused} local:{local} dropped_no_image:{dropped_no_image} errors:{errors}")
    print(f"Output NDJSON: {dst_path}")
    print(f"Images dir: {images_dir}")

def main():
    ap = argparse.ArgumentParser(description="Fast parallel image downloader for NDJSON; rewrites image to uploads/images/*")
    ap.add_argument("--in", dest="src", required=True, help="Input NDJSON")
    ap.add_argument("--out", dest="dst", required=True, help="Output NDJSON with local image paths")
    ap.add_argument("--images-dir", default=os.path.join('uploads', 'images'), help="Directory to save images")
    ap.add_argument("--workers", type=int, default=32, help="Number of parallel workers (default 32)")
    ap.add_argument("--timeout", type=float, default=0.0, help="Per-request timeout in seconds; 0 -> no timeout (fastest)")
    ap.add_argument("--verbose", action="store_true", help="Print every item progress")
    ap.add_argument("--log-every", type=int, default=100, help="Batch progress print frequency when not verbose")
    args = ap.parse_args()

    process_ndjson(args.src, args.dst, args.images_dir, args.workers, args.timeout, args.verbose, args.log_every)

if __name__ == "__main__":
    main()