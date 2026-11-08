# -*- coding: utf-8 -*-
"""한국형 레이아웃 도감 — 카드 1장을 PNG로 그린다.
의존: Pillow 만. 다이어그램은 JSON 스펙을 해석해 그린다.
"""
import json, math, os, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

W, H = 1086, 1448
BG      = (250, 248, 244)   # 한지 바탕
INK     = (32, 30, 28)      # 먹
SUB     = (122, 116, 108)   # 보조 회색
LINE    = (206, 199, 189)   # 안내선
ACCENT  = (176, 58, 46)     # 주칠 붉은색
FILL    = (214, 206, 194)   # 도형 채움

@lru_cache(maxsize=None)
def font(sz, bold=False):
    regular = os.environ.get("LAYOUT_FONT")
    bold_path = os.environ.get("LAYOUT_FONT_BOLD")
    custom = (bold_path or regular) if bold else regular
    windows = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    candidates = [(custom, 0)] if custom else [
        (os.path.join(windows, "malgunbd.ttf" if bold else "malgun.ttf"), 0),
        (os.path.join(windows, "NanumGothicExtraBold.ttf" if bold else "NanumGothic.ttf"), 0),
        ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 6 if bold else 0),
        ("NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc", 1),
    ]
    for path, index in candidates:
        try:
            face = ImageFont.truetype(path, sz, index=index)
        except OSError:
            continue
        if bytes(face.getmask("한")) != bytes(face.getmask("글")):
            return face
    raise SystemExit("한글 글꼴을 불러올 수 없습니다. LAYOUT_FONT와 LAYOUT_FONT_BOLD를 확인하세요.")

# ── 다이어그램 영역 (정사각) ─────────────────────────────
DX, DY, DW = 153, 356, 780         # left, top, size

def P(x, y):
    """0~1 정규좌표 → 다이어그램 픽셀좌표"""
    return (DX + x * DW, DY + y * DW)

def draw_diagram(d, spec):
    """spec: [{"t":"grid","x":3,"y":3}, ...] 순서대로 그린다"""
    for s in spec:
        t = s.get("t")
        col = {"ink": INK, "sub": SUB, "line": LINE, "accent": ACCENT,
               "fill": FILL, "none": None}.get(s.get("c", "ink"), INK)
        w = s.get("w", 3)

        if t == "grid":
            nx, ny = s.get("x", 3), s.get("y", 3)
            for i in range(1, nx):
                d.line([P(i/nx, 0), P(i/nx, 1)], fill=LINE, width=2)
            for j in range(1, ny):
                d.line([P(0, j/ny), P(1, j/ny)], fill=LINE, width=2)

        elif t == "frame":
            d.rectangle([P(0, 0), P(1, 1)], outline=s.get("oc", LINE), width=s.get("w", 3))

        elif t == "vline":
            d.line([P(s["x"], s.get("y0", 0)), P(s["x"], s.get("y1", 1))], fill=col, width=w)
        elif t == "hline":
            d.line([P(s.get("x0", 0), s["y"]), P(s.get("x1", 1), s["y"])], fill=col, width=w)
        elif t == "line":
            d.line([P(s["x1"], s["y1"]), P(s["x2"], s["y2"])], fill=col, width=w)

        elif t == "rect":
            box = [P(s["x"], s["y"]), P(s["x"] + s["w_"], s["y"] + s["h"])]
            if s.get("fill_", True): d.rectangle(box, fill=col)
            else: d.rectangle(box, outline=col, width=w)

        elif t == "circle":
            cx, cy = P(s["x"], s["y"]); r = s["r"] * DW
            box = [cx - r, cy - r, cx + r, cy + r]
            if s.get("fill_", True): d.ellipse(box, fill=col)
            else: d.ellipse(box, outline=col, width=w)

        elif t == "ellipse":
            cx, cy = P(s["x"], s["y"]); rx, ry = s["rx"] * DW, s["ry"] * DW
            box = [cx - rx, cy - ry, cx + rx, cy + ry]
            if s.get("fill_", True): d.ellipse(box, fill=col)
            else: d.ellipse(box, outline=col, width=w)

        elif t == "poly":
            pts = [P(*p) for p in s["pts"]]
            if s.get("fill_", True): d.polygon(pts, fill=col)
            else: d.polygon(pts, outline=col)

        elif t == "arc":
            cx, cy = P(s["x"], s["y"]); r = s["r"] * DW
            d.arc([cx - r, cy - r, cx + r, cy + r], s["a0"], s["a1"], fill=col, width=w)

        elif t == "spiral":
            pts = []
            turns, steps = s.get("turns", 2.5), 400
            for i in range(steps + 1):
                th = i / steps * turns * 2 * math.pi
                rr = s.get("r", 0.42) * (1 - i / steps)
                pts.append(P(0.5 + rr * math.cos(th), 0.5 + rr * math.sin(th)))
            d.line(pts, fill=col, width=w, joint="curve")

        elif t == "wave":
            pts = []
            for i in range(201):
                x = i / 200
                y = s.get("y", 0.5) + s.get("amp", 0.16) * math.sin(x * s.get("cyc", 2) * 2 * math.pi)
                pts.append(P(x, y))
            d.line(pts, fill=col, width=w, joint="curve")

        elif t == "zigzag":
            n = s.get("n", 5); pts = []
            for i in range(n * 2 + 1):
                x = i / (n * 2)
                y = s.get("y", 0.5) + (s.get("amp", 0.18) if i % 2 else -s.get("amp", 0.18))
                pts.append(P(x, y))
            d.line(pts, fill=col, width=w, joint="curve")

        elif t == "dots":
            r = s.get("r", 0.018) * DW
            for (x, y) in s["at"]:
                cx, cy = P(x, y)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

        elif t == "label":
            f = font(s.get("sz", 26), False)
            d.text(P(s["x"], s["y"]), s["s"], font=f, fill=col, anchor=s.get("anchor", "mm"))

