# -*- coding: utf-8 -*-
"""
つみたてNAVI 残り10記事 → Instagram 5枚カルーセル＋15秒動画 一括生成
記事04（5/16）〜記事13（5/26）を一気に出力。
出力先: ~/Desktop/つみたてInstagram/
"""
from PIL import Image, ImageDraw, ImageFont
import os, subprocess, sys

NAVY = "#0b2545"
GOLD = "#d4a574"
CREAM = "#f5ede0"
WHITE = "#ffffff"
SIZE = 1080
FONT_JP = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
FONT_LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_LAT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

OUT_BASE = os.path.expanduser("~/Desktop/つみたてInstagram")


def get_font(size, bold=True):
    return (
        ImageFont.truetype(FONT_JP, size),
        ImageFont.truetype(FONT_LAT if bold else FONT_LAT_REG, size),
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
    for i, (t, dd) in enumerate(items, 1):
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


def make_video(dir_path, out_name):
    """Generate 15s MP4 from the 5 PNG images in dir_path."""
    concat_path = os.path.join(dir_path, "_concat.txt")
    with open(concat_path, "w") as f:
        for i in [1, 2, 3, 4, 5]:
            name = ["01_cover.png", "02_why.png", "03_steps_1.png", "04_steps_2.png", "05_cta.png"][i-1]
            f.write(f"file '{os.path.join(dir_path, name)}'\nduration 3\n")
        # last image needs to be repeated for ffmpeg concat
        f.write(f"file '{os.path.join(dir_path, '05_cta.png')}'\n")
    out_path = os.path.join(dir_path, out_name)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path,
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        out_path
    ], check=True, capture_output=True)
    try:
        os.remove(concat_path)
    except Exception:
        pass


def build_article(article_dir, video_name, slides):
    """slides = dict of {cover, why, points1, points2, cta}"""
    os.makedirs(article_dir, exist_ok=True)
    slide_cover(os.path.join(article_dir, "01_cover.png"), **slides["cover"])
    slide_why(os.path.join(article_dir, "02_why.png"), **slides["why"])
    slide_points(os.path.join(article_dir, "03_steps_1.png"), **slides["points1"])
    slide_points(os.path.join(article_dir, "04_steps_2.png"), **slides["points2"])
    slide_cta(os.path.join(article_dir, "05_cta.png"), **slides["cta"])
    make_video(article_dir, video_name)
    return article_dir


