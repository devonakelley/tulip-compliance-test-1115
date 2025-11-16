#!/bin/bash
echo "=========================================="
echo "VERIFYING TRUNCATION BUG FIXES"
echo "=========================================="

echo ""
echo "FIX #1: Checking iso_diff_processor.py..."
if grep -q "\[:500\]" /app/backend/core/iso_diff_processor.py; then
    echo "❌ FAILED: Still has [:500] truncation"
else
    echo "✅ PASSED: No [:500] truncation found"
fi

echo ""
echo "FIX #2: Checking qsp_parser.py..."
if grep -q "\[:2000\]" /app/backend/core/qsp_parser.py; then
    echo "❌ FAILED: Still has [:2000] truncation"
else
    echo "✅ PASSED: No [:2000] truncation found"
fi

echo ""
echo "FIX #3: Checking change_impact_service_mongo.py..."
if grep -q "16000" /app/backend/core/change_impact_service_mongo.py; then
    echo "✅ PASSED: Embedding limit increased to 16000"
elif grep -q "> 8000" /app/backend/core/change_impact_service_mongo.py; then
    echo "❌ FAILED: Still using 8000 character limit"
else
    echo "⚠️  WARNING: Cannot determine embedding limit"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
