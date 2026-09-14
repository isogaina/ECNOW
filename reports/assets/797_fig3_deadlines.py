#!/usr/bin/env python3
"""797 図3: 開業日を起点にした届出の期限タイムラインのHTMLを生成する。

軸上の座標は日付から計算する（手打ちしない）。
- 開業届     : 事業の開始等の事実があった日の属する年分の確定申告期限まで
               https://www.nta.go.jp/taxes/tetsuzuki/shinsei/annai/shinkoku/annai/04.htm
- 青色申告承認申請書 : その年の3月15日まで
               （1月16日以後に開業した場合は開業日から2か月以内）
               https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/2090.htm

v2 の変更（読みにくさの原因を潰した）:
- 期限カードを2枚に絞り、下端を揃えて同じ高さに置いた（旧版は3枚が別々の高さ）
- カードと縦線の位置関係を統一した（旧版は左端／外側／右端でバラバラだった）
- 起点からの日数を2本の帯で並べ、どちらが先に来るかを長さで示すようにした
- 開業日は起点なのでカードをやめ、軸の下のピンに変更した
- 目盛りラベルの行数を全て2行に揃えた
"""
from datetime import date
from pathlib import Path

# 作図に使う例：2026年6月1日に開業した場合
OPEN = date(2026, 6, 1)
BLUE_DEADLINE = date(2026, 8, 1)      # 開業日から2か月以内
TAX_DEADLINE = date(2027, 3, 15)      # 開業した年分の確定申告期限

AXIS_START = date(2026, 4, 1)
AXIS_END = date(2027, 4, 30)
SPAN = (AXIS_END - AXIS_START).days

CHART_W = 1400          # チャートの実幅(px)。座標は全てここからの計算で出す
CARD_W = 470
CARD_BOTTOM = 150       # カード下端のy
BAR1_TOP, BAR2_TOP, BAR_H = 178, 232, 46
AXIS_TOP = 294


def x(d: date) -> float:
    """日付を軸上のx座標(px)に変換する。"""
    return (d - AXIS_START).days / SPAN * CHART_W


def months(start: date, end: date):
    """軸に置く月初の目盛りを列挙する。"""
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        yield date(y, m, 1)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def clamp_card(cx: float) -> float:
    """カード左端のx。中央をcxに置きつつチャート内に収める。"""
    return max(0.0, min(cx - CARD_W / 2, CHART_W - CARD_W))


X_OPEN, X_BLUE, X_TAX = x(OPEN), x(BLUE_DEADLINE), x(TAX_DEADLINE)
D_BLUE = (BLUE_DEADLINE - OPEN).days
D_TAX = (TAX_DEADLINE - OPEN).days

ticks = "\n".join(
    '  <div class="tick{cls}" style="left:{p:.2f}px">'
    '<span><b>{m}月</b><i>{y}</i></span></div>'.format(
        p=x(d),
        cls=" year" if d.month == 1 or d == AXIS_START else "",
        m=d.month,
        y=("%d年" % d.year) if (d.month == 1 or d == AXIS_START) else "&nbsp;",
    )
    for d in months(AXIS_START, AXIS_END)
)

