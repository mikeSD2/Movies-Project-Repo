#!/usr/bin/env python3
"""
VK Shorts Uploader

Uploads videos from a directory (e.g., ./shorts) to VK (community or user) via VK API.
Supports:
- Dry-run (no API calls)
- Test upload (upload to videos without wall post)
- Publish (post to wall immediately)
- Optional deletion after test upload

Requirements:
- Python 3.8+
- requests

Authentication & Config:
- Set environment variables or pass CLI flags:
  - VK_ACCESS_TOKEN: VK API access token with permissions: video, wall, groups, offline
  - VK_GROUP_ID:     Community ID without the minus sign (e.g., 123456789). If omitted, uploads to the user account
  - VK_API_VERSION:  API version, default 5.199

Examples:
- Dry-run (preview):
  python publish_shorts_to_vk.py --dir shorts --mode dry-run

- Test upload (no wall post, stays in community videos):
  python publish_shorts_to_vk.py --dir shorts --mode test --limit 1

- Publish (post on wall):
  python publish_shorts_to_vk.py --dir shorts --mode publish --limit 1

- Test upload and then delete after verification:
  python publish_shorts_to_vk.py --dir shorts --mode test --delete-after --limit 1

Filename to title mapping:
- By default, the file name (without extension) becomes the video title.
- You can override with --title-template (e.g., "Short: {basename}")

Notes on test modes:
- dry-run: will not call VK at all
- test: video.save with wallpost=0, so it won't appear on the wall; it will be stored in the community/user videos
- publish: video.save with wallpost=1, so it posts to the wall right away

If you want an isolated test environment, consider creating a private test community and use its VK_GROUP_ID.

"""
import argparse
import os
import sys
import time
import json
import pathlib
import mimetypes
from typing import Optional, Dict, Any, Tuple

import requests
from requests.exceptions import RequestException
import base64
import hashlib
import string
import secrets
import urllib.parse

# Load environment variables from config.env if present
# 1) Try python-dotenv if available
# 2) Fallback: parse config.env manually so VK_ACCESS_TOKEN works even without extra deps
_loaded_env = False
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    if load_dotenv("config.env"):
        _loaded_env = True
except Exception:
    # ignore
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
                        # don't overwrite if already in environment
                        if k and (k not in os.environ):
                            os.environ[k] = v
        except Exception:
            # best-effort
            pass

DEFAULT_API_VERSION = os.getenv("VK_API_VERSION", "5.199")


def human_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


class VKApiError(Exception):
    def __init__(self, method: str, error: Dict[str, Any]):
        self.method = method
        self.error = error
        self.code = error.get("error_code") if isinstance(error, dict) else None
        super().__init__(f"VK API error in {method}: {error}")


