#!/usr/bin/env python3
"""ベースフード 2026年2月期のチャネル別売上構成比（100%積み上げ帯）を SVG で生成する。

座標は一切手打ちせず、すべて売上金額から計算する。
出力後に 1059_fig2_verify.py でピクセル計測して構成比を逆算し、検算する。

出典: ベースフード 2026年2月期 決算説明会
      https://finance.logmi.jp/articles/384348
"""
from pathlib import Path

W, H = 1600, 900

# --- データ（億円）。決算説明会で示されたチャネル別売上高 ---
CHANNELS = [
    # (名前, 売上高[億円], 前期比[%], 色, 文字色)
    ("自社EC",              100.3,   3.2, "#2f6fed", "#ffffff"),
    ("卸売",                 39.4, -11.6, "#e8762a", "#ffffff"),
    ("他社EC",                9.5,  12.1, "#7fa8f2", "#ffffff"),
    ("海外",                  2.1,  18.8, "#f2b56b", "#ffffff"),
]
TOTAL_COMPANY = 151.9188  # 全社売上高（億円）。チャネル合計との差は端数

TOTAL = sum(c[1] for c in CHANNELS)          # 151.3
DIRECT = CHANNELS[0][1]                       # 自社EC
INDIRECT = TOTAL - DIRECT                     # 卸 + 他社EC + 海外

# --- 帯の幾何 ---
BAR_X, BAR_W = 130, 1340
BAR_Y, BAR_H = 372, 132
LABEL_Y = 640          # 小さいセグメントの引き出しラベルの基準線
BRACKET_Y = 330        # 帯の上に置く括弧

FONT = "Hiragino Sans, Hiragino Kaku Gothic ProN, Noto Sans JP, sans-serif"


def seg_width(value: float) -> float:
    return BAR_W * value / TOTAL


def pct(value: float) -> float:
    return 100.0 * value / TOTAL


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size, weight="400", fill="#1f2430", anchor="start", opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{op}>{esc(s)}</text>')


def bracket(x1, x2, y, label, sublabel, color):
    """帯の上に置く、下向きの角括弧と見出し。"""
    d = 14
    out = [
        f'<path d="M {x1:.1f} {y - d} L {x1:.1f} {y} L {x2:.1f} {y} L {x2:.1f} {y - d}" '
        f'fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
    ]
    cx = (x1 + x2) / 2
    out.append(text(cx, y - 56, label, 34, "700", color, "middle"))
    out.append(text(cx, y - 26, sublabel, 19, "400", "#7a8496", "middle"))
    return out


