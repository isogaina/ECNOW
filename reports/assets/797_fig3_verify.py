#!/usr/bin/env python3
"""797 図3の検算：出力PNGから軸と3つのマーカー位置を実測し、日付に逆変換して照合する。

目視では数日〜数週間のずれに気づけないため、必ずこれを通す。
"""
from datetime import date, timedelta
from pathlib import Path

from PIL import Image

AXIS_START = date(2026, 4, 1)
AXIS_END = date(2027, 4, 30)
SPAN = (AXIS_END - AXIS_START).days

EXPECTED = [
    ("開業日", date(2026, 6, 1), (0x5B, 0x65, 0x77)),
    ("青色期限", date(2026, 8, 1), (0xE8, 0x76, 0x2A)),
    ("確申期限", date(2027, 3, 15), (0x2F, 0x6F, 0xED)),
]

AXIS_RGB = (0xC3, 0xCA, 0xD6)
TOL = 24

img = Image.open(Path(__file__).with_name("797-deadlines@2x.png")).convert("RGB")
W, H = img.size
px = img.load()


def near(c, target, tol=TOL):
    return all(abs(c[i] - target[i]) <= tol for i in range(3))


# 1) 軸（薄いグレーの横線）が最も長く走る行を探し、そこから軸の左端・右端を得る
best = (0, None)
for y in range(H):
    run = sum(1 for x in range(W) if near(px[x, y], AXIS_RGB))
    if run > best[0]:
        best = (run, y)
axis_y = best[1]
xs = [x for x in range(W) if near(px[x, axis_y], AXIS_RGB)]
axis_x0, axis_x1 = min(xs), max(xs)
axis_w = axis_x1 - axis_x0
print("axis row y=%d  x=%d..%d  width=%dpx" % (axis_y, axis_x0, axis_x1, axis_w))

# 2) 各マーカーの丸（軸上に置かれた色付きの円）の中心を実測する
#    丸は軸線より上下に張り出すので、軸y近傍の数行で色の連なりが最も広い行を採る
ok = True
for name, expect_date, rgb in EXPECTED:
    best_run = None
    for y in range(axis_y - 14, axis_y + 15):
        if y < 0 or y >= H:
            continue
        runs, cur = [], None
        for x in range(W):
            if near(px[x, y], rgb):
                cur = [x, x] if cur is None else [cur[0], x]
            elif cur is not None:
                runs.append(cur)
                cur = None
        if cur is not None:
            runs.append(cur)
        # 縦線(3px*2=6px)や「2か月」バンドの枠線(帯の全幅)を拾わないよう
        # 丸(19px*2=38px)の幅に収まる連なりだけを候補にする
        for r in runs:
            w = r[1] - r[0] + 1
            if 20 <= w <= 50 and (best_run is None or w > best_run[1] - best_run[0] + 1):
                best_run = r
    if best_run is None:
        print("  %-6s 丸を検出できず" % name)
        ok = False
        continue

    cx = (best_run[0] + best_run[1]) / 2
    frac = (cx - axis_x0) / axis_w
    measured = AXIS_START + timedelta(days=round(frac * SPAN))
    diff_days = (measured - expect_date).days
    exp_cx = axis_x0 + axis_w * ((expect_date - AXIS_START).days / SPAN)
    status = "OK" if abs(diff_days) <= 2 else "NG"
    if status == "NG":
        ok = False
    print(
        "  %-6s 実測x=%.1f (期待%.1f / 差%.1fpx)  → %s（期待 %s / 差 %+d日）  %s"
        % (name, cx, exp_cx, cx - exp_cx, measured, expect_date, diff_days, status)
    )

print("\n結果:", "全マーカーが期待日と一致" if ok else "ずれあり")