def vk_api_call(method: str, params: Dict[str, Any], access_token: str, api_version: str = DEFAULT_API_VERSION, *, max_attempts: int = 3, backoff: float = 2.0) -> Dict[str, Any]:
    url = f"https://api.vk.com/method/{method}"
    payload = dict(params)
    payload["access_token"] = access_token
    payload["v"] = api_version

    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.post(url, data=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise VKApiError(method, data["error"])
            return data["response"]
        except (RequestException, VKApiError, ValueError) as e:
            last_exc = e
            if attempt < max_attempts:
                sleep_time = backoff ** (attempt - 1)
                print(f"[warn] {method} attempt {attempt} failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                break
    if isinstance(last_exc, VKApiError):
        raise last_exc
    raise Exception(f"{method} failed after {max_attempts} attempts: {last_exc}")


def vk_video_save(
    *,
    title: str,
    description: str = "",
    group_id: Optional[int] = None,
    wallpost: int = 0,
    is_private: int = 0,
    as_clip: bool = False,
    access_token: str,
    **extra,
) -> Dict[str, Any]:  # may raise VKApiError
    params: Dict[str, Any] = {
        "name": title[:128],  # VK title length constraints
        "description": description[:4096],
        "wallpost": wallpost,  # 1 to publish to wall
        "is_private": is_private,  # 1 to hide from search; not a full privacy lock
    }
    if group_id:
        params["group_id"] = group_id
    # Try parameters known in some VK API clients for short videos
    if as_clip:
        # undocumented/experimental; VK may ignore these without special access
        params.setdefault("short_video", 1)
        params.setdefault("is_short_video", 1)
    params.update(extra)
    return vk_api_call("video.save", params, access_token)


def vk_video_delete(video_id: int, owner_id: int, access_token: str) -> bool:
    try:
        resp = vk_api_call("video.delete", {"video_id": video_id, "owner_id": owner_id}, access_token)
        return bool(resp)
    except Exception as e:
        print(f"[warn] Failed to delete video {owner_id}_{video_id}: {e}")
        return False


def vk_wall_post(owner_id: int, message: str, attachments: str, from_group: int, access_token: str) -> Dict[str, Any]:
    params = {
        "owner_id": owner_id,  # negative for communities
        "message": message,
        "attachments": attachments,
        "from_group": from_group,  # 1 to post as community
        # "signed": 0,
        # "close_comments": 0,
    }
    return vk_api_call("wall.post", params, access_token)


def refresh_access_token(client_id: str, refresh_token: str, device_id: Optional[str] = None) -> Optional[str]:
    """Refresh VK ID access token using refresh_token. Returns new access_token or None on failure."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if device_id:
        payload["device_id"] = device_id
    for host in ("id.vk.com", "id.vk.ru"):
        try:
            resp = requests.post(
                f"https://{host}/oauth2/auth",
                data=payload,
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                if token:
                    print("[auth] access_token refreshed via", host)
                    return token
            else:
                # try next host
                pass
        except Exception:
            # ignore and try mirror
            pass
    print("[warn] Could not refresh access token; continue with existing token")
    return None


def upload_to_vk(upload_url: str, file_path: str, *, max_attempts: int = 3, backoff: float = 2.0) -> Dict[str, Any]:
    file_size = os.path.getsize(file_path)
    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or "video/mp4"
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            with open(file_path, "rb") as f:
                files = {"video_file": (os.path.basename(file_path), f, mime)}
                # VK handles large files with regular multipart; keep generous timeout
                resp = requests.post(upload_url, files=files, timeout=600)
                resp.raise_for_status()
                data = resp.json()
                # Expected keys: size, video_id, owner_id, direct_video_url (sometimes)
                return data
        except (RequestException, ValueError, Exception) as e:
            last_exc = e
            if attempt < max_attempts:
                sleep_time = backoff ** (attempt - 1)
                print(f"[warn] upload attempt {attempt} failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                break
    raise Exception(f"upload failed after {max_attempts} attempts: {last_exc}")


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


RU_NOUN_BY_CATEGORY = {
    # nominative singular
    "filmy": "фильм",
    "serialy": "сериал",
    "multfilmy": "мультфильм",
    "anime": "аниме",
}

RU_PLURAL_BY_CATEGORY = {
    # nominative plural for the block "фильмы 2025 года"
    "filmy": "фильмы",
    "serialy": "сериалы",
    "multfilmy": "мультфильмы",
    "anime": "аниме",
}

# Russian month names (genitive), to match premiere formatting like "1 октября 2025"
RU_MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def infer_month_from_premiere(premiere: Optional[str]) -> Optional[str]:
    if not premiere:
        return None
    s = str(premiere).strip().lower()
    # try simple tokenization: "DD <month> YYYY"
    parts = s.split()
    if len(parts) >= 2:
        m = parts[1]
        if m in RU_MONTHS_GEN:
            return m
    # fallback: search any known month token within the string
    for m in RU_MONTHS_GEN:
        if m in s:
            return m
    return None


def build_title_and_description(basename: str, movie: Optional[Dict[str, Any]], site_root: Optional[str], title_template: Optional[str]) -> Tuple[str, str]:
    # Extract fields
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

    # Title
    if title_template:
        title = title_template.format(basename=basename, RU_TITLE=(ru_title or basename), YEAR=(year or ""))
    else:
        # Build hashtag with 2025 fixed per request, change the noun by category
        noun = RU_NOUN_BY_CATEGORY.get(category or "", "фильм")
        # As requested: keep 2025 in the hashtag for discoverability
        title = f"{(ru_title or basename)} ({year or ''}) - Официальный русский трейлер | #{noun}2025 #новыесериалы #клип"

    # Description
    # Link block with dynamic per-movie URL if possible
    link_line = "ПОСМОТРЕТЬ ПОЛНОСТЬЮ МОЖНО ТУТ:\n"
    item_url = (site_root or "").rstrip("/")
    if movie and movie.get("category") and movie.get("id"):
        item_url = f"{(site_root or 'http://www.kino.lordfilmshd-2026.ru').rstrip('/')}" \
                   f"/{movie.get('category').strip('/')}/{movie.get('id')}"
    link_block = f"{link_line}{item_url}\n\n"

    # Short description up to 400 chars
    short_desc = (description or "")
    short_desc = short_desc.replace("\r\n", "\n").replace("\r", "\n")
    if len(short_desc) > 400:
        short_desc = short_desc[:400].rstrip() + "..."

    about_block = "О фильме:\n" + (short_desc or "") + "\n\n"

    # Keyword tail block
    plural = RU_PLURAL_BY_CATEGORY.get(category or "", "фильмы")

    # dynamic month hashtag like #новинкиоктября based on premiere, fallback to #новинки
    prem_mon = infer_month_from_premiere(movie.get('premiere') if movie else None)
    month_hashtag = f"#новинки{prem_mon}" if prem_mon else "#новинки"

    # build dynamic genre hashtags from movie.genres if present
    genres = []
    if movie:
        raw_genres = movie.get('genres') or []
        if isinstance(raw_genres, list):
            genres = [str(g).strip().lower() for g in raw_genres if str(g).strip()]
        elif isinstance(raw_genres, str):
            genres = [s.strip().lower() for s in raw_genres.split(',') if s.strip()]

    # map some common russian genre names to hashtags; pass-through unknowns
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
            # fallback: prepend '#' and strip spaces (no spaces allowed in hashtag)
            genre_tags.append('#' + g.replace(' ', ''))

    # assemble tail text and hashtags
    # Build dynamic keyword line with category-aware phrases
    singular = RU_NOUN_BY_CATEGORY.get(category or "", "фильм")
    keyword_line = (
        f"{(ru_title or basename)}, {(en_title or '')}, {plural} {(year or '')} года, русский трейлер, трейлеры, "
        f"официальный трейлер, дублированный трейлер, новые {plural}, премьера, в хорошем качестве, hd, "
        f"{plural} на вечер, что посмотреть, {singular}, кино, {plural} онлайн, лучшие {plural}, топ {plural}, смотреть онлайн бесплатно"
    )

    # add category hashtag
    CATEGORY_TAG = {
        'filmy': '#фильмы', 'serialy': '#сериалы', 'multfilmy': '#мультфильмы', 'anime': '#аниме'
    }
    category_tag = CATEGORY_TAG.get((category or '').lower(), '#фильмы')

    tail_lines = [
        "---",
        keyword_line,
        "",
        f"{category_tag} {' '.join(genre_tags[:12])} {month_hashtag}".strip(),
        "",
        f"#{plural}2025 #новинки2025 #премьеры2025 #ожидаемые{plural} #кино2025",
    ]
    desc = link_block + about_block + "\n".join(tail_lines)

    return title, desc


def iter_video_files(directory: str):
    p = pathlib.Path(directory)
    for ext in (".mp4", ".mov", ".mkv", ".webm"):
        for fp in sorted(p.glob(f"*{ext}")):
            yield str(fp)


def _b64url_no_pad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _sha256_b64url_no_pad(s: str) -> str:
    return _b64url_no_pad(hashlib.sha256(s.encode("ascii")).digest())


def main():
    parser = argparse.ArgumentParser(description="Upload shorts to VK")
    parser.add_argument("--dir", default="shorts", help="Directory with videos to upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process (0 = all)")
    parser.add_argument("--mode", choices=["dry-run", "test", "publish"], default="test", help="Upload mode")
    parser.add_argument("--delete-after", action="store_true", help="Delete video from VK after test upload")
    parser.add_argument("--title-template", default=None, help="Template for title, supports {basename}, {RU_TITLE}, {YEAR}")
    parser.add_argument("--site-url", default=os.getenv("SITE_URL", "http://www.kino.lordfilmshd-2026.ru"), help="Site root; final link will be {site}/{category}/{id}")
    parser.add_argument("--ndjson", default=os.getenv("MOVIES_NDJSON", "movies-data.ndjson"), help="Path to movies-data.ndjson to enrich title/description")
    parser.add_argument("--access-token", default=os.getenv("VK_ACCESS_TOKEN"), help="VK access token")
    parser.add_argument("--refresh-token", default=os.getenv("VK_REFRESH_TOKEN"), help="VK refresh token (optional, for auto-refresh)")
    parser.add_argument("--client-id", default=os.getenv("VK_CLIENT_ID"), help="VK APP_ID (client_id) — required to refresh token if refresh_token is provided")
    parser.add_argument("--group-id", type=int, default=int(os.getenv("VK_GROUP_ID", "0") or 0), help="Community ID without minus sign")
    parser.add_argument("--api-version", default=DEFAULT_API_VERSION, help="VK API version")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between uploads to avoid rate limits")
    parser.add_argument("--device-id", default=os.getenv("VK_DEVICE_ID"), help="Optional device_id to use for VK ID token refresh")
    parser.add_argument("--as-clip", action="store_true", help="Attempt to upload as VK short/clip (set is_short_video/short_video)")

    args = parser.parse_args()

    if args.mode == "dry-run":
        print("[mode] DRY RUN: no API calls will be made")

    # Validate tokens configuration
    if args.mode != "dry-run" and not args.access_token and not args.refresh_token:
        print("[error] Provide --access-token or --refresh-token to proceed (non dry-run)")
        return 2
    if args.refresh_token and not args.client_id:
        print("[error] --client-id (APP_ID) is required when --refresh-token is provided for auto-refresh")
        return 2

    # Build movies map to enrich titles/descriptions
    movies_map = load_movies_map(args.ndjson)

    files = list(iter_video_files(args.dir))
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"[info] No video files found in {args.dir}")
        return 0

    print(f"[info] Found {len(files)} files to process in {args.dir}")

    processed = 0
    for idx, fp in enumerate(files, start=1):
        size = os.path.getsize(fp)
        basename = pathlib.Path(fp).stem
        movie = movies_map.get(basename)
        title, desc = build_title_and_description(basename, movie, args.site_url, args.title_template)
        print(f"[{idx}/{len(files)}] {os.path.basename(fp)} ({human_size(size)}) -> title='{title}' mode={args.mode}")

        if args.mode == "dry-run":
            continue

        # Avoid duplicates: don't let video.save auto-post to wall; we'll always do explicit wall.post in publish
        wallpost = 0
        # Simple auto-refresh wrapper for token expiration (error_code 5 or 28)
        def _ensure_token_and_call(group_id_opt: Optional[int]):
            nonlocal args
            try:
                return vk_video_save(
                    title=title,
                    description=desc,
                    group_id=(group_id_opt or None),
                    wallpost=wallpost,
                    is_private=0,
                    as_clip=args.as_clip,
                    access_token=args.access_token,
                )
            except VKApiError as e:
                if e.code in (5, 28) and args.refresh_token and args.client_id:
                    # try refresh once
                    new_token = refresh_access_token(args.client_id, args.refresh_token, args.device_id)
                    if new_token:
                        args.access_token = new_token
                        return vk_video_save(
                            title=title,
                            description=desc,
                            group_id=(group_id_opt or None),
                            wallpost=wallpost,
                            is_private=0,
                            access_token=args.access_token,
                        )
                raise

        did_group_save = False
        try:
            save_resp = _ensure_token_and_call(args.group_id or 0)
            did_group_save = bool(args.group_id)
        except VKApiError as e:
            if (getattr(e, 'code', None) == 7) and args.group_id:
                print("[warn] No permission to upload to group videos (error 7). Will upload to USER account instead and continue.")
                try:
                    save_resp = _ensure_token_and_call(0)
                    did_group_save = False
                except Exception as e2:
                    print(f"[error] video.save (user) also failed for {fp}: {e2}")
                    continue
            else:
                print(f"[error] video.save failed for {fp}: {e}")
                continue
        except Exception as e:
            print(f"[error] video.save failed for {fp}: {e}")
            continue

        upload_url = save_resp.get("upload_url")
        owner_id = int(save_resp.get("owner_id"))  # when group save succeeds, API may return community id positive
        if did_group_save and args.group_id and owner_id > 0:
            # For group uploads, owner_id should be -group_id when referring to attachments/wall
            owner_id = -int(args.group_id)

        if not upload_url:
            print(f"[error] No upload_url for {fp}: {json.dumps(save_resp, ensure_ascii=False)}")
            continue

        try:
            upl = upload_to_vk(upload_url, fp)
        except Exception as e:
            print(f"[error] Upload failed for {fp}: {e}")
            continue

        video_id = int(upl.get("video_id") or upl.get("video") or 0)
        if not video_id:
            print(f"[warn] Unexpected upload response: {json.dumps(upl)}")
        else:
            print(f"[ok] Uploaded video id={owner_id}_{video_id} title='{title}'")

        # If publish mode, do a dedicated wall.post so the text (title+description) is visible on the community post
        if args.mode == "publish" and args.group_id and video_id:
            try:
                attachments = f"video{owner_id}_{video_id}"
                wall_owner_id = -int(args.group_id)
                message = f"{title}\n\n{desc}"  # Put description into wall post body so it’s visible in the post
                post_resp = vk_wall_post(owner_id=wall_owner_id, message=message, attachments=attachments, from_group=1, access_token=args.access_token)
                post_id = post_resp.get("post_id")
                print(f"[ok] Posted to group wall with post_id={post_id}, attachment={attachments}")
            except Exception as e:
                print(f"[warn] Failed to post to group wall: {e}")

        # In test mode with delete-after, remove the uploaded video from VK to leave no trace
        if args.mode == "test" and args.delete_after and video_id:
            deleted = vk_video_delete(video_id=video_id, owner_id=owner_id, access_token=args.access_token)
            print(f"[cleanup] delete-after={'ok' if deleted else 'failed'} for {owner_id}_{video_id}")

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
