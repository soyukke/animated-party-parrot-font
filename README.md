# Kinetic Seven

OpenType Variable Font の独自軸 `ANIM` を使った、アニメーションする実験フォントです。JavaScript は文字画像を交換せず、同じグリフの可変軸を動かしています。

```sh
python3 -m venv .venv
.venv/bin/pip install 'fonttools[woff]' brotli
.venv/bin/python build_font.py
python3 -m http.server 8000
```

ブラウザで <http://localhost:8000> を開いてください。見出しは直接編集でき、スライダーで `ANIM` 軸を手動操作できます。

生成物は `fonts/kinetic-seven-variable.ttf`（デスクトップ用）と `fonts/kinetic-seven-variable.woff2`（Web 用）です。

## Party Parrot Variable Font

`party.html` は、本家128×128 GIFの10フレームを別々のCOLRグリフへ変換し、40ms間隔で切り替えるカラーフォントの使用例です。
入力欄の各文字を1羽へ変換するプレイグラウンドも含み、空白を保ちながら最大18文字まで表示できます。
OpenType GSUBの標準合字`liga`により、`party`、`parrot`、`party_parrot`も単一のパロットグリフへ置換されます。
Pagesのデモからインストール用TTFとWeb用WOFF2を直接ダウンロードできます。

### Windows

Windows 10/11ではTTFを右クリックして「インストール」を選択します。本フォントはWindowsのDirectWrite互換性のためglyph ID 1を`.null`にし、COLR v0/CPALとGSUB `liga`を使用しています。対応アプリではカラーの静止フレームと合字が表示されます。フォント単体にタイマーはないため、10フレームのアニメーションにはWebデモまたはフレームを切り替えるアプリが必要です。

WindowsのフォントビューアーとmacOS Font Bookのサンプル表示をパロットで埋めるため、印刷可能なASCII英数字・記号はすべて公式第1フレームのカラーグリフへ割り当てています。各文字は別グリフのままなので、GSUBは`party`などの単語を引き続き1羽へ合字化できます。

```sh
.venv/bin/python build_party_parrot.py
python3 -m http.server 8000
```

<http://localhost:8000/party.html> を開いてください。生成物は `fonts/party-parrot-official.ttf` と `fonts/party-parrot-official.woff2` です。

Party Parrot SVG artwork © 2016 John Hobbs, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Source: <https://cultofthepartyparrot.com/assets/parrot.svg>. The SVG path data is embedded without shape modification; animation is applied with CSS transforms.

The build additionally requires Pillow (`.venv/bin/pip install pillow`) and downloads the official 10-frame GIF during generation.
