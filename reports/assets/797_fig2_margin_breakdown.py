#!/usr/bin/env python3
"""797（ネットショップ開業）図2：3,000円の商品が売れたときの内訳を積み上げ帯で描く。

座標は一切手打ちせず、金額から幅を計算する。
出力した PNG は 797_fig2_verify.py でピクセル計測して検算する。
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent / "797_fig2_margin_breakdown.svg"

PRICE = 3000  # 送料込みの販売価格

# (ラベル, 金額, 色, 補足)
SEGMENTS = [
    ("仕入れ値", 1500, "#6b7787", ""),
    ("決済手数料", 148, "#e8762a", "3.6%＋40円"),
    ("サービス利用料", 90, "#f2a65a", "3%"),
    ("送料", 430, "#4f8ff7", "レターパックライト"),
    ("梱包資材", 100, "#9dbdf5", "箱・緩衝材など"),
    ("手元に残る", 732, "#2fae6b", ""),
]

assert sum(s[1] for s in SEGMENTS) == PRICE, "内訳の合計が販売価格と一致しない"

W, H = 1600, 700
PAD_X = 64
BAR_X = PAD_X
BAR_W = W - PAD_X * 2          # 1472px = 3,000円
BAR_Y = 300
BAR_H = 116
PX_PER_YEN = BAR_W / PRICE

# 幅が十分あるセグメントは帯の中に名前と金額を書き、
# 細いセグメントだけ帯の下に引き出してラベルを置く（2段に振って重なりを避ける）。
INBAR_MIN_W = 150
ROW_Y = [520, 640]
LABEL_W = 250


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
    '<style>'
    'text{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;fill:#1f2430}'
    '.h1{font-size:40px;font-weight:700}'
    '.sub{font-size:21px;fill:#7a8496}'
    '.seg{font-size:30px;font-weight:700;fill:#ffffff}'
    '.segname{font-size:21px;font-weight:700;fill:#ffffff;opacity:.9}'
    '.lb{font-size:24px;font-weight:700}'
    '.lv{font-size:30px;font-weight:700}'
    '.ln{font-size:17px;fill:#8a94a6}'
    '.foot{font-size:19px;fill:#5b6577}'
    '.axis{font-size:19px;fill:#8a94a6}'
    '</style>',
    f'<text class="h1" x="{W/2}" y="78" text-anchor="middle">3,000円の商品が1件売れて手元に残るのは732円</text>',
    f'<text class="sub" x="{W/2}" y="122" text-anchor="middle">'
    'BASEのスタンダードプランで送料込み3,000円の商品を1件売った場合の内訳</text>',
]

# 目盛り（500円ごと）
for yen in range(0, PRICE + 1, 500):
    x = BAR_X + yen * PX_PER_YEN
    parts.append(
        f'<line x1="{x:.2f}" y1="{BAR_Y - 34}" x2="{x:.2f}" y2="{BAR_Y - 10}" '
        f'stroke="#dde2ea" stroke-width="2"/>'
    )
    parts.append(
        f'<text class="axis" x="{x:.2f}" y="{BAR_Y - 46}" text-anchor="middle">{yen:,}円</text>'
    )

# 帯
x = BAR_X
boxes = []
for i, (name, yen, color, note) in enumerate(SEGMENTS):
    w = yen * PX_PER_YEN
    parts.append(
        f'<rect x="{x:.2f}" y="{BAR_Y}" width="{w:.2f}" height="{BAR_H}" fill="{color}"/>'
    )
    # 幅に余裕があるセグメントは帯の中に名前と金額を書く
    if w >= INBAR_MIN_W:
        parts.append(
            f'<text class="segname" x="{x + w/2:.2f}" y="{BAR_Y + 44:.2f}" '
            f'text-anchor="middle">{esc(name)}</text>'
        )
        parts.append(
            f'<text class="seg" x="{x + w/2:.2f}" y="{BAR_Y + 88:.2f}" '
            f'text-anchor="middle">{yen:,}円</text>'
        )
    else:
        boxes.append((name, yen, color, note, x, w))
    x += w

parts.append(
    f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" '
    f'fill="none" stroke="#ffffff" stroke-width="2"/>'
)

# 細いセグメントのラベル。ラベル同士が重ならないよう、
# セグメントの中心の平均を軸にして等間隔（GAP）で並べ直し、引き出し線で結ぶ。
GAP = LABEL_W + 34
ly = ROW_Y[0]
if boxes:
    centers = [sx + sw / 2 for _, _, _, _, sx, sw in boxes]
    base = sum(centers) / len(centers)
    span = GAP * (len(boxes) - 1)
    start = min(
        max(base - span / 2, BAR_X + LABEL_W / 2),
        BAR_X + BAR_W - LABEL_W / 2 - span,
    )
    for i, (name, yen, color, note, sx, sw) in enumerate(boxes):
        cx = sx + sw / 2
        lx = start + GAP * i
        parts.append(
            f'<path d="M {cx:.2f} {BAR_Y + BAR_H} L {cx:.2f} {BAR_Y + BAR_H + 34} '
            f'L {lx:.2f} {ly - 74:.2f} L {lx:.2f} {ly - 58:.2f}" '
            f'fill="none" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(
            f'<rect x="{lx - LABEL_W/2:.2f}" y="{ly - 58:.2f}" width="{LABEL_W}" '
            f'height="{92 if note else 68}" rx="10" fill="#ffffff" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(
            f'<text class="lb" x="{lx:.2f}" y="{ly - 26:.2f}" text-anchor="middle" fill="{color}">{esc(name)}</text>'
        )
        parts.append(
            f'<text class="lv" x="{lx:.2f}" y="{ly + 8:.2f}" text-anchor="middle">{yen:,}円</text>'
        )
        if note:
            parts.append(
                f'<text class="ln" x="{lx:.2f}" y="{ly + 30:.2f}" text-anchor="middle">{esc(note)}</text>'
            )

parts.append(
    f'<rect x="{PAD_X}" y="{H - 92}" width="{W - PAD_X*2}" height="66" rx="10" fill="#f5f7fb"/>'
)
parts.append(
    f'<text class="foot" x="{PAD_X + 26}" y="{H - 52}">'
    '決済手数料とサービス利用料はBASEスタンダードプランの料率。仕入れ値・送料・梱包資材費は例として置いた金額で 商品によって変わります</text>'
)
parts.append("</svg>")

OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"wrote {OUT}")
print(f"BAR_W={BAR_W}px / {PRICE}円 = {PX_PER_YEN:.6f} px/円")
for name, yen, color, note, sx, sw in boxes:
    print(f"  {name:<8} {yen:>5}円  x={sx:8.2f}  w={sw:7.2f}px  {color}")
