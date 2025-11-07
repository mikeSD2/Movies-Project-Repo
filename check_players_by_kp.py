#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from typing import Optional

import requests

# Константы плееров
ALLOHA_URL_TMPL = "https://polygamist-as.stloadi.live/?kp={kp}&token=eb79c8a500d725f071c3bcc1e975bb"
ATOMICS_URL_TMPL = "https://api.atomics.ws/embed/kp/{kp}?theme=2&theme=2"
KODIK_API_SEARCH_URL = "https://kodikapi.com/search"

# HTTP-настройки
DEFAULT_UA = "Mozilla/5.0"
DEFAULT_REFERER = "http://localhost:3000"
TIMEOUT = 8

# Паттерны как на сервере:
RE_ERR_SPECIFIC = re.compile(
    r"(К сожалению,\s*(?:запрашиваемый контент не найден|видео недоступно)|"
    r"Контент не найден|"
    r"Приносим свои извинения за неудобства|"
    r"Видео запрещено к просмотру в данной стране|"
    r"Error\s*code:\s*[a-z0-9]+|"
    r"Видео не найдено)",
    re.I,
)
RE_PLAYER_MARKERS = re.compile(r"(allplay__video|allplay__player|rmp-vast|videojs|hls\.js)", re.I)
RE_TITLE_ERROR = re.compile(r"<title>\s*Ошибка!?<\/title>", re.I)
RE_404 = re.compile(r"404\s*Not\s*Found", re.I)


@dataclass
class ProbeResult:
    ok: bool
    status: int
    matched_error_text: bool
    has_player_markers: bool
    looks_bad: bool
    host: str
    sample: str
    error: Optional[str] = None


def http_get(url: str, referer: str) -> tuple[int, str, Optional[str]]:
    try:
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": DEFAULT_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": referer,
            },
            allow_redirects=True,
        )
        status = resp.status_code or 0
        body = resp.text if isinstance(resp.text, str) else ""
        return status, body, None
    except requests.RequestException as e:
        return 0, "", str(e)


def analyze_alloha(status: int, body: str) -> ProbeResult:
    host = "stloadi.live"
    matched_specific = bool(RE_ERR_SPECIFIC.search(body))
    has_markers = bool(RE_PLAYER_MARKERS.search(body))
    # Для Alloha «плохо» только если явный текст ошибки и НЕТ маркеров плеера
    looks_bad = matched_specific and not has_markers
    return ProbeResult(
        ok=not looks_bad,
        status=status,
        matched_error_text=matched_specific,
        has_player_markers=has_markers,
        looks_bad=looks_bad,
        host=host,
        sample=body[:800],
    )


def analyze_atomics(status: int, body: str) -> ProbeResult:
    host = "atomics.ws"
    matched_specific = bool(RE_ERR_SPECIFIC.search(body))
    has_markers = bool(RE_PLAYER_MARKERS.search(body))
    matched_title = bool(RE_TITLE_ERROR.search(body))
    matched_404 = bool(RE_404.search(body))

    # Для Atomics считаем «плохо» только при явном тексте ошибки (как на бэке)
    looks_bad = matched_specific
    # На всякий случай можно ужесточить:
    # looks_bad = (status >= 400) or matched_specific or matched_title or matched_404

    return ProbeResult(
        ok=not looks_bad,
        status=status,
        matched_error_text=matched_specific,
        has_player_markers=has_markers,
        looks_bad=looks_bad,
        host=host,
        sample=body[:800],
    )


def print_result(name: str, result: ProbeResult, debug: bool):
    status_line = f"[{name}] {'FOUND' if result.ok else 'NOT FOUND'} (status={result.status})"
    print(status_line)
    if debug:
        sample_clean = (result.sample or "").replace("\n", " ")
        details = (
            f"- host: {result.host}\n"
            f"- matched_error_text: {result.matched_error_text}\n"
            f"- has_player_markers: {result.has_player_markers}\n"
            f"- looks_bad: {result.looks_bad}\n"
            f"- sample: {sample_clean[:300]}\n"
            f"- error: {result.error or '-'}"
        )
        print(details)


def probe_sv(kp: str, base_url: str = "http://localhost:3002", publisher_id: str = "79") -> ProbeResult:
    try:
        r = requests.get(
            f"{base_url}/api/probe-sv",
            params={"kp": kp, "publisherId": publisher_id},
            timeout=12,
        )
        j = {}
        try:
            j = r.json()
        except Exception:
            j = {}
        ok = bool(j.get("ok"))
        probe = j.get("probe") or {}
        status = int(probe.get("status") or r.status_code or 0)
        matched = bool(probe.get("matched", False))
        sample = str(j)[:800]
        return ProbeResult(
            ok=ok,
            status=status,
            matched_error_text=matched,
            has_player_markers=False,
            looks_bad=not ok,
            host="cdnvideohub",
            sample=sample,
        )
    except Exception as e:
        return ProbeResult(
            ok=False,
            status=0,
            matched_error_text=False,
            has_player_markers=False,
            looks_bad=True,
            host="cdnvideohub",
            sample="",
            error=str(e),
        )


