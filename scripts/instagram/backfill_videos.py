#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
つみたてNAVI - 過去記事の Instagram素材 まとめ生成（バックフィル）

まだ Instagram素材（instagram/<記事>/）が無い過去記事をまとめて作る。
1記事ずつ gen_video_for_article.process_article を呼ぶ。

対象の絞り込み（環境変数）:
  SINCE_DATE  これ以降(含む)の日付の記事だけ対象。既定 2026-05-27
              （= 前回Instagramで作った 5/12〜5/26 の続きから）
  UNTIL_DATE  これ以前(含む)の日付の記事だけ対象。既定 9999-12-31
  FORCE       "1" のとき、既に素材があっても作り直す。既定は既存はスキップ

GitHub Actions（手動 Run workflow）から ANTHROPIC_API_KEY 付きで呼ぶ想定。
ローカルでも動く（APIキーが無ければ簡易フォールバックでスライド生成）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_video_for_article as g  # noqa: E402

SINCE_DATE = os.environ.get("SINCE_DATE", "2026-05-27")
UNTIL_DATE = os.environ.get("UNTIL_DATE", "9999-12-31")
FORCE = os.environ.get("FORCE", "") == "1"


def targets():
    out = []
    for p in sorted(g.ARTICLES_DIR.glob("*.html")):
        if p.stem.startswith("_"):
            continue
        date = p.stem[:10]  # YYYY-MM-DD
        if not (SINCE_DATE <= date <= UNTIL_DATE):
            continue
        mp4 = g.OUT_DIR / p.stem / f"{p.stem}.mp4"
        if mp4.exists() and not FORCE:
            print(f"[skip] {p.stem}（素材あり）")
            continue
        out.append(p)
    return out


def main():
    tgts = targets()
    print(f"[info] 対象 {len(tgts)} 記事（SINCE={SINCE_DATE} UNTIL={UNTIL_DATE} FORCE={FORCE}）")
    ok, ng = 0, 0
    for p in tgts:
        try:
            g.process_article(p)
            ok += 1
        except Exception as e:
            ng += 1
            print(f"[ERR] {p.stem}: {e}")
    print(f"[done] 成功 {ok} / 失敗 {ng}")


if __name__ == "__main__":
    main()
