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
SITE_URL = os.environ.get("SITE_URL", "https://tsumitate-navi.net")
SITE_NAME = "つみたてNAVI"
OGP_IMAGE = f"{SITE_URL}/ogp.png"

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
日本の投資制度（NISA・つみたて投資・米国株・日本株・iDeCo）に加えて、
投資信託・ETF・債券などの基礎、FX（為替）、金・銀・原油などのコモディティ、
仮想通貨（暗号資産）、そして中東情勢などの地政学リスクが市場に与える影響まで、
幅広いテーマをカバーします。専門用語をやさしい言葉に置き換え、
図表・具体例・数値シミュレーションを交えてわかりやすく解説します。

【テーマ別の注意（重要）】
- FX・仮想通貨・コモディティ（金銀原油）・レバレッジ取引を扱う回では、
  「価格変動が大きい」「レバレッジは損失も拡大する」「短期売買は初心者向きではない」
  といったリスクを、本文の早い段階でやさしく、しかし明確に伝えること。
  本サイトの主軸は長期・積立・分散である点に触れ、これらは「まず仕組みを知る」ための
  解説であるという中立的なスタンスを保つこと。
- 中東情勢・地政学リスクに触れる場合は、特定の最新ニュースや日付・固定の価格を
  断定しないこと（情報が古くなる恐れがあるため）。代わりに「なぜ・どういう経路で」
  価格が動くのかという普遍的な仕組みを説明する。例：
  「中東で緊張が高まると→原油の供給不安→原油高→インフレ懸念→金は安全資産として
  買われやすい／株式は不安定になりやすい」といった因果の流れを図解的に解説する。
- keywordsに「中東情勢」「地政学リスク」が含まれる回、または金・銀・原油・為替・
  仮想通貨がテーマの回では、本文中に
  <h2>中東情勢など地政学リスクが価格に与える影響</h2> のセクションを1つ設け、
  上記の因果メカニズムをやさしく解説すること。

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

【広告カードの出し分けルール】
本サイトは以下の案件と提携中（マネックス証券=ASP「アクセストレード」、DMM系=A8.net）。記事テーマに応じて出し分けること。
※マネックス証券を主力とし、サイト全体でマネックス証券の露出がDMM系より多くなるようにすること（迷ったらマネックス証券を1枚目に置く）。

■ 案件D: マネックス証券（NISA・投信・米国株・日本株・iDeCoの総合ネット証券）★主力
- 訴求軸：新NISA（つみたて投資枠・成長投資枠）対応、投資信託100円から、米国株の取扱銘柄が豊富、日本株・米国株とも1株（単元未満株「ワン株」）から購入可、クレカ積立でポイント還元、iDeCo対応、口座開設・維持費は無料
- クレカ積立（投信）に対応しているので、つみたて訴求もしてよい
- 該当テーマ：NISA・つみたて・投資信託・ETF・米国株・日本株・個別株・iDeCo・配当・基礎解説・家計など大半のテーマ

■ 案件A: DMM 株（株式現物・単元未満株・NISA成長投資枠）
- 訴求軸：日本株、米国株（CFD）、1株から買える単元未満株、NISA成長投資枠、シンプルな取引ツール
- クレカ積立（投信）は非対応。クレカ積立を強く推す訴求は書かないこと
- 該当テーマ：NISA・iDeCo・投資信託・ETF・株・債券などの基礎・つみたて・個別株・信託報酬・家計見直し 等

■ 案件B: TOSSY（DMM.com証券のオールインワン取引アプリ）
- 訴求軸：株式・株価指数（S&P500・日経・TOPIX等のCFD）・FX（為替）・暗号資産が1アプリで完結
- 特典訴求：新規アカウント登録で5,000円相当プレゼント
- 該当テーマ：株価指数・米国市場全般・FX（為替）・仮想通貨（暗号資産）・複数資産の分散

■ 案件C: DMM CFD（CFDで金・銀・原油などの商品や株価指数に投資できる）
- 訴求軸：スプレッド業界最狭水準・取引手数料0円・全額信託保全・初心者でも始めやすい
- 該当テーマ：金（ゴールド）・銀・プラチナ・原油などのコモディティ、商品価格、地政学リスクで動く資産

