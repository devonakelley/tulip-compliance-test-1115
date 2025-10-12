#!/bin/bash
set -e

echo "🚀 Deploying Enterprise QSP Compliance System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads processed logs backups

# Set permissions
chmod 755 uploads processed logs backups

# Check if .env files exist
if [ ! -f backend/.env ]; then
    echo "⚠️  Backend .env file not found. Copying from example..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your configuration before proceeding."
    exit 1
fi

if [ ! -f frontend/.env ]; then
    echo "⚠️  Frontend .env file not found. Copying from example..."
    cp frontend/.env.example frontend/.env
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Performing health checks..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Backend health check passed!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Backend health check failed after $max_attempts attempts"
        docker-compose logs backend
        exit 1
    fi
    
    echo "🔄 Health check attempt $attempt/$max_attempts failed, retrying..."
    sleep 2
    ((attempt++))
done

# Check frontend
if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible!"
else
    echo "⚠️  Frontend might still be starting up..."
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/api/docs"
echo "   Health Check: http://localhost:8001/health"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""