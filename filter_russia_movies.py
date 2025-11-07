import json
import argparse
import os
import sys

def is_russian_country(value) -> bool:
    # Принимает строку или массив; ищет 'россия' (регистронезависимо) как подстроку
    if value is None:
        return False
    if isinstance(value, list):
        values = value
    else:
        values = [value]
    for v in values:
        if isinstance(v, str) and 'россия' in v.strip().lower():
            return True
    return False

def iter_ndjson(fp):
    line_no = 0
    for line in fp:
        line_no += 1
        s = line.strip()
        if not s:
            continue
        try:
            yield json.loads(s)
        except json.JSONDecodeError as e:
            print(f"\n[WARN] Пропущена строка {line_no} из‑за ошибки JSON: {e}", file=sys.stderr)
            continue

def iter_json_array(fp, chunk_size=1024*1024):
    # Потоковый парсер JSON-массива на стандартном json.JSONDecoder
    decoder = json.JSONDecoder()
    buf = ''
    pos = 0
    in_array = False

    while True:
        chunk = fp.read(chunk_size)
        if not chunk:
            break
        buf += chunk

        while True:
            if not in_array:
                # Ищем первый символ '['
                i = pos
                n = len(buf)
                while i < n and buf[i] in ' \t\r\n':
                    i += 1
                if i >= n:
                    # Нужны ещё данные
                    break
                if buf[i] != '[':
                    raise ValueError("Ожидался JSON-массив (файл должен начинаться с '[').")
                in_array = True
                pos = i + 1

            # Пропускаем разделители/пробелы
            n = len(buf)
            while pos < n and buf[pos] in ' \t\r\n,':
                pos += 1
            if pos >= n:
                break

            if buf[pos] == ']':
                # Конец массива
                pos += 1
                # Можно игнорировать остаток (пробелы)
                return

            try:
                obj, new_pos = decoder.raw_decode(buf, pos)
            except json.JSONDecodeError:
                # Нужны ещё данные
                break
            yield obj
            pos = new_pos

        # Срезаем уже обработанную часть буфера, чтобы не раздувать память
        if pos > 0:
            buf = buf[pos:]
            pos = 0

    # Допускаем завершающие пробелы после ']' — если туда не дошли, значит формат нарушен.
    # Не падаем, просто выходим.

def detect_format(input_path):
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        head = f.read(4096)
    for ch in head:
        if ch in ' \t\r\n':
            continue
        # Если первый значимый символ '[' — это JSON-массив; иначе считаем NDJSON
        return 'array' if ch == '[' else 'ndjson'
    # Пустой файл — считаем массивом
    return 'array'

def process(input_path, output_path, progress_every=50000):
    fmt = detect_format(input_path)

    total = 0
    removed = 0
    kept = 0
    first_written = True

    with open(input_path, 'r', encoding='utf-8', newline='') as fin, \
         open(output_path, 'w', encoding='utf-8', newline='') as fout:

        # Пишем JSON-массив на выход потоково
        fout.write('[')

        iterator = iter_json_array(fin) if fmt == 'array' else iter_ndjson(fin)

        for item in iterator:
            total += 1
            if is_russian_country(item.get('country')):
                removed += 1
            else:
                if not first_written:
                    fout.write(',')
                json.dump(item, fout, ensure_ascii=False)
                first_written = False
                kept += 1

            if total % progress_every == 0:
                print(f"\rОбработано: {total:,} | Оставлено: {kept:,} | Удалено: {removed:,}", end='', flush=True)

        fout.write(']\n')

    print(f"\rОбработано: {total:,} | Оставлено: {kept:,} | Удалено: {removed:,}")
    print(f"Готово. Результат сохранён в: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Фильтрация записей с country='россия' из большого JSON/NDJSON.")
    parser.add_argument('--input', default='movies-data-withru.json', help="Путь к исходному файлу (JSON массив или NDJSON).")
    parser.add_argument('--output', default='movies-data.json', help="Путь к результирующему файлу (JSON массив).")
    parser.add_argument('--progress-every', type=int, default=50000, help="Как часто выводить прогресс (в записях).")
    args = parser.parse_args()
    process(args.input, args.output, args.progress_every)

if __name__ == "__main__":
    main()