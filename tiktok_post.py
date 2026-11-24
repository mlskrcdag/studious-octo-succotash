#!/usr/bin/env python3
"""TikTok foto-post üretici — "day in my life" estetiği.

Kullanım:
    python3 tiktok_post.py posts/ornek.json            # tek post
    python3 tiktok_post.py posts/*.json                # hepsi

Her JSON dosyası bir slaytı tarif eder (bkz. STYLE_GUIDE.md ve posts/ klasörü).
Çıktı: output/<json-adı>.jpg
"""
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# ---------------------------------------------------------------- paleti
PALETTE = {
    "cream": "#F6F1DE",      # büyük el yazısı başlık
    "white": "#FFFFFF",
    "blush": "#F2C6D3",      # "one", "6 am - 10 pm" gibi küçük etiketler
    "clock_bg": "#F2F2F2",   # flip-clock karoları
    "clock_ink": "#4A4A4A",  # flip-clock rakamları (nötr)
    "clock_pink": "#EC6F9A", # flip-clock rakamları (pembe varyant)
    "star_yellow": "#FFD34E",
    "pop_pink": "#F7A1B9",
    "tag_bg": "#F9CFDD",     # stil C: pembe vurgu etiketi zemini
    "berry": "#A3344F",      # stil C: etiket yazısı / arama butonu   # büyük sans başlık ("day in my life" office edition)
}

FONT_FILES = {
    "script": "PinyonScript-Regular.ttf",   # "Day in my Life" başlığı
    "script2": "GreatVibes-Regular.ttf",    # "breakfast platter" yemek etiketi
    "script3": "Allura-Regular.ttf",
    "script4": "Parisienne-Regular.ttf",
    "sans": "Inter-Regular.otf",            # caption yazısı (iOS/TikTok sistem fontu hissi)
    "sans_light": "Inter-Light.otf",
    "sans_medium": "Inter-Medium.otf",      # flip-clock rakamları
    "sans_bold": "Inter-SemiBold.otf",      # stil C: beyaz kalın başlık
    "hand": "Caveat.ttf",                   # el yazısı notlar / checklist (Türkçe karakter destekli)
}

_font_cache = {}


def font(name, size):
    key = (name, int(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / FONT_FILES[name]), int(size))
    return _font_cache[key]


def color(c):
    return PALETTE.get(c, c)


def rgba(c, alpha=255):
    c = color(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


# ---------------------------------------------------------------- emoji destekli metin
_EB = "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\u2300-\u23FF]"
_EM = "[\uFE0F\U0001F3FB-\U0001F3FF]*"
EMOJI_RE = re.compile("(" + _EB + _EM + "(?:\u200D" + _EB + _EM + ")*)")
_emoji_font = None


def _emoji_img(ch, px):
    global _emoji_font
    if _emoji_font is None:
        _emoji_font = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=_emoji_font, embedded_color=True)
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    scale = px / 128
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def _runs(text):
    parts = EMOJI_RE.split(text)
    return [(p, i % 2 == 1) for i, p in enumerate(parts) if p]


def text_width(text, f):
    w = 0
    for chunk, is_emoji in _runs(text):
        w += f.size * 1.15 if is_emoji else f.getlength(chunk)
    return w


def draw_line(layer, xy, text, f, fill):
    x, y = xy
    d = ImageDraw.Draw(layer)
    ascent, _ = f.getmetrics()
    for chunk, is_emoji in _runs(text):
        if is_emoji:
            em = _emoji_img(chunk, f.size * 1.05)
            if em:
                layer.alpha_composite(em, (int(x), int(y + ascent - em.height * 0.88)))
            x += f.size * 1.15
        else:
            d.text((x, y), chunk, font=f, fill=fill)
            x += f.getlength(chunk)


def wrap(text, f, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if text_width(test, f) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- yerleşim (layout)
def fit(img, w, h, focus=(0.5, 0.5)):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=tuple(focus))


