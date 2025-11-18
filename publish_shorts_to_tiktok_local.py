#!/usr/bin/env python3
"""
TikTok Web Uploader (local UI automation via Playwright)

DISCLAIMER:
- Это обходной путь без официального API. Он хрупкий: TikTok может менять разметку/защиту.
- Рекомендуется использовать только на своей машине, вручную пройдя логин 1 раз в сохраненном профиле.
- Возможны капчи/2FA/антибот. Скрипт не гарантирует стабильность и может перестать работать.

Идея:
- Используем Playwright с persistent storage (user data dir), чтобы один раз залогиниться и дальше переиспользовать сессию.
- Открываем https://www.tiktok.com/tiktokstudio/upload?from=creator_center
- Находим input[type=file][accept="video/*"] и загружаем файл.
- Вставляем подпись (caption) в contenteditable поле.
- В режиме publish нажимаем кнопку публикации.

Установка:
- Python 3.9+
- pip install playwright python-dotenv
- python -m playwright install

Примеры:
- Просмотр (без клика «Опубликовать»):
  python publish_shorts_to_tiktok_local.py --dir shorts --mode test --limit 1

- Публикация:
  python publish_shorts_to_tiktok_local.py --dir shorts --mode publish --limit 1

Замечания:
- Скрипт пытается подстроиться под русскую/английскую локаль (тексты кнопок могут отличаться).
- Поле подписи у TikTok одно (caption). Мы формируем его из заголовка и описания, но режем до лимита (~2200 символов).
"""
import argparse
import os
import sys
import time
import json
import pathlib
import random
from typing import Optional, Dict, Any, Tuple

# Optional: auto-load env like другие скрипты
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

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except Exception as e:
    print("[error] Playwright is not installed. Run: pip install playwright && python -m playwright install")
    raise


