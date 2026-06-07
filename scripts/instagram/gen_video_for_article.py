#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
つみたてNAVI - 記事 → Instagram投稿素材 自動生成パイプライン

1記事（デフォルトは最新記事）を読み込み、
Claude APIで「5枚カルーセル用のスライド内容」をJSONで生成し、
slide_render.py でカルーセル画像5枚＋15秒MP4（リール用）を作る。
Instagram投稿用のキャプション（caption.txt）も書き出す。

出力先: instagram/<記事スラッグ>/
  01_cover.png 〜 05_cta.png  … カルーセル投稿用（1080×1080）
  <slug>.mp4                  … リール/動画投稿用（15秒）
  caption.txt                … 投稿キャプション＋ハッシュタグ
  meta.json                  … 管理用メタ情報

※記事ページへの埋め込みやサイト掲載は行わない（あくまでInstagram投稿用素材）。

GitHub Actions（毎朝7時）から generate_article.py の直後に呼ばれる想定。

使い方:
  python scripts/instagram/gen_video_for_article.py            # 最新記事の素材を作る
  python scripts/instagram/gen_video_for_article.py <html path># 指定記事の素材を作る
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slide_render as sr  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARTICLES_DIR = ROOT / "articles"
OUT_DIR = ROOT / "instagram"
JST = timezone(timedelta(hours=9))
SITE_URL = os.environ.get("SITE_URL", "https://tsumitate-navi.net")

# カテゴリ別ハッシュタグ
BASE_TAGS = ["#投資", "#投資初心者", "#資産運用", "#お金の勉強", "#つみたてNAVI"]
CAT_TAGS = {
    "NISA": ["#NISA", "#新NISA"],
    "つみたて投資": ["#つみたて投資", "#積立投資"],
    "米国株": ["#米国株", "#SP500"],
    "日本株": ["#日本株", "#高配当株"],
    "資産形成": ["#資産形成", "#家計管理"],
    "基礎解説": ["#投資の基本", "#投資勉強"],
    "FX・為替": ["#FX", "#為替", "#円安"],
    "コモディティ": ["#金投資", "#ゴールド", "#コモディティ"],
    "仮想通貨": ["#仮想通貨", "#暗号資産", "#ビットコイン"],
    "世界経済": ["#世界経済", "#地政学リスク"],
}


# ---------------------------------------------------------------------
# 記事HTMLのパース
# ---------------------------------------------------------------------
def latest_article() -> Path:
    cands = sorted(
        [p for p in ARTICLES_DIR.glob("*.html") if not p.stem.startswith("_")],
        reverse=True,
    )
    if not cands:
        raise SystemExit("記事が見つかりません")
    return cands[0]


def strip_tags(html: str) -> str:
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&apos;", "'").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", text).strip()


