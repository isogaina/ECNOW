#!/usr/bin/env python3
"""図2（プラン切り替えの分岐点）のSVGをHTMLとして書き出す。
切片・傾き・交差点はすべて計算値。手で座標を書かない。"""

OUT = "/private/tmp/claude-501/-Users-nana-works-JPholic-ECNOW/08dd7da4-03e8-45cd-89b4-5214775e93de/scratchpad/fig2.html"

# --- 前提の数値 -------------------------------------------------------------
GANBARE_FIX, GANBARE_RATE = 25_000, 0.0425   # 公式レンジ 3.5%〜6.5% の範囲内
STANDARD_FIX, STANDARD_RATE = 65_000, 0.0200  # 公式レンジ 2.0%〜4.0% の範囲内
CROSS_SALES = (STANDARD_FIX - GANBARE_FIX) / (GANBARE_RATE - STANDARD_RATE)  # 円
assert abs(CROSS_SALES - 1_780_000) < 10_000, CROSS_SALES

X_MAX_MAN = 300          # 横軸の上限（万円）
Y_MAX = 160_000          # 縦軸の上限（円）

def ganbare(sales):  return GANBARE_FIX + GANBARE_RATE * sales
def standard(sales): return STANDARD_FIX + STANDARD_RATE * sales

# --- 描画領域 ---------------------------------------------------------------
W, H = 1600, 900
PX0, PX1 = 210, 1230     # プロット領域の左右（右側は凡例のスペースを確保）
PY0, PY1 = 190, 748      # 上（Y_MAX）と下（0円）

def sx(man):  return PX0 + (man / X_MAX_MAN) * (PX1 - PX0)
def sy(yen):  return PY1 - (yen / Y_MAX) * (PY1 - PY0)

C_ORANGE, C_BLUE = "#f97316", "#3b82f6"
C_TEXT, C_GRID, C_MUTED = "#1f2937", "#dfe3e9", "#9aa4b2"

cross_x, cross_y = sx(CROSS_SALES / 10_000), sy(ganbare(CROSS_SALES))
tick_178 = round(CROSS_SALES / 10_000)   # = 178

parts = []
add = parts.append

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# タイトル
add(f'<text x="{(PX0+PX1)/2}" y="72" text-anchor="middle" class="title">'
    f'月商{tick_178}万円でプランの有利不利が入れ替わる</text>')

# 横グリッドと縦軸目盛り
for yen, label in [(0, "0"), (50_000, "5万"), (100_000, "10万"), (150_000, "15万")]:
    y = sy(yen)
    if yen:
        add(f'<line x1="{PX0}" y1="{y:.1f}" x2="{PX1}" y2="{y:.1f}" stroke="{C_GRID}" '
            f'stroke-width="1.5" stroke-dasharray="7 6"/>')
    add(f'<text x="{PX0-18}" y="{y+8:.1f}" text-anchor="end" class="tick">{label}</text>')
add(f'<text x="{PX0-18}" y="{sy(Y_MAX)+8:.1f}" text-anchor="end" class="unit">（円）</text>')

# 軸線
add(f'<line x1="{PX0}" y1="{PY0-30}" x2="{PX0}" y2="{PY1}" stroke="{C_TEXT}" stroke-width="2.5"/>')
add(f'<line x1="{PX0}" y1="{PY1}" x2="{PX1+30}" y2="{PY1}" stroke="{C_TEXT}" stroke-width="2.5"/>')

# 横軸目盛り
for man in [0, 50, 100, 150, 250, 300]:
    x = sx(man)
    add(f'<line x1="{x:.1f}" y1="{PY1}" x2="{x:.1f}" y2="{PY1+10}" stroke="{C_TEXT}" stroke-width="2"/>')
    add(f'<text x="{x:.1f}" y="{PY1+48}" text-anchor="middle" class="tick">{man}</text>')
add(f'<line x1="{cross_x:.1f}" y1="{PY1}" x2="{cross_x:.1f}" y2="{PY1+10}" stroke="{C_TEXT}" stroke-width="2"/>')
add(f'<text x="{cross_x:.1f}" y="{PY1+48}" text-anchor="middle" class="tick-strong">{tick_178}</text>')
add(f'<text x="{(PX0+PX1)/2}" y="{PY1+94}" text-anchor="middle" class="axis-label">月商（万円）</text>')

# 縦軸ラベル
add(f'<text x="76" y="{(PY0+PY1)/2}" text-anchor="middle" class="axis-label" '
    f'transform="rotate(-90 76 {(PY0+PY1)/2})">月額出店料＋システム利用料の合計</text>')

# 有利な領域（線より下に置く）
add(f'<text x="{sx(85):.1f}" y="{sy(10_000):.1f}" text-anchor="middle" class="region">がんばれ！プランが有利</text>')
add(f'<text x="{sx(245):.1f}" y="{sy(10_000):.1f}" text-anchor="middle" class="region">スタンダードプランが有利</text>')

# 交差点の垂線
add(f'<line x1="{cross_x:.1f}" y1="{PY1}" x2="{cross_x:.1f}" y2="{cross_y:.1f}" '
    f'stroke="{C_MUTED}" stroke-width="2" stroke-dasharray="8 7"/>')

