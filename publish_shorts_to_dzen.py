#!/usr/bin/env python3
"""
Yandex Dzen Shorts Uploader (local UI automation via Playwright)

DISCLAIMER:
- Неофициальная автоматизация. Dzen может менять разметку/защиту — скрипт хрупкий.
- Рекомендуется использовать на своей машине, предварительно войдя в аккаунт и сохранив сессию в persistent-профиле.
- Возможны капчи/2FA/антибот. Скрипт не гарантирует стабильность и может перестать работать.

Идея:
- Используем Playwright с persistent storage (user data dir), чтобы один раз залогиниться и дальше переиспользовать сессию.
- Открываем страницу редактора публикаций с типом short_video (через URL профиля редактора).
- Нажимаем «Создать» → «Загрузить видео», загружаем файл.
- Вставляем описание (Quill editor) и теги (по одному, отделяя запятыми, чтобы UI превратил в чипсы).
- В режиме publish нажимаем кнопку «Опубликовать».

Установка:
- Python 3.9+
- pip install playwright python-dotenv
- python -m playwright install

Примеры:
- Просмотр (без клика «Опубликовать»):
  python publish_shorts_to_dzen.py --dir shorts --mode test --limit 1 \
    --editor-url "https://dzen.ru/profile/editor/id/6921e81127715c566bb5e840/publications?contentType=short_video&state=draft"

- Публикация:
  python publish_shorts_to_dzen.py --dir shorts --mode publish --limit 1

Замечания:
- Селекторы устойчивы по текстам и плейсхолдерам, но Dzen может их менять. В таком случае скорректируйте селекторы в коде.
"""
import argparse
import os
import time
import json
import pathlib
import random
from typing import Optional, Dict, Any, Tuple, List

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
except Exception:
    print("[error] Playwright is not installed. Run: pip install playwright && python -m playwright install")
    raise


RU_MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def infer_month_from_premiere(premiere: Optional[str]) -> Optional[str]:
    if not premiere:
        return None
    s = str(premiere).strip().lower()
    for m in RU_MONTHS_GEN:
        if m in s:
            return m
    parts = s.split()
    if len(parts) >= 2 and parts[1] in RU_MONTHS_GEN:
        return parts[1]
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


def build_description_and_tags(basename: str, movie: Optional[Dict[str, Any]], site_root: Optional[str],
                               default_tags: Optional[List[str]]) -> Tuple[str, List[str]]:
    # Описание: короткая шапка + ссылка + краткое описание
    ru_title = (movie or {}).get("title") or (movie or {}).get("ruTitle") or basename
    year = (movie or {}).get("year") or ""

    link_line = "ПОСМОТРЕТЬ ПОЛНОСТЬЮ МОЖНО ТУТ:\n"
    item_url = (site_root or "http://www.kino.lordfilmshd-2026.ru").rstrip("/")
    if movie and movie.get("category") and movie.get("id"):
        item_url = f"{(site_root or 'http://www.kino.lordfilmshd-2026.ru').rstrip('/')}/{movie.get('category').strip('/')}/{movie.get('id')}"
    link_block = f"{link_line}{item_url}\n\n"

    short_desc = (movie or {}).get("description") or ""
    short_desc = short_desc.replace("\r\n", "\n").replace("\r", "\n")
    if len(short_desc) > 400:
        short_desc = short_desc[:400].rstrip() + "..."

    about_block = "О фильме:\n" + short_desc + "\n\n"
    desc = f"{ru_title} ({year})\n\n" + link_block + about_block

    # Теги (UI Дзена: пишем тег, ставим запятую — он превращается в чипс)
    tags: List[str] = []
    if default_tags:
        tags.extend([t.strip() for t in default_tags if t and t.strip()])

    # Автогенерация из жанров/года
    if movie:
        year = str(movie.get("year") or "").strip()
        if year:
            tags.append(f"новинки {year}")
            tags.append(f"кино {year}")
        genres = movie.get("genres") or []
        if isinstance(genres, str):
            genres = [s.strip() for s in genres.split(',') if s.strip()]
        if isinstance(genres, list):
            for g in genres[:6]:
                g = str(g).lower().strip()
                if g:
                    tags.append(g)
        mon = infer_month_from_premiere(movie.get('premiere')) if movie else None
        if mon:
            tags.append(f"новинки {mon}")

    # Нормализуем, убираем дубликаты, без решеток
    norm = []
    seen = set()
    for t in tags:
        tt = t.replace('#', '').replace('  ', ' ').strip()
        if tt and tt.lower() not in seen:
            seen.add(tt.lower())
            norm.append(tt)
    return desc, norm[:15]  # ограничим разумно


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