def parse_article(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    title = strip_tags(title_m.group(1)) if title_m else path.stem
    cat_m = re.search(r'<span class="category-badge">(.*?)</span>', html, re.DOTALL)
    category = strip_tags(cat_m.group(1)) if cat_m else "投資"
    lead_m = re.search(r'<p class="lead">(.*?)</p>', html, re.DOTALL)
    lead = strip_tags(lead_m.group(1)) if lead_m else ""
    body_m = re.search(r'<div class="article-body-content">(.*?)<hr class="article-divider">',
                       html, re.DOTALL)
    body_html = body_m.group(1) if body_m else html
    # 広告カードは要約に不要なので落とす
    body_html = re.sub(r'<div class="affiliate-card">.*?</div>\s*', "", body_html, flags=re.DOTALL)
    body_text = strip_tags(body_html)
    date_m = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
    date = date_m.group(1) if date_m else datetime.now(JST).strftime("%Y-%m-%d")
    return {"slug": path.stem, "title": title, "category": category,
            "lead": lead, "body_text": body_text, "date": date, "path": path}


# ---------------------------------------------------------------------
# Claudeでスライド内容を生成
# ---------------------------------------------------------------------
SLIDE_SYSTEM = """あなたはInstagram向けの解説カルーセル（縦長5枚）の構成作家です。
与えられた投資記事を、初心者がスマホでサッと理解できる5枚のスライドに要約します。
出力は必ず次のJSONスキーマのみ（前後に文章やコードフェンスを付けない）。

{
  "cover": {
    "badge": "ジャンル名（6文字以内・例:基礎解説/FX入門/金とは）",
    "title_lines": ["タイトル上段(全角8文字以内)", "タイトル下段(全角8文字以内)"],
    "subtitle": "ひとことサブタイトル(全角28文字以内)"
  },
  "why": {
    "headline": "なぜ重要かの一文(全角28文字以内)",
    "body_lines": ["補足1(全角24文字以内)", "補足2", "補足3"],
    "highlight": "対比キーワード（必ず「A → B」の形式・各辺全角8文字以内）"
  },
  "points1": {
    "num": "02",
    "section_label": "英大文字ラベル＋日本語(例:BASIC 基本)",
    "headline": "見出し(全角16文字以内)",
    "items": [["小見出し(全角10文字以内)", "説明(全角28文字以内)"], ["..", ".."], ["..", ".."]]
  },
  "points2": {
    "num": "03",
    "section_label": "英大文字ラベル＋日本語(例:HOW 選び方)",
    "headline": "見出し(全角16文字以内)",
    "items": [["小見出し", "説明"], ["..", ".."], ["..", ".."]]
  },
  "cta": {
    "summary_lines": ["まとめ1(全角22文字以内)", "まとめ2", "まとめ3", "まとめ4"]
  }
}

ルール:
- 文字数上限は厳守。はみ出すと画像からあふれる。
- points1/points2 の items は各3〜4個。
- FX・仮想通貨・コモディティ・レバレッジの話題では、必ずどこかでリスク（価格変動・損失）に触れる。
- 中東情勢・地政学が記事に出てくる場合は、その因果（緊張→原油高→金は安全資産 等）を1スライドに織り込む。
- 誇大表現・利回り保証は禁止。中立でやさしいトーン。日本語で書く。
"""


def slides_via_claude(art: dict) -> dict:
    from anthropic import Anthropic
    client = Anthropic()
    user = f"""記事タイトル: {art['title']}
カテゴリ: {art['category']}
リード文: {art['lead']}

記事本文（抜粋）:
{art['body_text'][:3500]}

この記事を5枚スライドのJSONにしてください。"""
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        system=SLIDE_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(m.group(0) if m else raw)
    return normalize_slides(data, art)


def normalize_slides(data: dict, art: dict) -> dict:
    """欠損や型のゆらぎを吸収して描画関数が必ず動く形にする。"""
    def lines(v, n=None):
        if isinstance(v, str):
            v = [v]
        v = [str(x) for x in (v or [])]
        return v[:n] if n else v

    cover = data.get("cover", {})
    title_lines = lines(cover.get("title_lines") or [art["title"][:8], art["title"][8:16]], 2)
    title_lines = [t for t in title_lines if t] or [art["title"][:8]]
    why = data.get("why", {})
    p1 = data.get("points1", {})
    p2 = data.get("points2", {})
    cta = data.get("cta", {})

    def items(v):
        out = []
        for it in (v or []):
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                out.append([str(it[0]), str(it[1])])
            elif isinstance(it, dict):
                out.append([str(it.get("title", "")), str(it.get("desc", ""))])
        return out[:4] or [["ポイント", "記事本文をご覧ください"]]

    hl = why.get("highlight") or "仕組み → 理解"
    if "→" not in hl:
        hl = hl + " → 理解"

    return {
        "cover": {
            "badge": str(cover.get("badge") or art["category"])[:8],
            "title_lines": title_lines,
            "subtitle": str(cover.get("subtitle") or art["lead"])[:30],
        },
        "why": {
            "headline": str(why.get("headline") or art["lead"] or art["title"]),
            "body_lines": lines(why.get("body_lines") or [art["lead"]], 3),
            "highlight": hl,
        },
        "points1": {
            "num": "02",
            "section_label": str(p1.get("section_label") or "POINT ポイント"),
            "headline": str(p1.get("headline") or "押さえる基本"),
            "items": items(p1.get("items")),
        },
        "points2": {
            "num": "03",
            "section_label": str(p2.get("section_label") or "HOW 実践"),
            "headline": str(p2.get("headline") or "実践のヒント"),
            "items": items(p2.get("items")),
        },
        "cta": {
            "summary_lines": lines(cta.get("summary_lines") or [art["lead"]], 4),
        },
    }


def slides_fallback(art: dict) -> dict:
    """APIキーが無いときの簡易フォールバック（記事構造から機械的に作る）。"""
    html = art["path"].read_text(encoding="utf-8")
    ul_items = re.findall(r"<li[^>]*>(.*?)</li>", html, re.DOTALL)
    ul_items = [strip_tags(x) for x in ul_items if strip_tags(x)]
    h2 = [strip_tags(x) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)]
    pts1 = [[s[:10], s] for s in ul_items[:3]] or [["要点", art["lead"]]]
    pts2 = [[s[:10], s] for s in (h2[:3] or ul_items[3:6])] or [["詳細", "本文参照"]]
    raw = {
        "cover": {"badge": art["category"], "title_lines": [art["title"][:8], art["title"][8:16]],
                  "subtitle": art["lead"]},
        "why": {"headline": art["lead"] or art["title"], "body_lines": ul_items[:3],
                "highlight": "仕組み → 理解"},
        "points1": {"section_label": "POINT 要点", "headline": "この記事の要点", "items": pts1},
        "points2": {"section_label": "TOPIC 内容", "headline": "扱うテーマ", "items": pts2},
        "cta": {"summary_lines": ul_items[-4:] or [art["lead"]]},
    }
    return normalize_slides(raw, art)