# 2本の直線
for fn, color in [(ganbare, C_ORANGE), (standard, C_BLUE)]:
    add(f'<line x1="{sx(0):.1f}" y1="{sy(fn(0)):.1f}" x2="{sx(X_MAX_MAN):.1f}" '
        f'y2="{sy(fn(X_MAX_MAN*10_000)):.1f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')

# 切片の値（オレンジは線の下側 青は線の上側に置いて線と重ならないようにする）
add(f'<text x="{sx(3):.1f}" y="{sy(GANBARE_FIX)-20:.1f}" class="intercept" fill="{C_ORANGE}">'
    f'{GANBARE_FIX:,}円</text>')
add(f'<text x="{sx(3):.1f}" y="{sy(STANDARD_FIX)-40:.1f}" class="intercept" fill="{C_BLUE}">'
    f'{STANDARD_FIX:,}円</text>')

# 交差点マーカー
add(f'<circle cx="{cross_x:.1f}" cy="{cross_y:.1f}" r="10" fill="#ffffff" stroke="{C_TEXT}" stroke-width="3"/>')

# 吹き出し
bw, bh = 520, 132
bx, by = cross_x - bw/2, 168
add(f'<line x1="{cross_x:.1f}" y1="{by+bh}" x2="{cross_x:.1f}" y2="{cross_y-12:.1f}" '
    f'stroke="{C_BLUE}" stroke-width="2"/>')
add(f'<rect x="{bx:.1f}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="#eef3fe" '
    f'stroke="{C_BLUE}" stroke-width="2"/>')
add(f'<text x="{cross_x:.1f}" y="{by+44}" text-anchor="middle" class="callout-strong">'
    f'月商{tick_178}万円が切り替えの目安</text>')
add(f'<text x="{cross_x:.1f}" y="{by+78}" text-anchor="middle" class="callout">'
    f'ここより下はがんばれ！プラン</text>')
add(f'<text x="{cross_x:.1f}" y="{by+110}" text-anchor="middle" class="callout">'
    f'超えたらスタンダードプランが安くなる</text>')

# 右側の凡例
lx = PX1 + 40
gy, sy_ = sy(ganbare(X_MAX_MAN*10_000)), sy(standard(X_MAX_MAN*10_000))
add(f'<text x="{lx}" y="{gy+8:.1f}" class="legend" fill="{C_ORANGE}">がんばれ！プラン</text>')
add(f'<text x="{lx}" y="{gy+42:.1f}" class="legend-note">月額{GANBARE_FIX:,}円＋</text>')
add(f'<text x="{lx}" y="{gy+68:.1f}" class="legend-note">システム利用料3.5%〜6.5%</text>')
add(f'<text x="{lx}" y="{sy_+8:.1f}" class="legend" fill="{C_BLUE}">スタンダードプラン</text>')
add(f'<text x="{lx}" y="{sy_+42:.1f}" class="legend-note">月額{STANDARD_FIX:,}円＋</text>')
add(f'<text x="{lx}" y="{sy_+68:.1f}" class="legend-note">システム利用料2.0%〜4.0%</text>')

# 作図の前提（画像内に明記する）
add(f'<text x="{PX0-140}" y="{H-22}" class="footnote">'
    f'作図の料率はがんばれ！プラン{GANBARE_RATE*100:.2f}%／スタンダードプラン{STANDARD_RATE*100:.1f}%'
    f'（交差点が{tick_178}万円になる組み合わせ）実際の料率はジャンルとPC・モバイルで変わる</text>')

add('</svg>')

html = f'''<style>
  html,body{{margin:0;padding:0;background:#fff;}}
  svg{{display:block;}}
  text{{font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Noto Sans JP",sans-serif;fill:{C_TEXT};}}
  .title{{font-size:38px;font-weight:700;}}
  .tick{{font-size:26px;}}
  .tick-strong{{font-size:28px;font-weight:700;}}
  .unit{{font-size:20px;fill:{C_TEXT};}}
  .axis-label{{font-size:24px;}}
  .region{{font-size:24px;fill:{C_MUTED};}}
  .intercept{{font-size:24px;font-weight:700;}}
  .callout-strong{{font-size:26px;font-weight:700;}}
  .callout{{font-size:25px;}}
  .legend{{font-size:27px;font-weight:700;}}
  .legend-note{{font-size:20px;fill:{C_TEXT};}}
  .footnote{{font-size:19px;fill:{C_MUTED};}}
</style>
{''.join(parts)}
'''
open(OUT, 'w', encoding='utf-8').write(html)

print(f"交差点: 月商 {CROSS_SALES:,.0f}円（{CROSS_SALES/10_000:.1f}万円）  費用 {ganbare(CROSS_SALES):,.0f}円")
print(f"検算 スタンダード側: {standard(CROSS_SALES):,.0f}円")
print(f"月商300万円時: がんばれ {ganbare(3_000_000):,.0f}円 / スタンダード {standard(3_000_000):,.0f}円")
print(f"料率差: {(GANBARE_RATE-STANDARD_RATE)*100:.3f}%  = 40,000円 ÷ {CROSS_SALES:,.0f}円")
print("wrote", OUT)
