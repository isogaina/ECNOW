#!/usr/bin/env python3
"""リライトの効果測定レポートを作る。

各リライトの baseline を「前」、最新の GSC/GA4 データを「後」として並べる。
前回のサマリ（effect_summary_*.json）があれば「前回」列も出し、
1回前の測定からどう動いたかが分かるようにする。

  python3 scripts/effect_report.py
  python3 scripts/effect_report.py --gsc <file> --ga4 <file>

順位は impressions で重み付けした平均を使う。GSC の行は page × query 単位なので、
単純平均だと表示回数の少ないクエリが効きすぎる。

ROSTER にリライトの通し番号を持たせている。上司への報告で使う「N本目」と
一致させる必要があり、baseline の記録日から並べても公開順とはズレるため。
新しいリライトを公開したら ROSTER に1行足す。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"

# (通し番号, post_id, パス, 本番公開日, baselineファイル)
ROSTER = [
    (1, 2766, "/advanced/2766/", "2026-07-27", "baseline_20260727.json"),
    (2, 3012, "/beginner/3012/", "2026-07-31", "baseline_3012_20260730.json"),
    (3, 866, "/advanced/866/", "2026-08-05", "baseline_866_20260804.json"),
    (4, 328, "/beginner/328/", "2026-08-17", "baseline_328_20260810.json"),
    (5, 1055, "/beginner/1055/", "2026-08-17", "baseline_1055_20260812.json"),
    (6, 803, "/beginner/803/", "2026-08-19", "baseline_803_20260817.json"),
    (7, 911, "/advanced/911/", "2026-08-26", "baseline_911_20260819.json"),
    (8, 2687, "/beginner/2687/", "2026-08-26", "baseline_2687_20260824.json"),
    (9, 1059, "/beginner/1059/", "2026-09-03", "baseline_1059_20260826.json"),
    (10, 797, "/beginner/797/", "2026-09-04", "baseline_797_20260903.json"),
    (11, 2735, "/advanced/2735/", "2026-09-14", "baseline_2735_20260904.json"),
    (12, 1088, "/beginner/1088/", "2026-09-25", "baseline_1088_20260914.json"),
    (13, 258, "/beginner/258/", "2026-09-25", "baseline_258_20260914.json"),
]


def latest(dir_path: Path, pattern: str) -> Path:
    files = sorted(dir_path.glob(pattern))
    if not files:
        raise SystemExit(f"データが見つからない: {dir_path}/{pattern}")
    return files[-1]


def read_baseline(filename: str, path: str) -> dict:
    """baseline は3形式ある（初期の複数ページまとめ／旧単体／現行単体）ので揃える。"""
    d = json.loads((REPORTS / filename).read_text(encoding="utf-8"))

    if "pages" in d:  # 初期形式: 1ファイルに複数ページ
        p = d["pages"][path]
        return {
            "recorded_at": d["recorded_at"],
            "impressions": p["impressions"],
            "clicks": p["clicks"],
            "ctr_pct": p["ctr_pct"],
            "position": p["weighted_position"],
            "queries": p.get("query_count"),
            "pageviews": p.get("pageviews"),
            "bounce_rate": p.get("bounce_rate"),
            "avg_session_duration": p.get("avg_session_duration"),
        }

    if "avg_position" in d:  # 旧単体形式: GA4 が入れ子、順位キー名が違う
        ga4 = d.get("ga4") or {}
        return {
            "recorded_at": d.get("recorded_at") or d.get("measured_at"),
            "impressions": d["impressions"],
            "clicks": d["clicks"],
            "ctr_pct": d.get("ctr"),
            "position": d["avg_position"],
            "queries": d.get("query_count"),
            "pageviews": ga4.get("pageviews"),
            "bounce_rate": ga4.get("bounce_rate"),
            "avg_session_duration": ga4.get("avg_session_duration"),
        }

    return {  # 現行形式
        "recorded_at": d["recorded_at"],
        "impressions": d["impressions"],
        "clicks": d["clicks"],
        "ctr_pct": d.get("ctr_pct"),
        "position": d["weighted_avg_position"],
        "queries": d.get("query_count"),
        "pageviews": d.get("pageviews"),
        "bounce_rate": d.get("bounce_rate"),
        "avg_session_duration": d.get("avg_session_duration"),
    }


def gsc_metrics(gsc: dict, path: str) -> dict:
    rows = [r for r in gsc["rows"] if r["page"].rstrip("/").endswith(path.rstrip("/"))]
    impressions = sum(r["impressions"] for r in rows)
    clicks = sum(r["clicks"] for r in rows)
    position = (
        round(sum(r["position"] * r["impressions"] for r in rows) / impressions, 1)
        if impressions else None
    )
    return {
        "impressions": impressions,
        "clicks": clicks,
        "ctr_pct": round(clicks / impressions * 100, 2) if impressions else 0.0,
        "position": position,
        "queries": len(rows),
    }


def ga4_metrics(ga4: dict, path: str) -> dict:
    rows = [r for r in ga4["rows"] if r["path"].rstrip("/") == path.rstrip("/")]
    pv = sum(r["pageviews"] for r in rows)
    if not rows:
        return {"pageviews": None, "users": None, "bounce_rate": None,
                "avg_session_duration": None}

    def weighted(key):
        # 直帰率と滞在時間は行ごとの PV で重み付けして合成する
        if not pv:
            return None
        return round(sum(r[key] * r["pageviews"] for r in rows) / pv, 1)

    return {
        "pageviews": pv,
        "users": sum(r["users"] for r in rows),
        "bounce_rate": weighted("bounce_rate"),
        "avg_session_duration": weighted("avg_session_duration"),
    }


def previous_after() -> tuple:
    """直近のサマリから {post_id: after} と測定日を返す。"""
    files = sorted(REPORTS.glob("effect_summary_*.json"))
    if not files:
        return {}, None
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    return {i["post_id"]: i["after"] for i in d["items"]}, d.get("measured_at")


def fmt(v):
    return "-" if v is None else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsc")
    ap.add_argument("--ga4")
    args = ap.parse_args()

    gsc_file = Path(args.gsc) if args.gsc else latest(ROOT / "data" / "gsc", "gsc_*.json")
    ga4_file = Path(args.ga4) if args.ga4 else latest(ROOT / "data" / "ga4", "ga4_*.json")
    gsc = json.loads(gsc_file.read_text(encoding="utf-8"))
    ga4 = json.loads(ga4_file.read_text(encoding="utf-8"))
    prev, prev_date = previous_after()
    measured_at = datetime.now().strftime("%Y-%m-%d")

    items = []
    for n, post_id, path, published, bfile in ROSTER:
        before = read_baseline(bfile, path)
        after = {**gsc_metrics(gsc, path), **ga4_metrics(ga4, path)}
        # 公開直後は GSC の集計期間が旧内容を含むため、後の数値を効果として読めない
        weeks = (datetime.strptime(measured_at, "%Y-%m-%d")
                 - datetime.strptime(published, "%Y-%m-%d")).days / 7
        items.append({
            "n": n,
            "post_id": post_id,
            "path": path,
            "published": published,
            "weeks_since_publish": round(weeks, 1),
            "measurable": weeks >= 4,
            "before": {k: v for k, v in before.items() if k != "recorded_at"},
            "baseline_recorded_at": before["recorded_at"],
            "prev": prev.get(post_id),
            "after": after,
        })

    out = {
        "measured_at": measured_at,
        "gsc_period_after": gsc["period"],
        "ga4_period_after": ga4["period"],
        "prev_measured_at": prev_date,
        "items": items,
    }
    out_file = REPORTS / f"effect_summary_{datetime.now().strftime('%Y%m%d')}.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {out_file}")
    print(f"GSC(後): {gsc['period']} / GA4(後): {ga4['period']} / 前回測定: {prev_date}")
    print()
    print(f"{'n':>2} {'ID':>5} {'経過':>5}  {'表示 前→前回→後':<22} {'クリック':<11}"
          f" {'順位 前→前回→後':<22} {'PV':<11}")
    print("-" * 96)
    for i in items:
        b, p, a = i["before"], i["prev"] or {}, i["after"]
        imp = f"{fmt(b['impressions'])}→{fmt(p.get('impressions'))}→{fmt(a['impressions'])}"
        clk = f"{fmt(b['clicks'])}→{fmt(p.get('clicks'))}→{fmt(a['clicks'])}"
        pos = f"{fmt(b['position'])}→{fmt(p.get('position'))}→{fmt(a['position'])}"
        pv = f"{fmt(b['pageviews'])}→{fmt(p.get('pageviews'))}→{fmt(a['pageviews'])}"
        mark = "" if i["measurable"] else " ※期間不足"
        print(f"{i['n']:>2} {i['post_id']:>5} {i['weeks_since_publish']:>4}週"
              f"  {imp:<22} {clk:<11} {pos:<22} {pv:<11}{mark}")


if __name__ == "__main__":
    main()