RU_NOUN_BY_CATEGORY = {
    "filmy": "фильм",
    "serialy": "сериал",
    "multfilmy": "мультфильм",
    "anime": "аниме",
}
RU_PLURAL_BY_CATEGORY = {
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

    if title_template:
        title = title_template.format(basename=basename, RU_TITLE=(ru_title or basename), YEAR=(year or ""))
    else:
        noun = RU_NOUN_BY_CATEGORY.get(category or "", "фильм")
        title = f"{(ru_title or basename)} ({year or ''}) - Официальный русский трейлер | #{noun}2025 #новыесериалы #shorts"

    # Build link line (как в других скриптах)
    link_line = "ПОСМОТРЕТЬ ПОЛНОСТЬЮ МОЖНО ТУТ:\n"
    item_url = (site_root or "").rstrip("/")
    if movie and movie.get("category") and movie.get("id"):
        item_url = f"{(site_root or 'http://www.kino.lordfilmshd-2026.ru').rstrip('/')}" \
                   f"/{movie.get('category').strip('/')}/{movie.get('id')}"
    link_block = f"{link_line}{item_url}\n\n"

    short_desc = (description or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(short_desc) > 400:
        short_desc = short_desc[:400].rstrip() + "..."
    about_block = "О фильме:\n" + (short_desc or "") + "\n\n"

    plural = RU_PLURAL_BY_CATEGORY.get((movie.get("category") if movie else "") or "", "фильмы")
    singular = RU_NOUN_BY_CATEGORY.get((movie.get("category") if movie else "") or "", "фильм")
    prem_mon = infer_month_from_premiere(movie.get('premiere') if movie else None)
    month_hashtag = f"#новинки{prem_mon}" if prem_mon else "#новинки"

    # genres -> hashtags
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
        genre_tags.append(GENRE_TAG_MAP.get(g, '#' + g.replace(' ', '')))

    CATEGORY_TAG = {
        'filmy': '#фильмы', 'serialy': '#сериалы', 'multfilmy': '#мультфильмы', 'anime': '#аниме'
    }
    category_tag = CATEGORY_TAG.get(((movie.get("category") or '') if movie else '').lower(), '#фильмы')

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

    # TikTok имеет одно поле caption. Сформируем caption на основе title + адаптированного описания.
    description = keyword_line + "\n\n" + link_block + about_block + "\n".join(tail_lines)
    return title, description


def build_caption(title: str, description: str, limit: int = 2200) -> str:
    caption = f"{title}\n\n{description}".strip()
    if len(caption) > limit:
        # оставим начало и хэштеги из конца, если есть
        tail = caption[-600:]
        head = caption[: (limit - len(tail) - 10)]  # запас на разделитель
        caption = (head.rstrip() + "\n...\n" + tail).strip()
        if len(caption) > limit:
            caption = caption[:limit]
    return caption


def human_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def iter_video_files(directory: str):
    p = pathlib.Path(directory)
    for ext in (".mp4", ".mov", ".mkv", ".webm"):
        for fp in sorted(p.glob(f"*{ext}")):
            yield str(fp)


UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=creator_center"


def _goto_upload_with_retry(page, retries: int = 3, initial_delay: float = 0.5) -> bool:
    """Открывает страницу загрузки с повторами, если появляется ошибка
    "Что-то пошло не так / Повторите попытку" или аналогичные сбои загрузки.
    Возвращает True при успехе."""
    for attempt in range(1, retries + 1):
        try:
            page.goto(UPLOAD_URL, timeout=120_000)
        except Exception:
            pass
        # Небольшая пауза, чтобы отрендерилось
        time.sleep(initial_delay)
        # Проверим наличие текста об ошибке или кнопки повтора
        try:
            err = page.query_selector("text=Что-то пошло не так") or page.query_selector("text=Something went wrong")
            if err:
                # попробуем нажать Повторите попытку/Retry
                try:
                    retry_btn = page.query_selector("button:has-text('Повторите попытку')") or page.query_selector("button:has-text('Retry')")
                    if retry_btn:
                        retry_btn.click()
                        time.sleep(1.0)
                        # Проверим, ушла ли ошибка
                        gone = not (page.query_selector("text=Что-то пошло не так") or page.query_selector("text=Something went wrong"))
                        if gone:
                            return True
                except Exception:
                    pass
                # Если кнопка не помогла — попробуем перезагрузить страницу
                try:
                    page.reload()
                except Exception:
                    pass
                time.sleep(1.0 + attempt * 0.5)
                continue
        except Exception:
            pass
        # Также проверим, что реально виден UI загрузки
        try:
            ok = page.query_selector("[data-e2e='select_video_button']") or page.query_selector("input[type='file']")
            if ok:
                return True
        except Exception:
            pass
        # Дадим шанс ещё раз
        time.sleep(0.8 + attempt * 0.5)
    return False


def _close_blocking_modals(page, timeout: int = 1000) -> bool:
    """Пытается закрыть/подтвердить блокирующие модалки, если они открыты.
    Возвращает True, если какие-то действия были выполнены (что-то закрылось/подтвердилось).
    """
    acted = False
    try:
        # 0) Специальный кейс: модалка 'Продолжить публикацию?' с TUXButton
        try:
            modal = page.query_selector(".common-modal-confirm-modal, .TUXModal.common-modal[title*='Продолжить публикацию']")
            if modal:
                # Попробуем найти primary кнопку
                btn = modal.query_selector("button.TUXButton--primary, .TUXButton.TUXButton--primary, button:has-text('Опубликовать')")
                if btn:
                    try:
                        btn.click()
                    except Exception:
                        try:
                            page.evaluate("el => el.click()", btn)
                        except Exception:
                            pass
                    acted = True
                    page.wait_for_timeout(200)
                else:
                    # Попробуем найти label 'Опубликовать' и подняться к button
                    lbls = modal.query_selector_all(".TUXButton-label") or []
                    for l in lbls:
                        try:
                            txt = (l.inner_text() or "").strip()
                        except Exception:
                            txt = ""
                        if txt and ("Опубликовать" in txt or "Publish" in txt):
                            try:
                                page.evaluate("el => { const b = el.closest('button'); if (b) b.click(); }", l)
                                acted = True
                                page.wait_for_timeout(200)
                                break
                            except Exception:
                                pass
        except Exception:
            pass
        # Популярные варианты кнопок подтверждения/закрытия
        btn_selectors = [
            "[data-e2e='modal-close']",
            "div.common-modal-close",
            "div.common-modal-close-icon",
            # Русские варианты
            "button:has-text('Все равно опубликовать')",
            "button:has-text('Опубликовать все равно')",
            "button:has-text('Опубликовать всё равно')",
            "button:has-text('Продолжить публикацию')",
            "[role='button']:has-text('Продолжить публикацию')",
            "button:has-text('Опубликовать')",
            "[role='button']:has-text('Опубликовать')",
            "button:has-text('Продолжить')",
            "[role='button']:has-text('Продолжить')",
            "button:has-text('Понятно')",
            "button:has-text('ОК')",
            # Английские варианты
            "button:has-text('Publish anyway')",
            "[role='button']:has-text('Publish anyway')",
            "button:has-text('Continue publishing')",
            "[role='button']:has-text('Continue publishing')",
            "button:has-text('Publish')",
            "[role='button']:has-text('Publish')",
            "button:has-text('OK')",
            "button:has-text('Ok')",
            "button:has-text('Close')",
            "button:has-text('Continue')",
            "button:has-text('Got it')",
            # Кнопка "Заменить видео" нам не нужна — избегаем её
        ]
        # Сначала пробуем крестик в заголовке
        for sel in ["div.common-modal-close", "div.common-modal-close-icon", "[aria-label='Закрыть']", "[aria-label='Close']"]:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    acted = True
                    page.wait_for_timeout(200)
            except Exception:
                pass
        # Затем подтверждающие кнопки
        for sel in btn_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    # Защитимся от клика по "Заменить видео" — пропустим
                    text = ""
                    try:
                        text = (el.inner_text() or "").strip().lower()
                    except Exception:
                        pass
                    if "заменить видео" in text:
                        continue
                    el.click()
                    acted = True
                    page.wait_for_timeout(250)
            except Exception:
                pass
        # На всякий случай: найдём любой активный диалог и нажмём последнюю primary-кнопку
        try:
            dialogs = page.query_selector_all("[role='dialog'], .TUXModal, .common-modal") or []
            for d in dialogs:
                try:
                    btns = d.query_selector_all("button") or []
                    for b in btns[::-1]:
                        try:
                            t = (b.inner_text() or "").strip().lower()
                        except Exception:
                            t = ""
                        if t and ("заменить видео" in t):
                            continue
                        if t and any(ok in t for ok in ["опубликовать", "продолжить", "понятно", "ok", "close", "got it"]):
                            b.click()
                            acted = True
                            page.wait_for_timeout(250)
                            break
                except Exception:
                    continue
        except Exception:
            pass
    except Exception:
        pass
    return acted


class TikTokUploader:
    def __init__(self, *, user_data_dir: str, headless: bool = False, slow_mo: float = 0,
                 use_yandex: bool = False, yandex_path: Optional[str] = None, yandex_user_data_dir: Optional[str] = None,
                 cdp_port: int = 9222, attach_running: bool = False, yandex_profile_directory: Optional[str] = None):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.slow_mo = slow_mo
        self.use_yandex = use_yandex
        self.yandex_path = yandex_path
        # В режиме Yandex по умолчанию используем профиль браузера по умолчанию (Default)
        self.yandex_user_data_dir = yandex_user_data_dir
        # Если профиль не указан — подставим системный "Default" сразу здесь
        try:
            import platform
            if use_yandex and not self.yandex_user_data_dir:
                system = platform.system().lower()
                if system == 'windows':
                    self.yandex_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%/Yandex/YandexBrowser/User Data/Default")
                elif system == 'darwin':
                    self.yandex_user_data_dir = os.path.expanduser("~/Library/Application Support/Yandex/YandexBrowser/Default")
                else:
                    self.yandex_user_data_dir = os.path.expanduser("~/.config/yandex-browser/Default")
        except Exception:
            pass
        self.cdp_port = cdp_port
        self.attach_running = attach_running
        self.play = None
        self.browser = None
        self.context = None
        self.page = None
        self._ext_browser_proc = None

    def __enter__(self):
        import subprocess, time, platform, urllib.request, psutil, signal
        self.play = sync_playwright().start()
        if self.use_yandex:
            # Если просили подключиться к уже запущенному браузеру — просто цепляемся по CDP и открываем новую вкладку
            if getattr(self, 'attach_running', False):
                endpoint = f"http://localhost:{self.cdp_port}" if not str(self.cdp_port).startswith("http") else str(self.cdp_port)
                try:
                    print(f"[info] Подключаюсь к уже запущенному Yandex по {endpoint}...")
                    self.browser = self.play.chromium.connect_over_cdp(endpoint)
                    # Пытаемся открыть новую вкладку через CDP HTTP API, чтобы гарантированно создать target в текущем окне/профиле
                    try:
                        import urllib.parse
                        new_url = f"{endpoint}/json/new?{urllib.parse.quote(UPLOAD_URL, safe=':/?&=') }"
                        with urllib.request.urlopen(new_url, timeout=2) as resp:
                            _ = resp.read()
                        time.sleep(0.5)
                    except Exception:
                        pass
                    # Найдём страницу с нужным URL
                    target_page = None
                    ctxs = getattr(self.browser, 'contexts', []) or []
                    for ctx in ctxs:
                        try:
                            for p in ctx.pages:
                                u = ''
                                try:
                                    u = p.url
                                except Exception:
                                    u = ''
                                if 'tiktokstudio/upload' in u:
                                    target_page = p
                                    self.context = ctx
                                    break
                            if target_page:
                                break
                        except Exception:
                            continue
                    if not target_page:
                        # fallback: попробуем создать вкладку через Playwright в первом контексте
                        if ctxs:
                            try:
                                self.context = ctxs[0]
                                target_page = self.context.new_page()
                            except Exception:
                                pass
                    if not target_page:
                        raise RuntimeError("Не удалось найти/создать вкладку в уже запущенном Yandex. Убедитесь, что запущен с --remote-debugging-port и откройте любую вкладку вручную.")
                    self.page = target_page
                    return self
                except Exception as e:
                    # В режиме attach-running НИКОГДА не запускаем новое окно, чтобы не терять сессию
                    raise RuntimeError(f"Не удалось подключиться к уже запущенному Yandex по {endpoint}: {e}")
            # Перезапуск Яндекса под нужным профилем, если попросили
            if getattr(self, 'args', None) and getattr(self.args, 'restart_yandex', False):
                # Убьём процессы browser.exe
                try:
                    for p in psutil.process_iter(['name', 'exe', 'cmdline']):
                        if (p.info.get('name') or '').lower().startswith('browser') and 'YandexBrowser' in (p.info.get('exe') or ''):
                            try:
                                p.terminate()
                            except Exception:
                                pass
                    time.sleep(1.0)
                except Exception:
                    pass
            # Автоопределение пути к Yandex Browser, если не указан
            if not self.yandex_path:
                env_path = os.getenv("YANDEX_BROWSER_PATH")
                if env_path and os.path.exists(env_path):
                    self.yandex_path = env_path
                else:
                    system = platform.system().lower()
                    candidates = []
                    if system == 'windows':
                        candidates += [
                            os.path.expandvars(r"%LOCALAPPDATA%/Yandex/YandexBrowser/Application/browser.exe"),
                            os.path.expandvars(r"%PROGRAMFILES%/Yandex/YandexBrowser/Application/browser.exe"),
                            os.path.expandvars(r"%PROGRAMFILES(X86)%/Yandex/YandexBrowser/Application/browser.exe"),
                        ]
                        if not self.yandex_user_data_dir:
                            self.yandex_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%/Yandex/YandexBrowser/User Data/Default")
                    elif system == 'darwin':
                        candidates += [
                            "/Applications/Yandex.app/Contents/MacOS/Yandex",
                            "/Applications/YandexBrowser.app/Contents/MacOS/YandexBrowser",
                        ]
                        if not self.yandex_user_data_dir:
                            self.yandex_user_data_dir = os.path.expanduser("~/Library/Application Support/Yandex/YandexBrowser/Default")
                    else:
                        candidates += [
                            "/usr/bin/yandex-browser",
                            "/usr/bin/yandex-browser-stable",
                            "/opt/yandex/browser-beta/yandex-browser",
                        ]
                        if not self.yandex_user_data_dir:
                            self.yandex_user_data_dir = os.path.expanduser("~/.config/yandex-browser/Default")
                    self.yandex_path = next((p for p in candidates if os.path.exists(p)), None)
            if not self.yandex_path or not os.path.exists(self.yandex_path):
                raise RuntimeError("Не найден Yandex Browser. Укажите --yandex-path или переменную окружения YANDEX_BROWSER_PATH")
            # Убедимся, что есть папка профиля (если задана)
            if self.yandex_user_data_dir and not os.path.exists(self.yandex_user_data_dir):
                try:
                    os.makedirs(self.yandex_user_data_dir, exist_ok=True)
                except Exception:
                    pass
            print(f"[info] Yandex path: {self.yandex_path}")
            print(f"[info] Yandex profile: {self.yandex_user_data_dir}")
            print(f"[info] DevTools port: {self.cdp_port}")
            args = [
                self.yandex_path,
                f"--remote-debugging-port={self.cdp_port}",
                f"--user-data-dir={self.yandex_user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            try:
                self._ext_browser_proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                raise RuntimeError(f"Не удалось запустить Yandex: {e}")
            # Ждём, пока поднимется DevTools endpoint
            endpoint = f"http://localhost:{self.cdp_port}"
            for _ in range(120):
                try:
                    with urllib.request.urlopen(endpoint, timeout=0.5) as _r:
                        break
                except Exception:
                    time.sleep(0.5)
            # Подключаемся к уже запущенному Yandex по CDP
            self.browser = self.play.chromium.connect_over_cdp(endpoint)
            # Берём первый контекст или создаём новый
            ctxs = self.browser.contexts
            self.context = ctxs[0] if ctxs else self.browser.new_context()
        else:
            # Обычный persistent Chromium от Playwright
            self.context = self.play.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--no-sandbox",
                ],
            )
        self.page = self.context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser and not self.use_yandex:
                self.browser.close()
        except Exception:
            pass
        try:
            if self.play:
                self.play.stop()
        except Exception:
            pass
        # Если мы сами запускали Yandex — попробуем закрыть
        try:
            if self._ext_browser_proc:
                self._ext_browser_proc.terminate()
        except Exception:
            pass

    def ensure_logged_in(self, timeout_ms: int = 120_000):
        # Переходим на upload и ждём появления контейнера загрузки
        p = self.page
        if not _goto_upload_with_retry(p, retries=4):
            raise RuntimeError("Не удалось открыть страницу загрузки после нескольких попыток")
        # Попробуем закрыть возможные попапы (cookies/unsaved draft)
        try:
            # Cookies banner
            for sel in ["button:has-text('Accept')", "button:has-text('Принять')", "button:has-text('Принять все')"]:
                btn = p.query_selector(sel)
                if btn:
                    btn.click()
                    time.sleep(0.2)
                    break
        except Exception:
            pass
        try:
            # Unsaved draft dialog -> click Continue/Продолжить
            for sel in ["button:has-text('Продолжить')", "button:has-text('Continue')"]:
                btn = p.query_selector(sel)
                if btn:
                    btn.click()
                    time.sleep(0.3)
                    break
        except Exception:
            pass
        # если не залогинен, TikTok может редиректить на /login
        # Поищем input в основной странице и во фреймах
        deadline = time.time() + (timeout_ms/1000)
        while time.time() < deadline:
            try:
                el = p.query_selector("input[type=file]")
                if el:
                    return True
                # сканируем фреймы
                for fr in p.frames:
                    try:
                        el = fr.query_selector("input[type=file]")
                        if el:
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            time.sleep(0.5)
        # Не нашли — дадим пользователю войти и повторим длинным ожиданием
        print("[info] Похоже, требуется вход в аккаунт TikTok или UI не загрузился. Выполните логин, если требуется.")
        p.wait_for_selector("[data-e2e='select_video_button'], input[type='file']", timeout=600_000)
        return True

    def upload_one(self, file_path: str, caption_text: str, mode: str = "test") -> bool:
        page = self.page
        abs_path = os.path.abspath(file_path)
        # гарантируем, что мы на странице загрузки
        if not _goto_upload_with_retry(page, retries=4):
            print("[warn] Не удалось открыть страницу загрузки, пропускаю файл")
            return False
        time.sleep(0.5)
        used_fc = False
        # 0) Попробуем закрыть всплывашки и нажать "Выбрать видео". Если поддерживается нативный FileChooser — используем его.
        try:
            btn = page.query_selector("[data-e2e='select_video_button']") or page.query_selector("button:has-text('Выбрать видео')") or page.query_selector("button:has-text('Select video')")
            if btn:
                try:
                    with page.expect_file_chooser(timeout=2000) as fc_info:
                        try:
                            btn.click()
                        except Exception:
                            # Иногда требуется двойной клик
                            try:
                                btn.dispatch_event("click")
                            except Exception:
                                pass
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_path)
                    print("[info] Файл выбран через FileChooser API")
                    used_fc = True
                    # Ждём, что карточка выбора исчезнет
                    try:
                        page.wait_for_selector("[data-e2e='select_video_button']", timeout=10_000, state='detached')
                    except Exception:
                        pass
                except Exception:
                    # Если FileChooser не всплыл — просто кликнем и продолжим стандартный поиск input
                    try:
                        btn.click()
                    except Exception:
                        try:
                            btn.dispatch_event("click")
                        except Exception:
                            pass
                time.sleep(0.6)
        except Exception:
            pass

        uploaded = False
        last_err = None

        if not used_fc:
            # 1) Находим input file и загружаем видео (в том числе, если он display:none)
            inputs = []
            try:
                inputs = page.query_selector_all("input[type='file']")
            except Exception:
                inputs = []
            if not inputs:
                # На всякий случай попробуем кликнуть по контейнеру выбора видео, чтобы смонтировать input
                try:
                    cont = page.query_selector("[data-e2e='select_video_container']")
                    if cont:
                        cont.click()
                        time.sleep(0.3)
                except Exception:
                    pass
                # На всякий случай проверим фреймы
                try:
                    for fr in page.frames:
                        try:
                            fr_inputs = fr.query_selector_all("input[type='file']")
                            if fr_inputs:
                                inputs.extend(fr_inputs)
                        except Exception:
                            continue
                except Exception:
                    pass
                # Попробуем альтернативные локаторы (XPath, без кавычек в селекторе)
                try:
                    xpath_inputs = page.query_selector_all("xpath=//input[@type='file']")
                    if xpath_inputs:
                        inputs.extend(xpath_inputs)
                except Exception:
                    pass

            if not inputs:
                try:
                    # Диагностика: посчитаем количество file-инпутов через JS
                    cnt = page.evaluate("() => document.querySelectorAll('input[type=\\'file\\']').length")
                    print(f"[debug] На странице найдено input[type=file]: {cnt}")
                except Exception:
                    pass
                print("[error] Не найден input для загрузки видео. UI TikTok мог измениться. Попробуйте нажать 'Выбрать видео' вручную.")
                return False

            for idx, el in enumerate(inputs, start=1):
                try:
                    el.set_input_files(abs_path)
                    print(f"[info] Файл отправлен в загрузку через input #{idx}: {os.path.basename(abs_path)}")
                    uploaded = True
                    break
                except Exception as e:
                    last_err = e
                    continue
            if not uploaded:
                print(f"[error] Не удалось передать файл в инпут: {last_err}")
                return False
        else:
            uploaded = True

        print("[info] Файл отправлен в загрузку, ожидаем завершение анализа/обработки...")

        # 2) Дождаться, что файл принят (появление прогресса/миниатюры/стадии редактирования)
        # Ждём исчезновение карточки before-upload/new-stage или появление caption
        try:
            page.wait_for_selector("[data-e2e='select_video_button']", timeout=10_000, state='detached')
        except Exception:
            pass

        # Ждём поле caption (contenteditable)
        caption_sel_candidates = [
            "div.public-DraftEditor-content[contenteditable='true']",
            "div[contenteditable='true'][role='combobox']",
            "div[aria-label*='Расскажите о своем видео']",
        ]
        caption_el = None
        for sel in caption_sel_candidates:
            try:
                caption_el = page.wait_for_selector(sel, timeout=120_000)
                if caption_el:
                    break
            except PWTimeout:
                continue

        if not caption_el:
            print("[warn] Не удалось обнаружить поле подписи. Попробую продолжить.")
        else:
            # Сфокусироваться и вставить caption. Часто лучше эмулировать Ctrl+A + ввод текста
            # Небольшие случайные задержки и набор текста с вариативной скоростью
            caption_el.click()
            time.sleep(random.uniform(0.2, 0.6))
            page.keyboard.press("Control+A")
            time.sleep(random.uniform(0.1, 0.3))
            # Разобьём на куски, как будто печатаем абзацами
            for chunk in caption_text.split("\n"):
                page.keyboard.type(chunk, delay=random.uniform(0.4, 1.2))
                page.keyboard.press("Enter")
                time.sleep(random.uniform(0.05, 0.2))
            print("[info] Подпись заполнена (усечена до лимита при необходимости)")

        # 3) В режиме publish нажать кнопку публикации с обработкой блокирующих модалок
        if mode == "publish":
            # Небольшая случайная пауза, как будто человек
            time.sleep(random.uniform(0.6, 1.5))
            publish_btn_selectors = [
                "button:has-text('Опубликовать')",
                "button:has-text('Publish')",
                "[data-e2e='post_btn']",
            ]

            def click_publish() -> bool:
                # Избегаем длинных блокирующих ожиданий: коротко опрашиваем селекторы и кликаем, если активны
                t_end = time.time() + 5.0
                while time.time() < t_end:
                    for sel in publish_btn_selectors:
                        try:
                            btn = page.query_selector(sel)
                            if btn:
                                try:
                                    page.evaluate("el => el.scrollIntoView({block: 'center'})", btn)
                                except Exception:
                                    pass
                                # Иногда кнопка в custom-компоненте: попробуем и click, и press Enter
                                if btn.is_enabled():
                                    try:
                                        btn.click()
                                    except Exception:
                                        try:
                                            btn.focus()
                                            page.keyboard.press("Enter")
                                        except Exception:
                                            pass
                                    return True
                        except Exception:
                            continue
                    time.sleep(0.25)
                return False

            published = False
            for attempt in range(1, 4):
                print(f"[info] Попытка публикации #{attempt}")
                clicked = click_publish()
                if not clicked:
                    print("[warn] Кнопка публикации не обнаружена/не активна. Возможно, загрузка ещё не завершена.")
                    # Дадим ещё времени обработке
                    time.sleep(3)
                    continue
                # После клика могут всплывать модалки/предупреждения — попробуем их закрыть/подтвердить
                handled_any = False
                t0 = time.time()
                while time.time() - t0 < 12:
                    acted = _close_blocking_modals(page)
                    if acted:
                        handled_any = True
                        # Возможно, требуется повторный клик "Опубликовать" после подтверждения
                        time.sleep(0.8)
                    else:
                        # Если ничего не нашли — подождём немного (ожидание серверной обработки)
                        time.sleep(0.8)
                # Если были модалки — попробуем кликнуть Опубликовать ещё раз
                if handled_any:
                    time.sleep(1.0)
                    _ = click_publish()
                # Эвристика успеха: кнопка пропала/стала disabled/появился тост/навигация
                try:
                    page.wait_for_selector("[data-e2e='post_btn']", timeout=3000, state='detached')
                    print("[ok] Похоже, публикация ушла (кнопка исчезла)")
                    published = True
                    break
                except Exception:
                    pass
                try:
                    btn = page.query_selector("[data-e2e='post_btn']")
                    if btn and not btn.is_enabled():
                        print("[ok] Похоже, публикация ушла (кнопка стала неактивной)")
                        published = True
                        break
                except Exception:
                    pass
                # Небольшая пауза перед следующей попыткой
                time.sleep(2)

            if not published:
                print("[warn] Не удалось убедиться в публикации автоматически. Проверьте UI: если всплыла модалка — закройте/подтвердите и нажмите Опубликовать ещё раз.")
                # Не считаем фатальной ошибкой, продолжаем со следующим файлом
                try:
                    page.goto(UPLOAD_URL, timeout=60_000)
                except Exception:
                    pass
                time.sleep(2)
                return True

            # Подождём немного, чтобы TikTok завершил серверную обработку
            time.sleep(3)
            print("[ok] Команда публикации отправлена (проверьте в UI статус загрузки/модерации)")
            # Вернёмся на страницу загрузки для следующего файла
            try:
                page.goto(UPLOAD_URL, timeout=60_000)
            except Exception:
                pass
            time.sleep(1.5)
        else:
            print("[test] Режим test: публикация не нажималась. Проверьте, что всё корректно.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Upload shorts to TikTok via Web UI (Playwright)")
    parser.add_argument("--dir", default="shorts", help="Directory with videos to upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process (0 = all)")
    parser.add_argument("--mode", choices=["dry-run", "test", "publish"], default="test", help="Mode: no click, or click Publish")
    parser.add_argument("--title-template", default=None, help="Template for title, supports {basename}, {RU_TITLE}, {YEAR}")
    parser.add_argument("--site-url", default=os.getenv("SITE_URL", "http://www.kino.lordfilmshd-2026.ru"), help="Site root; final link will be {site}/{category}/{id}")
    parser.add_argument("--ndjson", default=os.getenv("MOVIES_NDJSON", "movies-data.ndjson"), help="Path to movies-data.ndjson to enrich title/description")
    parser.add_argument("--user-data-dir", default=os.getenv("TIKTOK_USER_DATA_DIR", "tiktok_user_data"), help="Playwright persistent user data dir (stores login session)")
    parser.add_argument("--headless", action="store_true", help="Run headless (not recommended for login)")
    parser.add_argument("--slow-mo", type=float, default=float(os.getenv("TIKTOK_SLOW_MO", "0")), help="Slow down actions in ms (e.g., 50)")
    # Яндекс-Браузер режим
    parser.add_argument("--use-yandex", action="store_true", help="Использовать Яндекс.Браузер через DevTools (запуск и подключение)")
    parser.add_argument("--yandex-path", default=os.getenv("YANDEX_BROWSER_PATH"), help="Путь к Yandex Browser (browser.exe)")
    parser.add_argument("--yandex-user-data-dir", default=os.getenv("YANDEX_USER_DATA_DIR"), help="Папка профиля для Yandex Browser")
    parser.add_argument("--cdp-port", type=int, default=int(os.getenv("YANDEX_CDP_PORT", "9222")), help="Порт DevTools для подключения")
    parser.add_argument("--attach-running", action="store_true", help="Подключаться к уже запущенному Yandex (ожидает, что он запущен с --remote-debugging-port)")
    parser.add_argument("--restart-yandex", action="store_true", help="Перед запуском перезапускать Yandex и поднимать его с нужными флагами и вашим профилем")
    parser.add_argument("--yandex-profile-dir", default=os.getenv("YANDEX_PROFILE_DIR", "Default"), help="Имя директории профиля (Default, Profile 1 и т.п.)")

    args = parser.parse_args()

    movies_map = load_movies_map(args.ndjson)
    files = list(iter_video_files(args.dir))
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"[info] No video files found in {args.dir}")
        return 0

    print(f"[info] Found {len(files)} files to process in {args.dir}")

    if args.mode == "dry-run":
        for idx, fp in enumerate(files, start=1):
            size = os.path.getsize(fp)
            basename = pathlib.Path(fp).stem
            movie = movies_map.get(basename)
            title, desc = build_title_and_description(basename, movie, args.site_url, args.title_template)
            caption = build_caption(title, desc)
            print(f"[{idx}/{len(files)}] {os.path.basename(fp)} ({human_size(size)}) -> title='{title}' caption_len={len(caption)} [DRY]")
        return 0

    with TikTokUploader(user_data_dir=args.user_data_dir, headless=args.headless, slow_mo=args.slow_mo,
                         use_yandex=args.use_yandex, yandex_path=args.yandex_path, yandex_user_data_dir=args.yandex_user_data_dir,
                         cdp_port=args.cdp_port, attach_running=args.attach_running) as bot:
        try:
            bot.ensure_logged_in()
        except Exception as e:
            print(f"[error] Не удалось открыть страницу загрузки/войти: {e}")
            return 2

        processed = 0
        for idx, fp in enumerate(files, start=1):
            size = os.path.getsize(fp)
            basename = pathlib.Path(fp).stem
            movie = movies_map.get(basename)
            title, desc = build_title_and_description(basename, movie, args.site_url, args.title_template)
            caption = build_caption(title, desc)
            print(f"[{idx}/{len(files)}] {os.path.basename(fp)} ({human_size(size)}) -> title='{title}' mode={args.mode}")

            ok = False
            try:
                ok = bot.upload_one(fp, caption, mode=args.mode)
            except Exception as e:
                print(f"[error] Ошибка при автоматизации загрузки {fp}: {e}")
                ok = False

            if ok:
                processed += 1
            # Дадим UI время «переварить» между роликами с небольшим рандомом
            if idx < len(files):
                time.sleep(random.uniform(2.5, 5.5))

        print(f"[done] Processed {processed} file(s)")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(130)
