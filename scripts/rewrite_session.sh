#!/bin/bash
# ECNOWリライトセッション起動スクリプト
# 1. GSC/GA4データ取得
# 2. 分析・候補抽出
# 3. Claude Codeセッション開始

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== ECNOW リライトセッション ==="
echo ""

# Activate venv
source venv/bin/activate

echo "[1/3] GSCデータ取得中..."
python3 scripts/fetch_gsc.py
echo ""

echo "[2/3] GA4データ取得中..."
python3 scripts/fetch_ga4.py
echo ""

echo "[3/3] リライト候補分析中..."
python3 scripts/analyze.py
echo ""

echo "=== データ準備完了 ==="
echo "Claude Codeで以下を実行してください:"
echo ""
echo '  claude "data/candidates_$(date +%Y%m%d).json を読んでリライト候補を提案して"'