def straighten(img, deg):
    """Fotoğrafı deg derece döndür (+ saat yönünün tersi), boş köşeleri kırp."""
    if not deg:
        return img
    w, h = img.size
    r = img.rotate(deg, resample=Image.BICUBIC)
    t = math.radians(abs(deg))
    s = 1 / (math.cos(t) + math.sin(t) * max(w / h, h / w))
    cw, ch = int(w * s), int(h * s)
    return r.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2))


def keystone(img, quad):
    """Perspektif düzeltme: quad = fotoğraftaki dikdörtgen nesnenin köşeleri
    [sol-üst, sağ-üst, sağ-alt, sol-alt] (piksel). O nesne düz dikdörtgen olacak şekilde
    bütün fotoğraf düzeltilir."""
    if not quad:
        return img
    import numpy as np
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = quad
    L, R = (x0 + x3) / 2, (x1 + x2) / 2
    T, B = (y0 + y1) / 2, (y2 + y3) / 2
    dst = [(L, T), (R, T), (R, B), (L, B)]
    A, bvec = [], []
    for (u, v), (x, y) in zip(quad, dst):   # çıktı(x,y) -> girdi(u,v)
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); bvec.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); bvec.append(v)
    coeffs = np.linalg.solve(np.array(A, float), np.array(bvec, float))
    out = img.transform(img.size, Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
    # kenarlarda oluşan siyah boşlukları kırp
    m = 0.06
    w, h = img.size
    return out.crop((int(w * m), int(h * m), int(w * (1 - m)), int(h * (1 - m))))


def load(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB")


def build_base(spec):
    W, H = spec.get("size", [1080, 1440])
    layout = spec.get("layout", "full")
    photos = spec["photos"]
    foc = spec.get("focus", [[0.5, 0.5]] * len(photos))
    rots = spec.get("rotate", [0] * len(photos))
    _load = load
    quads = spec.get("keystone", [None] * len(photos))
    load_r = lambda i: straighten(keystone(_load(photos[i]), quads[i]), rots[i])
    canvas = Image.new("RGB", (W, H), "white")
    split = spec.get("split", 0.5)
    if layout == "full":
        canvas.paste(fit(load_r(0), W, H, foc[0]), (0, 0))
    elif layout == "stack2":            # üst + alt (görsel 1, 3, 4)
        h1 = int(H * split)
        canvas.paste(fit(load_r(0), W, h1, foc[0]), (0, 0))
        canvas.paste(fit(load_r(1), W, H - h1, foc[1]), (0, h1))
    elif layout == "top_split":         # üstte tek, altta yan yana iki (görsel 2)
        h1 = int(H * split)
        canvas.paste(fit(load_r(0), W, h1, foc[0]), (0, 0))
        w2 = W // 2
        canvas.paste(fit(load_r(1), w2, H - h1, foc[1]), (0, h1))
        canvas.paste(fit(load_r(2), W - w2, H - h1, foc[2]), (w2, h1))
    elif layout == "stack3":            # üç yatay bant, üstten alta
        fr = spec.get("splits", [1 / 3, 1 / 3, 1 / 3])
        y = 0
        for i in range(3):
            h = H - y if i == 2 else int(H * fr[i])
            canvas.paste(fit(load_r(i), W, h, foc[i]), (0, y))
            y += h
    else:
        raise ValueError(f"bilinmeyen layout: {layout}")
    return canvas.convert("RGBA")


# ---------------------------------------------------------------- öğeler
def shadowed(base, layer, blur, alpha):
    """Metnin altına yumuşak gölge — açık zeminlerde okunurluk için."""
    if alpha > 0:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
        a = a.point(lambda v: int(v * alpha / 255))
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(a)
        base.alpha_composite(sh)
    base.alpha_composite(layer)


def el_caption(base, e, W, H):
    """Beyaz, sade, ortalı caption (iOS Story yazısı hissi)."""
    f = font(e.get("font", "sans"), e.get("size", 0.03) * W)
    max_w = e.get("width", 0.62) * W
    lines = wrap(e["text"], f, max_w)
    lh = f.size * e.get("line_height", 1.22)
    block_h = lh * len(lines)
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    align = e.get("align", "center")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    for i, ln in enumerate(lines):
        tw = text_width(ln, f)
        if align == "left":
            x = cx
        elif align == "right":
            x = cx - tw
        else:
            x = cx - tw / 2
        draw_line(layer, (x, cy - block_h / 2 + i * lh), ln, f, rgba(e.get("color", "white")))
    shadowed(base, layer, f.size * 0.25, e.get("shadow", 90))


def el_script(base, e, W, H):
    """Büyük el yazısı başlık. Her satır ayrı konumlanabilir (merdiven efekti)."""
    f = font(e.get("font", "script"), e.get("size", 0.12) * W)
    lines = e["text"].split("\n")
    offsets = e.get("offsets", [0] * len(lines))   # satır başına yatay kayma (W oranı)
    lh = f.size * e.get("line_height", 0.95)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    top = cy - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text((cx - tw / 2 + offsets[i] * W, top + i * lh), ln, font=f, fill=rgba(e.get("color", "cream")))
    if e.get("rotate"):
        layer = layer.rotate(e["rotate"], resample=Image.BICUBIC, center=(cx, cy))
    shadowed(base, layer, f.size * 0.06, e.get("shadow", 70))


def el_label(base, e, W, H):
    """Küçük ince sans etiket: 'one', '6 am - 10 pm'."""
    f = font(e.get("font", "sans_light"), e.get("size", 0.04) * W)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tw = text_width(e["text"], f)
    x = e.get("x", 0.5) * W
    if e.get("align", "left") == "center":
        x -= tw / 2
    draw_line(layer, (x, e.get("y", 0.1) * H), e["text"], f, rgba(e.get("color", "blush")))
    shadowed(base, layer, f.size * 0.2, e.get("shadow", 40))


def el_clock(base, e, W, H):
    """Flip-clock saat damgası. style='glass' (varsayılan): buzlu cam, şeffaf karolar,
    beyaz rakam. style='solid': açık gri dolu karolar."""
    if e.get("style") == "plain":
        # sade saat yazısı: "8:45 am" — beyaz, düz sans, hafif gölge
        f = font("sans", e.get("size", 0.06) * W)
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        txt = e["time"]
        tw = f.getlength(txt)
        asc, desc = f.getmetrics()
        ImageDraw.Draw(layer).text((e.get("x", 0.5) * W - tw / 2, e.get("y", 0.5) * H - (asc + desc) / 2),
                                   txt, font=f, fill=rgba(e.get("color", "white")))
        shadowed(base, layer, f.size * 0.15, e.get("shadow", 70))
        return
    digits = e["time"].replace(":", "")
    tile_w = e.get("size", 0.065) * W
    tile_h = tile_w * 1.42
    gap = tile_w * 0.1
    total = tile_w * 4 + gap * 3
    x0 = e.get("x", 0.5) * W - total / 2
    y0 = e.get("y", 0.2) * H - tile_h / 2
    f = font("sans_medium", tile_h * 0.86)
    glass = e.get("style", "glass") == "glass"
    ink = rgba(e.get("color", "white" if glass else "clock_ink"))
    rad = tile_w * 0.14
    boxes = [[x0 + i * (tile_w + gap), y0, x0 + i * (tile_w + gap) + tile_w, y0 + tile_h] for i in range(4)]
    if glass:
        # arkadaki fotoğrafı bulanıklaştır (buzlu cam), üstüne çok hafif beyaz
        mask = Image.new("L", base.size, 0)
        md = ImageDraw.Draw(mask)
        for b in boxes:
            md.rounded_rectangle(b, radius=rad, fill=255)
        blurred = base.filter(ImageFilter.GaussianBlur(tile_w * 0.18))
        base.paste(blurred, (0, 0), mask)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for b, ch in zip(boxes, digits[:4]):
        if glass:
            d.rounded_rectangle(b, radius=rad, fill=(255, 255, 255, e.get("bg_alpha", 45)),
                                outline=(255, 255, 255, 140), width=max(1, int(tile_w * 0.025)))
        else:
            d.rounded_rectangle(b, radius=rad, fill=rgba(e.get("bg", "clock_bg"), e.get("bg_alpha", 225)))
        bb = d.textbbox((0, 0), ch, font=f)
        d.text((b[0] + (tile_w - (bb[2] - bb[0])) / 2 - bb[0],
                y0 + (tile_h - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=ink)
        my = y0 + tile_h / 2
        line = (255, 255, 255, 110) if glass else (120, 120, 120, 170)
        d.line([b[0], my, b[2], my], fill=line, width=max(1, int(tile_h * 0.018)))
    if glass:
        shadowed(base, layer, tile_w * 0.08, e.get("shadow", 60))
    else:
        shadowed(base, layer, tile_w * 0.15, e.get("shadow", 35))


def _star_points(cx, cy, r, rot=-90, inner=0.42):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def el_star(base, e, W, H):
    """Yıldız sticker'ları: style = white | yellow | polka."""
    r = e.get("size", 0.025) * W
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    style = e.get("style", "white")
    rot = -90 + e.get("rotate", 0)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = _star_points(cx, cy, r, rot)
    if style == "twinkle":
        # 4 köşeli parıltı yıldızı + yumuşak ışıma
        pts = []
        for i in range(8):
            rr = r if i % 2 == 0 else r * 0.2
            a = math.radians(rot + i * 45)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=(255, 255, 255, 150))
        glow = glow.filter(ImageFilter.GaussianBlur(r * 0.35))
        base.alpha_composite(glow)
        d.polygon(pts, fill=rgba(e.get("color", "white")))
        base.alpha_composite(layer)
        return
    if style == "yellow":
        d.polygon(_star_points(cx, cy, r, rot, 0.5), fill=rgba("star_yellow"))
        hl = _star_points(cx - r * 0.12, cy - r * 0.12, r * 0.45, rot, 0.5)
        d.polygon(hl, fill=(255, 240, 170, 200))
    elif style == "polka":
        d.polygon(pts, fill=rgba("#FBF6EA"))
        mask = Image.new("L", base.size, 0)
        ImageDraw.Draw(mask).polygon(pts, fill=255)
        dots = Image.new("RGBA", base.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(dots)
        step = r * 0.32
        yy = cy - r
        row = 0
        while yy < cy + r:
            xx = cx - r + (step / 2 if row % 2 else 0)
            while xx < cx + r:
                dd.ellipse([xx - step * 0.16, yy - step * 0.16, xx + step * 0.16, yy + step * 0.16], fill=(20, 20, 20, 255))
                xx += step
            yy += step * 0.9
            row += 1
        from PIL import ImageChops
        dots.putalpha(ImageChops.multiply(dots.getchannel("A"), mask))
        layer.alpha_composite(dots)
    else:
        d.polygon(pts, fill=rgba("white"))
    shadowed(base, layer, r * 0.12, e.get("shadow", 60))


def el_pill(base, e, W, H):
    """Konum/tarih hapı: yarı saydam beyaz zemin + pin ikonu + metin."""
    f = font("sans", e.get("size", 0.032) * W)
    text = e["text"]
    pad_x, pad_y = f.size * 0.75, f.size * 0.5
    icon_w = f.size * 0.9 if e.get("icon", True) else 0
    tw = text_width(text, f)
    w = tw + pad_x * 2 + icon_w
    h = f.size * 1.2 + pad_y * 2
    x0 = e.get("x", 0.5) * W - w / 2
    y0 = e.get("y", 0.9) * H - h / 2
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h * 0.32, fill=(255, 255, 255, e.get("alpha", 70)))
    ink = rgba(e.get("color", "white"))
    if icon_w:
        px, py, pr = x0 + pad_x + f.size * 0.3, y0 + h / 2 - f.size * 0.12, f.size * 0.3
        lw = max(2, int(f.size * 0.08))
        d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=ink, width=lw)
        d.line([px - pr * 0.85, py + pr * 0.5, px, py + pr * 1.9], fill=ink, width=lw)
        d.line([px + pr * 0.85, py + pr * 0.5, px, py + pr * 1.9], fill=ink, width=lw)
        d.ellipse([px - pr * 0.3, py - pr * 0.3, px + pr * 0.3, py + pr * 0.3], outline=ink, width=lw)
    asc, desc = f.getmetrics()
    draw_line(layer, (x0 + pad_x + icon_w, y0 + (h - asc - desc) / 2), text, f, ink)
    base.alpha_composite(layer)


def el_emoji(base, e, W, H):
    """Tek başına emoji sticker'ı (ör. 🐾, 🍊), isteğe bağlı döndürme."""
    em = _emoji_img(e["text"], e.get("size", 0.08) * W)
    if em is None:
        return
    if e.get("rotate"):
        em = em.rotate(e["rotate"], resample=Image.BICUBIC, expand=True)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.alpha_composite(em, (int(e.get("x", 0.5) * W - em.width / 2), int(e.get("y", 0.5) * H - em.height / 2)))
    shadowed(base, layer, em.width * 0.06, e.get("shadow", 50))


def el_title(base, e, W, H):
    """Büyük, düz sans başlık (küçük harf, sıkı satır aralığı) — 'day / in my / life'."""
    f = font(e.get("font", "sans"), e.get("size", 0.17) * W)
    lines = e["text"].split("\n")
    lh = f.size * e.get("line_height", 0.86)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    top = cy - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text((cx - tw / 2, top + i * lh), ln, font=f, fill=rgba(e.get("color", "pop_pink")))
    shadowed(base, layer, f.size * 0.04, e.get("shadow", 40))


def _wobbly_box(d, x, y, s, fill, width):
    """Elle çizilmiş gibi hafif titrek kare."""
    import random
    rnd = random.Random(int(x * 7 + y * 13))
    j = lambda: rnd.uniform(-s * 0.06, s * 0.06)
    pts = [(x + j(), y + j()), (x + s + j(), y + j()), (x + s + j(), y + s + j()), (x + j(), y + s + j())]
    d.line(pts + [pts[0]], fill=fill, width=width, joint="curve")


def el_hand(base, e, W, H):
    """El yazısı not (beyaz kalem hissi): 'double shot please!', 'my morning fuel'.
    checklist: true ise ':' ile biten satıra kadar başlık, sonrakiler kutucuklu madde olur.
    '- ' ile başlayan satır bir önceki maddenin devamı (girintili)."""
    f = font("hand", e.get("size", 0.05) * W)
    ink = rgba(e.get("color", "white"))
    lines = e["text"].split("\n")
    lh = f.size * e.get("line_height", 1.0)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0 = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    align = e.get("align", "left" if e.get("checklist") else "center")
    box = f.size * 0.5
    gap = f.size * 0.35
    # başlık satırları: ':' ile biten ilk satıra kadar (yoksa sadece ilk satır)
    n_head = next((k + 1 for k, l in enumerate(lines) if l.rstrip().endswith(":")), 1)
    total_h = lh * len(lines) + (lh * 0.3 if e.get("checklist") else 0)
    y = y0 - total_h / 2
    for i, ln in enumerate(lines):
        x = x0
        item = e.get("checklist") and i >= n_head
        if item and ln.startswith("- "):
            ln = ln[2:]
            x += box + gap
        elif item:
            asc, _ = f.getmetrics()
            by = y + asc - box * 1.05
            _wobbly_box(d, x, by, box, ink, max(2, int(f.size * 0.06)))
            x += box + gap
        tw = text_width(ln, f)
        if align == "center":
            x -= tw / 2
        draw_line(layer, (x, y), ln, f, ink)
        y += lh
        if e.get("checklist") and i == n_head - 1:
            y += lh * 0.3
    if e.get("rotate"):
        layer = layer.rotate(e["rotate"], resample=Image.BICUBIC, center=(x0, y0))
    shadowed(base, layer, f.size * 0.12, e.get("shadow", 90))


def el_doodle(base, e, W, H):
    """Elle çizilmiş doodle'lar: arrow | heart | sparkle | underline | circle | swirl."""
    kind = e.get("shape", "arrow")
    s = e.get("size", 0.08) * W
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    ink = rgba(e.get("color", "white"))
    lw = max(2, int(e.get("width", 0.004) * W))
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    def curve(pts, n=40):
        # Catmull-Rom yumuşatma
        out = []
        P = [pts[0]] + pts + [pts[-1]]
        for k in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[k - 1], P[k], P[k + 1], P[k + 2]
            for t in [i / n for i in range(n)]:
                t2, t3 = t * t, t * t * t
                out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                        + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
        out.append(pts[-1])
        return out
    P = lambda u, v: (cx + u * s, cy + v * s)
    if kind == "arrow":
        line = curve([P(-0.5, 0.1), P(-0.15, -0.12), P(0.2, -0.05), P(0.5, 0.0)])
        d.line(line, fill=ink, width=lw, joint="curve")
        d.line([P(0.32, -0.15), P(0.5, 0.0), P(0.3, 0.13)], fill=ink, width=lw, joint="curve")
    elif kind == "heart":
        d.line(curve([P(0, 0.45), P(-0.4, 0.05), P(-0.38, -0.3), P(-0.1, -0.35), P(0, -0.12),
                      P(0.1, -0.35), P(0.38, -0.3), P(0.4, 0.05), P(0.02, 0.43)]), fill=ink, width=lw, joint="curve")
    elif kind == "sparkle":
        for a, r in [(0, 0.5), (90, 0.5), (45, 0.25), (135, 0.25)]:
            t = math.radians(a)
            d.line([P(-math.cos(t) * r, -math.sin(t) * r), P(math.cos(t) * r, math.sin(t) * r)], fill=ink, width=lw)
    elif kind == "underline":
        d.line(curve([P(-0.5, 0), P(-0.2, 0.04), P(0.15, -0.02), P(0.5, 0.03)]), fill=ink, width=lw, joint="curve")
    elif kind == "circle":
        pts = [P(0.5 * math.cos(math.radians(a)) * (1 + 0.04 * math.sin(a)), 0.32 * math.sin(math.radians(a)))
               for a in range(-20, 370, 30)]
        d.line(curve(pts), fill=ink, width=lw, joint="curve")
    elif kind == "swirl":
        pts = [P(0.08 * k / 6 * math.cos(k * 0.9) * 3, 0.08 * k / 6 * math.sin(k * 0.9) * 3) for k in range(1, 16)]
        d.line(curve(pts), fill=ink, width=lw, joint="curve")
    if e.get("rotate"):
        layer = layer.rotate(e["rotate"], resample=Image.BICUBIC, center=(cx, cy))
    shadowed(base, layer, lw * 1.5, e.get("shadow", 90))


def el_tag(base, e, W, H):
    """Pembe vurgu etiketi: '[ as a student ]' — açık pembe dikdörtgen, koyu pembe yazı."""
    f = font(e.get("font", "sans"), e.get("size", 0.04) * W)
    txt = e["text"]
    if e.get("brackets", True):
        txt = "[ " + txt + " ]"
    tw = text_width(txt, f)
    asc, desc = f.getmetrics()
    px, py = f.size * 0.25, f.size * 0.08
    w, h = tw + px * 2, asc + desc + py * 2
    layer = Image.new("RGBA", (int(w) + 4, int(h) + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, 0, w, h], fill=rgba(e.get("bg", "tag_bg"), 235))
    draw_line(layer, (px, py), txt, f, rgba(e.get("color", "berry")))
    if e.get("rotate"):
        layer = layer.rotate(e["rotate"], resample=Image.BICUBIC, expand=True)
    base.alpha_composite(layer, (int(e.get("x", 0.5) * W - layer.width / 2), int(e.get("y", 0.5) * H - layer.height / 2)))


def el_search(base, e, W, H):
    """Arama çubuğu: beyaz yuvarlak kutu, pembe vurgulu metin + imleçler, sağda yuvarlak ok butonu."""
    f = font("sans", e.get("size", 0.034) * W)
    w = e.get("width", 0.66) * W
    h = f.size * 2.3
    x0 = e.get("x", 0.5) * W - w / 2
    y0 = e.get("y", 0.8) * H - h / 2
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0 - h * 0.12, y0 - h * 0.12, x0 + w + h * 0.12, y0 + h * 1.12], radius=h * 0.62, fill=(255, 255, 255, 120))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h / 2, fill=(255, 255, 255, 245),
                        outline=(225, 225, 225, 255), width=max(1, int(h * 0.02)))
    berry = rgba("berry")
    tx = x0 + h * 0.55
    tw = text_width(e["text"], f)
    asc, desc = f.getmetrics()
    ty = y0 + (h - asc - desc) / 2
    d.rectangle([tx, ty, tx + tw, ty + asc + desc], fill=rgba("tag_bg", 200))
    draw_line(layer, (tx, ty), e["text"], f, (60, 60, 60, 255))
    lw = max(2, int(f.size * 0.07))
    for cx_, top in ((tx - lw, True), (tx + tw + lw, False)):
        d.line([cx_, ty - f.size * 0.05, cx_, ty + asc + desc + f.size * 0.05], fill=berry, width=lw)
        r = f.size * 0.12
        cy_ = ty - f.size * 0.05 if top else ty + asc + desc + f.size * 0.05
        d.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=berry)
    br = h * 0.32
    bx, by = x0 + w - h * 0.55, y0 + h / 2
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=berry)
    aw = max(2, int(br * 0.18))
    d.line([bx, by + br * 0.5, bx, by - br * 0.5], fill=(255, 255, 255, 255), width=aw)
    d.line([bx - br * 0.4, by - br * 0.1, bx, by - br * 0.5, bx + br * 0.4, by - br * 0.1], fill=(255, 255, 255, 255), width=aw, joint="curve")
    shadowed(base, layer, h * 0.15, e.get("shadow", 40))


