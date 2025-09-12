# get_movie_by_kp_id_script.py
import re
import sys
import json
import asyncio
from typing import Optional, Tuple, Dict, Any
from ddgs import DDGS

ddgs_client = DDGS(timeout=6)

DEBUG = True
def dprint(*args):
    if DEBUG:
        print(*args)

def _norm(s: str) -> str:
    s = (s or '').lower()
    s = s.replace('ё', 'е')
    s = re.sub(r'["“”«»\'`]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_premiere_date(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    s = date_str.strip()
    months_gen = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',
    }
    month_name_to_num = {
        'января':1, 'январь':1, 'янв':1,
        'февраля':2, 'февраль':2, 'фев':2,
        'марта':3, 'март':3, 'мар':3,
        'апреля':4, 'апрель':4, 'апр':4,
        'мая':5, 'май':5,
        'июня':6, 'июнь':6, 'июн':6,
        'июля':7, 'июль':7, 'июл':7,
        'августа':8, 'август':8, 'авг':8,
        'сентября':9, 'сентябрь':9, 'сен':9, 'сент':9,
        'октября':10, 'октябрь':10, 'окт':10,
        'ноября':11, 'ноябрь':11, 'ноя':11, 'нояб':11,
        'декабря':12, 'декабрь':12, 'дек':12,
    }
    low = s.lower()

    m = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', low)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f'{d} {months_gen.get(mo, str(mo))} {y}'

    m = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', low)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f'{d} {months_gen.get(mo, str(mo))} {y}'

    m = re.search(r'(\d{1,2})\s+([А-Яа-яЁё]+)\s+(\d{4})', low)
    if m:
        d, mon_name, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        mo = month_name_to_num.get(mon_name)
        if mo and 1 <= d <= 31:
            return f'{d} {months_gen[mo]} {y}'
        return f'{d} {mon_name} {y}'

    return s

def _extract_title_year_from_title(ddg_title: str) -> Tuple[Optional[str], Optional[int]]:
    t = ddg_title.split('—', 1)[0].split('–', 1)[0].strip()
    m = re.match(r'^(?:Сериал\s+)?(.+?)\s*\((\d{4})\)$', t)
    if m:
        title = m.group(1).strip()
        year = int(m.group(2))
        return title, year
    m2 = re.search(r'\((19|20)\d{2}\)', t)
    if m2:
        year = int(m2.group(0).strip('()'))
        title = re.sub(r'\s*\((19|20)\d{2}\)\s*$', '', t).strip()
        return title or None, year
        return None, None

def _extract_hint(body: str) -> Tuple[Optional[str], Optional[str]]:
    if not body:
        return None, None
    b = body.replace('\u00a0', ' ')

    m = re.search(r'Режисс[её]р[:\s]+([^.;,\n]+)', b, flags=re.I)
    if m:
        director = m.group(1).strip()
        return 'director', director

    m = re.search(r'Премьер[аы][^:]*[:\s]+([^.]+)', b, flags=re.I)
    if m:
        prem_raw = m.group(1).strip()
        prem_norm = normalize_premiere_date(prem_raw) or prem_raw
        return 'premiere', prem_norm

    m = re.search(r'(В\s+ролях|Акт[её]ры)[:\s]+([^.;\n]+)', b, flags=re.I)
    if m:
        actors = m.group(2).strip()
        first = actors.split(',')[0].strip()
        if first:
            return 'actor', first

    return None, None

async def _ddg_search(query: str) -> list[dict]:
    return await asyncio.to_thread(
            ddgs_client.text, 
            query, 
            max_results=5,
            region='ru-ru',
            safesearch='off',
            backend='api',
        )

async def get_kp_basic_by_id(kp_id: str) -> Dict[str, Any]:
    kp_id = str(kp_id).strip()
    queries = [
        f'site:www.kinopoisk.ru/film/{kp_id} -site:hd.kinopoisk.ru',
        f'site:www.kinopoisk.ru/series/{kp_id} -site:hd.kinopoisk.ru',
    ]
    for q in queries:
        dprint(f'[DDG] query: {q}')
        try:
            results = await _ddg_search(q)
        except Exception as e:
            dprint(f'[DDG] search_failed: {e}')
            return {'id': kp_id, 'error': f'search_failed: {e}'}

        dprint(f'[DDG] results: {len(results or [])}')
        for idx, r in enumerate(results or [], start=1):
            url = r.get('href', '')
            title_field = r.get('title') or ''
            body = r.get('body') or ''
            body_snip = re.sub(r'\s+', ' ', body).strip()
            if len(body_snip) > 240:
                body_snip = body_snip[:240] + '…'

            dprint(f'  {idx}. title={title_field!r}')
            dprint(f'     url={url}')
            dprint(f'     body={body_snip!r}')

            m = re.search(r'kinopoisk\.ru/(film|series)/(\d+)', url)
            if not m:
                dprint('     skip: not film/series page')
                continue
            if m.group(2) != kp_id:
                dprint(f'     skip: id mismatch {m.group(2)} != {kp_id}')
                continue

            kind = m.group(1)
            title, year = _extract_title_year_from_title(title_field)
            if year is None:
                m_y = re.search(r'\b((?:19|20)\d{2})\b', body)
                if m_y:
                    year = int(m_y.group(1))
            hint_type, hint_value = _extract_hint(body)

            dprint(f'  [MATCH] type={kind} title={title!r} year={year} hint={hint_type}:{hint_value}')
            return {
                'id': kp_id,
                'type': kind,
                'url': url,
                'title': title,
                'year': year,
                'hintType': hint_type,
                'hintValue': hint_value,
                'source': 'ddg',
            }

    return {
        'id': kp_id,
        'error': 'not_found',
    }

async def main():
    ids = [a for a in sys.argv[1:] if a.strip()]
    if not ids:
        print('Usage: python get_movie_by_kp_id_script.py <kp_id1> <kp_id2> ...')
        print('Example: python get_movie_by_kp_id_script.py 6441870')
        return

    tasks = [get_kp_basic_by_id(k) for k in ids]
    results = await asyncio.gather(*tasks)

    for r in results:
        if 'error' in r:
            print(f"❌ {r['id']}: {r['error']}")
        else:
            t = r.get('title') or '(no title)'
            y = r.get('year') or '?'
            ht, hv = r.get('hintType'), r.get('hintValue')
            hint_str = f"{ht}: {hv}" if ht and hv else "no hint"
            print(f"✅ {r['id']} [{r['type']}]: {t} ({y}) | {hint_str} | {r['url']}")

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())