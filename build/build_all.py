# -*- coding: utf-8 -*-
"""data/*.json 을 읽어 images/ 아래 카드 PNG 를 전부 다시 만든다.
사용: python build/build_all.py
"""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_card import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

CATEGORIES = [
    "01-composition-logic",
    "02-visual-principles",
    "03-editorial-advertising",
    "04-type-grid",
    "06-film-frame",
    "07-korean-tradition",
    "08-presentation",
]

def load_specs():
    """diagrams-*.json 을 전부 합친다 (id → spec)"""
    spec = {}
    for p in sorted(glob.glob(os.path.join(DATA, "diagrams-*.json"))):
        entries = json.load(open(p, encoding="utf-8"))
        duplicates = spec.keys() & entries.keys()
        if duplicates:
            raise SystemExit(f"중복 도해 번호: {', '.join(sorted(duplicates))}")
        spec.update(entries)
    return spec

def main():
    spec = load_specs()
    total, missing = 0, []
    for slug in CATEGORIES:
        path = os.path.join(DATA, slug + ".json")
        cat = json.load(open(path, encoding="utf-8"))
        n = 0
        for sub in cat["subcategories"]:
            for it in sub["items"]:
                s = spec.get(str(it["id"]))
                if not s:
                    missing.append((slug, it["id"], it["ko"])); continue
                out = os.path.join(ROOT, "images", cat["slug"],
                                   f"{it['id']:03d}-{it['ko']}.png")
                render(it, cat["category"], sub["name"], s, out)
                n += 1
        print(f"  {n:3d}  {cat['category']}")
        total += n
    print(f"\n총 {total}장 생성")
    if missing:
        print("도해 스펙 없음:")
        for slug, i, ko in missing:
            print(f"  {slug} {i:03d} {ko}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