# ---------------------------------------------------------------------
# Instagram投稿キャプション
# ---------------------------------------------------------------------
def make_caption(art: dict) -> str:
    tags = BASE_TAGS + CAT_TAGS.get(art["category"], [])
    return (
        f"{art['title']}\n\n"
        f"{art['lead']}\n\n"
        "👉 詳しい解説はプロフィールのリンク（ブログ）から\n"
        f"{SITE_URL}/articles/{art['slug']}.html\n\n"
        "※投資は自己責任で。元本保証ではありません。\n\n"
        + " ".join(tags)
    )


# ---------------------------------------------------------------------
# 1記事のInstagram素材を生成
# ---------------------------------------------------------------------
def process_article(target: Path) -> str:
    """1記事→カルーセル画像5枚＋15秒MP4＋caption.txt＋meta.json。slugを返す。"""
    art = parse_article(target)
    print(f"[info] article = {art['slug']} / {art['title']}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            slides = slides_via_claude(art)
        except Exception as e:
            print(f"[warn] Claude生成に失敗→フォールバック: {e}")
            slides = slides_fallback(art)
    else:
        print("[warn] ANTHROPIC_API_KEY未設定→フォールバックでスライド生成")
        slides = slides_fallback(art)

    out_dir = OUT_DIR / art["slug"]
    video_name = f"{art['slug']}.mp4"
    sr.build_article_assets(str(out_dir), video_name, slides)
    print(f"[ok] generated カルーセル5枚 + {video_name}")

    (out_dir / "caption.txt").write_text(make_caption(art), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({
        "slug": art["slug"], "title": art["title"], "category": art["category"],
        "date": art["date"], "video": f"{art['slug']}/{video_name}",
    }, ensure_ascii=False), encoding="utf-8")
    print("[ok] wrote caption.txt + meta.json")
    return art["slug"]


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_article()
    process_article(target)
    print("[done]")


if __name__ == "__main__":
    main()
