#!/usr/bin/env python3
"""
YouTube Shorts Uploader

Uploads short videos from a directory (e.g., ./shorts) to YouTube via YouTube Data API v3.

Modes:
- dry-run: no API calls, only prints planned uploads
- test: upload as Unlisted (optionally delete after)
- publish: upload as Public

Features:
- Title/description generation similar to the VK uploader (enriched from movies-data.ndjson)
- Resumable uploads via googleapiclient MediaFileUpload
- Optional delete-after for test runs
- Auto-load environment from config.env if present (like VK script)

Requirements:
- Python 3.9+
- pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 python-dotenv

Auth setup (high-level):
- Create OAuth client ID in Google Cloud Console for Desktop app
- Download client_secrets.json and place near this script (or set YT_CLIENT_SECRETS=path)
- First run will open a browser to authorize; token.json will be created and used next time

Environment variables (optional):
- SITE_URL: site root used in description links (default http://www.kino.lordfilmshd-2026.ru)
- MOVIES_NDJSON: path to movies-data.ndjson for enrichment
- YT_CLIENT_SECRETS: path to client_secrets.json (default ./client_secrets.json)
- YT_TOKEN_FILE: path to token.json (default ./token.json)
- YT_CATEGORY_ID: YouTube categoryId (default 1 = Film & Animation)
- YT_MADE_FOR_KIDS: "true"/"false" (default false)

CLI examples:
- Dry-run:
  python publish_shorts_to_youtube.py --dir shorts --mode dry-run

- Test (Unlisted):
  python publish_shorts_to_youtube.py --dir shorts --mode test --limit 1

- Publish (Public):
  python publish_shorts_to_youtube.py --dir shorts --mode publish --limit 1

- Test and delete after:
  python publish_shorts_to_youtube.py --dir shorts --mode test --delete-after --limit 1

Notes:
- YouTube does not have a separate Shorts API. A video is treated as a Short if it is vertical (>= 9:16) and < 60 seconds, or if tagged #Shorts. This script adds #Shorts automatically in the title tail.
"""
import argparse
import os
import sys
import time
import json
import pathlib
from typing import Optional, Dict, Any, Tuple

# Try to load env from config.env (similar to VK script)
_loaded_env = False
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    if load_dotenv("config.env"):
        _loaded_env = True
except Exception:
    pass

if not _loaded_env:
    cfg_path = os.path.join(os.getcwd(), "config.env")
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and (k not in os.environ):
                            os.environ[k] = v
        except Exception:
            pass

# Google API imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes: upload + basic channel management for metadata
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def human_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


RU_NOUN_BY_CATEGORY = {
    # nominative singular
    "filmy": "фильм",
    "serialy": "сериал",
    "multfilmy": "мультфильм",
    "anime": "аниме",
}

RU_PLURAL_BY_CATEGORY = {
    # nominative plural
    "filmy": "фильмы",
    "serialy": "сериалы",
    "multfilmy": "мультфильмы",
    "anime": "аниме",
}

RU_MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def infer_month_from_premiere(premiere: Optional[str]) -> Optional[str]:
    if not premiere:
        return None
    s = str(premiere).strip().lower()
    parts = s.split()
    if len(parts) >= 2:
        m = parts[1]
        if m in RU_MONTHS_GEN:
            return m
    for m in RU_MONTHS_GEN:
        if m in s:
            return m
    return None


