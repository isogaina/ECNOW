#!/usr/bin/env python3
"""リライト前の数値を baseline として記録する。

  python3 scripts/baseline.py --post-id 3030 --path /beginner/3030/ --title "現行タイトル"

reports/baseline_<post_id>_<日付>.json に書く。effect_report.py が読む形式に
揃えてあるので、記録したら effect_report.py の ROSTER に1行足す。

順位は impressions で重み付けした平均を使う。GSC の行は page × query 単位なので、
単純平均だと表示回数の少ないクエリが効きすぎる。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def latest(dir_name: str, pattern: str) -> dict:
    d = ROOT / "data" / dir_name
    files = sorted(d.glob(pattern))
    if not files:
        raise SystemExit(f"データが見つからない: {d}/{pattern}")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-id", type=int, required=True)
    ap.add_argument("--path", required=True, help="例 /beginner/3030/")
    ap.add_argument("--title", default=None, help="リライト前の post_title")
    ap.add_argument("--top-queries", type=int, default=20)
    args = ap.parse_args()

    gsc = latest("gsc", "gsc_*.json")
    ga4 = latest("ga4", "ga4_*.json")
    path = args.path

    # GSC はアンカー付きURL を別行で返すので、パス末尾の一致で拾う
    rows = [r for r in gsc["rows"] if r["page"].rstrip("/").endswith(path.rstrip("/"))]
    impressions = sum(r["impressions"] for r in rows)
    clicks = sum(r["clicks"] for r in rows)
    position = (
        round(sum(r["position"] * r["impressions"] for r in rows) / impressions, 1)
        if impressions else None
    )

    g_rows = [r for r in ga4["rows"] if r["path"].rstrip("/") == path.rstrip("/")]
    pv = sum(r["pageviews"] for r in g_rows)

    def weighted(key):
        if not pv:
            return None
        return round(sum(r[key] * r["pageviews"] for r in g_rows) / pv, 1)

    out = {
        "recorded_at": datetime.now().strftime("%Y-%m-%d"),
        "gsc_period": gsc["period"],
        "ga4_period": ga4["period"],
        "post_id": args.post_id,
        "path": path,
        "title_before": args.title,
        "impressions": impressions,
        "clicks": clicks,
        "ctr_pct": round(clicks / impressions * 100, 2) if impressions else 0.0,
        "weighted_avg_position": position,
        "best_position": min((r["position"] for r in rows), default=None),
        "query_count": len(rows),
        "pageviews": pv if g_rows else None,
        "users": sum(r["users"] for r in g_rows) if g_rows else None,
        "bounce_rate": weighted("bounce_rate"),
        "avg_session_duration": weighted("avg_session_duration"),
        "top_queries": [
            {"query": r["query"], "clicks": r["clicks"],
             "impressions": r["impressions"], "position": r["position"]}
            for r in sorted(rows, key=lambda r: -r["impressions"])[: args.top_queries]
        ],
    }
    if not g_rows:
        out["ga4_note"] = "GA4に該当パスの行なし（期間中のPVが計測下限）"

    out_file = (ROOT / "reports" /
                f"baseline_{args.post_id}_{datetime.now().strftime('%Y%m%d')}.json")
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {out_file}")
    print(f"GSC: {gsc['period']} / GA4: {ga4['period']}")
    print(f"表示{out['impressions']} ／ クリック{out['clicks']} ／ CTR{out['ctr_pct']}% ／ "
          f"順位{out['weighted_avg_position']}位 ／ クエリ{out['query_count']}本")
    print(f"PV{out['pageviews']} ／ 直帰{out['bounce_rate']}% ／ 滞在{out['avg_session_duration']}秒")


if __name__ == "__main__":
    main()
