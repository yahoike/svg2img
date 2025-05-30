# svg2img: SVG to PNG/JPG Auto Converter

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

ローカルのSVGファイルを、Playwright + HTML + JavaScript によって **高精度なPNG/JPG画像** に自動変換するPythonスクリプトです。  
将棋AI「やねうら王（MyShogi）」の局面図SVG出力など、**ベクター画像しか保存できない環境**でも、簡単にSNSやブログ用の画像ファイルとして保存できます。

---

## ✅ 特徴

- 📁 ローカルSVG → PNG / JPG に変換（両方出力）
- 🖼️ 背景透過（PNG）／白背景（JPG）に自動対応
- 🌐 ブラウザ描画ベースなので **正確で美しいレンダリング**
- 🤖 Playwrightによる**完全自動実行**（クリック不要）
- 🧹 一時HTMLファイルは自動でゴミ箱へ移動

---

## 🛡️ オンライン変換ツールとの違い

多くのSVG→画像変換サービスはWeb上で提供されていますが、以下のような課題があります：

- ❌ 突然のサービス終了（メンテや閉鎖で利用不能に）
- ❌ 変換精度やサイズが不安定／広告表示あり
- ❌ ファイルを外部にアップロードする必要がある
- ❌ オフライン環境で使えない
- ❌ 独自実装で正確にレンダリングされないことがある

**svg2img.py** はこれらをすべて回避：

- ✅ 完全ローカルで動作（アップロード不要）
- ✅ ブラウザ描画による高精度な変換
- ✅ Playwrightによる自動処理
- ✅ オフラインでも使用可能
- ✅ 拡張や検証が自由なPythonスクリプト

---

## 📦 必要環境

- Python 3.8 以降
- Google Chrome または Chromium
- 以下のPythonパッケージ：

```bash
pip install playwright send2trash
playwright install
```

## トラブルシューティング

### `'playwright' は、内部コマンドまたは外部コマンド...`

これは、Playwrightがまだ有効になっていないか、仮想環境をアクティブにしていない場合に出ます。

#### ✅ 解決策：

**方法①：仮想環境を使っているなら、まずアクティブにする：**

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**方法②：Python経由で `playwright` を実行：**

```bash
python -m playwright install
```

> `python -m playwright install` を使えば、環境に依存せず確実に動作します。

---

## 🚀 使い方

1. 任意のSVGファイル（例: `sample.svg`）を用意
2. 以下のように実行：

```bash
python svg2img.py sample.svg
```

3. `sample.png` と `sample.jpg` が同じディレクトリに自動生成されます。

---

## 🔧 補足

- Playwrightでブラウザが一瞬立ち上がります（`headless=False` のため）
- SVGの内容はHTMLにBase64エンコードで埋め込まれ、セキュアに処理されます
- 出力画像サイズはSVGそのもののサイズに自動で合わせられます（`<img width="400">` 表示は変換結果に影響しません）

---

## 🧪 想定ユースケース

- 将棋AI「やねうら王（MyShogi）」のSVG局面図をSNS用に変換
- Markdownブログに貼る用の静的画像生成
- ベクター画像を高品質なラスタ画像に変換したいとき

---

## 📄 ライセンス

MIT License

---

## 👤 作者

Created by Yaho Ike
※ このスクリプトは ChatGPT（OpenAI）との共同開発（ペアプログラミング）によって制作されました。✨