【配置ルール】※マネックス証券を最優先。サイト全体でマネックス証券>DMM系の比率を保つこと。
- NISA・つみたて・投信・ETF・米国株・日本株・債券・個別株・iDeCo・配当・基礎解説・家計など（=大半の記事）：1枚目=マネックス証券、2枚目=DMM株（2枚ともマネックス証券でも可。2枚目は別ボタン文言で）
- FX・仮想通貨・株価指数・複数資産が記事の主題：1枚目=マネックス証券（米国株・投信の文脈）、2枚目=TOSSY
- 金・銀・プラチナ・原油などコモディティが記事の主題：1枚目=マネックス証券（投信・分散の文脈）、2枚目=DMM CFD
- 中東情勢・地政学リスクが記事の主題：1枚目=DMM CFD（金・原油の文脈）、2枚目=マネックス証券（長期分散の文脈）
- ※マネックス証券は現物の証券口座。FX・仮想通貨・CFDそのものの取引主体としては訴求しないこと（あくまでNISA・投信・米国株など現物の文脈で出す）
- ※FX・仮想通貨・コモディティのカードでは、広告文でもレバレッジ・価格変動リスクに必ず一言触れること

【マネックス証券カードのテンプレート】★主力（コピペして使用、リンク・referrerpolicy・計測imgは絶対変更不可）
<div class="affiliate-card">
  <h4>（記事テーマに合わせた広告見出し。末尾に【マネックス証券】を付けると分かりやすい）</h4>
  <p>（本文・約60〜100文字。マネックス証券の「新NISA対応」「投資信託100円から」「米国株の取扱が豊富」「日本株・米国株を1株（ワン株）から」「クレカ積立でポイント還元」「口座開設・維持費無料」のいずれかに触れる）</p>
  <a href="https://h.accesstrade.net/sp/cc?rk=010072vk00otc5" class="affiliate-btn" target="_blank" rel="nofollow sponsored noopener" referrerpolicy="no-referrer-when-downgrade">マネックス証券の口座開設を見る(PR)</a>
  <img src="https://h.accesstrade.net/sp/rr?rk=010072vk00otc5" width="1" height="1" border="0" alt="" style="display:none;">
  <p style="margin-top:12px; font-size:12px; color:#9ca3af;">※本リンクはアフィリエイト広告（PR）を含みます。投資にはリスクがあり、元本は保証されません。</p>
</div>

【DMM株カードのテンプレート】（コピペして使用、リンクは絶対変更不可）
<div class="affiliate-card">
  <h4>（記事テーマに合わせた広告見出し）</h4>
  <p>（本文・約60〜100文字。DMM株の「1株から購入できる単元未満株」「NISA成長投資枠対応」「シンプルな取引ツール」「サポート充実」のいずれかに触れる）</p>
  <a href="https://px.a8.net/svt/ejp?a8mat=4B3XB7+8GTZA2+1WP2+15R4NM" class="affiliate-btn" target="_blank" rel="nofollow sponsored noopener">DMM 株の口座開設を見る(PR)</a>
  <img border="0" width="1" height="1" src="https://www19.a8.net/0.gif?a8mat=4B3XB7+8GTZA2+1WP2+15R4NM" alt="" style="display:none;">
  <p style="margin-top:12px; font-size:12px; color:#9ca3af;">※本リンクはアフィリエイト広告（PR）を含みます。投資にはリスクがあり、元本は保証されません。</p>
</div>

