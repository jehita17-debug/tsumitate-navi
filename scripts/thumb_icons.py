# -*- coding: utf-8 -*-
"""
つみたてNAVI - 記事カードのサムネイル用カテゴリアイコン

各カテゴリに対応した「記事内容が一目でわかる」シンプルなSVGアイコンを返す。
index.html のカード生成（generate_article.py / rebuild_indexes.py）で
従来の <span>N</span> の代わりに使う。

外部ファイル不要のインラインSVGなので、画像ホスティングや読み込み遅延がなく、
どの画面サイズでもくっきり表示される。色はサムネ側の color (currentColor) を継承。
"""

# カテゴリ → インラインSVG（class="thumb-icon"、stroke=currentColor）
_ICONS = {
    # NISA … 非課税で「守りながら増やす」イメージ → 盾＋チェック
    "NISA":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M24 5l15 5v10c0 9-6.2 15.6-15 18-8.8-2.4-15-9-15-18V10z"/>'
        '<path d="M17 24l5 5 10-11"/></svg>',

    # つみたて投資 … コツコツ積み上げる → コインの山
    "つみたて投資":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<ellipse cx="24" cy="13" rx="12" ry="4.5"/>'
        '<path d="M12 13v6c0 2.5 5.4 4.5 12 4.5s12-2 12-4.5v-6"/>'
        '<path d="M12 19v6c0 2.5 5.4 4.5 12 4.5s12-2 12-4.5v-6"/>'
        '<path d="M12 25v6c0 2.5 5.4 4.5 12 4.5s12-2 12-4.5v-6"/></svg>',

    # 米国株 … 右肩上がりの株価 → 上昇チャート
    "米国株":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="7,33 19,23 27,29 41,14"/>'
        '<polyline points="31,14 41,14 41,24"/></svg>',

    # 日本株 … 円建ての国内株 → ¥マーク入り円
    "日本株":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="24" cy="24" r="18"/>'
        '<path d="M17 15l7 9 7-9"/><path d="M24 24v10"/>'
        '<path d="M18 27h12"/><path d="M18 31h12"/></svg>',

    # 資産形成 … お金を育てる → 双葉（芽）
    "資産形成":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M24 40V22"/>'
        '<path d="M24 27c-1.5-5.5-6.5-8-12-7-.5 5.5 4 9.5 9.5 9.5"/>'
        '<path d="M24 23c1.5-5.5 6.5-8 12-7 .5 5.5-4 9.5-9.5 9.5"/>'
        '<path d="M16 40h16"/></svg>',

    # 基礎解説 … 学び → 開いた本
    "基礎解説":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M24 13c-4-2.5-9-2.5-14-1v23c5-1.5 10-1.5 14 1 4-2.5 9-2.5 14-1V12c-5-1.5-10-1.5-14 1z"/>'
        '<path d="M24 13v23"/></svg>',

    # FX・為替 … 通貨の交換 → 双方向の矢印
    "FX・為替":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="15,13 9,19 15,25"/>'
        '<path d="M9 19h26c2.2 0 4 1.8 4 4v2"/>'
        '<polyline points="33,35 39,29 33,23"/>'
        '<path d="M39 29H13c-2.2 0-4-1.8-4-4v-2"/></svg>',

    # コモディティ … 金（ゴールド） → 金塊の山
    "コモディティ":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M19 15h10l3 8H16z"/>'
        '<path d="M11 25h10l3 8H8z"/>'
        '<path d="M27 25h10l3 8H24z"/></svg>',

    # 仮想通貨 … 暗号資産 → ₿コイン
    "仮想通貨":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="24" cy="24" r="17"/>'
        '<path d="M20 15v18"/><path d="M25 13v3M25 32v3"/>'
        '<path d="M19 18h9a4 4 0 0 1 0 8h-9"/>'
        '<path d="M19 26h10a4 4 0 0 1 0 8H19"/></svg>',

    # 世界経済 … グローバル → 地球儀
    "世界経済":
        '<svg class="thumb-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="24" cy="24" r="17"/><path d="M7 24h34"/>'
        '<path d="M24 7c5 5 8 11 8 17s-3 12-8 17c-5-5-8-11-8-17s3-12 8-17z"/></svg>',
}

# 未知カテゴリ用の既定アイコン（上昇チャート）
_DEFAULT = _ICONS["米国株"]


def category_icon(category: str) -> str:
    """カテゴリ名に対応したサムネ用インラインSVGを返す。未知なら既定アイコン。"""
    return _ICONS.get((category or "").strip(), _DEFAULT)
