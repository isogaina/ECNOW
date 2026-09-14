#!/usr/bin/env python3
"""258 図2: Amazon手数料の内訳を売上比の積み上げ帯で示すHTMLを生成する。

帯の幅は手数料の実額から計算する（手打ちしない）。
出典:
- 出品プラン料金・販売手数料・FBA配送代行手数料
  https://sell.amazon.co.jp/pricing

作図に使う前提:
- 単価3,000円のビューティー商品（1,500円超のため販売手数料10.4%として計算）
- 配送代行手数料は標準サイズの下限318円（商品価格1,000円超）
- 在庫保管手数料と自己発送の送料・梱包費は含めない（帯の外に注記する）
"""
from pathlib import Path

CHART_W = 1080          # 帯のトラック幅(px)。売上100%がこの幅にあたる
UNIT_PRICE = 3000
FEE_RATE = 0.104        # ビューティー 1,500円超の販売手数料
MONTHLY_FEE = 4900      # 大口出品の月額登録料（税抜）
PER_ITEM_FEE = 100      # 小口出品の基本成約料
FBA_SHIP = 318          # FBA配送代行手数料（標準サイズの下限）

COLORS = {
    "plan": "#5b6577",
    "sales": "#e8762a",
    "fba": "#2f6fed",
    "rest": "#dde2ea",
}


def case(name, sub, qty, *, plan):
    """1ケース分の金額と帯の幅を組み立てる。"""
    revenue = UNIT_PRICE * qty
    sales_fee = round(UNIT_PRICE * FEE_RATE) * qty
    if plan == "small":
        plan_fee = PER_ITEM_FEE * qty
        plan_label = "基本成約料"
        fba = 0
    else:
        plan_fee = MONTHLY_FEE
        plan_label = "月額登録料"
        fba = FBA_SHIP * qty
    total = plan_fee + sales_fee + fba
    rest = revenue - total
    segs = [("plan", plan_label, plan_fee), ("sales", "販売手数料", sales_fee)]
    if fba:
        segs.append(("fba", "配送代行手数料", fba))
    segs.append(("rest", "手元に残る", rest))
    return {
        "name": name, "sub": sub, "qty": qty, "revenue": revenue,
        "total": total, "pct": total / revenue * 100,
        "segs": [
            {"key": k, "label": l, "yen": y,
             "pct": y / revenue * 100, "px": y / revenue * CHART_W}
            for k, l, y in segs
        ],
    }


CASES = [
    case("ケースA　小口出品＋自己発送", "月30個 売れた場合", 30, plan="small"),
    case("ケースB　大口出品＋FBA", "月100個 売れた場合", 100, plan="large"),
]


def rows_html():
    out = []
    for c in CASES:
        segs = "\n".join(
            '        <div class="seg {k}" style="width:{px:.3f}px"></div>'.format(
                k=s["key"], px=s["px"])
            for s in c["segs"]
        )
        fee_px = sum(s["px"] for s in c["segs"] if s["key"] != "rest")
        items = "　／　".join(
            "%s %s円" % (s["label"], format(s["yen"], ","))
            for s in c["segs"] if s["key"] != "rest"
        )
        out.append(f"""  <div class="row">
    <div class="side">
      <div class="nm">{c['name']}</div>
      <div class="sb">{c['sub']}</div>
      <div class="rv">売上 {c['revenue']:,}円</div>
    </div>
    <div class="track">
      <div class="bar">
{segs}
      </div>
      <div class="mark" style="left:{fee_px:.3f}px">
        <div class="pct">手数料 {c['total']:,}円（売上の{c['pct']:.1f}%）</div>
      </div>
      <div class="items">{items}</div>
    </div>
  </div>""")
    return "\n\n".join(out)


