#!/usr/bin/env python3
"""出力画像をピクセル計測し、帯グラフの構成比が売上金額どおりかを逆算して検算する。

目視では数ピクセルのずれに気づけないため、色ごとの実測幅から構成比を復元し、
決算値から計算した理論値と突き合わせる。
"""
from PIL import Image
from pathlib import Path

import importlib.util

spec = importlib.util.spec_from_file_location(
    "fig2", Path(__file__).with_name("1059_fig2_basefood_channels.py"))
fig2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig2)

IMG = Path(__file__).with_name("1059-basefood-channels.png")
im = Image.open(IMG).convert("RGB")
W, H = im.size
scale = W / fig2.W

# 帯の縦中央より少し下（文字が乗っていない行）を走査する
y = int((fig2.BAR_Y + fig2.BAR_H - 12) * scale)
row = [im.getpixel((x, y)) for x in range(W)]


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def close(a, b, tol=10):
    return all(abs(p - q) <= tol for p, q in zip(a, b))


print(f"計測行 y={y}px（画像 {W}x{H}）\n")

widths = {}
for name, value, yoy, color, _ in fig2.CHANNELS:
    target = hex2rgb(color)
    xs = [x for x, px in enumerate(row) if close(px, target)]
    if not xs:
        print(f"  {name}: 該当ピクセルなし")
        continue
    widths[name] = (min(xs), max(xs), max(xs) - min(xs) + 1)

# 白い区切り線(3px)ぶんは各セグメントから欠けるので、境界の中点で幅を取り直す
bounds = sorted((v[0], v[1], k) for k, v in widths.items())
measured = {}
for i, (x0, x1, name) in enumerate(bounds):
    left = x0 if i == 0 else (bounds[i - 1][1] + x0) / 2
    right = x1 if i == len(bounds) - 1 else (x1 + bounds[i + 1][0]) / 2
    measured[name] = right - left

total_px = sum(measured.values())
print(f"{'チャネル':<10}{'理論%':>9}{'実測%':>9}{'差':>8}")
ok = True
for name, value, yoy, color, _ in fig2.CHANNELS:
    theo = fig2.pct(value)
    meas = 100 * measured[name] / total_px
    diff = meas - theo
    flag = "" if abs(diff) < 0.35 else "  ← ずれ"
    if abs(diff) >= 0.35:
        ok = False
    print(f"{name:<10}{theo:>8.3f}%{meas:>8.3f}%{diff:>+8.3f}{flag}")

# 帯全体の位置も確認
bar_left = min(v[0] for v in widths.values())
bar_right = max(v[1] for v in widths.values())
print(f"\n帯の実測範囲 x=[{bar_left}, {bar_right}]  幅={bar_right - bar_left + 1}px")
print(f"理論値       x=[{fig2.BAR_X * scale:.0f}, {(fig2.BAR_X + fig2.BAR_W) * scale:.0f}]  "
      f"幅={fig2.BAR_W * scale:.0f}px")

# 自社EC と それ以外 の比率（記事本文の「約3分の2 / 約3分の1」の根拠）
direct = 100 * measured["自社EC"] / total_px
print(f"\n自社EC {direct:.2f}%（理論 {fig2.pct(fig2.DIRECT):.2f}%） / "
      f"それ以外 {100 - direct:.2f}%（理論 {fig2.pct(fig2.INDIRECT):.2f}%）")
print("\n検算結果:", "OK" if ok else "NG")
