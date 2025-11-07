import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

DATA_PATH = Path("movies-data.json")
REMOVED_PATH = Path("removed-movies.json")


def _load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return json.loads(json.dumps(default))
    with path.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Не удалось прочитать {path}: {exc}") from exc


def _save_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def delete_movie(movie_id: str) -> None:
    db = _load_json(DATA_PATH, {"movies": []})
    movies: List[Dict[str, Any]] = db.get("movies", [])
    for idx, movie in enumerate(movies):
        if str(movie.get("id")) == movie_id:
            removed_movie = movies.pop(idx)
            _save_json(DATA_PATH, db)

            removed = _load_json(REMOVED_PATH, {"movies": []})
            removed.setdefault("movies", []).append(removed_movie)
            _save_json(REMOVED_PATH, removed)

            print(f"Фильм с id={movie_id} удалён и перенесён в {REMOVED_PATH.name}.")
            return

    print(f"Фильм с id={movie_id} не найден — изменений нет.")


def update_movie_id(old_id: str, new_id: str) -> None:
    if old_id == new_id:
        print("Старый и новый id совпадают — изменений нет.")
        return

    db = _load_json(DATA_PATH, {"movies": []})
    movies: List[Dict[str, Any]] = db.get("movies", [])

    if any(str(movie.get("id")) == new_id for movie in movies):
        print(f"Фильм с id={new_id} уже существует — выберите другой id.")
        return

    for movie in movies:
        if str(movie.get("id")) == old_id:
            movie["id"] = new_id
            _save_json(DATA_PATH, db)
            print(f"id фильма изменён: {old_id} → {new_id}.")
            return

    print(f"Фильм с id={old_id} не найден — изменений нет.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Утилита для работы с movies-data.json"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    delete_parser = subparsers.add_parser("delete", help="Удалить фильм по id")
    delete_parser.add_argument("movie_id", help="id фильма, который нужно удалить")

    update_parser = subparsers.add_parser("update-id", help="Изменить id фильма")
    update_parser.add_argument("old_id", help="Текущий id фильма")
    update_parser.add_argument("new_id", help="Новый id фильма")

    args = parser.parse_args()

    if args.command == "delete":
        delete_movie(args.movie_id)
    elif args.command == "update-id":
        update_movie_id(args.old_id, args.new_id)


if __name__ == "__main__":
    main()