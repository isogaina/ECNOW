#!/usr/bin/env python3
"""258 図2 の検算。

出力画像をピクセル計測し、積み上げ帯の各セグメントの幅が
「金額 ÷ 売上」の比率と一致しているかを確かめる。
目視では数pxのずれに気づけないため、必ずこれを通す。
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

spec = importlib.util.spec_from_file_location(
    "fig2", Path(__file__).with_name("258_fig2_fee_breakdown.py")
)
fig2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig2)

SCALE = 2
TOL = 20
PAGE_PAD_L = 60         # body の padding-left
SIDE_W = 360            # .row の左カラム幅
GAP = 20                # .row の列間
TRACK_L = (PAGE_PAD_L + SIDE_W + GAP) * SCALE          # 帯の左端(実ピクセル)
TRACK_R = TRACK_L + fig2.CHART_W * SCALE               # 帯の右端(実ピクセル)
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in fig2.COLORS.items()}


def row_groups(mask_rows):
    """連続する行番号をグループにまとめる。"""
    groups, cur = [], []
    for r in mask_rows:
        if cur and r - cur[-1] > 1:
            groups.append(cur)
            cur = []
        cur.append(r)
    if cur:
        groups.append(cur)
    return groups


def segments_at(arr, y, x0=None, x1=None):
    """指定行を左から走査し、(色キー, 幅px) の並びを返す。

    セグメントの境界にはアンチエイリアスの中間色が出る。許容誤差で弾くと
    境界のたびに数pxが計測から消え、全セグメントが一律に短く出てしまう
    （実際これで 0.3pt のずれが出た）。そのため中間色も「最も近い色」に
    割り当てて、1pxも捨てずに数える。
    """
    x0 = TRACK_L if x0 is None else x0
    x1 = TRACK_R if x1 is None else x1
    row = arr[y].astype(int)
    keys = list(RGB)
    ref = np.array([RGB[k] for k in keys])
    out = []
    for x in range(x0, x1):
        px = row[x]
        d = np.abs(ref - px).sum(axis=1)
        j = int(d.argmin())
        # 帯の内側だけを走査しているので、全画素をいずれかの色に割り当てる
        hit = keys[j]
        if hit is None:
            if out and out[-1][0] is not None:
                out.append([None, 1])
            elif out:
                out[-1][1] += 1
            continue
        if out and out[-1][0] == hit:
            out[-1][1] += 1
        else:
            out.append([hit, 1])
    return [(k, w) for k, w in out if k is not None and w > 4]


def main(path):
    arr = np.array(Image.open(path).convert("RGB"))
    print("画像 %s  %dx%d" % (path, arr.shape[1], arr.shape[0]))
    print("トラック幅 %dpx（実ピクセル x=%d〜%d）= 売上100%%"
          % (fig2.CHART_W, TRACK_L, TRACK_R))

    # 帯の行を特定する。凡例のスウォッチ(19px)を拾わないよう長い連続だけを見る
    om = (np.abs(arr.astype(int) - np.array(RGB["sales"])) <= TOL).all(axis=2)
    rows = np.where(om.sum(axis=1) > 150)[0]
    groups = [g for g in row_groups(rows) if len(g) > 20]
    if len(groups) != len(fig2.CASES):
        raise SystemExit("帯が %d 本しか見つからない（期待 %d 本）"
                         % (len(groups), len(fig2.CASES)))

    ok = True
    for g, c in zip(groups, fig2.CASES):
        y = g[len(g) // 2]
        segs = segments_at(arr, y)
        print("\n%s  （帯の行 y=%d）" % (c["name"], y))
        want = c["segs"]
        if len(segs) != len(want):
            print("  NG セグメント数 実測 %d ／ 期待 %d" % (len(segs), len(want)))
            print("     実測:", segs)
            ok = False
            continue
        for (k, w), s in zip(segs, want):
            if k != s["key"]:
                print("  NG 色の並びが違う 実測 %s ／ 期待 %s" % (k, s["key"]))
                ok = False
                continue
            got_pct = w / (fig2.CHART_W * SCALE) * 100
            diff = got_pct - s["pct"]
            mark = "OK " if abs(diff) <= 0.25 else "NG "
            if abs(diff) > 0.25:
                ok = False
            print("  %s%-8s 実測 %7.2fpx = %6.3f%% ／ 期待 %6.3f%%（%s円）／ ずれ %+.3fpt"
                  % (mark, s["label"], w / SCALE, got_pct, s["pct"],
                     format(s["yen"], ","), diff))

        fee_pct = sum(w for (k, w), s in zip(segs, want) if s["key"] != "rest") \
            / (fig2.CHART_W * SCALE) * 100
        diff = fee_pct - c["pct"]
        mark = "OK " if abs(diff) <= 0.25 else "NG "
        if abs(diff) > 0.25:
            ok = False
        print("  %s手数料合計 実測 %.3f%% ／ 期待 %.3f%%（%s円）"
              % (mark, fee_pct, c["pct"], format(c["total"], ",")))

    print("\n判定:", "全て一致" if ok else "ずれあり")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
