import base64
import os
import sys
from playwright.sync_api import sync_playwright
from send2trash import send2trash

# === 設定 ===================
OUTPUT_FORMATS = ["png", "jpg"]  # 出力したい画像形式（両方書けば両方出力される）
# ============================

def svg_to_img_data_uri(svg_file_path):
    """
    SVGファイルをbase64にエンコードして、data URI形式に変換する。

    理由：
    - HTML内に<image>タグでSVGを埋め込むために、data URI形式を使用する。
    - base64に変換することで、SVGをHTMLに直接埋め込み可能になり、外部ファイル参照が不要になる。
    - Playwright等の自動ブラウザ操作ツールで、file://によるローカルファイル読み込みが制限される環境でも安定して動作する。
    - セキュリティ上の制約（CORSやXSS、クロスドメインなど）を回避できる。
    - 結果として、SVGをimg要素に埋め込み、JavaScriptでcanvasに描画して画像形式（PNG/JPG）へ確実に変換する仕組みを実現する。

    戻り値：
        "data:image/svg+xml;base64,..." の形式の文字列
    """
    if not os.path.exists(svg_file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {svg_file_path}")
    
    with open(svg_file_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    svg_bytes = svg_content.encode('utf-8')
    base64_encoded = base64.b64encode(svg_bytes).decode('utf-8')
    
    return f'data:image/svg+xml;charset=utf-8;base64,{base64_encoded}'

def generate_html(data_uri, output_filename, html_file, output_format):
    """
    SVGのdata URIをimgタグに埋め込んだHTMLを生成し、ローカルHTMLファイルとして保存する。

    主な処理内容：
    - SVGのbase64エンコード済みのdata URIをHTML内の<img>タグに埋め込む。
    - <canvas>を使ってJavaScript経由で画像（PNGまたはJPG）に変換する処理を定義。
    - PNG出力時は透明背景のまま保存、JPG出力時は白背景で塗りつぶす処理を挿入。
    - ボタンクリックでcanvasから画像データを生成し、自動的にダウンロードする仕組みを提供。
    - 書き出されるHTMLは、Playwrightなどのブラウザ自動操作ツールから開いて操作可能。

    引数:
        data_uri (str): SVGをbase64エンコードしたdata URI文字列。
        output_filename (str): ブラウザ上で保存される画像ファイル名（例: 'example.png'）。
        html_file (str): 生成されたHTMLファイルの保存先パス（例: 'temp_output.html'）。
        output_format (str): 出力フォーマット（"png" または "jpg"）。

    備考：
    - 画像サイズはSVGに依存して自動的にキャンバスサイズに適応。
    - クライアントサイドで完結するため、外部APIやWebサーバを必要としない。
    - プレーンなHTML + JavaScriptのみで構成されており、ブラウザ互換性も高い。
    """
    mime = "image/png" if output_format == "png" else "image/jpeg"
    quality = "undefined" if output_format == "png" else "0.95"
    button_text = "PNGとして保存" if output_format == "png" else "JPGとして保存"

    # JPG形式では背景が黒くなるのを防ぐため、canvasに白背景を塗る処理を挿入。
    # PNG形式は透明を保持できるので背景塗りつぶしは不要。
    # 丸括弧 () で囲っているのは、Pythonでは長い式を複数行に分けて書くための書き方。
    # 内容自体は if-else による三項演算子で、出力形式に応じて適切なコードを生成している。
    fill_background = (
        "ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height);"
        if output_format == "jpg" else ""
    )

    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>SVG to {output_format.upper()}</title>
</head>
<body>
  <!-- 
    注意：
    この <img> タグの width="400" は表示上のスケーリングにのみ影響し、
    実際に出力される画像サイズ（canvasのサイズ）は SVG の元のサイズに依存します。
    canvas.width / height は image の自然サイズ（intrinsic size）を使用。
  -->
  <img src="{data_uri}" alt="SVG Image" width="400">
  <script>
    function download() {{
      const img = document.querySelector('img');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      const image = new Image();
      image.onload = function () {{
        canvas.width = image.width;
        canvas.height = image.height;
        {fill_background}
        ctx.drawImage(image, 0, 0);
        const data = canvas.toDataURL("{mime}"{', ' + quality if output_format == "jpg" else ''});
        const a = document.createElement('a');
        a.href = data;
        a.download = '{output_filename}';
        a.click();
      }};
      image.src = img.src;
    }}
  </script>
  <button onclick="download()">{button_text}</button>
</body>
</html>
'''
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def auto_download(html_path, download_dir, output_format):
    """
    指定されたHTMLファイルをChromiumベースのブラウザで開き、JavaScriptによる画像保存処理を自動実行する。

    主な処理内容：
    - HTMLファイルをローカルURL（file://）として開く。
    - 出力フォーマットに応じた「PNGとして保存」または「JPGとして保存」ボタンをクリック。
    - JavaScript側で<canvas>に描画された画像をtoDataURLで生成し、自動ダウンロード。
    - Playwrightの `expect_download` を使ってファイルのダウンロード完了を待ち、指定ディレクトリへ保存。
    - 処理完了後、ブラウザを閉じる。

    引数:
        html_path (str): 実行対象のローカルHTMLファイルへのパス。
        download_dir (str): ダウンロードファイルの保存先ディレクトリ。
        output_format (str): 出力形式。 "png" または "jpg" に限定。

    備考：
    - headless=False で実行しているため、ブラウザウィンドウは表示される。
    - Playwrightの `accept_downloads=True` によってファイル保存が可能になる。
    - ボタンクリックによる保存は HTML 側で埋め込まれたJavaScriptに依存している。
    - 同期版 Playwright API（`sync_playwright`）を利用している。

    制約:
    - ボタンのテキストは日本語 ("PNGとして保存" / "JPGとして保存") 固定のため、HTML側とズレると失敗する。
    - Chrome系ブラウザ以外の動作は想定していない（Chromium使用）。
    """
    html_url = f"file://{os.path.abspath(html_path)}"
    button_text = "PNGとして保存" if output_format == "png" else "JPGとして保存"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try :
            page.goto(html_url)

            with page.expect_download() as download_info:
                page.click(f"text={button_text}")

            # ✅ download_info.value はダウンロード完了後に取得される Download オブジェクト
            #    withブロック内で click() をトリガーしておけば、ブロック終了時に download が確定する。
            #    Playwright公式ドキュメントにも同様の使用例あり：
            #    https://playwright.dev/python/docs/downloads#download-events
            #    ブロック外でも安全にアクセスできる仕様なので、ここで save_as() を呼び出してOK。
            download = download_info.value
            save_path = os.path.join(download_dir, download.suggested_filename)
            download.save_as(save_path)
            print(f"✅ 保存完了: {save_path}")
        finally:
            # ✅ Playwrightでは browser > context の順で生成されるため、
            #    closeも context → browser の順が望ましい。
            #    公式にも close() でリソース解放を推奨：
            #    https://playwright.dev/python/docs/api/class-browsercontext#browsercontext-close
            #    https://playwright.dev/python/docs/api/class-browser#browser-close
            context.close()
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python svg2img.py input.svg")
        sys.exit(1)

    svg_file = sys.argv[1]
    try:
        basename = os.path.splitext(os.path.basename(svg_file))[0]
        data_uri = svg_to_img_data_uri(svg_file)

        for output_format in OUTPUT_FORMATS:
            if output_format not in ("png", "jpg"):
                print(f"⚠️ 無効な形式: {output_format}")
                continue

            output_filename = f"{basename}.{output_format}"
            html_filename = f"temp_output_{output_format}.html"

            generate_html(data_uri, output_filename, html_filename, output_format)
            auto_download(html_filename, ".", output_format)

            try:
                send2trash(html_filename)
                print(f"🗑️ 一時ファイルをゴミ箱へ移動しました: {html_filename}")
            except Exception as e:
                print(f"⚠️ ゴミ箱に移動できなかったので削除します: {e}")
                try:
                    os.remove(html_filename)
                except:
                    print(f"❌ 削除にも失敗したので放置します: {e}")

    except Exception as e:
        print(f"エラー: {e}")
