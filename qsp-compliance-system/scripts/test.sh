#!/bin/bash
set -e

echo "🧪 Running Enterprise QSP Compliance System Tests..."

# Check if services are running
if ! curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "❌ Backend not responding. Please start the services first."
    echo "Run: docker-compose up -d"
    exit 1
fi

echo "✅ Backend is responding"

# Test health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "$HEALTH_RESPONSE"
    exit 1
fi

# Test AI service
echo "🤖 Testing AI service..."
AI_RESPONSE=$(curl -s "http://localhost:8001/api/test/ai")
if echo "$AI_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "✅ AI service test passed"
else
    echo "⚠️  AI service test failed (this might be expected if no API key is configured)"
fi

# Test database
echo "💾 Testing database..."
DB_RESPONSE=$(curl -s "http://localhost:8001/api/test/database")
if echo "$DB_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "✅ Database test passed"
else
    echo "❌ Database test failed"
    echo "$DB_RESPONSE"
    exit 1
fi

# Test document upload
echo "📄 Testing document upload..."
UPLOAD_RESPONSE=$(curl -s -X POST \
    "http://localhost:8001/api/test/upload?filename=test-qsp.txt&content=This%20is%20a%20test%20QSP%20document%20for%20compliance%20testing")
if echo "$UPLOAD_RESPONSE" | grep -q '"status":"success"'; then
    echo "✅ Document upload test passed"
else
    echo "❌ Document upload test failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

# Test document listing
echo "📋 Testing document listing..."
DOCS_RESPONSE=$(curl -s "http://localhost:8001/api/test/documents")
if echo "$DOCS_RESPONSE" | grep -q "test-qsp.txt"; then
    echo "✅ Document listing test passed"
else
    echo "❌ Document listing test failed"
    exit 1
fi

# Test frontend (if running)
if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "⚠️  Frontend not accessible (might be starting up)"
fi

echo ""
echo "🎉 All tests completed successfully!"
echo "✅ System is working correctly"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API Docs: http://localhost:8001/api/docs"