#!/usr/bin/env python3
"""797 図3(v2) の検算。

出力画像をピクセル計測し、帯の端が本当にその日付の位置にあるかを確かめる。
目視では数pxのずれに気づけないため、必ずこれを通す。

検証する内容:
  1. 2本の帯の左端が一致し、その位置が 2026-06-01 であること
  2. オレンジの帯の右端が 2026-08-01 であること
  3. 青い帯の右端が 2027-03-15 であること
  4. 帯の長さの比が 287/61 = 4.70倍 であること
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "fig3", Path(__file__).with_name("797_fig3_deadlines.py")
)
# 生成スクリプトは import 時に HTML を書き出すが、値の定義を借りるだけなので許容する
fig3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig3)

SCALE = 2                       # --force-device-scale-factor=2 で撮影した前提
PAGE_PAD_L = 60                 # body の padding-left
CHART_MARGIN_L = (1600 - PAGE_PAD_L * 2 - fig3.CHART_W) / 2   # margin:auto の左余白
ORIGIN = (PAGE_PAD_L + CHART_MARGIN_L) * SCALE                # チャート x=0 の実ピクセル

ORANGE = (232, 118, 42)         # #e8762a
BLUE = (47, 111, 237)           # #2f6fed
AXIS_GRAY = (195, 202, 214)     # #c3cad6
TOL = 26


def band_extent(arr, y0, y1, rgb):
    """y0..y1 の帯の中から指定色の境界線を探し、左端・右端の実ピクセルを返す。"""
    sub = arr[int(y0):int(y1)]
    m = (np.abs(sub.astype(int) - np.array(rgb)) <= TOL).all(axis=2)
    cols = np.where(m.any(axis=0))[0]
    if len(cols) == 0:
        raise SystemExit("色 %s が見つからない（y=%d..%d）" % (rgb, y0, y1))
    return cols.min(), cols.max()


def px_to_date(px):
    """実ピクセルを軸上の日付に戻す。"""
    chart_x = (px - ORIGIN) / SCALE
    days = chart_x / fig3.CHART_W * fig3.SPAN
    return fig3.AXIS_START + __import__("datetime").timedelta(days=round(days)), days


def main(path):
    arr = np.array(Image.open(path).convert("RGB"))
    print("画像 %s  %dx%d" % (path, arr.shape[1], arr.shape[0]))
    print("チャート原点 x=%.1fpx（実ピクセル）／1日あたり %.4fpx"
          % (ORIGIN, fig3.CHART_W / fig3.SPAN * SCALE))

    # チャートの縦位置は h1/sub の実高に依存するため、軸そのものを探して基準にする。
    # 軸は #c3cad6 がチャート全幅(1400px*2)にわたって並ぶ唯一の行なので一意に決まる。
    axm = (np.abs(arr.astype(int) - np.array(AXIS_GRAY)) <= TOL).all(axis=2)
    axis_rows = np.where(axm.sum(axis=1) > fig3.CHART_W * SCALE * 0.9)[0]
    if len(axis_rows) == 0:
        raise SystemExit("軸が見つからない")
    chart_y0 = axis_rows.min() - fig3.AXIS_TOP * SCALE
    print("軸の実測y=%d → チャート原点 y=%.1fpx" % (axis_rows.min(), chart_y0))

    # 帯の縦中央だけを見る（引き出し線は帯の上下にあり ここには入らない）
    y1 = chart_y0 + (fig3.BAR1_TOP + fig3.BAR_H / 2) * SCALE
    y2 = chart_y0 + (fig3.BAR2_TOP + fig3.BAR_H / 2) * SCALE

    o_l, o_r = band_extent(arr, y1 - 6, y1 + 6, ORANGE)
    b_l, b_r = band_extent(arr, y2 - 6, y2 + 6, BLUE)

    ok = True
    checks = [
        ("オレンジ帯 左端", o_l, fig3.OPEN),
        ("オレンジ帯 右端", o_r, fig3.BLUE_DEADLINE),
        ("青帯 左端", b_l, fig3.OPEN),
        ("青帯 右端", b_r, fig3.TAX_DEADLINE),
    ]
    print()
    for name, px, want in checks:
        got, days = px_to_date(px)
        want_px = ORIGIN + fig3.x(want) * SCALE
        diff = px - want_px
        mark = "OK " if abs(diff) <= 4 else "NG "
        if abs(diff) > 4:
            ok = False
        print("  %s%-16s 実測 x=%6.1fpx → %s ／ 期待 %s (x=%6.1fpx) ／ ずれ %+.1fpx (%+.1f日)"
              % (mark, name, px, got, want, want_px, diff,
                 diff / SCALE / fig3.CHART_W * fig3.SPAN))

    # 左端の一致
    d = abs(o_l - b_l)
    mark = "OK " if d <= 4 else "NG "
    if d > 4:
        ok = False
    print("\n  %s2本の帯の左端の差 %.1fpx（起点が揃っていること）" % (mark, d))

    # 長さの比
    ratio = (b_r - b_l) / (o_r - o_l)
    want_ratio = fig3.D_TAX / fig3.D_BLUE
    mark = "OK " if abs(ratio - want_ratio) < 0.06 else "NG "
    if abs(ratio - want_ratio) >= 0.06:
        ok = False
    print("  %s帯の長さの比 実測 %.3f倍 ／ 期待 %d/%d=%.3f倍"
          % (mark, ratio, fig3.D_TAX, fig3.D_BLUE, want_ratio))

    print("\n判定:", "全て一致" if ok else "ずれあり")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