def main():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        text(W / 2, 92, "ベースフードの売上は自社ECが約3分の2", 42, "700", "#1f2430", "middle"),
        text(W / 2, 146, "残りの3分の1は卸と他社ECが占めている", 42, "700", "#1f2430", "middle"),
        text(W / 2, 196, "2026年2月期 チャネル別売上高（合計 151.3億円）", 22, "400", "#7a8496", "middle"),
    ]

    # --- 上の括弧（自社EC / それ以外） ---
    x_split = BAR_X + seg_width(DIRECT)
    parts += bracket(BAR_X, x_split, BRACKET_Y,
                     f"約3分の2（{pct(DIRECT):.0f}%）", "自社ECの直販", "#2f6fed")
    parts += bracket(x_split, BAR_X + BAR_W, BRACKET_Y,
                     f"約3分の1（{pct(INDIRECT):.0f}%）", "卸・他社EC・海外", "#e8762a")

    # --- 帯本体 ---
    parts.append(f'<clipPath id="barclip"><rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" '
                 f'height="{BAR_H}" rx="10"/></clipPath>')
    parts.append(f'<g clip-path="url(#barclip)">')

    x = float(BAR_X)
    geom = []  # (name, x0, w, color, pct, yoy)
    for name, value, yoy, color, tcolor in CHANNELS:
        w = seg_width(value)
        parts.append(f'<rect x="{x:.2f}" y="{BAR_Y}" width="{w:.2f}" height="{BAR_H}" fill="{color}"/>')
        geom.append((name, x, w, color, pct(value), yoy, value, tcolor))
        x += w
    parts.append("</g>")

    # セグメントの境目に白い区切り線（クリップ外に描いて角丸を保つ）
    x = float(BAR_X)
    for _, value, *_ in CHANNELS[:-1]:
        x += seg_width(value)
        parts.append(f'<line x1="{x:.2f}" y1="{BAR_Y}" x2="{x:.2f}" y2="{BAR_Y + BAR_H}" '
                     f'stroke="#ffffff" stroke-width="3"/>')

    # --- ラベル ---
    # 幅の広いセグメントは帯の中に、狭いものは引き出し線で下に出す
    INSIDE_MIN_W = 200
    leaders = []
    for name, x0, w, color, share, yoy, value, tcolor in geom:
        cx = x0 + w / 2
        if w >= INSIDE_MIN_W:
            parts.append(text(cx, BAR_Y + 48, name, 28, "700", tcolor, "middle"))
            parts.append(text(cx, BAR_Y + 86, f"{value:.1f}億円", 30, "700", tcolor, "middle"))
            parts.append(text(cx, BAR_Y + 116, f"{share:.1f}%", 20, "400", tcolor, "middle", opacity="0.85"))
        else:
            leaders.append((name, cx, color, share, yoy, value))

    # 引き出し線は互いに重ならないよう、右から順に間隔を空けて置く
    step = 250
    base_x = BAR_X + BAR_W - 40
    for i, (name, cx, color, share, yoy, value) in enumerate(reversed(leaders)):
        lx = base_x - i * step
        ly = LABEL_Y + i * 0
        parts.append(f'<path d="M {cx:.1f} {BAR_Y + BAR_H} L {cx:.1f} {ly - 78:.1f} '
                     f'L {lx:.1f} {ly - 78:.1f}" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<circle cx="{lx:.1f}" cy="{ly - 78:.1f}" r="4" fill="{color}"/>')
        parts.append(text(lx, ly - 42, name, 25, "700", "#1f2430", "middle"))
        parts.append(text(lx, ly - 8, f"{value:.1f}億円（{share:.1f}%）", 21, "400", "#5b6577", "middle"))

    # --- 前期比 ---
    parts.append(text(BAR_X, 726, "前期比", 20, "700", "#7a8496"))
    yoy_x = BAR_X + 110
    for i, (name, x0, w, color, share, yoy, value, tcolor) in enumerate(geom):
        gx = yoy_x + i * 300
        up = yoy >= 0
        arrow_color = "#2f9e5e" if up else "#d84c3f"
        sign = "+" if up else ""
        parts.append(f'<rect x="{gx:.1f}" y="700" width="14" height="14" rx="3" fill="{color}"/>')
        parts.append(text(gx + 26, 713, name, 21, "700", "#1f2430"))
        parts.append(text(gx + 26, 745, f"{sign}{yoy:.1f}%", 25, "700", arrow_color))

    # --- 脚注 ---
    parts.append(text(BAR_X, 818,
                      "構成比は4チャネルの合計151.3億円を100%として算出（全社売上高は151億9,188万円）",
                      18, "400", "#98a1b0"))
    parts.append(text(BAR_X, 848,
                      "出典：ベースフード 2026年2月期 決算説明会",
                      18, "400", "#98a1b0"))

    parts.append("</svg>")

    out = Path(__file__).with_name("1059_fig2_basefood_channels.svg")
    out.write_text("\n".join(parts), encoding="utf-8")

    # 検算用に期待値を出しておく
    print(f"TOTAL={TOTAL:.1f}億円  BAR_X={BAR_X} BAR_W={BAR_W}")
    x = float(BAR_X)
    for name, value, yoy, color, _ in CHANNELS:
        w = seg_width(value)
        print(f"  {name:8s} {value:6.1f}億円  {pct(value):6.3f}%  x=[{x:8.2f}, {x + w:8.2f}]  w={w:8.2f}  {color}")
        x += w
    print(f"  自社EC比率 {pct(DIRECT):.3f}%  それ以外 {pct(INDIRECT):.3f}%")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