def load_movies_map(ndjson_path: str) -> Dict[str, Dict[str, Any]]:
    mp: Dict[str, Dict[str, Any]] = {}
    if not ndjson_path or not os.path.isfile(ndjson_path):
        return mp
    try:
        with open(ndjson_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                mid = str(obj.get("id") or "").strip()
                if mid:
                    mp[mid] = obj
    except Exception:
        pass
    return mp


def build_title_and_description(basename: str, movie: Optional[Dict[str, Any]], site_root: Optional[str], title_template: Optional[str]) -> Tuple[str, str]:
    # Полностью повторяем формат из VK-скрипта, с единственным отличием:
    # - в title вместо #клип используем #shorts
    # - в описании добавляем тег №Клип (вместо любых упоминаний short/Shorts)
    ru_title = None
    en_title = None
    year = None
    category = None
    description = None
    if movie:
        category = (movie.get("category") or "").lower()
        ru_title = movie.get("title") or movie.get("ru_title") or movie.get("ruTitle")
        en_title = movie.get("originalTitle") or movie.get("en_title") or movie.get("orig_title")
        year = movie.get("year")
        description = movie.get("description")

    # Title (как в VK, но #клип -> #shorts)
    if title_template:
        title = title_template.format(basename=basename, RU_TITLE=(ru_title or basename), YEAR=(year or ""))
    else:
        noun = RU_NOUN_BY_CATEGORY.get(category or "", "фильм")
        title = f"{(ru_title or basename)} ({year or ''}) - Официальный русский трейлер | #{noun}2025 #новыесериалы #shorts"

    # Блок ссылки
    link_line = "ПОСМОТРЕТЬ ПОЛНОСТЬЮ МОЖНО ТУТ:\n"
    item_url = (site_root or "").rstrip("/")
    if movie and movie.get("category") and movie.get("id"):
        item_url = f"{(site_root or 'http://www.kino.lordfilmshd-2026.ru').rstrip('/')}/{movie.get('category').strip('/')}/{movie.get('id')}"
    link_block = f"{link_line}{item_url}\n\n"

    # Короткий синопсис
    short_desc = (description or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(short_desc) > 400:
        short_desc = short_desc[:400].rstrip() + "..."
    about_block = "О фильме:\n" + (short_desc or "") + "\n\n"

    # Хвост описания (как в VK)
    plural = RU_PLURAL_BY_CATEGORY.get(category or "", "фильмы")
    singular = RU_NOUN_BY_CATEGORY.get(category or "", "фильм")
    prem_mon = infer_month_from_premiere(movie.get('premiere') if movie else None)
    month_hashtag = f"#новинки{prem_mon}" if prem_mon else "#новинки"

    # Жанры
    genres = []
    if movie:
        raw_genres = movie.get('genres') or []
        if isinstance(raw_genres, list):
            genres = [str(g).strip().lower() for g in raw_genres if str(g).strip()]
        elif isinstance(raw_genres, str):
            genres = [s.strip().lower() for s in raw_genres.split(',') if s.strip()]
    GENRE_TAG_MAP = {
        'боевик': '#боевик', 'триллер': '#триллер', 'ужасы': '#ужасы', 'комедия': '#комедия', 'драма': '#драма',
        'фантастика': '#фантастика', 'детектив': '#детективы', 'криминал': '#криминал', 'приключения': '#приключения',
        'семейный': '#семейный', 'фэнтези': '#фэнтези', 'мелодрама': '#мелодрама', 'аниме': '#аниме', 'мультфильм': '#мультфильмы',
        'история': '#история', 'биография': '#биография', 'вестерн': '#вестерн', 'война': '#военное', 'военный': '#военное',
        'фильм-нуар': '#нуар', 'нуар': '#нуар', 'спорт': '#спорт', 'документальный': '#документальный', 'музыка': '#музыка',
        'короткометражка': '#короткометражка', 'короткометражный': '#короткометражка', 'триллеры': '#триллер', 'детективы': '#детективы',
    }
    genre_tags = []
    for g in genres:
        if g in GENRE_TAG_MAP:
            genre_tags.append(GENRE_TAG_MAP[g])
        else:
            genre_tags.append('#' + g.replace(' ', ''))

    CATEGORY_TAG = {
        'filmy': '#фильмы', 'serialy': '#сериалы', 'multfilmy': '#мультфильмы', 'anime': '#аниме'
    }
    category_tag = CATEGORY_TAG.get((category or '').lower(), '#фильмы')

    keyword_line = (
        f"{(ru_title or basename)}, {(en_title or '')}, {plural} {(year or '')} года, русский трейлер, трейлеры, "
        f"официальный трейлер, дублированный трейлер, новые {plural}, премьера, в хорошем качестве, hd, "
        f"{plural} на вечер, что посмотреть, {singular}, кино, {plural} онлайн, лучшие {plural}, топ {plural}, смотреть онлайн бесплатно"
    )

    tail_lines = [
        "---",
        f"{category_tag} {' '.join(genre_tags[:12])} {month_hashtag}".strip(),
        "",
        f"#{plural}2025 #новинки2025 #премьеры2025 #ожидаемые{plural} #кино2025",
        "#Клип",
    ]

    # Переносим keyword_line в самый верх описания
    desc = keyword_line + "\n\n" + link_block + about_block + "\n".join(tail_lines)
    return title, desc


def iter_video_files(directory: str):
    p = pathlib.Path(directory)
    for ext in (".mp4", ".mov", ".mkv", ".webm"):
        for fp in sorted(p.glob(f"*{ext}")):
            yield str(fp)


def get_privacy(mode: str) -> str:
    if mode == "publish":
        return "public"
    if mode == "test":
        return "unlisted"
    return "private"


def get_authenticated_service(client_secrets: str, token_file: str, *, browser: Optional[str] = None, browser_path: Optional[str] = None):
    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception:
            creds = None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
        # Configure browser for local server OAuth
        # Options:
        #  - browser='yandex' (auto detect typical Windows or macOS paths)
        #  - browser_path='C:/Users/.../AppData/Local/Yandex/YandexBrowser/Application/browser.exe'
        #  - otherwise default system browser is used
        if browser or browser_path:
            import webbrowser, socket
            # Try to register Yandex browser or a custom path
            if browser_path and os.path.exists(browser_path):
                webbrowser.register('custom-browser', None, webbrowser.BackgroundBrowser(browser_path))
                used_browser = webbrowser.get('custom-browser')
            elif (browser or '').lower() in ['yandex', 'yabrowser', 'yandexbrowser']:
                import platform
                system = platform.system().lower()
                candidate_paths = []
                if system == 'windows':
                    candidate_paths += [
                        os.path.expandvars(r"%LOCALAPPDATA%/Yandex/YandexBrowser/Application/browser.exe"),
                        os.path.expandvars(r"%PROGRAMFILES%/Yandex/YandexBrowser/Application/browser.exe"),
                        os.path.expandvars(r"%PROGRAMFILES(X86)%/Yandex/YandexBrowser/Application/browser.exe"),
                    ]
                elif system == 'darwin':
                    candidate_paths += [
                        "/Applications/Yandex.app/Contents/MacOS/Yandex",
                        "/Applications/YandexBrowser.app/Contents/MacOS/YandexBrowser",
                    ]
                else:
                    candidate_paths += [
                        "/usr/bin/yandex-browser",
                        "/usr/bin/yandex-browser-stable",
                        "/opt/yandex/browser-beta/yandex-browser",
                    ]
                yandex_path = next((p for p in candidate_paths if os.path.exists(p)), None)
                if yandex_path:
                    webbrowser.register('yandex', None, webbrowser.BackgroundBrowser(yandex_path))
                    used_browser = webbrowser.get('yandex')
                else:
                    used_browser = None
            else:
                used_browser = None

            if used_browser:
                # Robust approach: patch webbrowser to force chosen browser, and let run_local_server handle state/url
                import webbrowser as _wb
                _orig_get = _wb.get
                _orig_open = _wb.open
                _orig_open_new = getattr(_wb, 'open_new', None)
                _orig_open_new_tab = getattr(_wb, 'open_new_tab', None)
                def _forced_get(name=None):
                    return used_browser
                def _forced_open(url, new=0, autoraise=True):
                    return used_browser.open(url, new=new, autoraise=autoraise)
                def _forced_open_new(url):
                    return used_browser.open(url, new=1)
                def _forced_open_new_tab(url):
                    return used_browser.open(url, new=2)
                _wb.get = _forced_get
                _wb.open = _forced_open
                if _orig_open_new:
                    _wb.open_new = _forced_open_new
                if _orig_open_new_tab:
                    _wb.open_new_tab = _forced_open_new_tab
                try:
                    creds = flow.run_local_server(port=0, open_browser=True)
                finally:
                    _wb.get = _orig_get
                    _wb.open = _orig_open
                    if _orig_open_new:
                        _wb.open_new = _orig_open_new
                    if _orig_open_new_tab:
                        _wb.open_new_tab = _orig_open_new_tab
            else:
                creds = flow.run_local_server(port=0, open_browser=True)
        else:
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)


def youtube_upload(youtube, file_path: str, title: str, description: str, *, category_id: str, privacy_status: str, made_for_kids: bool) -> str:
    body = {
        'snippet': {
            'title': title[:100],  # YouTube title limit ~100
            'description': description[:5000],
            'categoryId': category_id,
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': bool(made_for_kids),
        }
    }
    media = MediaFileUpload(file_path, chunksize=5 * 1024 * 1024, resumable=True)

    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if response is not None:
                # Successful upload
                return response.get('id')
        except HttpError as e:
            error = e
            if e.resp.status in [500, 502, 503, 504]:
                retry += 1
                sleep_s = min(2 ** retry, 16)
                print(f"[warn] Retriable HTTP error {e.resp.status}: {e}. Sleeping {sleep_s}s")
                time.sleep(sleep_s)
            else:
                raise
        except Exception as e:
            error = e
            retry += 1
            sleep_s = min(2 ** retry, 16)
            print(f"[warn] Retriable error: {e}. Sleeping {sleep_s}s")
            time.sleep(sleep_s)
        if retry > 5:
            raise Exception(f"Upload failed after retries: {error}")


def youtube_delete(youtube, video_id: str) -> bool:
    try:
        youtube.videos().delete(id=video_id).execute()
        return True
    except Exception as e:
        print(f"[warn] Delete failed for {video_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload shorts to YouTube")
    parser.add_argument("--dir", default="shorts", help="Directory with videos to upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process (0 = all)")
    parser.add_argument("--mode", choices=["dry-run", "test", "publish"], default="test", help="Upload mode")
    parser.add_argument("--delete-after", action="store_true", help="Delete video from YouTube after test upload")
    parser.add_argument("--title-template", default=None, help="Template for title, supports {basename}, {RU_TITLE}, {YEAR}")
    parser.add_argument("--site-url", default=os.getenv("SITE_URL", "http://www.kino.lordfilmshd-2026.ru"), help="Site root; final link will be {site}/{category}/{id}")
    parser.add_argument("--ndjson", default=os.getenv("MOVIES_NDJSON", "movies-data.ndjson"), help="Path to movies-data.ndjson to enrich title/description")
    parser.add_argument("--client-secrets", default=os.getenv("YT_CLIENT_SECRETS", "client_secrets.json"), help="Path to YouTube OAuth client_secrets.json (auto-detects client_secret_*.json in current dir)")
    parser.add_argument("--token-file", default=os.getenv("YT_TOKEN_FILE", "token.json"), help="Path to token.json where refresh token is stored")
    parser.add_argument("--category-id", default=os.getenv("YT_CATEGORY_ID", "1"), help="YouTube categoryId; default 1 (Film & Animation)")
    parser.add_argument("--made-for-kids", dest="made_for_kids", action="store_true", help="Mark video as made for kids (default false)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between uploads to avoid rate limits")
    parser.add_argument("--browser", choices=["yandex", "system"], default=os.getenv("YT_BROWSER", None), help="Browser to use for OAuth (yandex/system). Default: system")
    parser.add_argument("--browser-path", default=os.getenv("YT_BROWSER_PATH", None), help="Explicit path to browser executable for OAuth")

    args = parser.parse_args()

    # Auto-detect client_secret_*.json if default path doesn't exist
    if args.client_secrets == 'client_secrets.json' and not os.path.exists(args.client_secrets):
        for name in os.listdir('.'):
            if name.startswith('client_secret_') and name.endswith('.json') and os.path.isfile(name):
                print(f"[info] Auto-detected OAuth client secrets: {name}")
                args.client_secrets = name
                break

    if args.mode == "dry-run":
        print("[mode] DRY RUN: no API calls will be made")

    movies_map = load_movies_map(args.ndjson)

    files = list(iter_video_files(args.dir))
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"[info] No video files found in {args.dir}")
        return 0

    print(f"[info] Found {len(files)} files to process in {args.dir}")

    youtube = None
    if args.mode != "dry-run":
        if not os.path.exists(args.client_secrets):
            print(f"[error] client_secrets.json not found at {args.client_secrets}. See instructions in the script header.")
            return 2
        try:
            youtube = get_authenticated_service(args.client_secrets, args.token_file, browser=args.browser, browser_path=args.browser_path)
        except Exception as e:
            print(f"[error] Auth failed: {e}")
            return 2

    processed = 0
    for idx, fp in enumerate(files, start=1):
        size = os.path.getsize(fp)
        basename = pathlib.Path(fp).stem
        movie = movies_map.get(basename)
        title, desc = build_title_and_description(basename, movie, args.site_url, args.title_template)
        privacy = get_privacy(args.mode)
        print(f"[{idx}/{len(files)}] {os.path.basename(fp)} ({human_size(size)}) -> title='{title}' mode={args.mode} privacy={privacy}")

        if args.mode == "dry-run":
            continue

        try:
            video_id = youtube_upload(
                youtube,
                fp,
                title,
                desc,
                category_id=str(args.category_id),
                privacy_status=privacy,
                made_for_kids=bool(args.made_for_kids),
            )
            print(f"[ok] Uploaded video https://youtu.be/{video_id} title='{title}'")
        except Exception as e:
            print(f"[error] Upload failed for {fp}: {e}")
            continue

        if args.mode == "test" and args.delete_after and video_id:
            deleted = youtube_delete(youtube, video_id)
            print(f"[cleanup] delete-after={'ok' if deleted else 'failed'} for {video_id}")

        processed += 1
        if idx < len(files) and args.sleep > 0:
            time.sleep(args.sleep)

    print(f"[done] Processed {processed} file(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(130)
