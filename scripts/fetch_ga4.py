#!/usr/bin/env python3
"""GA4 データ取得"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials/service-account.json")
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")

def get_client():
    creds_path = Path(__file__).resolve().parent.parent / CREDENTIALS_PATH
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=SCOPES
    )
    return BetaAnalyticsDataClient(credentials=credentials)

def fetch_page_metrics(days=28):
    client = get_client()
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[
            DateRange(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
        ],
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="pageTitle"),
        ],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
            Metric(name="engagedSessions"),
            Metric(name="totalUsers"),
        ],
        limit=500,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        rows.append({
            "path": row.dimension_values[0].value,
            "title": row.dimension_values[1].value,
            "pageviews": int(row.metric_values[0].value),
            "avg_session_duration": round(float(row.metric_values[1].value), 1),
            "bounce_rate": round(float(row.metric_values[2].value) * 100, 1),
            "engaged_sessions": int(row.metric_values[3].value),
            "users": int(row.metric_values[4].value),
        })

    rows.sort(key=lambda x: x["pageviews"], reverse=True)

    return {
        "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        "total_rows": len(rows),
        "rows": rows,
    }

def fetch_and_save():
    data = fetch_page_metrics()
    output_dir = Path(__file__).resolve().parent.parent / "data" / "ga4"
    output_file = output_dir / f"ga4_{datetime.now().strftime('%Y%m%d')}.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"GA4 data saved: {output_file}")
    print(f"Period: {data['period']}")
    print(f"Total rows: {data['total_rows']}")
    return output_file

if __name__ == "__main__":
    fetch_and_save()