def el_folder(base, e, W, H):
    """Pembe masaüstü klasör ikonu + altında etiket ('photo dump')."""
    s = e.get("size", 0.16) * W
    cx, cy = e.get("x", 0.2) * W, e.get("y", 0.15) * H
    x0, y0 = cx - s / 2, cy - s * 0.4
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    back, front = rgba("#F4A9C4"), rgba("#F9C3D7")
    r = s * 0.06
    d.rounded_rectangle([x0, y0, x0 + s * 0.42, y0 + s * 0.2], radius=r, fill=back)
    d.rounded_rectangle([x0, y0 + s * 0.08, x0 + s, y0 + s * 0.72], radius=r, fill=back)
    d.rounded_rectangle([x0, y0 + s * 0.18, x0 + s, y0 + s * 0.8], radius=r, fill=front)
    if e.get("text"):
        f = font("sans_medium", s * 0.17)
        tw = text_width(e["text"], f)
        draw_line(layer, (cx - tw / 2, y0 + s * 0.88), e["text"], f, rgba("white"))
    shadowed(base, layer, s * 0.05, e.get("shadow", 80))


ELEMENTS = {
    "caption": el_caption, "script": el_script, "label": el_label,
    "clock": el_clock, "star": el_star, "pill": el_pill, "emoji": el_emoji,
    "title": el_title, "hand": el_hand, "doodle": el_doodle,
    "tag": el_tag, "search": el_search, "folder": el_folder,
}


