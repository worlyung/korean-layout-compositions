# -*- coding: utf-8 -*-
"""썸네일 생성 + docs/ 분류별 마크다운 갤러리 + catalog.csv 생성."""
import json, os, sys, csv, glob
from urllib.parse import quote
from PIL import Image
from build_all import CATEGORIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
THUMB_W = 340

def rel(p):
    """저장소 루트 기준 상대경로를 URL 인코딩 (한글 파일명 대응)"""
    return "/".join(quote(s) for s in p.split("/"))

def make_thumb(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert("RGB")
    im.thumbnail((THUMB_W, THUMB_W * 2), Image.LANCZOS)
    im.save(dst, quality=86)

def main():
    cats, rows = [], []
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

    for slug in CATEGORIES:
        path = os.path.join(DATA, slug + ".json")
        cat = json.load(open(path, encoding="utf-8"))
        n_items = sum(len(s["items"]) for s in cat["subcategories"])
        cats.append((cat, n_items))

        lines = [f"# {cat['category']} · {cat['category_en']}", "",
                 f"> {cat['note']}", "",
                 f"**{n_items}종** · [← 전체 목차](README.md)", ""]

        for sub in cat["subcategories"]:
            if sub["slug"] == "hangul-typesetting":
                lines += ['<a id="hangul-typesetting"></a>', ""]
            lines += [f"## {sub['name']} · {sub['name_en']}", ""]
            if sub.get("note"): lines += [f"> {sub['note']}", ""]
            items = sub["items"]
            # 4열 표
            for i in range(0, len(items), 4):
                chunk = items[i:i+4]
                cells, caps = [], []
                for it in chunk:
                    png = f"images/{cat['slug']}/{it['id']:03d}-{it['ko']}.png"
                    jpg = f"thumbnails/{cat['slug']}/{it['id']:03d}-{it['ko']}.jpg"
                    src, dst = os.path.join(ROOT, png), os.path.join(ROOT, jpg)
                    make_thumb(src, dst)
                    rows.append({
                        "id": it["id"], "name_ko": it["ko"], "name_en": it["en"],
                        "category": cat["category"], "category_slug": cat["slug"],
                        "subcategory": sub["name"], "image": png, "thumbnail": jpg,
                        "desc": it["desc"],
                    })
                    cells.append(f'<a href="../{rel(png)}"><img src="../{rel(jpg)}" width="200" alt="{it["ko"]}"></a>')
                    caps.append(f'**{it["id"]:03d}**<br>{it["ko"]}')
                while len(cells) < 4: cells.append("&nbsp;"); caps.append("&nbsp;")
                lines += ["| " + " | ".join(cells) + " |",
                          "| :---: | :---: | :---: | :---: |",
                          "| " + " | ".join(caps) + " |", ""]
        open(os.path.join(ROOT, "docs", slug + ".md"), "w", encoding="utf-8").write("\n".join(lines))
        print(f"  docs/{slug}.md  ({n_items})")

    # 전체 목차
    total = sum(n for _, n in cats)
    idx = ["# 목차", "",
           f"**{total}종**의 구성 원리. 분류를 눌러 들어간다.", ""]
    for cat, n in cats:
        idx.append(f"### [{cat['category']} · {n}종]({cat['slug']}.md)")
        idx += [f"{cat['note']}", ""]
        subs = " · ".join(f"{s['name']}({len(s['items'])})" for s in cat["subcategories"])
        idx += [f"<sub>{subs}</sub>", ""]
    idx += ["---", "", "[축제 포스터와 공공 제안서 예시](examples.md) · [← 저장소 홈](../README.md)"]
    open(os.path.join(ROOT, "docs", "README.md"), "w", encoding="utf-8").write("\n".join(idx))

    # catalog.csv
    rows.sort(key=lambda r: r["id"])
    with open(os.path.join(ROOT, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(ROOT, "catalog.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"\n docs/README.md · catalog.csv ({len(rows)}행) · 썸네일 {len(rows)}장")

if __name__ == "__main__":
    main()
