# つみたてNAVI

投資初心者向けアフィリエイトサイト（NISA・つみたて投資・米国株・日本株）。
毎朝7時に新着記事を自動配信します。

## ディレクトリ構成

```
アフィリエイトサイト/
├── index.html              トップページ（記事一覧）
├── about.html              サイトについて
├── privacy.html            プライバシーポリシー
├── disclaimer.html         免責事項（投資サイト必須）
├── contact.html            お問い合わせ
├── feed.xml                RSSフィード
├── sitemap.xml             サイトマップ（SEO用）
├── robots.txt              クローラー向け
├── css/
│   └── style.css           メインスタイル
├── articles/               日々の記事
│   ├── _template.html        自動生成用テンプレート
│   └── 2026-05-12-...html    記事ファイル（日付-スラグ.html）
├── scripts/
│   ├── generate_article.py   記事自動生成スクリプト
│   ├── topics.json           トピックプール（20件）
│   └── requirements.txt
└── .github/workflows/
    └── daily-article.yml   GitHub Actions（毎朝7時JST）
```

---

## 毎朝7時の自動配信：2つの方法

### 方法A：Cowork のスケジュールタスク（設定済み）

すでに `tsumitate-navi-daily-article` という名前で登録済みです。
Coworkを開いている状態（または起動時）に、毎日7時にClaudeが記事を1本生成し、`articles/` と `index.html` を更新します。

- Coworkサイドバーの「Scheduled」セクションから、即時実行・編集・停止が可能
- A8.netリンクの差し替えは生成後に手動

### 方法B：GitHub Actions（推奨：完全自動）

GitHubに公開すれば、PC不要で毎朝7時(JST)に自動投稿されます。

#### 1. GitHubリポジトリを作る

```bash
cd "C:\Users\user\OneDrive\同窓会名簿\Claude\Projects\アフィリエイトサイト"
git init
git add .
git commit -m "initial commit"
gh repo create tsumitate-navi --public --source=. --push
# または GitHub.com で空のリポジトリを作って push
```

#### 2. GitHub Pages を有効化

リポジトリの **Settings → Pages → Source: main / root** を選択。
数分後に `https://<ユーザー名>.github.io/tsumitate-navi/` で公開されます。

#### 3. Anthropic API キーをシークレットに登録

1. https://console.anthropic.com/ で API キーを発行
2. リポジトリの **Settings → Secrets and variables → Actions** で
   `ANTHROPIC_API_KEY` という名前で登録

これで `.github/workflows/daily-article.yml` が毎朝7時に動き、新記事をコミットしてくれます。

#### 4. SITE_URL を本番URLに差し替え

- `scripts/generate_article.py` の `SITE_URL`
- `sitemap.xml` / `feed.xml` / `robots.txt` 内の URL

を、実際の公開URLに置き換えてください。

---

## A8.netアフィリエイトリンクの貼り方

サイト内の広告枠は `<div class="affiliate-card">` で統一されています。検索すれば全部見つかります。

```html
<div class="affiliate-card">
  <h4>初心者に人気のネット証券（口座開設は無料）</h4>
  <p>説明文...</p>
  <a href="https://px.a8.net/svt/ejp?a8mat=XXXXX..." class="affiliate-btn" target="_blank" rel="nofollow noopener">公式サイトで詳細を見る</a>
  <!-- A8.netの計測タグ（透明画像）もここに -->
  <img border="0" width="1" height="1" src="https://www10.a8.net/0.gif?a8mat=XXXXX">
</div>
```

A8.netの管理画面で「広告リンク作成」→「素材タイプ：バナー（横）またはテキスト」を取得し、上のテンプレ `href` と `<img>` 部分を差し替えてください。

### おすすめジャンルのプログラム例
- SBI証券、楽天証券、マネックス証券（ネット証券）
- マネックス証券 米国株口座
- マネースクール（投資セミナー系）
- マネきゃん・グローバルファイナンシャルスクール（投資講座）
- iDeCo関連サービス

---

## 記事を手動で追加する

```bash
cp articles/_template.html articles/2026-05-13-myarticle.html
# {{TITLE}} {{EXCERPT}} {{CATEGORY}} {{DATE}} {{CONTENT}} を置換
# index.html の <!-- ▼▼▼ 自動生成記事はここに追加されます ▼▼▼ --> 直後にカードを追加
```

---

## ローカル確認

ローカルでサイトを確認するには：

```bash
cd "C:\Users\user\OneDrive\同窓会名簿\Claude\Projects\アフィリエイトサイト"
python -m http.server 8000
# ブラウザで http://localhost:8000/ を開く
```

または `index.html` をダブルクリックでもOK。

---

## サイト名候補（変更したい場合）

- つみたてNAVI（採用中）
- マネハジ（マネー始めよう）
- 資産形成ラボ
- かんたん投資ガイド
- インデキ（インデックス投資）

`index.html` ほか各ページで `つみたてNAVI` を検索して一括置換してください。

---

## チェックリスト

- [ ] A8.netの審査用：about / privacy / disclaimer / contact ページ → 4つとも設置済み
- [ ] サイト名・運営者情報を確定
- [ ] お問い合わせフォーム（Googleフォーム等）のURLを `contact.html` に設定
- [ ] GitHub Pages公開（または独自ドメイン）
- [ ] A8.net管理画面でサイトを審査申請
- [ ] 記事を3〜5本書いて、A8.net審査に提出（投資系は審査基準やや厳しめ）
- [ ] アフィリエイトリンクを各記事の `affiliate-card` に貼り替え
- [ ] Googleアナリティクス・Search Consoleを設定（任意）