# ---------------------------------------------------------------- renk düzeltme (isteğe bağlı)
def grade(img, g):
    """Hafif 'warm & soft' ton: parlaklık, kontrast, sıcaklık, solukluk."""
    from PIL import ImageEnhance
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(g.get("brightness", 1.0))
    rgb = ImageEnhance.Contrast(rgb).enhance(g.get("contrast", 1.0))
    rgb = ImageEnhance.Color(rgb).enhance(g.get("saturation", 1.0))
    warmth = g.get("warmth", 0)          # -20..20
    if warmth:
        r, gg, b = rgb.split()
        r = r.point(lambda v: min(255, v + warmth))
        b = b.point(lambda v: max(0, v - warmth))
        rgb = Image.merge("RGB", (r, gg, b))
    fade = g.get("fade", 0)              # 0..40: siyahları kaldırır (mat görünüm)
    if fade:
        rgb = rgb.point(lambda v: int(fade + v * (255 - fade) / 255))
    return rgb.convert("RGBA")


def add_insets(base, spec):
    """Ana fotoğrafın üstüne küçük 'polaroid' kart(lar): spec["insets"] listesi.
    Her kart: photo, x, y (merkez, 0–1), w (genişlik oranı), aspect (y/g, ör. 1.0 kare, 1.25 dikey),
    crop [sol, üst, sağ, alt] (0–1, isteğe bağlı), focus, rotate, frame: polaroid | plain | rounded."""
    W, H = base.size
    for c in spec.get("insets", []):
        img = load(c["photo"])
        if c.get("crop"):
            l, t, r, b = c["crop"]
            img = img.crop((int(l * img.width), int(t * img.height), int(r * img.width), int(b * img.height)))
        if c.get("grade", spec.get("grade")):
            img = grade(img.convert("RGBA"), c.get("grade", spec.get("grade"))).convert("RGB")
        w = int(c.get("w", 0.42) * W)
        h = int(w * c.get("aspect", 1.25))
        photo = fit(img, w, h, tuple(c.get("focus", [0.5, 0.5])))
        frame = c.get("frame", "polaroid")
        if frame == "polaroid":
            pad = int(w * 0.05)
            card = Image.new("RGBA", (w + pad * 2, h + pad * 2 + int(w * 0.14)), (250, 248, 243, 255))
            card.paste(photo, (pad, pad))
        elif frame == "rounded":
            card = photo.convert("RGBA")
            m = Image.new("L", card.size, 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, w, h], radius=int(w * 0.06), fill=255)
            card.putalpha(m)
        else:
            pad = int(w * 0.02)
            card = Image.new("RGBA", (w + pad * 2, h + pad * 2), (255, 255, 255, 255))
            card.paste(photo, (pad, pad))
        if c.get("rotate"):
            card = card.rotate(c["rotate"], resample=Image.BICUBIC, expand=True)
        cx, cy = c.get("x", 0.7) * W, c.get("y", 0.3) * H
        pos = (int(cx - card.width / 2), int(cy - card.height / 2))
        # yumuşak gölge
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        a = Image.new("L", base.size, 0)
        a.paste(card.getchannel("A"), (pos[0] + int(w * 0.015), pos[1] + int(w * 0.03)))
        a = a.filter(ImageFilter.GaussianBlur(w * 0.03)).point(lambda v: int(v * 0.45))
        sh.putalpha(a)
        base.alpha_composite(sh)
        base.alpha_composite(card, pos)
    return base


def render(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    base = build_base(spec)
    if spec.get("grade"):
        base = grade(base, spec["grade"])
    base = add_insets(base, spec)
    W, H = base.size
    for e in spec.get("elements", []):
        ELEMENTS[e["type"]](base, e, W, H)
    out = ROOT / "output" / (Path(spec_path).stem + ".jpg")
    out.parent.mkdir(exist_ok=True)
    base.convert("RGB").save(out, quality=95)
    print("✓", out.relative_to(ROOT))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        render(p)
