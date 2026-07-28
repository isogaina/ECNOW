#!/usr/bin/env python3
"""GSC + GA4 データを統合分析し、リライト候補を抽出"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def load_latest(data_dir: str, required: bool = True) -> dict:
    d = Path(__file__).resolve().parent.parent / "data" / data_dir
    files = sorted(d.glob("*.json"))
    if not files:
        if required:
            print(f"No data in {d}")
            sys.exit(1)
        print(f"[warn] No data in {d} - continuing without it", file=sys.stderr)
        return None
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def merge_data(gsc_data: dict, ga4_data: dict) -> list:
    from urllib.parse import urlparse, urlunparse

    ga4_by_path = {}
    for row in (ga4_data or {}).get("rows", []):
        ga4_by_path[row["path"]] = row

    # GSC はアンカー付きURL (#index_id0 等) を別行で返し、同じ表示回数を重複計上する。
    # フラグメントを落とし、(path, query) ごとに最大の行だけを採用する。
    best_row = {}
    for row in gsc_data["rows"]:
        parsed = urlparse(row["page"])
        path = parsed.path
        key = (path, row["query"])
        prev = best_row.get(key)
        if prev is None or row["impressions"] > prev["impressions"]:
            best_row[key] = {
                **row,
                "page": urlunparse(parsed._replace(fragment="", query="")),
                "path": path,
            }

    page_stats = defaultdict(lambda: {
        "queries": [],
        "total_clicks": 0,
        "total_impressions": 0,
        "best_position": 999,
        "avg_position": 0,
        "ga4": None,
    })

    for row in best_row.values():
        path = row["path"]
        stats = page_stats[path]
        stats["url"] = row["page"]
        stats["queries"].append({
            "query": row["query"],
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": row["ctr"],
            "position": row["position"],
        })
        stats["total_clicks"] += row["clicks"]
        stats["total_impressions"] += row["impressions"]
        if row["position"] < stats["best_position"]:
            stats["best_position"] = row["position"]

    for path, stats in page_stats.items():
        qs = stats["queries"]
        # 表示回数で重み付けした平均順位（ロングテールの外れ値に引きずられないように）
        imp_total = sum(q["impressions"] for q in qs)
        if imp_total:
            stats["avg_position"] = round(
                sum(q["position"] * q["impressions"] for q in qs) / imp_total, 1
            )
        else:
            stats["avg_position"] = round(sum(q["position"] for q in qs) / len(qs), 1) if qs else 0
        stats["simple_avg_position"] = round(sum(q["position"] for q in qs) / len(qs), 1) if qs else 0
        stats["query_count"] = len(qs)
        qs.sort(key=lambda x: x["impressions"], reverse=True)
        if path in ga4_by_path:
            stats["ga4"] = ga4_by_path[path]

    return [{"path": k, **v} for k, v in page_stats.items()]


def find_rewrite_candidates(merged: list, min_pos=11, max_pos=30, min_impressions=100) -> list:
    candidates = []
    for page in merged:
        if min_pos <= page["avg_position"] <= max_pos and page["total_impressions"] >= min_impressions:
            score = page["total_impressions"] * (1 / page["avg_position"])
            candidates.append({**page, "rewrite_score": round(score, 1)})

    candidates.sort(key=lambda x: x["rewrite_score"], reverse=True)
    return candidates


def run(min_pos=11, max_pos=30, min_impressions=100):
    gsc_data = load_latest("gsc")
    ga4_data = load_latest("ga4", required=False)

    merged = merge_data(gsc_data, ga4_data)
    candidates = find_rewrite_candidates(merged, min_pos, max_pos, min_impressions)

    output = {
        "gsc_period": gsc_data["period"],
        "ga4_period": ga4_data["period"] if ga4_data else None,
        "filter": {
            "position_range": f"{min_pos}-{max_pos}",
            "min_impressions": min_impressions,
        },
        "total_pages_analyzed": len(merged),
        "candidates_found": len(candidates),
        "candidates": candidates,
    }

    output_file = Path(__file__).resolve().parent.parent / "data" / f"candidates_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-pos", type=int, default=11)
    parser.add_argument("--max-pos", type=int, default=30)
    parser.add_argument("--min-impressions", type=int, default=100)
    args = parser.parse_args()
    run(args.min_pos, args.max_pos, args.min_impressions)
