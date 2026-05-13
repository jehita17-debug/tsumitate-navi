# つみたてNAVI - URL・アカウント一覧

最終更新：2026年5月12日

---

## サイト関連

| 項目 | URL |
|---|---|
| 公開サイト | https://jehita17-debug.github.io/tsumitate-navi/ |
| サイトマップ（Search Console提出用） | https://jehita17-debug.github.io/tsumitate-navi/sitemap.xml |
| RSSフィード | https://jehita17-debug.github.io/tsumitate-navi/feed.xml |

## GitHub関連

| 項目 | URL |
|---|---|
| リポジトリ | https://github.com/jehita17-debug/tsumitate-navi |
| Actions（自動投稿の実行履歴） | https://github.com/jehita17-debug/tsumitate-navi/actions |
| Secrets（APIキー管理） | https://github.com/jehita17-debug/tsumitate-navi/settings/secrets/actions |
| Pages設定 | https://github.com/jehita17-debug/tsumitate-navi/settings/pages |
| GitHubアカウント | jehita17-debug |

## ローカル作業フォルダ

| 項目 | パス |
|---|---|
| GitHub Desktop クローン先 | C:\Users\user\Documents\GitHub\tsumitate-navi |
| 元データ（OneDrive） | C:\Users\user\OneDrive\同窓会名簿\Claude\Projects\アフィリエイトサイト |

※ 編集するときは GitHub Desktop のクローン先（Documents配下）で作業する。OneDrive側は元データのバックアップ。

## サードパーティサービス

| サービス | URL | 用途 |
|---|---|---|
| Anthropic Console | https://console.anthropic.com/ | APIキー管理・利用料金確認 |
| A8.net | https://www.a8.net/ | アフィリエイト広告（登録済み） |
| Google Search Console（任意） | https://search.google.com/search-console | SEO分析（未登録） |
| Google Analytics（任意） | https://analytics.google.com/ | アクセス解析（未登録） |

## 自動投稿スケジュール

| 項目 | 内容 |
|---|---|
| 実行時刻 | 毎日 朝7時（JST） |
| 実行場所 | GitHub Actions（PC不要） |
| バックアップ実行 | Coworkスケジュールタスク `tsumitate-navi-daily-article` |
| 使用モデル | Claude Sonnet 4 |
| 1記事あたりのAPI料金目安 | 3〜8円 |

## 設定済みSecrets

| 名前 | 用途 |
|---|---|
| ANTHROPIC_API_KEY | GitHub ActionsからClaude APIを呼ぶためのキー |

※ キー自体はGitHubに登録済み。再発行する場合は console.anthropic.com で新しいキーを作って、同じ名前で上書き登録する。

## 記事の手動追加・編集手順

1. GitHub Desktop で `Documents\GitHub\tsumitate-navi` を最新化（Fetch origin → Pull）
2. メモ帳・VS Code等でファイル編集
3. GitHub Desktop で Commit → Push

## 困ったときの最初の確認場所

- 自動投稿が止まった → GitHub Actions の最新Runのログ
- サイトが表示されない → GitHub Pages の Settings画面 / Public設定の確認
- 記事内容を変えたい → `scripts/topics.json` のトピック編集 / `scripts/generate_article.py` のシステムプロンプト調整

## A8.net 連携の次ステップ

1. A8.net管理画面でサイトを追加（URLは上記の公開サイトURL）
2. 投資系プログラム（SBI証券・楽天証券・マネックス証券など）に提携申請
   - 記事が10本溜まってから申請の方が通りやすい
3. 取得した広告タグを各記事の `<div class="affiliate-card">` に貼り替え
