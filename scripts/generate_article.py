#!/usr/bin/env python3
"""
つみたてNAVI - 毎日の記事自動生成スクリプト

GitHub Actionsから毎朝7時(JST)に呼ばれ、
Claude APIを使って投資記事を1本生成し、HTMLとして保存する。
さらに index.html / feed.xml / sitemap.xml も更新する。
"""

import json
import os
import re
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("anthropic SDK not installed. Run: pip install anthropic")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
ARTICLES_DIR = ROOT / "articles"
TEMPLATE = ARTICLES_DIR / "_template.html"
INDEX = ROOT / "index.html"
FEED = ROOT / "feed.xml"
SITEMAP = ROOT / "sitemap.xml"
TOPICS_FILE = ROOT / "scripts" / "topics.json"

JST = timezone(timedelta(hours=9))
SITE_URL = os.environ.get("SITE_URL", "https://jehita17-debug.github.io/tsumitate-navi")

# ---------------------------------------------------------------------
# トピック選択
# ---------------------------------------------------------------------
def pick_topic():
    """まだ書いていないトピックを優先して選ぶ"""
    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))["topics"]
    existing = {p.stem for p in ARTICLES_DIR.glob("*.html") if not p.stem.startswith("_")}
    # 既存タイトルキーワードと一致しないものを優先
    candidates = []
    for t in topics:
        slug_seed = slugify(t["title_seed"])
        if not any(slug_seed in name for name in existing):
            candidates.append(t)
    pool = candidates if candidates else topics
    return random.choice(pool)


def slugify(text: str) -> str:
    """日本語タイトルから簡易スラグを作る"""
    # ローマ字化は厳密ではないので、英数とハイフンに正規化
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:40] or "article"

# ---------------------------------------------------------------------
# Claude APIで記事本文を生成
# ---------------------------------------------------------------------
SYSTEM_PROMPT = """あなたは投資初心者向けの記事を書くプロのライターです。
日本の投資制度（特にNISA・つみたて投資・米国株・日本株）に詳しく、
専門用語をやさしい言葉に置き換え、図表・具体例・数値シミュレーションを交えて
わかりやすく解説します。

出力ルール：
1. 出力は HTML 断片のみ。<!DOCTYPE> や <html> や <body> タグは含めない。
2. 記事本文は <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>, <blockquote> を使う。
3. 構成：
   - 最初に <div class="point-box"> で「この記事でわかること」をリスト化
   - <h2> 3〜4セクション、各セクションに <h3> サブ見出しを設ける
   - 数値比較がある場合は <table> を使う
   - 重要な引用には <blockquote> を使う
   - 最後に <div class="point-box"> で「まとめ」をリスト化
   - 途中に <div class="affiliate-card"> を1〜2枚挿入（A8.net広告枠用）
4. 全体の分量は 1,800〜2,300文字。
5. 必ず日本語で書く。
6. 「投資勧誘ではない」「価格変動リスクがある」「自己責任」の注意喚起を本文に自然に織り込む。
7. 誇大な表現・断定的な利回り保証は禁止。

アフィリエイトカード（広告枠）のテンプレートは以下：
<div class="affiliate-card">
  <h4>（広告の見出し）</h4>
  <p>（本文・約60〜100文字）</p>
  <a href="#" class="affiliate-btn">（CTAボタン文言）</a>
  <p style="margin-top:12px; font-size:12px; color:#9ca3af;">※A8.netのアフィリエイトリンクを貼り替えてください</p>
</div>
"""

def generate_body(topic: dict) -> tuple[str, str, str]:
    """Claude APIで本文を生成し、(title, excerpt, body_html) を返す"""
    client = Anthropic()
    user_msg = f"""今日のテーマ: 「{topic['title_seed']}」
カテゴリ: {topic['category']}

このテーマで、投資初心者向けの記事をHTMLで書いてください。
記事タイトルと冒頭リード文（80〜120文字）も含めて、以下のJSON形式で返してください：

```json
{{
  "title": "（記事タイトル）",
  "excerpt": "（リード文・80〜120文字）",
  "body_html": "（記事本文のHTML断片）"
}}
```

JSONブロック以外は出力しないでください。
"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = resp.content[0].text
    # ```json ... ``` を取り出す
    m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    payload = m.group(1) if m else raw
    data = json.loads(payload)
    return data["title"], data["excerpt"], data["body_html"]

# ---------------------------------------------------------------------
# HTMLファイル書き出し
# ---------------------------------------------------------------------
def write_article(date_str: str, slug: str, title: str, excerpt: str,
                  body_html: str, topic: dict) -> Path:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    html = (tpl
            .replace("{{TITLE}}", title)
            .replace("{{EXCERPT}}", excerpt)
            .replace("{{KEYWORDS}}", topic.get("keywords", ""))
            .replace("{{SLUG}}", f"{date_str}-{slug}")
            .replace("{{CATEGORY}}", topic["category"])
            .replace("{{DATE}}", date_str.replace("-", "."))
            .replace("{{CONTENT}}", body_html))
    out = ARTICLES_DIR / f"{date_str}-{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] wrote {out.name}")
    return out

# ---------------------------------------------------------------------
# index.htmlに新しい記事カードを差し込む
# ---------------------------------------------------------------------
def update_index(date_str: str, slug: str, title: str, excerpt: str, topic: dict):
    idx = INDEX.read_text(encoding="utf-8")
    card = f"""      <article class=\"article-card\">
        <a href=\"articles/{date_str}-{slug}.html\">
          <div class=\"article-thumb {topic['thumb_class']}\">
            <span class=\"article-thumb-label\">{topic['category']}</span>
            <span>N</span>
          </div>
          <div class=\"article-body\">
            <div class=\"article-date\">{date_str.replace('-', '.')}</div>
            <h3 class=\"article-title\">{title}</h3>
            <p class=\"article-excerpt\">{excerpt}</p>
          </div>
        </a>
      </article>