HTML = f"""<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1600px; height:700px; background:#fff;
    font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;
    color:#1f2430;
    display:flex; flex-direction:column;
    padding:38px 60px 28px;
  }}
  h1 {{ font-size:39px; font-weight:700; text-align:center; }}
  .sub {{ text-align:center; font-size:20px; color:#7a8496; margin-top:9px; }}

  .legend {{
    display:flex; justify-content:center; gap:26px; margin-top:22px;
    font-size:17px; color:#5b6577;
  }}
  .legend span {{ display:flex; align-items:center; gap:8px; }}
  .legend i {{ width:19px; height:19px; border-radius:4px; display:block; }}

  .rows {{ flex:1; margin-top:24px; display:flex; flex-direction:column; justify-content:center; gap:46px; }}
  .row {{ display:grid; grid-template-columns:360px {CHART_W}px; gap:0 20px; align-items:start; }}

  .side {{ padding-top:2px; }}
  .side .nm {{ font-size:24px; font-weight:700; color:#1f2430; line-height:1.3; }}
  .side .sb {{ font-size:17px; color:#7a8496; margin-top:3px; }}
  .side .rv {{ font-size:19px; font-weight:700; color:#5b6577; margin-top:7px; }}

  .track {{ position:relative; }}
  .bar {{
    display:flex; height:52px; border-radius:8px; overflow:hidden;
    outline:2px solid #c3cad6;
  }}
  .seg {{ height:100%; flex:none; }}
  .seg.plan {{ background:{COLORS['plan']}; }}
  .seg.sales {{ background:{COLORS['sales']}; }}
  .seg.fba {{ background:{COLORS['fba']}; }}
  .seg.rest {{ background:{COLORS['rest']}; }}

  /* 引き出し線は帯の上で止める。帯を横切らせるとデータの上に線が乗る */
  .mark {{ position:absolute; top:-30px; height:30px; }}
  .mark::before {{
    content:""; position:absolute; left:0; top:8px; width:3px; height:22px;
    background:#1f2430; transform:translateX(-50%);
  }}
  .mark .pct {{
    position:absolute; left:0; top:-4px; transform:translateX(-50%);
    font-size:19px; font-weight:700; color:#1f2430; white-space:nowrap;
    background:#fff; padding:0 10px;
  }}
  .items {{ margin-top:11px; font-size:17px; color:#5b6577; }}

  .foot {{
    margin-top:20px; background:#f5f7fb; border-radius:10px; padding:15px 24px;
    font-size:18px; line-height:1.6; color:#5b6577;
  }}
  .foot b {{ color:#1f2430; }}
  .foot .src {{ display:block; margin-top:6px; font-size:15px; color:#8a94a6; }}
</style>

<h1>FBAを使うと手数料は売上の13.7%から22.6%に上がる</h1>
<p class="sub">単価3,000円のビューティー商品（販売手数料10.4%）で計算した場合</p>

<div class="legend">
  <span><i style="background:{COLORS['plan']}"></i>プラン料金</span>
  <span><i style="background:{COLORS['sales']}"></i>販売手数料</span>
  <span><i style="background:{COLORS['fba']}"></i>配送代行手数料</span>
  <span><i style="background:{COLORS['rest']}"></i>手元に残る（原価・送料・利益）</span>
</div>

<div class="rows">
{rows_html()}
</div>

<div class="foot">
  <b>ケースAの13.7%には送料も梱包費も人件費も入っていない</b>——自己発送の1件あたりコストが318円を超えるならFBAのほうが安くなる ケースBには在庫保管手数料が別途かかる
  <span class="src">販売手数料はカテゴリーで5〜15.4%（メディアを除き最低30円）。配送代行手数料は標準サイズの下限318円で計算。2026年9月14日時点の<a href="https://sell.amazon.co.jp/pricing">Amazon出品サービスの料金プラン</a>より</span>
</div>
"""

out = Path(__file__).with_name("258_fig2_fee_breakdown.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out)
for c in CASES:
    print("\n%s（%d個・売上%s円）" % (c["name"], c["qty"], format(c["revenue"], ",")))
    for s in c["segs"]:
        print("  %-8s %9s円  %6.3f%%  %8.3fpx" %
              (s["label"], format(s["yen"], ","), s["pct"], s["px"]))
    print("  手数料合計 %s円 = 売上の %.3f%%" % (format(c["total"], ","), c["pct"]))