HTML = f"""<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1600px; height:760px; background:#fff;
    font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;
    color:#1f2430;
    display:flex; flex-direction:column;
    padding:38px 60px 28px;
  }}
  h1 {{ font-size:39px; font-weight:700; text-align:center; }}
  .sub {{ text-align:center; font-size:20px; color:#7a8496; margin-top:9px; }}

  .chart {{ position:relative; width:{CHART_W}px; height:432px; margin:34px auto 0; }}

  /* --- 軸と目盛り --- */
  .axis {{
    position:absolute; left:0; width:{CHART_W}px; top:{AXIS_TOP}px; height:5px;
    background:#c3cad6; border-radius:3px;
  }}
  .tick {{ position:absolute; top:{AXIS_TOP + 5}px; }}
  .tick::before {{
    content:""; position:absolute; left:0; top:-10px; width:2px; height:14px; background:#c3cad6;
  }}
  .tick.year::before {{ height:20px; top:-16px; width:3px; background:#8a94a6; }}
  .tick span {{
    position:absolute; left:0; top:11px; transform:translateX(-50%);
    font-size:16px; color:#8a94a6; white-space:nowrap; text-align:center; line-height:1.3;
    display:flex; flex-direction:column; align-items:center;
  }}
  .tick b {{ font-weight:400; }}
  .tick i {{ font-style:normal; font-size:14px; color:#aab3c0; }}
  .tick.year b {{ color:#5b6577; font-weight:700; }}
  .tick.year i {{ color:#5b6577; font-weight:700; }}

  /* --- 起点からの日数を示す帯 --- */
  .bar {{ position:absolute; height:{BAR_H}px; border-radius:8px; display:flex; align-items:center; }}
  .bar .lb {{
    font-size:20px; font-weight:700; white-space:nowrap;
    position:absolute; left:50%; transform:translateX(-50%);
  }}
  .bar.warn {{ background:#fbe0c8; border:3px solid #e8762a; }}
  .bar.warn .lb {{ color:#a3520f; }}
  .bar.calm {{ background:#e4ecfd; border:3px solid #2f6fed; }}
  .bar.calm .lb {{ color:#1f4fae; }}

  /* --- 期限カード --- */
  .card {{
    position:absolute; width:{CARD_W}px; height:{CARD_BOTTOM}px; top:0;
    border-radius:12px; padding:13px 20px; border:3px solid;
  }}
  .card .date {{ font-size:17px; font-weight:700; letter-spacing:.03em; }}
  .card .txt {{ font-size:29px; font-weight:700; line-height:1.22; margin-top:3px; }}
  .card .ex {{ font-size:16px; color:#5b6577; margin-top:6px; line-height:1.45; }}
  .card.warn {{ border-color:#e8762a; background:#fdf0e4; }}
  .card.warn .date, .card.warn .txt {{ color:#a3520f; }}
  .card.calm {{ border-color:#2f6fed; background:#eef3fe; }}
  .card.calm .date, .card.calm .txt {{ color:#1f4fae; }}
  .card .flag {{
    position:absolute; top:-17px; left:18px;
    font-size:15px; font-weight:700; color:#fff; background:#e8762a;
    padding:4px 13px; border-radius:999px; letter-spacing:.04em;
  }}

  /* --- カードと帯をつなぐ線／帯と軸をつなぐ線 --- */
  .lead {{ position:absolute; width:3px; transform:translateX(-50%); }}
  .lead.warn {{ background:#e8762a; }}
  .lead.calm {{ background:#2f6fed; }}
  .lead.start {{ background:#8a94a6; }}

  .dot {{
    position:absolute; width:19px; height:19px; border-radius:50%;
    border:4px solid #fff; transform:translate(-50%,-50%); top:{AXIS_TOP + 2}px;
  }}
  .dot.warn {{ background:#e8762a; }}
  .dot.calm {{ background:#2f6fed; }}
  .dot.start {{ background:#5b6577; }}

  /* --- 開業日のピン --- */
  .pin {{
    position:absolute; top:{AXIS_TOP + 66}px; transform:translateX(-50%);
    background:#eef1f6; border:3px solid #8a94a6; border-radius:10px;
    padding:7px 16px; text-align:center; white-space:nowrap;
  }}
  .pin .d {{ font-size:15px; font-weight:700; color:#5b6577; }}
  .pin .t {{ font-size:22px; font-weight:700; color:#1f2430; margin-top:1px; }}
  .pinline {{
    position:absolute; width:3px; background:#8a94a6; transform:translateX(-50%);
    top:{AXIS_TOP + 5}px; height:61px;
  }}

  .foot {{
    margin-top:auto; background:#f5f7fb; border-radius:10px; padding:15px 24px;
    font-size:18px; line-height:1.6; color:#5b6577;
  }}
  .foot b {{ color:#1f2430; }}
  .foot .row + .row {{ margin-top:6px; }}
</style>

<h1>開業届と青色申告承認申請書は期限が違う</h1>
<p class="sub">2026年6月1日に開業した場合　先に来るのは青色申告承認申請書のほう</p>

<div class="chart">
  <div class="axis"></div>
{ticks}

  <!-- 期限カード（下端を揃えて同じ高さに置く） -->
  <div class="card warn" style="left:{clamp_card(X_BLUE):.2f}px">
    <div class="flag">先に来る</div>
    <div class="date">2026年8月1日／開業日から2か月以内</div>
    <div class="txt">青色申告承認申請書の期限</div>
    <div class="ex">過ぎると初年度は白色申告になり 65万円控除も赤字の3年繰越も使えない</div>
  </div>
  <div class="card calm" style="left:{clamp_card(X_TAX):.2f}px">
    <div class="date">2027年3月15日／確定申告期限</div>
    <div class="txt">開業届の期限</div>
    <div class="ex">「開業から1か月以内」ではない（国税庁の手続案内）</div>
  </div>

  <!-- カード下端から帯の右端へ落とす線 -->
  <div class="lead warn" style="left:{X_BLUE:.2f}px; top:{CARD_BOTTOM}px; height:{BAR1_TOP - CARD_BOTTOM}px"></div>
  <div class="lead calm" style="left:{X_TAX:.2f}px; top:{CARD_BOTTOM}px; height:{BAR2_TOP - CARD_BOTTOM}px"></div>

  <!-- 開業日を起点にした2本の帯（長さがそのまま余裕の差） -->
  <div class="bar warn" style="left:{X_OPEN:.2f}px; width:{X_BLUE - X_OPEN:.2f}px; top:{BAR1_TOP}px">
    <div class="lb">2か月（{D_BLUE}日）</div>
  </div>
  <div class="bar calm" style="left:{X_OPEN:.2f}px; width:{X_TAX - X_OPEN:.2f}px; top:{BAR2_TOP}px">
    <div class="lb">9か月半（{D_TAX}日）</div>
  </div>

  <!-- 帯の端から軸へ落とす線 -->
  <div class="lead start" style="left:{X_OPEN:.2f}px; top:{BAR1_TOP}px; height:{AXIS_TOP - BAR1_TOP}px"></div>
  <div class="lead warn" style="left:{X_BLUE:.2f}px; top:{BAR1_TOP + BAR_H}px; height:{AXIS_TOP - BAR1_TOP - BAR_H}px"></div>
  <div class="lead calm" style="left:{X_TAX:.2f}px; top:{BAR2_TOP + BAR_H}px; height:{AXIS_TOP - BAR2_TOP - BAR_H}px"></div>

  <div class="dot start" style="left:{X_OPEN:.2f}px"></div>
  <div class="dot warn" style="left:{X_BLUE:.2f}px"></div>
  <div class="dot calm" style="left:{X_TAX:.2f}px"></div>

  <div class="pinline" style="left:{X_OPEN:.2f}px"></div>
  <div class="pin" style="left:{X_OPEN:.2f}px">
    <div class="d">2026年6月1日</div>
    <div class="t">開業日</div>
  </div>
</div>

<div class="foot">
  <div class="row">青色申告承認申請書は<b>その年の3月15日まで</b>。1月16日以後に開業した場合だけ<b>開業日から2か月以内</b>になる。開業日は売り始めた日を自分で決めて届出書に書く。</div>
  <div class="row">期限は先でも、<b>楽天市場などのモールは出店の申込時点で開業届の控えを求める</b>ため、モールを考えているなら先に出しておく。</div>
</div>
"""

out = Path(__file__).with_name("797_fig3_deadlines.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out)
print("axis %s -> %s (%d days), chart width %dpx" % (AXIS_START, AXIS_END, SPAN, CHART_W))
for name, d in (("開業日", OPEN), ("青色期限", BLUE_DEADLINE), ("確申期限", TAX_DEADLINE)):
    print("  %-6s %s  x=%8.2fpx (%.4f%%)" % (name, d, x(d), x(d) / CHART_W * 100))
print("  帯の長さ  青色=%d日 / 開業届=%d日  比 %.2f倍" % (D_BLUE, D_TAX, D_TAX / D_BLUE))