# ============================================================
# 残り10記事の内容定義
# ============================================================
ARTICLES = [
    {
        "folder": "04_iDeCo_vs_NISA",
        "video": "04_iDeCo_vs_NISA_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "制度比較", "title_lines": ["iDeCoとNISA", "どっち優先？"], "subtitle": "ライフステージ別の選び方を初心者向けに整理"},
            "why": {"headline": "目的と引き出しルールがまったく違う制度", "body_lines": ["どちらも運用益が非課税。", "ただし税制・上限・引き出しが別物。", "順番を間違えると効果半減。"], "highlight": "NISA→自由 / iDeCo→老後専用"},
            "points1": {"num": "02", "section_label": "BASIC 基本の違い", "headline": "2つの非課税制度の役割", "items": [
                ("NISA", "運用益・売却益・配当が非課税。いつでも引き出しOK"),
                ("iDeCo", "掛金が全額所得控除。原則60歳まで引き出せない"),
                ("併用", "両方使ってOK。手取りと将来の使い道で配分"),
            ]},
            "points2": {"num": "03", "section_label": "HOW 優先順位の決め方", "headline": "迷ったらこの順番", "items": [
                ("まず生活防衛資金", "現金で生活費6か月分を確保"),
                ("次にNISA", "流動性も活かせて初心者の入口に最適"),
                ("余力でiDeCo", "節税効果を狙うなら掛金は所得控除フル活用"),
            ]},
            "cta": {"summary_lines": ["NISAは使いみち自由・即引き出しOK", "iDeCoは老後資金専用＋三段階節税", "生活防衛資金→NISA→iDeCoの順", "家計に合わせて配分を決めよう"]},
        },
    },
    {
        "folder": "05_年代別積立額",
        "video": "05_年代別積立額_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "積立額の目安", "title_lines": ["毎月いくら", "積み立てる？"], "subtitle": "年代別の目安と手取りからの計算方法"},
            "why": {"headline": "金額より「続けられること」が最優先", "body_lines": ["背伸びすると下落時にやめがち。", "1万円を20年続ける方が、", "3万円を3年で挫折より強い。"], "highlight": "短く多く → 長く少なく"},
            "points1": {"num": "02", "section_label": "AGE 年代別の目安", "headline": "ライフステージ別の積立額", "items": [
                ("20代", "5,000〜2万円 / 時間が最大の武器"),
                ("30代", "1〜3万円 / 住宅・教育費とバランス"),
                ("40代", "2〜5万円 / 老後資金の本格積み増し"),
                ("50代", "3〜6万円 / 退職までの最終追い込み"),
            ]},
            "points2": {"num": "03", "section_label": "CALC 手取りから3ステップ", "headline": "自分に合う金額の出し方", "items": [
                ("手取り月収を把握", "差引支給額＋ボーナス÷12が月平均"),
                ("10〜20%を上限ラインに", "貯蓄＋投資の合計で考える"),
                ("先取り自動引き落とし", "残ったお金ではなく最初に確保"),
            ]},
            "cta": {"summary_lines": ["金額より長く続けることが最優先", "20代5千円〜・50代3万円〜が目安", "手取りの10〜20%を貯蓄＋投資に", "生活防衛資金を確保してから"]},
        },
    },
    {
        "folder": "06_つみたて枠と成長投資枠",
        "video": "06_つみたて枠と成長投資枠_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "新NISA", "title_lines": ["つみたて枠と", "成長投資枠"], "subtitle": "初心者が迷わない2つの枠の使い分け"},
            "why": {"headline": "2つの枠は対象商品と上限が違う", "body_lines": ["つみたて＝金融庁基準の投信のみ。", "成長投資＝個別株・ETFもOK。", "併用すれば年間360万円まで非課税。"], "highlight": "つみたて120万 / 成長240万"},
            "points1": {"num": "02", "section_label": "COMPARE 違いを整理", "headline": "枠ごとの守備範囲", "items": [
                ("つみたて投資枠", "年120万円 / 投信のみ / 毎月積立向き"),
                ("成長投資枠", "年240万円 / 株・ETFもOK / スポットOK"),
                ("生涯1,800万円", "うち成長枠は最大1,200万円まで"),
            ]},
            "points2": {"num": "03", "section_label": "PATTERN 使い分け3つ", "headline": "初心者の選び方パターン", "items": [
                ("シンプル派", "つみたて枠だけ。月3〜5万円ならこれで十分"),
                ("フル積立派", "両方の枠で同じ投信を積立。管理シンプル"),
                ("コアサテライト派", "つみたて＝コア / 成長＝個別株でチャレンジ"),
            ]},
            "cta": {"summary_lines": ["つみたて枠＝年120万円・投信のみ", "成長投資枠＝年240万円・株もOK", "迷ったらつみたて枠だけでも十分", "両方で同じ投信を買うのも選択肢"]},
        },
    },
    {
        "folder": "07_全米vs全世界",
        "video": "07_全米vs全世界_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "インデックス比較", "title_lines": ["全米株式 vs", "全世界株式"], "subtitle": "VTIとオルカン、どっちを選ぶ？"},
            "why": {"headline": "投資対象の範囲がまったく違う", "body_lines": ["全米＝アメリカ4,000銘柄に集中。", "全世界＝47か国3,000銘柄に分散。", "ただし全世界も中身の6割は米国。"], "highlight": "1国集中 vs 47か国分散"},
            "points1": {"num": "02", "section_label": "COMPARE 違いを整理", "headline": "数字で比べる2つの指数", "items": [
                ("投資対象国", "全米=米国1国 / オルカン=47か国"),
                ("銘柄数", "全米=約4,000 / オルカン=約3,000"),
                ("米国比率", "全米=100% / オルカン=約60%"),
                ("信託報酬", "どちらも年0.05〜0.11%前後"),
            ]},
            "points2": {"num": "03", "section_label": "HOW 選ぶ3基準", "headline": "初心者の判断軸", "items": [
                ("米国一強を信じるか", "信じるなら全米。慎重なら全世界"),
                ("為替リスクの分散", "オルカンの方が通貨が分散される"),
                ("迷ったら全世界", "保険的に薄く広く分散できる"),
            ]},
            "cta": {"summary_lines": ["全米=米国1国に集中・成長期待大", "全世界=47か国に分散・米国6割", "コストはほぼ同水準", "迷ったら全世界（オルカン）から"]},
        },
    },
    {
        "folder": "08_日経vsTOPIX",
        "video": "08_日経vsTOPIX_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "日本株指数", "title_lines": ["日経平均と", "TOPIX"], "subtitle": "計算方法も採用銘柄も別物の2大指数"},
            "why": {"headline": "計算方法が違うので値動きの性格も違う", "body_lines": ["日経平均=株価平均型・225銘柄。", "TOPIX=時価総額加重型・約2,100銘柄。", "ニュースの「円」と「ポイント」の差。"], "highlight": "225銘柄 vs 約2,100銘柄"},
            "points1": {"num": "02", "section_label": "COMPARE 違いを整理", "headline": "2つの指数を比較", "items": [
                ("採用銘柄数", "日経=225 / TOPIX=約2,100"),
                ("計算方法", "日経=株価平均 / TOPIX=時価総額加重"),
                ("値動きの傾向", "日経=値がさ株に偏る / TOPIX=広く分散"),
            ]},
            "points2": {"num": "03", "section_label": "HOW 選ぶ3基準", "headline": "投信を選ぶときの軸", "items": [
                ("分散重視ならTOPIX", "幅広い銘柄に薄く分散できる"),
                ("成長期待なら日経", "ハイテク・値がさ株の比率が高い"),
                ("コストの低い方を選ぶ", "同じ指数連動なら信託報酬で決める"),
            ]},
            "cta": {"summary_lines": ["日経=値がさ225銘柄の株価平均", "TOPIX=約2,100銘柄の時価総額加重", "分散重視ならTOPIX", "同じ指数なら低コストを選ぶ"]},
        },
    },
    {
        "folder": "09_信託報酬の比較",
        "video": "09_信託報酬の比較_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "投信のコスト", "title_lines": ["信託報酬", "比較のコツ"], "subtitle": "コスト負けしない投信の選び方"},
            "why": {"headline": "0.1%と1%で20年後に100万円以上の差", "body_lines": ["信託報酬は保有中ずっと毎日引かれる。", "相場が下がっても引かれ続ける。", "唯一「最初から確実に抑えられる」要素。"], "highlight": "年0.9%の差 → 100万円超"},
            "points1": {"num": "02", "section_label": "IMPACT 影響度", "headline": "月3万円×20年×年利5%で試算", "items": [
                ("年0.1%", "約1,205万円（基準）"),
                ("年0.5%", "約1,158万円（-47万円）"),
                ("年1.0%", "約1,103万円（-102万円）"),
                ("年1.5%", "約1,051万円（-154万円）"),
            ]},
            "points2": {"num": "03", "section_label": "HOW 選ぶ3基準", "headline": "低コスト投信を見抜く軸", "items": [
                ("インデックスは0.2%以下", "S&P500・オルカンは0.05〜0.2%が標準"),
                ("アクティブは実績で判断", "10年以上の超過リターンを確認"),
                ("実質コストも要確認", "運用報告書の数字までチェック"),
            ]},
            "cta": {"summary_lines": ["信託報酬は毎日コツコツ引かれる", "0.9%差で20年100万円以上の差", "インデックスは0.2%以下が目安", "実質コストまで運用報告書で確認"]},
        },
    },
    {
        "folder": "10_家計の見直し",
        "video": "10_家計の見直し_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "投資の前準備", "title_lines": ["投資の前に", "家計を見直す"], "subtitle": "最初に整える6つのチェックポイント"},
            "why": {"headline": "家計に余裕がないと相場下落で売ってしまう", "body_lines": ["余剰資金で長く続けるのが大原則。", "ギリギリだと暴落時に狼狽売り。", "投資の土台は家計から作る。"], "highlight": "固定費 → 投資原資"},
            "points1": {"num": "02", "section_label": "CHECK 見直し対象6つ", "headline": "効果が大きい順に見直す", "items": [
                ("①通信費", "格安SIMで月3,000〜5,000円減"),
                ("②保険料", "重複や過剰を削減で月3,000〜10,000円減"),
                ("③サブスク", "使ってない契約を解約"),
                ("④電気ガス", "プラン乗り換えで月1,000〜3,000円減"),
            ]},
            "points2": {"num": "03", "section_label": "ORDER 取り組む順番", "headline": "家計→生活防衛→投資の順", "items": [
                ("固定費から手を付ける", "一度の見直しで毎月効果が続く"),
                ("生活防衛資金を確保", "生活費3〜12か月分を現金で"),
                ("余裕分を投資に回す", "先取り自動積立で確実に"),
            ]},
            "cta": {"summary_lines": ["家計の土台が下落耐性を作る", "通信費・保険から見直すと効果大", "生活防衛資金が先・投資はその後", "余裕分を先取りで自動積立"]},
        },
    },
    {
        "folder": "11_NISA失敗7選",
        "video": "11_NISA失敗7選_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "失敗回避", "title_lines": ["新NISA", "失敗7選"], "subtitle": "初心者がやりがちな落とし穴と対策"},
            "why": {"headline": "途中でやめると非課税メリットを活かせない", "body_lines": ["税制は強力だが「長く続けてこそ」。", "短期で売却すると恩恵を実感できず", "相場変動だけが目立つ結果に。"], "highlight": "短期売買 → 非課税枠の無駄"},
            "points1": {"num": "02", "section_label": "TOP3 影響度大の失敗", "headline": "特にハマる3つの失敗", "items": [
                ("①短期売買を繰り返す", "売却分の非課税枠は翌年復活で機会損失"),
                ("②テーマ型に集中投資", "値動きが激しく狼狽売りを誘発"),
                ("③暴落時の狼狽売り", "損失確定＋回復局面の利益も逃す"),
            ]},
            "points2": {"num": "03", "section_label": "TRAP 見落としがちな4つ", "headline": "残り4つの落とし穴", "items": [
                ("④使い切りを焦る", "無理な積立は家計を圧迫"),
                ("⑤高コスト商品を選ぶ", "長期で数百万円の差"),
                ("⑥防衛資金なしで投資", "急な出費で解約せざるを得ない"),
                ("⑦家族で同じ商品に集中", "家計全体でリスク偏り"),
            ]},
            "cta": {"summary_lines": ["長く続けてこそ非課税が活きる", "短期売買とテーマ集中は要注意", "暴落時の狼狽売りが最大の敵", "使い切りより使い続けることが大事"]},
        },
    },
    {
        "folder": "12_生活防衛資金",
        "video": "12_生活防衛資金_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "緊急資金", "title_lines": ["生活防衛資金", "いくら必要？"], "subtitle": "投資と分けて考える緊急用の現金"},
            "why": {"headline": "暴落と急な出費が重なると投資を売る羽目に", "body_lines": ["株価10〜20%下落は数年に1度。", "30〜50%級は10年に1度の頻度。", "現金があれば下落時に売らずに済む。"], "highlight": "現金 = 投資の盾"},
            "points1": {"num": "02", "section_label": "AMOUNT 必要額の目安", "headline": "職業・家族構成別の目安", "items": [
                ("独身・会社員", "生活費3〜6か月分（60〜120万円）"),
                ("共働き夫婦", "生活費3〜6か月分（60〜120万円）"),
                ("片働き＋子あり", "生活費6〜12か月分（120〜240万円）"),
                ("自営業・フリー", "生活費12か月分（240万円〜）"),
            ]},
            "points2": {"num": "03", "section_label": "WHERE 置き場所", "headline": "すぐ引き出せて元本割れしない場所", "items": [
                ("普通預金ネット銀行", "いつでも引き出せて利回りも比較的高め"),
                ("定期預金1〜3年", "一部を分散。中途解約は利息減"),
                ("個人向け国債変動10年", "1年経てば解約可。余裕分の置き場に"),
            ]},
            "cta": {"summary_lines": ["暴落と急出費が重なると致命傷", "生活費3〜12か月分が目安", "普通預金がメイン置き場所", "貯まる前のNISA並行も選択肢"]},
        },
    },
    {
        "folder": "13_20年積立シミュレーション",
        "video": "13_20年積立シミュレーション_投稿動画.mp4",
        "slides": {
            "cover": {"badge": "シミュレーション", "title_lines": ["20年積立で", "いくらになる？"], "subtitle": "月3万円・年利5%で約1,233万円の試算"},
            "why": {"headline": "毎月3万円・20年・年利5%で約1,233万円", "body_lines": ["元本720万円 → 約1.7倍に。", "運用益およそ513万円。", "後半ほど複利が雪だるま式に効く。"], "highlight": "元本720万 → 約1,233万"},
            "points1": {"num": "02", "section_label": "RATE 年利別の到達点", "headline": "月3万円×20年で年利別に試算", "items": [
                ("年1%（定期預金級）", "約795万円（運用益約75万円）"),
                ("年3%（保守的）", "約985万円（運用益約265万円）"),
                ("年5%（全世界株想定）", "約1,233万円（運用益約513万円）"),
                ("年7%（米国強気）", "約1,562万円（運用益約842万円）"),
            ]},
            "points2": {"num": "03", "section_label": "AMOUNT 月額別の到達点", "headline": "年利5%・20年で月額別に試算", "items": [
                ("月1万円", "約411万円（元本240万円）"),
                ("月3万円", "約1,233万円（元本720万円）"),
                ("月5万円", "約2,055万円（元本1,200万円）"),
                ("月10万円", "約4,110万円（元本2,400万円）"),
            ]},
            "cta": {"summary_lines": ["月3万円20年で約1,233万円の試算", "年利の差で結果は大きく変わる", "後半ほど複利の効きが加速", "新NISAなら運用益まるごと非課税"]},
        },
    },
]


def main():
    print(f"Output base: {OUT_BASE}")
    os.makedirs(OUT_BASE, exist_ok=True)
    results = []
    for art in ARTICLES:
        dir_path = os.path.join(OUT_BASE, art["folder"])
        try:
            build_article(dir_path, art["video"], art["slides"])
            results.append((art["folder"], "OK"))
            print(f"[OK] {art['folder']}")
        except Exception as e:
            results.append((art["folder"], f"ERR: {e}"))
            print(f"[ERR] {art['folder']}: {e}")
    print("\n=== RESULTS ===")
    for f, s in results:
        print(f"  {f}: {s}")
    print(f"Done. Total: {len(ARTICLES)} articles.")


if __name__ == "__main__":
    main()
