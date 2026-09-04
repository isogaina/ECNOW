#!/usr/bin/env python3
"""797 図3: 開業日を起点にした届出の期限タイムラインのHTMLを生成する。

軸上の座標は日付から計算する（手打ちしない）。
- 開業届     : 事業の開始等の事実があった日の属する年分の確定申告期限まで
               https://www.nta.go.jp/taxes/tetsuzuki/shinsei/annai/shinkoku/annai/04.htm
- 青色申告承認申請書 : その年の3月15日まで
               （1月16日以後に開業した場合は開業日から2か月以内）
               https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/2090.htm
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


def pos(d: date) -> float:
    """日付を軸上の位置(%)に変換する。"""
    return (d - AXIS_START).days / SPAN * 100


def months(start: date, end: date):
    """軸に置く月初の目盛りを列挙する。"""
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        yield date(y, m, 1)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


P_OPEN = pos(OPEN)
P_BLUE = pos(BLUE_DEADLINE)
P_TAX = pos(TAX_DEADLINE)

ticks = "\n".join(
    '  <div class="tick{cls}" style="left:{p:.4f}%"><span>{label}</span></div>'.format(
        p=pos(d),
        cls=" year" if d.month == 1 else "",
        label=("%d年<br>%d月" % (d.year, d.month)) if d.month in (1, 4) else "%d月" % d.month,
    )
    for d in months(AXIS_START, AXIS_END)
)

HTML = f"""<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1600px; height:730px; background:#fff;
    font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;
    color:#1f2430;
    display:flex; flex-direction:column;
    padding:38px 60px 28px;
  }}
  h1 {{ font-size:39px; font-weight:700; text-align:center; }}
  .sub {{ text-align:center; font-size:20px; color:#7a8496; margin-top:9px; }}

  .chart {{ position:relative; height:400px; margin:66px 40px 0; }}

  .axis {{
    position:absolute; left:0; right:0; top:330px; height:5px;
    background:#c3cad6; border-radius:3px;
  }}
  .tick {{ position:absolute; top:335px; }}
  .tick::before {{
    content:""; position:absolute; left:0; top:-9px; width:2px; height:13px; background:#c3cad6;
  }}
  .tick.year::before {{ height:19px; top:-15px; width:3px; background:#8a94a6; }}
  .tick span {{
    position:absolute; left:0; top:12px; transform:translateX(-50%);
    font-size:16px; color:#8a94a6; white-space:nowrap; text-align:center; line-height:1.25;
  }}
  .tick.year span {{ color:#5b6577; font-weight:700; }}

  .band {{
    position:absolute; top:268px; height:56px;
    background:#fdf0e4; border:3px solid #e8762a; border-radius:10px;
  }}
  .band .label {{
    position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
    font-size:21px; font-weight:700; color:#a3520f; white-space:nowrap;
  }}

  .mark {{ position:absolute; top:0; height:330px; }}
  .mark::before {{
    content:""; position:absolute; left:0; bottom:0; width:3px; height:330px;
    background:#2f6fed; transform:translateX(-50%);
  }}
  .mark::after {{
    content:""; position:absolute; left:0; bottom:-9px; width:19px; height:19px;
    border-radius:50%; background:#2f6fed; border:4px solid #fff;
    transform:translate(-50%,50%);
  }}
  .mark .box {{
    position:absolute; bottom:112px; width:400px;
    border:3px solid #2f6fed; background:#eef3fe; border-radius:12px; padding:12px 20px;
  }}
  .mark .box .date {{ font-size:17px; font-weight:700; color:#2f6fed; letter-spacing:.04em; }}
  .mark .box .txt {{ font-size:28px; font-weight:700; line-height:1.25; margin-top:2px; }}
  .mark .box .ex {{ font-size:16px; color:#5b6577; margin-top:5px; line-height:1.45; }}

  .mark.start::before, .mark.start::after {{ background:#5b6577; }}
  .mark.start .box {{ border-color:#5b6577; background:#f5f7fb; }}
  .mark.start .box .date {{ color:#5b6577; }}

  .mark.warn::before, .mark.warn::after {{ background:#e8762a; }}
  .mark.warn .box {{ border-color:#e8762a; background:#fdf0e4; }}
  .mark.warn .box .date {{ color:#a3520f; }}
  .mark.warn .box .txt {{ color:#a3520f; }}

  .foot {{
    margin-top:auto; background:#f5f7fb; border-radius:10px; padding:15px 24px;
    font-size:18px; line-height:1.6; color:#5b6577;
  }}
  .foot b {{ color:#1f2430; }}
  .foot .row + .row {{ margin-top:6px; }}
</style>

<h1>開業届と青色申告承認申請書は期限が違う</h1>
<p class="sub">2026年6月1日に開業した場合　急ぐのは青色申告承認申請書のほう</p>

<div class="chart">
  <div class="axis"></div>
{ticks}

  <div class="band" style="left:{P_OPEN:.4f}%; width:{P_BLUE - P_OPEN:.4f}%">
    <div class="label">2か月</div>
  </div>

  <div class="mark start" style="left:{P_OPEN:.4f}%">
    <div class="box" style="left:-30px">
      <div class="date">2026年6月1日</div>
      <div class="txt">開業日</div>
      <div class="ex">売り始めた日を自分で決めて届出書に書く</div>
    </div>
  </div>

  <div class="mark warn" style="left:{P_BLUE:.4f}%">
    <div class="box" style="left:30px; bottom:236px">
      <div class="date">2026年8月1日／開業日から2か月以内</div>
      <div class="txt">青色申告承認申請書の期限</div>
      <div class="ex">過ぎると初年度は白色申告になり 65万円控除も赤字の3年繰越も使えない</div>
    </div>
  </div>

  <div class="mark" style="left:{P_TAX:.4f}%">
    <div class="box" style="right:-30px">
      <div class="date">2027年3月15日／確定申告期限</div>
      <div class="txt">開業届の期限</div>
      <div class="ex">「開業から1か月以内」ではない（国税庁の手続案内）</div>
    </div>
  </div>
</div>

<div class="foot">
  <div class="row">青色申告承認申請書は<b>その年の3月15日まで</b>。1月16日以後に開業した場合だけ<b>開業日から2か月以内</b>になる。</div>
  <div class="row">期限は先でも、<b>楽天市場などのモールは出店の申込時点で開業届の控えを求める</b>ため、モールを考えているなら先に出しておく。</div>
</div>
"""

out = Path(__file__).with_name("797_fig3_deadlines.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out)
print("axis %s -> %s (%d days)" % (AXIS_START, AXIS_END, SPAN))
for name, d in (("開業日", OPEN), ("青色期限", BLUE_DEADLINE), ("確申期限", TAX_DEADLINE)):
    print("  %-6s %s  x=%.4f%%" % (name, d, pos(d)))
