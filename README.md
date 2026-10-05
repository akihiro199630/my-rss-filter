# RSS フィルター

設定した RSS フィードを取得し、記事ページの `#contents` 内に指定キーワードを含む `alt` 属性の画像がある記事を除外します。GitHub Actions が毎時実行し、結果を GitHub Pages で配信します。

## GitHub で動かす手順

### 1. GitHub にリポジトリを作成して push

GitHub で空のリポジトリを作成します。Windows PowerShell でこのプロジェクトのフォルダーに移動し、`<ユーザー名>` と `<リポジトリ名>` を実際の値に置き換えて実行してください。

```powershell
cd "<プロジェクトフォルダー>"
git init -b main
git add .
git commit -m "Add RSS filter"
git remote add origin https://github.com/<ユーザー名>/<リポジトリ名>.git
git push -u origin main
```

### 2. Repository Variables を設定

リポジトリの **Settings → Secrets and variables → Actions → Variables** で、次の Repository Variables を作成します。

| Name | Value |
| --- | --- |
| `SOURCE_RSS_URL` | 取得するRSSフィードの完全なURL |
| `TARGET_ALT_TEXT` | `〇〇,××` |

`TARGET_ALT_TEXT` はカンマ区切りで複数指定できます。未設定または空の場合は `〇〇` を使います。

`SOURCE_RSS_URL` はソースコードにフィードURLを直書きしないための設定です。Repository Variable は秘密情報ではありません。実行時の接続先を隠すものではなく、生成RSSに含まれる記事リンクやフィードの情報から接続先を推測できる場合があります。

### 3. GitHub Pages を設定

リポジトリの **Settings → Pages → Build and deployment** で以下を選び、保存します。

- **Source:** `Deploy from a branch`
- **Branch:** `gh-pages`
- **Folder:** `/(root)`

初回実行前は `gh-pages` ブランチが一覧にない場合があります。その場合は次の手順を先に実行し、デプロイ後に Pages の設定を行ってください。

### 4. Actions を手動実行

**Actions** タブで **Generate filtered RSS** を選び、**Run workflow → Run workflow** を押します。実行結果が成功になったら、次の形式のURLでRSSを確認できます。

```text
https://<ユーザー名>.github.io/<リポジトリ名>/filtered_rss.xml
```

反映に数分かかる場合があります。以降は毎時（UTCの毎時0分）に自動実行され、Actionsから手動実行もできます。

## ローカル実行

Windows では `run.bat` を使います。実行前に PowerShell で接続先と除外キーワードを設定します。

```powershell
$env:SOURCE_RSS_URL = "<取得するRSSフィードの完全なURL>"
$env:TARGET_ALT_TEXT = "〇〇,××"
.\run.bat
```

RSS は `public/filtered_rss.xml` に生成されます。
