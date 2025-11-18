#!/usr/bin/env python3
"""
Replace image paths in a target JSON using values from a reference JSON matched by id.

Usage:
  python replace_images_by_id.py \
      --reference movies-data-sorted-rightImages.json \
      --target movies-data-sorted-oldid.json \
      --output movies-data-sorted-merged.json

Options:
  --id-field ID_FIELD       Field name for the id key (default: id)
  --image-field IMAGE_FIELD Field name for the image key (default: image)
  --in-place                Overwrite the target file instead of writing to --output

Both JSON files are expected to be lists of objects, each containing the id and image fields.
The script will copy image from reference to target where ids match. If reference has empty or missing image, target is left unchanged.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple, Optional


def load_json_and_get_list(path: str, list_key: str | None) -> tuple[Any, List[Dict[str, Any]], str | None]:
    """
    Load JSON file and return a tuple of (root, list_reference, wrapper_key).
    - If JSON is a list, wrapper_key is None and list_reference is the root list.
    - If JSON is an object, attempts to use list_key (if provided) or auto-detect
      the first list value. Returns that list reference and the key name.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, list):
        return data, data, None

    if isinstance(data, dict):
        # Try provided key first
        if list_key and list_key in data and isinstance(data[list_key], list):
            return data, data[list_key], list_key
        # Auto-detect the first list-valued key
        for k, v in data.items():
            if isinstance(v, list):
                return data, v, k
        print(f"Error: {path} is an object but does not contain a list under key '{list_key or 'movies'}' or any list value to auto-detect.", file=sys.stderr)
        sys.exit(1)

    print(f"Error: {path} must contain either a JSON array or an object with a list field (e.g., 'movies').", file=sys.stderr)
    sys.exit(1)


def build_image_map(reference: List[Dict[str, Any]], id_field: str, image_field: str) -> Dict[Any, str]:
    mapping: Dict[Any, str] = {}
    for i, item in enumerate(reference):
        if not isinstance(item, dict):
            continue
        _id = item.get(id_field)
        img = item.get(image_field)
        if _id is None:
            continue
        if isinstance(img, str) and img.strip():
            mapping[_id] = img.strip()
    return mapping


def replace_images(target: List[Dict[str, Any]], image_map: Dict[Any, str], id_field: str, image_field: str) -> Tuple[int, int]:
    updated = 0
    candidates = 0
    for obj in target:
        if not isinstance(obj, dict):
            continue
        _id = obj.get(id_field)
        if _id in image_map:
            candidates += 1
            ref_img = image_map[_id]
            cur_img = obj.get(image_field)
            if cur_img != ref_img:
                obj[image_field] = ref_img
                updated += 1
    return candidates, updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Replace image paths in target JSON by id using reference JSON.")
    ap.add_argument('--reference', '-r', required=True, help='Path to reference JSON (provides correct images)')
    ap.add_argument('--target', '-t', required=True, help='Path to target JSON (will be updated)')
    ap.add_argument('--output', '-o', help='Path to write updated JSON (omit if using --in-place)')
    ap.add_argument('--id-field', default='id', help='Id field name (default: id)')
    ap.add_argument('--image-field', default='image', help='Image field name (default: image)')
    ap.add_argument('--list-key-ref', default=None, help="Wrapper key for list in reference JSON if it's an object (e.g., 'movies'). If omitted, auto-detect.")
    ap.add_argument('--list-key-target', default=None, help="Wrapper key for list in target JSON if it's an object (e.g., 'movies'). If omitted, auto-detect.")
    ap.add_argument('--in-place', action='store_true', help='Overwrite target file')

    args = ap.parse_args()

    if not args.in_place and not args.output:
        print('Error: either --in-place or --output must be provided', file=sys.stderr)
        sys.exit(2)

    # Load reference and target, obtaining both the root JSON and the list we will operate on
    ref_root, ref_list, _ = load_json_and_get_list(args.reference, args.list_key_ref)
    tgt_root, tgt_list, _ = load_json_and_get_list(args.target, args.list_key_target)

    image_map = build_image_map(ref_list, args.id_field, args.image_field)
    candidates, updated = replace_images(tgt_list, image_map, args.id_field, args.image_field)

    out_path = args.target if args.in_place else args.output

    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(tgt_root, f, ensure_ascii=False, separators=(',', ':'), indent=2)
    except Exception as e:
        print(f"Error writing output to {out_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Candidates matched by id: {candidates}")
    print(f"Images updated: {updated}")
    print(f"Written: {out_path}")


if __name__ == '__main__':
    main()