def wrap(d, text, f, maxw):
    """어절 단위로 끊는다. 한 어절이 줄보다 길 때만 글자 단위로 쪼갠다."""
    out, line = [], ""
    for word in text.split(" "):
        cand = word if not line else line + " " + word
        if d.textlength(cand, font=f) <= maxw:
            line = cand
            continue
        if line:
            out.append(line); line = ""
        if d.textlength(word, font=f) <= maxw:
            line = word
        else:                      # 어절 하나가 줄보다 길면 글자로 쪼갠다
            buf = ""
            for ch in word:
                if d.textlength(buf + ch, font=f) > maxw and buf:
                    out.append(buf); buf = ch
                else:
                    buf += ch
            line = buf
    if line: out.append(line)
    return out

def render(item, cat, sub, spec, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 상단 분류 라인
    f_cat = font(24)
    d.text((93, 96), f"{cat}  ·  {sub}", font=f_cat, fill=SUB)
    d.line([(93, 140), (W - 93, 140)], fill=LINE, width=2)

    # 번호
    f_no = font(30, True)
    d.text((W - 93, 96), f"{item['id']:03d}", font=f_no, fill=ACCENT, anchor="ra")

    # 제목
    f_ko = font(76, True)
    d.text((93, 190), item["ko"], font=f_ko, fill=INK)
    f_en = font(30)
    d.text((95, 300), item["en"].upper(), font=f_en, fill=SUB)

    # 다이어그램
    d.rectangle([DX, DY, DX + DW, DY + DW], fill=(255, 253, 250), outline=LINE, width=2)
    draw_diagram(d, spec)

    # 설명 (푸터 위까지만)
    f_desc = font(30)
    y = DY + DW + 56
    for ln in wrap(d, item["desc"], f_desc, W - 186):
        if y + 40 > H - 120: break
        d.text((93, y), ln, font=f_desc, fill=INK); y += 46

    # 하단
    d.line([(93, H - 96), (W - 93, H - 96)], fill=LINE, width=2)
    f_ft = font(22)
    d.text((93, H - 74), "한국형 레이아웃 구성 도감", font=f_ft, fill=SUB)
    d.text((W - 93, H - 74), "KOREAN LAYOUT COMPOSITIONS", font=f_ft, fill=SUB, anchor="ra")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path

if __name__ == "__main__":
    print("이 파일은 build_all.py 에서 호출한다.")