DEFAULT_EDITOR_URL = "https://dzen.ru/profile/editor/id/6921e81127715c566bb5e840/publications?contentType=short_video&state=draft"


def _goto_editor_with_retry(page, editor_url: str, retries: int = 3, initial_delay: float = 0.6) -> bool:
    for attempt in range(1, retries + 1):
        try:
            page.goto(editor_url, timeout=120_000)
        except Exception:
            pass
        time.sleep(initial_delay)
        try:
            # кнопка "Создать" или меню публикации
            ok = page.query_selector("button:has-text('Создать')") or page.query_selector("[aria-label='Контекстное меню']")
            if ok:
                return True
        except Exception:
            pass
        try:
            page.reload()
        except Exception:
            pass
        time.sleep(0.8 + attempt * 0.7)
    return False


class DzenUploader:
    def __init__(self, *, user_data_dir: str, headless: bool = False, slow_mo: float = 0,
                 use_yandex: bool = True, yandex_path: Optional[str] = None, yandex_user_data_dir: Optional[str] = None,
                 cdp_port: int = 9222, attach_running: bool = False, start_url: Optional[str] = None):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.slow_mo = slow_mo
        self.use_yandex = use_yandex
        self.yandex_path = yandex_path
        self.yandex_user_data_dir = yandex_user_data_dir
        self.cdp_port = cdp_port
        self.attach_running = attach_running
        self.start_url = start_url
        self.play = None
        self.browser = None
        self.context = None
        self.page = None
        self._ext_browser_proc = None

    def __enter__(self):
        import subprocess, platform, urllib.request, psutil
        self.play = sync_playwright().start()
        if self.use_yandex:
            if getattr(self, 'attach_running', False):
                endpoint = f"http://localhost:{self.cdp_port}"
                print(f"[info] Подключаюсь к уже запущенному Yandex по {endpoint}...")
                self.browser = self.play.chromium.connect_over_cdp(endpoint)
                # ВАЖНО: не создаём новые контексты/окна и не дергаем /json/new,
                # используем существующий контекст (как в тикток-скрипте поведение)
                ctxs = getattr(self.browser, 'contexts', []) or []
                if not ctxs:
                    raise RuntimeError("Не найдено ни одного открытого окна Яндекс.Браузера. Откройте окно заранее и повторите (attach-running)")
                self.context = ctxs[0]
                # Создаём новую вкладку в текущем окне и переходим на editor_url
                self.page = self.context.new_page()
                try:
                    start = self.start_url or DEFAULT_EDITOR_URL
                    self.page.goto(start, timeout=120_000)
                except Exception:
                    pass
                return self
            # Автопоиск браузера и профиля
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
            if self.yandex_user_data_dir and not os.path.exists(self.yandex_user_data_dir):
                os.makedirs(self.yandex_user_data_dir, exist_ok=True)
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
            self._ext_browser_proc = subprocess.Popen(args)
            endpoint = f"http://localhost:{self.cdp_port}"
            for _ in range(120):
                try:
                    with urllib.request.urlopen(endpoint, timeout=0.5) as _r:
                        break
                except Exception:
                    time.sleep(0.5)
            self.browser = self.play.chromium.connect_over_cdp(endpoint)
            ctxs = self.browser.contexts
            self.context = ctxs[0] if ctxs else self.browser.new_context()
        else:
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
        try:
            if self._ext_browser_proc:
                self._ext_browser_proc.terminate()
        except Exception:
            pass

    def ensure_on_editor(self, editor_url: str):
        p = self.page
        if not _goto_editor_with_retry(p, editor_url, retries=4):
            raise RuntimeError("Не удалось открыть страницу редактора Дзена после нескольких попыток")
        # Закроем возможные баннеры cookie/подсказки
        try:
            for sel in ["button:has-text('Принять')", "button:has-text('ОК')", "button:has-text('Понятно')"]:
                btn = p.query_selector(sel)
                if btn:
                    btn.click()
                    time.sleep(0.2)
                    break
        except Exception:
            pass
        return True

    def upload_one(self, *, file_path: str, description: str, tags: List[str], mode: str = "test", editor_url: str = DEFAULT_EDITOR_URL) -> bool:
        page = self.page
        abs_path = os.path.abspath(file_path)
        # Открыть страницу редактора
        if not _goto_editor_with_retry(page, editor_url, retries=4):
            print("[warn] Не удалось открыть страницу редактора, пропускаю файл")
            return False
        time.sleep(0.5)

        # 1) Клик "Создать" → "Загрузить видео"
        created = False
        try:
            create_btn = page.query_selector("button:has-text('Создать')")
            if create_btn:
                try:
                    create_btn.click()
                except Exception:
                    try:
                        create_btn.dispatch_event("click")
                    except Exception:
                        pass
                time.sleep(0.4)
                # В меню найти "Загрузить видео"
                up_item = None
                for sel in [
                    "label:has-text('Загрузить видео')",
                    "[aria-label='Загрузить видео']",
                    "div:has-text('Загрузить видео')",
                ]:
                    up_item = page.query_selector(sel)
                    if up_item:
                        break
                if up_item:
                    try:
                        up_item.click()
                    except Exception:
                        try:
                            up_item.dispatch_event("click")
                        except Exception:
                            pass
                    created = True
                else:
                    print("[warn] Не нашёл пункт меню 'Загрузить видео'. Попробую продолжить.")
            else:
                # возможно уже открыт попап загрузки
                created = True
        except Exception:
            pass

        # 2) Найти input[type=file] у диалога загрузки (надёжно)
        # Ждём появления экрана загрузки
        try:
            page.wait_for_selector(".video-editor--video-upload-dialog__uploadScreen-1T, .video-editor--video-upload-dialog__dragArea-1U", timeout=40_000)
        except Exception:
            pass
        uploaded = False
        last_err = None
        # 2.1 Попробуем нативный FileChooser на кнопке "Выбрать видео"
        try:
            btn = page.query_selector("button:has-text('Выбрать видео')")
            if btn:
                try:
                    with page.expect_file_chooser(timeout=2500) as fc_info:
                        try:
                            btn.click()
                        except Exception:
                            try:
                                btn.dispatch_event("click")
                            except Exception:
                                pass
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_path)
                    print("[info] Файл выбран через FileChooser API (Дзен)")
                    uploaded = True
                except Exception as e:
                    last_err = e
        except Exception:
            pass
        # 2.2 Если FileChooser не сработал — найдём сам input
        if not uploaded:
            # Типичные варианты: input[name='video-popup__file'] или с классом video-editor--video-upload-dialog__file-3F
            input_selectors = [
                "input[name='video-popup__file']",
                "input.video-editor--video-upload-dialog__file-3F",
                "input[type='file'][accept*='video']",
                "xpath=//input[@type='file' and (contains(@accept,'video') or @name='video-popup__file')]",
            ]
            inputs = []
            for sel in input_selectors:
                try:
                    found = page.query_selector_all(sel)
                    if found:
                        inputs.extend(found)
                except Exception:
                    continue
            # Попробуем найти input внутри активных диалогов
            if not inputs:
                try:
                    dialogs = page.query_selector_all("[role='dialog'], .Popup2, .video-editor--video-upload-dialog__uploadScreen-1T") or []
                    for d in dialogs:
                        try:
                            els = d.query_selector_all("input[type='file']") or []
                            if els:
                                inputs.extend(els)
                        except Exception:
                            continue
                except Exception:
                    pass
            # Проверим фреймы
            if not inputs:
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
            if not inputs:
                try:
                    cnt = page.evaluate("() => document.querySelectorAll('input[type=\\'file\\']').length")
                    print(f"[debug] На странице найдено input[type=file]: {cnt}")
                except Exception:
                    pass
                # Снимем скрин для диагностики
                try:
                    page.screenshot(path="tmp_rovodev_dzen_upload_debug.png", full_page=True)
                    print("[debug] Сохранён скриншот: tmp_rovodev_dzen_upload_debug.png")
                except Exception:
                    pass
                print("[error] Не найден input[type=file] для загрузки видео на Дзен")
                return False
            # Передадим файл в первый корректный инпут
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
            print(f"[error] Не удалось передать файл: {last_err}")
            # Снимем скрин
            try:
                page.screenshot(path="tmp_rovodev_dzen_upload_failed.png", full_page=True)
                print("[debug] Сохранён скриншот: tmp_rovodev_dzen_upload_failed.png")
            except Exception:
                pass
            return False

        # 3) Дождаться появления формы редактирования (поле описания Quill)
        desc_el = None
        for sel in [
            ".ql-editor[contenteditable='true']",
            "div.video-editor--quill-text-field__editorContainer- .ql-editor",
        ]:
            try:
                desc_el = page.wait_for_selector(sel, timeout=120_000)
                if desc_el:
                    break
            except Exception:
                continue
        if not desc_el:
            print("[warn] Не удалось найти поле описания. Продолжаю без текста.")
        else:
            desc_el.click()
            time.sleep(random.uniform(0.2, 0.5))
            # Вставим текст так, чтобы сохранились переносы строк в Quill
            # Способ 1: через execCommand('insertText') — Quill корректно разбивает \n в <p>
            inserted = False
            try:
                page.evaluate(
                    "(sel, text) => {\n"
                    "  const el = document.querySelector(sel);\n"
                    "  if (!el) return false;\n"
                    "  el.focus();\n"
                    "  const r = document.createRange();\n"
                    "  r.selectNodeContents(el);\n"
                    "  const s = window.getSelection();\n"
                    "  s.removeAllRanges();\n"
                    "  s.addRange(r);\n"
                    "  try { document.execCommand('insertText', false, text); } catch(e) { return false; }\n"
                    "  return true;\n"
                    "}",
                    ".ql-editor",
                    description,
                )
                inserted = True
            except Exception:
                inserted = False
            # Способ 2 (fallback): установить innerHTML с параграфами
            if not inserted:
                try:
                    page.evaluate(
                        "(sel, text) => {\n"
                        "  const el = document.querySelector(sel);\n"
                        "  if (!el) return false;\n"
                        "  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}\n"
                        "  const lines = String(text).split(/\r?\n/);\n"
                        "  const html = lines.map(l => l ? ('<p>'+esc(l)+'</p>') : '<p><br></p>').join('');\n"
                        "  el.innerHTML = html;\n"
                        "  return true;\n"
                        "}",
                        ".ql-editor",
                        description,
                    )
                    inserted = True
                except Exception:
                    inserted = False
            # Способ 3 (fallback): печатать вручную с Shift+Enter
            if not inserted:
                try:
                    page.keyboard.press("Control+A")
                except Exception:
                    pass
                for i, chunk in enumerate(description.split("\n")):
                    if chunk:
                        page.keyboard.type(chunk, delay=random.uniform(0.3, 0.9))
                    # Для визуального переноса используем Shift+Enter, чтобы не схлопывалось
                    page.keyboard.press("Shift+Enter")
                    time.sleep(random.uniform(0.05, 0.2))
            print("[info] Описание заполнено с переносами строк")

        # 4) Ввод тегов: input[placeholder*='теги'] и разделяем запятыми
        tag_input = None
        try:
            tag_input = page.query_selector("input[placeholder*='теги'], input[placeholder*='тег']")
        except Exception:
            tag_input = None
        if not tag_input:
            # попробуем найти по классу-контейнеру и затем input внутри
            try:
                cont = page.query_selector("[class*='tag-input__container']") or page.query_selector("[class*='tag-input__tagInput']")
                if cont:
                    tag_input = cont.query_selector("input")
            except Exception:
                pass
        if tag_input and tags:
            tag_input.click()
            time.sleep(0.2)
            for t in tags:
                page.keyboard.type(t, delay=random.uniform(0.2, 0.55))
                page.keyboard.type(",")  # запятая превращает в тег-чипс
                time.sleep(random.uniform(0.1, 0.25))
            print(f"[info] Добавлено тегов: {len(tags)}")
        else:
            print("[warn] Поле тегов не найдено или список тегов пуст")

        # 5) Публикация
        if mode == "publish":
            time.sleep(random.uniform(0.6, 1.3))
            published = False
            for attempt in range(1, 4):
                print(f"[info] Попытка публикации #{attempt}")
                clicked = False
                for sel in [
                    "button[data-testid='publish-btn']",
                    "button:has-text('Опубликовать')",
                    "[type='submit']:has-text('Опубликовать')",
                ]:
                    try:
                        btn = page.query_selector(sel)
                    except Exception:
                        btn = None
                    if btn:
                        try:
                            page.evaluate("el => el.scrollIntoView({block: 'center'})", btn)
                        except Exception:
                            pass
                        try:
                            btn.click()
                            clicked = True
                            break
                        except Exception:
                            try:
                                btn.focus()
                                page.keyboard.press("Enter")
                                clicked = True
                                break
                            except Exception:
                                pass
                if not clicked:
                    time.sleep(2)
                    continue
                # Эвристика успеха: появилось сообщение об успешной обработке/кнопка стала disabled
                try:
                    page.wait_for_selector("button[data-testid='publish-btn']", timeout=4000, state='detached')
                    published = True
                    break
                except Exception:
                    pass
                try:
                    btn = page.query_selector("button[data-testid='publish-btn']")
                    if btn and not btn.is_enabled():
                        published = True
                        break
                except Exception:
                    pass
                time.sleep(2)
            if not published:
                print("[warn] Не удалось автоматически подтвердить публикацию. Проверьте UI вручную.")
                # Переходим обратно к списку публикаций
                try:
                    page.goto(editor_url, timeout=60_000)
                except Exception:
                    pass
                time.sleep(1.2)
                return True
            print("[ok] Команда публикации отправлена")
            try:
                page.goto(editor_url, timeout=60_000)
            except Exception:
                pass
            time.sleep(1.0)
        else:
            print("[test] Режим test: публикация не нажималась. Проверьте форму.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Upload shorts to Yandex Dzen via Web UI (Playwright)")
    parser.add_argument("--dir", default="shorts", help="Directory with videos to upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process (0 = all)")
    parser.add_argument("--mode", choices=["dry-run", "test", "publish"], default="test", help="Mode: no click, or click Publish")
    parser.add_argument("--site-url", default=os.getenv("SITE_URL", "http://www.kino.lordfilmshd-2026.ru"), help="Site root; final link will be {site}/{category}/{id}")
    parser.add_argument("--ndjson", default=os.getenv("MOVIES_NDJSON", "movies-data.ndjson"), help="Path to movies-data.ndjson to enrich description/tags")
    parser.add_argument("--default-tags", default=os.getenv("DZEN_DEFAULT_TAGS", "сериалы детективы драма, новинки октября, сериалы 2025, новинки 2025, премьеры 2025, ожидаемые сериалы, кино 2025"),
                        help="Comma-separated default tags (without #). Each will be typed followed by a comma")
    parser.add_argument("--editor-url", default=os.getenv("DZEN_EDITOR_URL", DEFAULT_EDITOR_URL), help="Editor publications URL for your channel (short_video drafts)")
    parser.add_argument("--user-data-dir", default=os.getenv("DZEN_USER_DATA_DIR", "dzen_user_data"), help="Playwright persistent user data dir (stores login session)")
    parser.add_argument("--headless", action="store_true", help="Run headless (not recommended for login)")
    parser.add_argument("--slow-mo", type=float, default=float(os.getenv("DZEN_SLOW_MO", "0")), help="Slow down actions in ms (e.g., 50)")
    # Яндекс-Браузер режим (как в тикток-скрипте)
    parser.add_argument("--use-yandex", action="store_true", default=True, help="Использовать Яндекс.Браузер через DevTools (запуск и подключение)")
    parser.add_argument("--yandex-path", default=os.getenv("YANDEX_BROWSER_PATH"), help="Путь к Yandex Browser (browser.exe)")
    parser.add_argument("--yandex-user-data-dir", default=os.getenv("YANDEX_USER_DATA_DIR"), help="Папка профиля для Yandex Browser")
    parser.add_argument("--cdp-port", type=int, default=int(os.getenv("YANDEX_CDP_PORT", "9222")), help="Порт DevTools для подключения")
    parser.add_argument("--attach-running", action="store_true", help="Подключаться к уже запущенному Yandex (ожидает, что он запущен с --remote-debugging-port)")

    args = parser.parse_args()

    movies_map = load_movies_map(args.ndjson)
    files = list(iter_video_files(args.dir))
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"[info] No video files found in {args.dir}")
        return 0

    print(f"[info] Found {len(files)} files to process in {args.dir}")

    # разберём теги по запятым
    default_tags = [t.strip() for t in (args.default_tags or '').split(',') if t.strip()]

    if args.mode == "dry-run":
        for idx, fp in enumerate(files, start=1):
            size = os.path.getsize(fp)
            basename = pathlib.Path(fp).stem
            movie = movies_map.get(basename)
            desc, tags = build_description_and_tags(basename, movie, args.site_url, default_tags)
            print(f"[{idx}/{len(files)}] {os.path.basename(fp)} ({human_size(size)}) -> tags={tags} [DRY]")
        return 0

    with DzenUploader(user_data_dir=args.user_data_dir, headless=args.headless, slow_mo=args.slow_mo,
                       use_yandex=args.use_yandex, yandex_path=args.yandex_path, yandex_user_data_dir=args.yandex_user_data_dir,
                       cdp_port=args.cdp_port, attach_running=args.attach_running, start_url=args.editor_url) as bot:
        try:
            bot.ensure_on_editor(args.editor_url)
        except Exception as e:
            print(f"[error] Не удалось открыть страницу редактора/войти: {e}")
            return 2

        processed = 0
        for idx, fp in enumerate(files, start=1):
            size = os.path.getsize(fp)
            basename = pathlib.Path(fp).stem
            movie = movies_map.get(basename)
            desc, tags = build_description_and_tags(basename, movie, args.site_url, default_tags)

            print(f"[{idx}/{len(files)}] Uploading: {os.path.basename(fp)} ({human_size(size)}) -> tags={tags}")
            ok = False
            try:
                ok = bot.upload_one(file_path=fp, description=desc, tags=tags, mode=args.mode, editor_url=args.editor_url)
            except Exception as e:
                print(f"[error] Ошибка при загрузке {os.path.basename(fp)}: {e}")
                ok = False
            if ok:
                processed += 1
            # Небольшая пауза между элементами, чтобы не выглядеть как бот
            time.sleep(random.uniform(0.8, 1.6))

        print(f"[done] Processed {processed}/{len(files)} files")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
