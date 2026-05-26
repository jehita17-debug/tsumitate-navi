#!/usr/bin/env python3
"""
過去記事のプレースホルダー affiliate-card を
A8.net の本物のリンクに差し替える一回限りの使い捨てバッチ。

マッピング（2026-05-26時点）:
- 株価指数系（5/14, 5/19, 5/20）: 1枚目=DMM株, 2枚目=TOSSY
- 5/21 trust-fee-comparison: 1枚のみ→DMM株
- それ以外:                       1枚目=DMM株, 2枚目=DMM株（ボタン文言違い）

A8 案件:
- DMM 株:  a8mat = 4B3XB7+8GTZA2+1WP2+15R4NM
- TOSSY :  a8mat = 4B3XB7+82JKRE+1WP2+1HPXWX

実行方法: python scripts/inject_affiliates.py
（--dry でドライラン）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ARTICLES = ROOT / "articles"

# ---- A8 タグ ----
DMM_LINK = "https://px.a8.net/svt/ejp?a8mat=4B3XB7+8GTZA2+1WP2+15R4NM"
DMM_PIXEL = "https://www19.a8.net/0.gif?a8mat=4B3XB7+8GTZA2+1WP2+15R4NM"
TOSSY_LINK = "https://px.a8.net/svt/ejp?a8mat=4B3XB7+82JKRE+1WP2+1HPXWX"
TOSSY_PIXEL = "https://www14.a8.net/0.gif?a8mat=4B3XB7+82JKRE+1WP2+1HPXWX"

# (link, pixel, button_text) のセット
DMM_1ST = (DMM_LINK, DMM_PIXEL, "DMM 株の口座開設を見る(PR)")
DMM_2ND = (DMM_LINK, DMM_PIXEL, "DMM 株を詳しく見る(PR)")
TOSSY_2ND = (TOSSY_LINK, TOSSY_PIXEL, "TOSSYで取引してみる(PR)")

# 記事ごとの配置順 ([1枚目, 2枚目])
PLACEMENTS = {
    "2026-05-12-nisa-start-guide.html":         [DMM_1ST, DMM_2ND],
    "2026-05-13-dollar-cost-averaging.html":    [DMM_1ST, DMM_2ND],
    "2026-05-14-sp500-guide.html":              [DMM_1ST, TOSSY_2ND],
    "2026-05-16-ideco-vs-nisa.html":            [DMM_1ST, DMM_2ND],
    "2026-05-17-monthly-amount-by-age.html":    [DMM_1ST, DMM_2ND],
    "2026-05-18-tsumitate-vs-growth-quota.html": [DMM_1ST, DMM_2ND],
    "2026-05-19-vti-vs-all-country.html":       [DMM_1ST, TOSSY_2ND],
    "2026-05-20-nikkei-vs-topix.html":          [DMM_1ST, TOSSY_2ND],
    "2026-05-21-trust-fee-comparison.html":     [DMM_1ST],
    "2026-05-22-household-budget-review.html":  [DMM_1ST, DMM_2ND],
}

ANCHOR_RE = re.compile(r'<a href="#" class="affiliate-btn">[^<]*</a>')
NOTE_RE = re.compile(
    r'<p style="margin-top:12px; font-size:12px; color:#9ca3af;">'
    r'※A8\.netのアフィリエイトリンクを貼り替えてください</p>'
)


def build_anchor(link: str, pixel: str, btn: str) -> str:
    return (
        f'<a href="{link}" class="affiliate-btn" '
        f'target="_blank" rel="nofollow sponsored noopener">{btn}</a>\n'
        f'    <img border="0" width="1" height="1" '
        f'src="{pixel}" alt="" style="display:none;">'
    )


NEW_NOTE = (
    '<p style="margin-top:12px; font-size:12px; color:#9ca3af;">'
    '※本リンクはアフィリエイト広告（PR）を含みます。'
    '投資にはリスクがあり、元本は保証されません。</p>'
)


def replace_in_file(path: Path, placements: list, dry: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    anchors = list(ANCHOR_RE.finditer(text))
    notes = list(NOTE_RE.finditer(text))

    if len(anchors) != len(notes) or len(anchors) != len(placements):
        print(
            f"[SKIP] {path.name}: count mismatch "
            f"(anchors={len(anchors)}, notes={len(notes)}, expected={len(placements)})"
        )
        return False

    # 後ろから置換（前のインデックスを保持するため）
    out = text
    pairs = list(zip(anchors, notes, placements))
    for anchor_m, note_m, (link, pixel, btn) in reversed(pairs):
        new_anchor = build_anchor(link, pixel, btn)
        out = out[: note_m.start()] + NEW_NOTE + out[note_m.end():]
        out = out[: anchor_m.start()] + new_anchor + out[anchor_m.end():]

    action = "DRY" if dry else "WRITE"
    btns = ", ".join(p[2].split("(")[0].strip() for p in placements)
    print(f"[{action}] {path.name}: {len(placements)} card(s) -> {btns}")
    if not dry:
        path.write_text(out, encoding="utf-8")
    return True


def main():
    dry = "--dry" in sys.argv
    print(f"=== inject_affiliates.py ({'DRY RUN' if dry else 'WRITE'}) ===")
    total = 0
    ok = 0
    for filename, placements in PLACEMENTS.items():
        path = ARTICLES / filename
        if not path.exists():
            print(f"[MISS] {filename}: not found")
            continue
        total += 1
        if replace_in_file(path, placements, dry):
            ok += 1
    print(f"=== done: {ok}/{total} files processed ===")


if __name__ == "__main__":
    main()
