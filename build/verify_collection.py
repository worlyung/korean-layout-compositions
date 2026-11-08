"""카드 원본, 배포 목록, 이미지와 문서의 일관성을 검사한다."""
import csv
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image

from build_all import CATEGORIES, ROOT, load_specs
from render_card import W, H


def verify():
    root = Path(ROOT)
    expected = {}
    for slug in CATEGORIES:
        category = json.loads((root / "data" / f"{slug}.json").read_text(encoding="utf-8"))
        for sub in category["subcategories"]:
            for item in sub["items"]:
                number = item["id"]
                if number in expected:
                    raise ValueError(f"중복 카드 번호: {number}")
                stem = f"{slug}/{number:03d}-{item['ko']}"
                expected[number] = {
                    "id": number,
                    "name_ko": item["ko"],
                    "name_en": item["en"],
                    "category": category["category"],
                    "category_slug": slug,
                    "subcategory": sub["name"],
                    "image": f"images/{stem}.png",
                    "thumbnail": f"thumbnails/{stem}.jpg",
                    "desc": item["desc"],
                }
    specs = load_specs()
    if set(specs) != {str(number) for number in expected} or not all(specs.values()):
        raise ValueError("카드 번호와 비어 있지 않은 도해 번호가 일치해야 합니다.")

    rows = [expected[number] for number in sorted(expected)]
    if json.loads((root / "catalog.json").read_text(encoding="utf-8")) != rows:
        raise ValueError("catalog.json이 카드 데이터와 다릅니다.")
    with (root / "catalog.csv").open(encoding="utf-8-sig", newline="") as source:
        if list(csv.DictReader(source)) != [
            {key: str(value) for key, value in row.items()} for row in rows
        ]:
            raise ValueError("catalog.csv가 카드 데이터와 다릅니다.")

    for row in rows:
        for field, format_name in (("image", "PNG"), ("thumbnail", "JPEG")):
            with Image.open(root / row[field]) as image:
                if image.format != format_name or (field == "image" and image.size != (W, H)):
                    raise ValueError(f"이미지 형식 또는 크기 오류: {row[field]}")
                image.verify()

    for page in [root / "README.md", *(root / "docs").glob("*.md")]:
        source = page.read_text(encoding="utf-8")
        for html_link, markdown_link in re.findall(r'(?:href|src)="([^"]+)"|\]\(([^)]+)\)', source):
            link = urlsplit(html_link or markdown_link)
            if link.scheme or link.netloc:
                continue
            target = page.parent / unquote(link.path) if link.path else page
            if not target.is_file():
                raise ValueError(f"{page.name}: 파일 링크 오류 ({link.path})")
            if link.fragment and target.suffix == ".md":
                if f'id="{unquote(link.fragment)}"' not in target.read_text(encoding="utf-8"):
                    raise ValueError(f"{page.name}: 문서 앵커 오류 ({link.fragment})")
    print(f"카드 {len(rows)}종, CSV·JSON, 이미지·썸네일, 문서 링크 검증 통과")


if __name__ == "__main__":
    try:
        verify()
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from None