def probe_kodik(kp: str, base_url: str = "http://localhost:3000") -> ProbeResult:
    def as_result(j, r):
        ok = bool(j.get("ok"))
        status = int(j.get("status") or getattr(r, "status_code", 0) or 0)
        sample = str(j)[:800]
        return ProbeResult(
            ok=ok,
            status=status,
            matched_error_text=False,
            has_player_markers=False,
            looks_bad=not ok,
            host="kodik",
            sample=sample,
        )

    try:
        # 1) быстрый jsdom-вариант
        r1 = requests.get(f"{base_url}/api/probe-kodik", params={"kp": kp, "verbose": "1"}, timeout=12)
        try:
            j1 = r1.json()
        except Exception:
            j1 = {}
        if j1.get("ok"):
            return as_result(j1, r1)

        # 2) лёгкий браузерный фолбэк
        r2 = requests.get(f"{base_url}/api/probe-kodik-browser", params={"kp": kp, "verbose": "1"}, timeout=25)
        try:
            j2 = r2.json()
        except Exception:
            j2 = {}
        return as_result(j2, r2)
    except Exception as e:
        return ProbeResult(
            ok=False, status=0, matched_error_text=False, has_player_markers=False,
            looks_bad=True, host="kodik", sample="", error=str(e),
        )


def probe_kodik_api(kp: str, token: str) -> ProbeResult:
    """
    Проверка наличия тайтла в базе Kodik через официальный API по kinopoisk_id.
    Упрощённая логика: наличие результатов => ok=True.
    """
    try:
        r = requests.get(
            KODIK_API_SEARCH_URL,
            params={
                "token": token,
                "kinopoisk_id": kp,
                "limit": 1,  # достаточно понять, что хотя бы один нашёлся
            },
            timeout=12,
        )
        status = r.status_code or 0
        try:
            j = r.json()
        except Exception:
            j = {}

        results = j.get("results")
        if not isinstance(results, list):
            results = []

        total = j.get("total")
        try:
            total = int(total)
        except Exception:
            total = None

        found = (len(results) > 0) or (isinstance(total, int) and total > 0)

        return ProbeResult(
            ok=found,
            status=status,
            matched_error_text=False,
            has_player_markers=False,
            looks_bad=not found,
            host="kodikapi.com",
            sample=str(j)[:800],
        )
    except Exception as e:
        return ProbeResult(
            ok=False,
            status=0,
            matched_error_text=False,
            has_player_markers=False,
            looks_bad=True,
            host="kodikapi.com",
            sample="",
            error=str(e),
        )


def main():
    parser = argparse.ArgumentParser(
        description="Проверка наличия контента в плеерах Alloha, Atomics, SV и Kodik по Kinopoisk ID."
    )
    parser.add_argument("kinopoisk_id", help="Kinopoisk ID (число)")
    parser.add_argument("--referer", default=DEFAULT_REFERER, help="HTTP Referer (по умолчанию localhost)")
    parser.add_argument("--debug", action="store_true", help="Печатать детали проверки")
    parser.add_argument("--kodik-token", default=os.environ.get("KODIK_API_TOKEN", ""), help="Kodik API токен (или KODIK_API_TOKEN в окружении)")
    args = parser.parse_args()

    kp = str(args.kinopoisk_id).strip()
    if not kp.isdigit():
        print("kinopoisk_id должен быть числом.", file=sys.stderr)
        sys.exit(2)

    # Alloha
    alloha_url = ALLOHA_URL_TMPL.format(kp=kp)
    st, body, err = http_get(alloha_url, args.referer)
    if err:
        alloha_res = ProbeResult(
            ok=False, status=0, matched_error_text=False, has_player_markers=False,
            looks_bad=True, host="stloadi.live", sample="", error=err
        )
    else:
        alloha_res = analyze_alloha(st, body)
    print_result("Alloha", alloha_res, args.debug)

    # Atomics
    atomics_url = ATOMICS_URL_TMPL.format(kp=kp)
    st, body, err = http_get(atomics_url, args.referer)
    if err:
        atomics_res = ProbeResult(
            ok=False, status=0, matched_error_text=False, has_player_markers=False,
            looks_bad=True, host="atomics.ws", sample="", error=err
        )
    else:
        atomics_res = analyze_atomics(st, body)
    print_result("Atomics", atomics_res, args.debug)

    # SV (cdnvideohub)
    sv_res = probe_sv(kp, base_url="http://localhost:3002")
    print_result("SV", sv_res, args.debug)

    # Kodik — локальный сервер (если настроен)
    kodik_res = probe_kodik(kp, base_url="http://localhost:3002")
    print_result("KodikLocal", kodik_res, args.debug)

    # Kodik — официальный API (если передан токен)
    kodik_api_res = None
    if args.kodik_token:
        kodik_api_res = probe_kodik_api(kp, args.kodik_token)
        print_result("KodikAPI", kodik_api_res, args.debug)

    any_ok = alloha_res.ok or atomics_res.ok or sv_res.ok or kodik_res.ok or (kodik_api_res.ok if kodik_api_res else False)
    sys.exit(0 if any_ok else 1)


if __name__ == "__main__":
    main()