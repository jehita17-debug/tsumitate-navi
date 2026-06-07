# -*- coding: utf-8 -*-
"""
つみたてNAVI スライド描画モジュール（再利用用）

5枚カルーセル（Cover / Why / Points1 / Points2 / CTA）のPNGと
それをつないだ15秒MP4を生成する描画関数群。
gen_remaining_articles.py の描画ロジックを切り出し、
フォント解決を環境非依存（GitHub Actions/ローカル両対応）にしたもの。
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

NAVY = "#0b2545"
GOLD = "#d4a574"
CREAM = "#f5ede0"
WHITE = "#ffffff"
SIZE = 1080

# --- フォント解決（最初に見つかったものを使う） ---
_JP_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
]
_LAT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
_LAT_REG_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


FONT_JP = _first_existing(_JP_CANDIDATES)
FONT_LAT = _first_existing(_LAT_BOLD_CANDIDATES)
FONT_LAT_REG = _first_existing(_LAT_REG_CANDIDATES)

if FONT_JP is None:
    # 日本語フォントが無い環境では英字フォントで代用（豆腐になるが落ちはしない）
    FONT_JP = FONT_LAT or FONT_LAT_REG
if FONT_LAT is None:
    FONT_LAT = FONT_JP
if FONT_LAT_REG is None:
    FONT_LAT_REG = FONT_LAT


def get_font(size, bold=True):
    jp_path = FONT_JP
    lat_path = FONT_LAT if bold else FONT_LAT_REG
    return (
        ImageFont.truetype(jp_path, size),
        ImageFont.truetype(lat_path, size),
    )


def measure(draw, text, fonts):
    fjp, flat = fonts
    w = 0
    h = 0
    for c in text:
        f = flat if ord(c) < 128 else fjp
        bbox = draw.textbbox((0, 0), c, font=f)
        w += bbox[2] - bbox[0] + (2 if ord(c) < 128 else 0)
        h = max(h, bbox[3] - bbox[1])
    return w, h


def draw_mixed(draw, x, y, text, fonts, fill):
    fjp, flat = fonts
    cx = x
    for c in text:
        f = flat if ord(c) < 128 else fjp
        draw.text((cx, y), c, font=f, fill=fill)
        bbox = draw.textbbox((cx, y), c, font=f)
        cx = bbox[2] + (2 if ord(c) < 128 else 0)
    return cx


def wrap_jp(text, max_chars):
    lines = []
    cur = ""
    for c in text:
        weight = 0.5 if ord(c) < 128 else 1
        cur_w = sum(0.5 if ord(x) < 128 else 1 for x in cur)
        if cur_w + weight > max_chars and cur:
            lines.append(cur)
            cur = c
        else:
            cur += c
    if cur:
        lines.append(cur)
    return lines


def make_base(bg=NAVY, accent=GOLD):
    img = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SIZE, 8], fill=accent)
    d.rectangle([0, SIZE - 8, SIZE, SIZE], fill=accent)
    fjp, flat = get_font(28, bold=True)
    draw_mixed(d, SIZE - 280, 30, "つみたてNAVI", (fjp, flat), accent)
    return img, d


def slide_cover(out_path, badge, title_lines, subtitle):
    img, d = make_base(NAVY, GOLD)
    fjp_b, flat_b = get_font(32, bold=True)
    badge_w, _ = measure(d, badge, (fjp_b, flat_b))
    bx = (SIZE - badge_w - 80) // 2
    d.rounded_rectangle([bx, 200, bx + badge_w + 80, 270], radius=35, fill=GOLD)
    draw_mixed(d, bx + 40, 213, badge, (fjp_b, flat_b), NAVY)
    fjp_t, flat_t = get_font(72, bold=True)
    y = 360
    for line in title_lines:
        w, _ = measure(d, line, (fjp_t, flat_t))
        draw_mixed(d, (SIZE - w) // 2, y, line, (fjp_t, flat_t), WHITE)
        y += 100
    fjp_s, flat_s = get_font(36, bold=False)
    y += 40
    for line in wrap_jp(subtitle, 22):
        w, _ = measure(d, line, (fjp_s, flat_s))
        draw_mixed(d, (SIZE - w) // 2, y, line, (fjp_s, flat_s), CREAM)
        y += 56
    fjp_h, flat_h = get_font(28, bold=False)
    hint = "スワイプして詳しく"
    w, _ = measure(d, hint, (fjp_h, flat_h))
    hx = (SIZE - w - 40) // 2
    draw_mixed(d, hx, SIZE - 100, hint, (fjp_h, flat_h), GOLD)
    ax = hx + w + 18
    ay = SIZE - 92
    d.polygon([(ax, ay), (ax, ay + 24), (ax + 22, ay + 12)], fill=GOLD)
    img.save(out_path, "PNG")


def slide_why(out_path, headline, body_lines, highlight=None):
    img, d = make_base(WHITE, NAVY)
    d.ellipse([80, 100, 230, 250], fill=NAVY)
    fjp, flat = get_font(64, bold=True)
    w, _ = measure(d, "01", (fjp, flat))
    draw_mixed(d, 80 + (150 - w) // 2, 135, "01", (fjp, flat), GOLD)
    fjp, flat = get_font(28, bold=True)
    draw_mixed(d, 260, 145, "WHY  なぜ重要？", (fjp, flat), GOLD)
    fjp_h, flat_h = get_font(56, bold=True)
    y = 340
    for line in wrap_jp(headline, 16):
        draw_mixed(d, 80, y, line, (fjp_h, flat_h), NAVY)
        y += 80
    if highlight:
        y += 30
        fjp_b, flat_b = get_font(44, bold=True)
        parts = highlight.split("→")
        left = parts[0].strip()
        right = parts[1].strip() if len(parts) > 1 else ""
        lw, lh = measure(d, left, (fjp_b, flat_b))
        rw, rh = measure(d, right, (fjp_b, flat_b))
        total_w = lw + 60 + rw
        d.rounded_rectangle([60, y - 20, 60 + total_w + 60, y + max(lh, rh) + 40], radius=20, fill=GOLD)
        draw_mixed(d, 90, y, left, (fjp_b, flat_b), NAVY)
        ax = 90 + lw + 15
        ay = y + 18
        d.polygon([(ax, ay), (ax, ay + 32), (ax + 30, ay + 16)], fill=NAVY)
        draw_mixed(d, ax + 45, y, right, (fjp_b, flat_b), NAVY)
        y += max(lh, rh) + 80
    fjp_b, flat_b = get_font(34, bold=False)
    for line in body_lines:
        for sub in wrap_jp(line, 27):
            draw_mixed(d, 80, y, sub, (fjp_b, flat_b), "#374151")
            y += 50
        y += 14
    img.save(out_path, "PNG")


def slide_points(out_path, num, section_label, headline, items):
    img, d = make_base(CREAM, NAVY)
    d.ellipse([80, 100, 230, 250], fill=NAVY)
    fjp, flat = get_font(64, bold=True)
    w, _ = measure(d, num, (fjp, flat))
    draw_mixed(d, 80 + (150 - w) // 2, 135, num, (fjp, flat), GOLD)
    fjp, flat = get_font(28, bold=True)
    draw_mixed(d, 260, 145, section_label, (fjp, flat), GOLD)
    fjp_h, flat_h = get_font(50, bold=True)
    y = 320
    for line in wrap_jp(headline, 17):
        draw_mixed(d, 80, y, line, (fjp_h, flat_h), NAVY)
        y += 70
    y += 30
    fjp_t, flat_t = get_font(38, bold=True)
    fjp_d, flat_d = get_font(28, bold=False)
    for i, item in enumerate(items, 1):
        t, dd = item[0], item[1]
        d.rounded_rectangle([80, y + 5, 140, y + 65], radius=8, fill=NAVY)
        mw, _ = measure(d, f"{i:02d}", (fjp_t, flat_t))
        draw_mixed(d, 80 + (60 - mw) // 2, y + 12, f"{i:02d}", (fjp_t, flat_t), GOLD)
        draw_mixed(d, 170, y + 10, t, (fjp_t, flat_t), NAVY)
        y += 75
        for sub in wrap_jp(dd, 28):
            draw_mixed(d, 170, y, sub, (fjp_d, flat_d), "#4b5563")
            y += 42
        y += 24
    img.save(out_path, "PNG")


def slide_cta(out_path, summary_lines, site_url="tsumitate-navi.net"):
    img, d = make_base(NAVY, GOLD)
    fjp, flat = get_font(48, bold=True)
    label = "まとめ"
    w, h = measure(d, label, (fjp, flat))
    lx = (SIZE - w) // 2
    draw_mixed(d, lx, 130, label, (fjp, flat), GOLD)
    line_y = 130 + h // 2 + 5
    d.rectangle([lx - 120, line_y - 2, lx - 30, line_y + 2], fill=GOLD)
    d.rectangle([lx + w + 30, line_y - 2, lx + w + 120, line_y + 2], fill=GOLD)
    fjp_s, flat_s = get_font(38, bold=True)
    y = 280
    for line in summary_lines:
        d.line([(108, y + 28), (130, y + 46), (162, y + 12)], fill=GOLD, width=8)
        for sub in wrap_jp(line, 22):
            draw_mixed(d, 180, y, sub, (fjp_s, flat_s), WHITE)
            y += 52
        y += 24
    d.line([(150, 760), (SIZE - 150, 760)], fill=GOLD, width=2)
    fjp_b, flat_b = get_font(64, bold=True)
    brand = "つみたてNAVI"
    w, _ = measure(d, brand, (fjp_b, flat_b))
    draw_mixed(d, (SIZE - w) // 2, 800, brand, (fjp_b, flat_b), GOLD)
    fjp_t, flat_t = get_font(28, bold=False)
    tag = "投資初心者のためのやさしい解説"
    w, _ = measure(d, tag, (fjp_t, flat_t))
    draw_mixed(d, (SIZE - w) // 2, 885, tag, (fjp_t, flat_t), CREAM)
    fjp_u, flat_u = get_font(34, bold=True)
    w, _ = measure(d, site_url, (fjp_u, flat_u))
    draw_mixed(d, (SIZE - w) // 2, 940, site_url, (fjp_u, flat_u), WHITE)
    img.save(out_path, "PNG")


def make_video(dir_path, out_name, seconds_per_slide=3):
    """dir_path内の5枚PNGから15秒MP4を生成する。"""
    names = ["01_cover.png", "02_why.png", "03_steps_1.png", "04_steps_2.png", "05_cta.png"]
    concat_path = os.path.join(dir_path, "_concat.txt")
    with open(concat_path, "w") as f:
        for name in names:
            f.write(f"file '{os.path.join(dir_path, name)}'\nduration {seconds_per_slide}\n")
        # ffmpeg concat は最後の画像をもう一度書く必要がある
        f.write(f"file '{os.path.join(dir_path, names[-1])}'\n")
    out_path = os.path.join(dir_path, out_name)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path,
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        out_path
    ], check=True, capture_output=True)
    try:
        os.remove(concat_path)
    except Exception:
        pass
    return out_path


def build_article_assets(article_dir, video_name, slides):
    """slides = {cover, why, points1, points2, cta} の各dict。PNG5枚＋MP4を生成。"""
    os.makedirs(article_dir, exist_ok=True)
    slide_cover(os.path.join(article_dir, "01_cover.png"), **slides["cover"])
    slide_why(os.path.join(article_dir, "02_why.png"), **slides["why"])
    slide_points(os.path.join(article_dir, "03_steps_1.png"), **slides["points1"])
    slide_points(os.path.join(article_dir, "04_steps_2.png"), **slides["points2"])
    slide_cta(os.path.join(article_dir, "05_cta.png"), **slides["cta"])
    return make_video(article_dir, video_name)
