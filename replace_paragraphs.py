import sys
import os
import shutil
import tempfile
from datetime import datetime

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "movies-data.json"
    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return

    # Читаем без преобразования переводов строк, чтобы сохранить исходный стиль EOL
    with open(path, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    # Подсчёт замен на основе исходного содержимого
    cnt_crlf = content.count("\r\n\r\n")
    cnt_lf = content.count("\n\n")
    cnt_escaped = content.count("\\n\\n")

    # Замены (разные случаи EOL + экранированные \n)
    updated = content.replace("\r\n\r\n", "\r\n<div></div>\r\n")
    updated = updated.replace("\n\n", "\n<div></div>\n")
    updated = updated.replace("\\n\\n", "\\n<div></div>\\n")

    if updated == content:
        print("Изменений нет — нечего записывать.")
        return

    # Бэкап
    backup_name = f"{path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copyfile(path, backup_name)

    # Атомарная запись
    dir_name = os.path.dirname(os.path.abspath(path)) or "."
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=dir_name, delete=False) as tmp:
        tmp.write(updated)
        tmp_path = tmp.name

    os.replace(tmp_path, path)

    total = cnt_crlf + cnt_lf + cnt_escaped
    print(f"Готово. Заменено блоков: {total} "
          f"(CRLF: {cnt_crlf}, LF: {cnt_lf}, escaped \\n: {cnt_escaped}). "
          f"Бэкап: {backup_name}")

if __name__ == "__main__":
    main()