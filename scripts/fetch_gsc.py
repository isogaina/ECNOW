#!/usr/bin/env python3
"""Google Search Console データ取得"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials/service-account.json")
GSC_PROPERTY = os.getenv("GSC_PROPERTY")

def get_service():
    creds_path = Path(__file__).resolve().parent.parent / CREDENTIALS_PATH
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=credentials)

def fetch_pages(days=28, row_limit=25000):
    service = get_service()
    end_date = datetime.now() - timedelta(days=3)
    start_date = end_date - timedelta(days=days)

    request_body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "dimensions": ["page", "query"],
        "rowLimit": row_limit,
        "dimensionFilterGroups": [
            {
                "filters": [
                    {
                        "dimension": "page",
                        "operator": "includingRegex",
                        "expression": os.getenv("SITE_URL", ""),
                    }
                ]
            }
        ],
    }

    response = service.searchanalytics().query(
        siteUrl=GSC_PROPERTY, body=request_body
    ).execute()

    rows = []
    for row in response.get("rows", []):
        rows.append({
            "page": row["keys"][0],
            "query": row["keys"][1],
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": round(row["ctr"] * 100, 2),
            "position": round(row["position"], 1),
        })

    return {
        "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        "total_rows": len(rows),
        "rows": rows,
    }

def fetch_and_save():
    data = fetch_pages()
    output_dir = Path(__file__).resolve().parent.parent / "data" / "gsc"
    output_file = output_dir / f"gsc_{datetime.now().strftime('%Y%m%d')}.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"GSC data saved: {output_file}")
    print(f"Period: {data['period']}")
    print(f"Total rows: {data['total_rows']}")
    return output_file

if __name__ == "__main__":
    fetch_and_save()