【TOSSYカードのテンプレート】（コピペして使用、リンクは絶対変更不可）
<div class="affiliate-card">
  <h4>（記事テーマに合わせた広告見出し）</h4>
  <p>（本文・約60〜100文字。TOSSYの「株式・株価指数・FX・暗号資産がワンアプリで完結」「新規登録で5,000円相当プレゼント」のいずれかに触れる）</p>
  <a href="https://px.a8.net/svt/ejp?a8mat=4B3XB7+82JKRE+1WP2+1HPXWX" class="affiliate-btn" target="_blank" rel="nofollow sponsored noopener">TOSSYで取引してみる(PR)</a>
  <img border="0" width="1" height="1" src="https://www14.a8.net/0.gif?a8mat=4B3XB7+82JKRE+1WP2+1HPXWX" alt="" style="display:none;">
  <p style="margin-top:12px; font-size:12px; color:#9ca3af;">※本リンクはアフィリエイト広告（PR）を含みます。投資にはリスクがあり、元本は保証されません。</p>
</div>

【DMM CFDカードのテンプレート】（コピペして使用、リンクは絶対変更不可。金・銀・原油などコモディティ／地政学テーマ用）
<div class="affiliate-card">
  <h4>（記事テーマに合わせた広告見出し）</h4>
  <p>（本文・約60〜100文字。DMM CFDの「金・原油などの商品に少額から投資できる」「スプレッド業界最狭水準・手数料0円」「全額信託保全」のいずれかに触れる。CFDはレバレッジがかかり価格変動リスクが大きい点に一言触れること）</p>
  <a href="https://px.a8.net/svt/ejp?a8mat=4B3XB7+6SP76I+1WP2+NZ4J7" class="affiliate-btn" target="_blank" rel="nofollow sponsored noopener">DMM CFDを詳しく見る(PR)</a>
  <p style="margin-top:12px; font-size:12px; color:#9ca3af;">※本リンクはアフィリエイト広告（PR）を含みます。CFDはレバレッジ取引であり、相場急変時には元本を超える損失が生じる可能性があります。</p>
</div>

【重要・厳守事項】
- <a href="..."> のURL、計測用 <img> タグ、最下部の注意書き <p> は絶対に変更しないこと
- 変更してよいのは <h4> と最初の <p>（本文）のみ
- ボタン文言は基本「マネックス証券の口座開設を見る(PR)」「DMM 株の口座開設を見る(PR)」「TOSSYで取引してみる(PR)」「DMM CFDを詳しく見る(PR)」とするが、同じ案件を2枚使う場合は文言を変えて良い。ただし末尾の (PR) は必ず残す
- マネックス証券はアクセストレード案件（rk=010072vk00otc5）。リンク・計測imgに加え referrerpolicy="no-referrer-when-downgrade" 属性も必ず残すこと
- DMM株・TOSSY・DMM CFDは同じDMM.com証券グループだが別案件。a8matタグは絶対に取り違えないこと（DMM株=8GTZA2 / TOSSY=82JKRE / DMM CFD=6SP76I）
- DMM CFDカードには現状 計測用 <img> ピクセルを入れていない（クリック計測はリンクで行われる）。圭太さんがA8管理画面から正式な計測タグを取得したら差し込む
- DMM株はクレカ積立（投信）非対応。クレカ積立を強く推す訴求は書かないこと
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
        max_tokens=5120,
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
    # JSON-LDとmetaタグでHTMLエスケープが必要
    title_esc = esc(title)
    excerpt_esc = esc(excerpt)
    date_iso = f"{date_str}T07:00:00+09:00"
    html = (tpl
            .replace("{{SITE_URL}}", SITE_URL)
            .replace("{{TITLE}}", title_esc)
            .replace("{{EXCERPT}}", excerpt_esc)
            .replace("{{KEYWORDS}}", esc(topic.get("keywords", "")))
            .replace("{{SLUG}}", f"{date_str}-{slug}")
            .replace("{{CATEGORY}}", esc(topic["category"]))
            .replace("{{DATE}}", date_str.replace("-", "."))
            .replace("{{DATE_ISO}}", date_iso)
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
    print("[ok] updated feed.xml")

    # ---- sitemap ----
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
    for p in articles:
        # 記事の公開日をlastmodに（ファイル名のYYYY-MM-DDから抽出）
        date_m = re.match(r"(\d{4}-\d{2}-\d{2})", p.stem)
        lastmod = date_m.group(1) if date_m else today
        urls.append(f"  <url><loc>{SITE_URL}/articles/{p.name}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
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
