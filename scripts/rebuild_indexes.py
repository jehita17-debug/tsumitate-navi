#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
つみたてNAVI - index.html / feed.xml / sitemap.xml まるごと再生成ツール

articles/ フォルダにある記事HTMLを正として、
  - index.html の記事カード一覧
  - feed.xml（RSS）
  - sitemap.xml
を全部作り直す。

【使いどころ】
GitHub Desktop で pull したときに feed.xml / index.html / sitemap.xml が
コンフリクトしたら、どちらか片方で merge を完了させたあと、このスクリプトを
1回走らせれば「記事フォルダにある全記事」をもとに3ファイルが正しい状態に揃う。
（自動投稿で追加された記事も、ローカルで足した記事も、両方ちゃんと載る）

外部ライブラリ不要。Python標準ライブラリだけで動く。

使い方（C:\\GITHub\\tsumitate-navi など、リポジトリ直下で）:
    python scripts/rebuild_indexes.py
"""
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 同じ scripts/ ディレクトリの共有モジュールを読めるようにする
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb_icons import category_icon

ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIR = ROOT / "articles"
INDEX = ROOT / "index.html"
FEED = ROOT / "feed.xml"
SITEMAP = ROOT / "sitemap.xml"
VIDEOS_DIR = ROOT / "videos"
TOPICS_FILE = ROOT / "scripts" / "topics.json"

JST = timezone(timedelta(hours=9))
SITE_URL = "https://tsumitate-navi.net"

START_MARKER = "<!-- ▼▼▼ 自動生成記事はここに追加されます ▼▼▼ -->"
END_MARKER = "<!-- ▲▲▲ 記事カードのテンプレ ▲▲▲ -->"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def category_thumb_map() -> dict:
    """topics.json から カテゴリ→サムネクラス の対応表を作る。"""
    m = {}
    try:
        topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))["topics"]
        for t in topics:
            m.setdefault(t["category"], t.get("thumb_class", "thumb-nisa"))
    except Exception:
        pass
    # 念のため既定値も補完
    m.setdefault("資産形成", "thumb-nisa")
    return m


def first(pattern, html, default=""):
    mm = re.search(pattern, html, re.DOTALL)
    return mm.group(1).strip() if mm else default


def collect_articles():
    """記事HTMLを読み、日付降順で (name, date, category, title_raw, excerpt_raw) を返す。"""
    items = []
    for p in ARTICLES_DIR.glob("*.html"):
        if p.stem.startswith("_"):
            continue
        html = p.read_text(encoding="utf-8")
        date_m = re.match(r"(\d{4})-(\d{2})-(\d{2})", p.stem)
        if not date_m:
            continue
        date_iso = "-".join(date_m.groups())
        # title は <h1>（HTMLエスケープ済みの生のまま使う）。無ければ <title> から
        title = first(r"<h1[^>]*>(.*?)</h1>", html)
        if not title:
            t = first(r"<title>(.*?)</title>", html)
            title = t.split(" | ")[0]
        # index カード・feed の抜粋は meta description が正（lead は長文の場合がある）
        excerpt = first(r'<meta name="description" content="(.*?)"', html)
        if not excerpt:
            excerpt = first(r'<p class="lead">(.*?)</p>', html)
        category = first(r'<span class="category-badge">(.*?)</span>', html, "投資")
        items.append({
            "name": p.name, "date": date_iso, "category": category,
            "title": title, "excerpt": excerpt,
        })
    items.sort(key=lambda x: (x["date"], x["name"]), reverse=True)
    return items


def rebuild_index(items, thumb_map):
    html = INDEX.read_text(encoding="utf-8")
    if START_MARKER not in html or END_MARKER not in html:
        print("[skip] index.html にマーカーが見つからないため再生成しません")
        return
    cards = []
    for it in items:
        thumb = thumb_map.get(it["category"], "thumb-nisa")
        date_dot = it["date"].replace("-", ".")
        cards.append(
            "      <article class=\"article-card\">\n"
            f"        <a href=\"articles/{it['name']}\">\n"
            f"          <div class=\"article-thumb {thumb}\">\n"
            f"            <span class=\"article-thumb-label\">{it['category']}</span>\n"
            f"            {category_icon(it['category'])}\n"
            "          </div>\n"
            "          <div class=\"article-body\">\n"
            f"            <div class=\"article-date\">{date_dot}</div>\n"
            f"            <h3 class=\"article-title\">{it['title']}</h3>\n"
            f"            <p class=\"article-excerpt\">{it['excerpt']}</p>\n"
            "          </div>\n"
            "        </a>\n"
            "      </article>"
        )
    block = (START_MARKER + "\n\n" + "\n\n".join(cards) + "\n\n      " + END_MARKER)
    new_html = re.sub(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        lambda _: block, html, count=1, flags=re.DOTALL,
    )
    INDEX.write_text(new_html, encoding="utf-8")
    print(f"[ok] index.html 再生成（{len(items)}記事）")


def rebuild_feed(items):
    rss_items = []
    for it in items[:20]:
        y, mo, d = it["date"].split("-")
        pub = datetime(int(y), int(mo), int(d), 7, 0, tzinfo=JST).strftime(
            "%a, %d %b %Y %H:%M:%S +0900")
        # title/excerpt は生(エスケープ済み)なので一旦戻してから再エスケープ
        title = unescape(it["title"])
        desc = unescape(it["excerpt"])
        rss_items.append(f"""    <item>
      <title>{esc(title)}</title>
      <link>{SITE_URL}/articles/{it['name']}</link>
      <description>{esc(desc)}</description>
      <pubDate>{pub}</pubDate>
      <guid>{SITE_URL}/articles/{it['name']}</guid>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>つみたてNAVI</title>
    <link>{SITE_URL}/</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
    <description>投資初心者のための情報サイト。NISA・つみたて投資・米国株・日本株を毎朝7時に配信。</description>
    <language>ja</language>
    <lastBuildDate>{datetime.now(JST).strftime('%a, %d %b %Y %H:%M:%S +0900')}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>
"""
    FEED.write_text(rss, encoding="utf-8")
    print("[ok] feed.xml 再生成")


def rebuild_sitemap(items):
    today = datetime.now(JST).strftime("%Y-%m-%d")
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    static_pages = [
        ("about.html", "monthly", "0.5"),
        ("privacy.html", "yearly", "0.3"),
        ("disclaimer.html", "yearly", "0.3"),
        ("contact.html", "monthly", "0.4"),
    ]
    for page, freq, pri in static_pages:
        urls.append(f"  <url><loc>{SITE_URL}/{page}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>")
    if (VIDEOS_DIR / "index.html").exists():
        urls.append(f"  <url><loc>{SITE_URL}/videos/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>")
    for it in items:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{it['name']}</loc><lastmod>{it['date']}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""
    SITEMAP.write_text(sitemap, encoding="utf-8")
    print("[ok] sitemap.xml 再生成")


def unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'"))


def main():
    items = collect_articles()
    if not items:
        print("[warn] articles/ に記事が見つかりません")
        return
    thumb_map = category_thumb_map()
    rebuild_index(items, thumb_map)
    rebuild_feed(items)
    rebuild_sitemap(items)
    print(f"[done] 合計 {items[0]['date']} 〜 {items[-1]['date']} の {len(items)} 記事で再構築しました")


if __name__ == "__main__":
    main()
