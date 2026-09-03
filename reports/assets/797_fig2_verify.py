#!/usr/bin/env python3
"""797 図2の検算：出力PNGの帯を実測して、各セグメントの金額を逆算する。"""

from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PNG = HERE / "797-margin-breakdown@2x.png"

PRICE = 3000
EXPECTED = [
    ("仕入れ値", 1500, (0x6b, 0x77, 0x87)),
    ("決済手数料", 148, (0xe8, 0x76, 0x2a)),
    ("サービス利用料", 90, (0xf2, 0xa6, 0x5a)),
    ("送料", 430, (0x4f, 0x8f, 0xf7)),
    ("梱包資材", 100, (0x9d, 0xbd, 0xf5)),
    ("手元に残る", 732, (0x2f, 0xae, 0x6b)),
]

img = Image.open(PNG).convert("RGB")
W, H = img.size
scale = W / 1600
# 帯の内部（文字やラベル枠を避けるため、帯の上端寄りを走査する）
y = int((300 + 18) * scale)
row = [img.getpixel((x, y)) for x in range(W)]


def near(px, ref, tol=12):
    return all(abs(px[i] - ref[i]) <= tol for i in range(3))


print(f"PNG {W}x{H} (scale={scale:g}) / 走査行 y={y}")
runs = []
for name, yen, rgb in EXPECTED:
    xs = [x for x, px in enumerate(row) if near(px, rgb)]
    if not xs:
        print(f"  {name}: 色が見つからない")
        continue
    runs.append((name, yen, min(xs), max(xs)))

total_px = sum(hi - lo + 1 for _, _, lo, hi in runs)
print(f"帯の実測合計 {total_px}px → 1円あたり {total_px/PRICE:.4f}px\n")
ok = True
for name, yen, lo, hi in runs:
    w = hi - lo + 1
    measured = w / total_px * PRICE
    diff = measured - yen
    flag = "OK " if abs(diff) <= max(6, yen * 0.01) else "NG "
    ok &= flag == "OK "
    print(f"  {flag}{name:<8} 指定{yen:>5}円  実測{measured:8.1f}円  差{diff:+6.1f}円  ({lo}〜{hi}px)")

# セグメントが連続して並んでいるか（隙間や重なりがないか）
runs.sort(key=lambda r: r[2])
for a, b in zip(runs, runs[1:]):
    # 境界の1px はアンチエイリアスで中間色になるため許容する
    gap = b[2] - a[3] - 1
    if gap > 2:
        ok = False
        print(f"  NG 隙間 {a[0]}→{b[0]}: {gap}px")

print("\n判定:", "全セグメント一致" if ok else "ずれあり")