"""
    marker = "<!-- ▼▼▼ 自動生成記事はここに追加されます ▼▼▼ -->\n"
    idx = idx.replace(marker, marker + "\n" + card)
    INDEX.write_text(idx, encoding="utf-8")
    print("[ok] updated index.html")

# ---------------------------------------------------------------------
# RSSとsitemapを更新
# ---------------------------------------------------------------------
def update_feed_and_sitemap():
    articles = sorted(
        [p for p in ARTICLES_DIR.glob("*.html") if not p.stem.startswith("_")],
        reverse=True,
    )

    # ---- RSS feed ----
    rss_items = []
    for p in articles[:20]:
        body = p.read_text(encoding="utf-8")
        title_m = re.search(r"<title>([^<]+)</title>", body)
        desc_m = re.search(r'<meta name="description" content="([^"]+)"', body)
        if not title_m: continue
        title = title_m.group(1).split(" | ")[0]
        desc = desc_m.group(1) if desc_m else ""
        date_m = re.match(r"(\d{4})-(\d{2})-(\d{2})", p.stem)
        if date_m:
            y, mo, d = date_m.groups()
            pub_date = datetime(int(y), int(mo), int(d), 7, 0, tzinfo=JST).strftime(
                "%a, %d %b %Y %H:%M:%S +0900"
            )
        else:
            pub_date = datetime.now(JST).strftime("%a, %d %b %Y %H:%M:%S +0900")
        rss_items.append(f"""    <item>
      <title>{esc(title)}</title>
      <link>{SITE_URL}/articles/{p.name}</link>
      <description>{esc(desc)}</description>
      <pubDate>{pub_date}</pubDate>
      <guid>{SITE_URL}/articles/{p.name}</guid>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>つみたてNAVI</title>
    <link>{SITE_URL}/</link>
    <description>投資初心者のための情報サイト。NISA・つみたて投資・米国株・日本株を毎朝7時に配信。</description>
    <language>ja</language>
    <lastBuildDate>{datetime.now(JST).strftime('%a, %d %b %Y %H:%M:%S +0900')}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>
"""
    FEED.write_text(rss, encoding="utf-8")
    print("[ok] updated feed.xml")

    # ---- sitemap ----
    today = datetime.now(JST).strftime("%Y-%m-%d")
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>"]
    for page in ["about.html", "privacy.html", "disclaimer.html", "contact.html"]:
        urls.append(f"  <url><loc>{SITE_URL}/{page}</loc><lastmod>{today}</lastmod><priority>0.5</priority></url>")
    for p in articles:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{p.name}</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""
    SITEMAP.write_text(sitemap, encoding="utf-8")
    print("[ok] updated sitemap.xml")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))

# ---------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------
def main():
    today = datetime.now(JST).strftime("%Y-%m-%d")
    topic = pick_topic()
    print(f"[info] today={today} topic={topic['title_seed']}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        title, excerpt, body = generate_body(topic)
    else:
        # API キーがなければダミー記事
        print("[warn] ANTHROPIC_API_KEY not set, using dummy article body")
        title = topic["title_seed"]
        excerpt = f"{topic['category']}の基礎をやさしく解説します。"
        body = f"""<div class="point-box"><div class="point-box-title">この記事でわかること</div><ul><li>{topic['title_seed']}の基本</li></ul></div>
<h2>はじめに</h2><p>（本文は ANTHROPIC_API_KEY を設定すると自動生成されます）</p>
<div class="point-box"><div class="point-box-title">まとめ</div><ul><li>仕組みを理解してから始めよう</li></ul></div>"""

    slug = slugify(topic["title_seed"])
    write_article(today, slug, title, excerpt, body, topic)
    update_index(today, slug, title, excerpt, topic)
    update_feed_and_sitemap()
    print("[done]")


if __name__ == "__main__":
    main()
