# Enterprise QSP Compliance System - Deployment Guide

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
cd qsp-compliance-system
./scripts/deploy.sh
```

This will automatically:
- Create necessary directories
- Check for .env files
- Build and start all services with Docker Compose
- Perform health checks
- Display access URLs

### Option 2: Manual Deployment

1. **Environment Setup**
```bash
# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files
nano backend/.env  # Add your EMERGENT_LLM_KEY
nano frontend/.env
```

2. **Start Services**
```bash
# Using Docker Compose
docker-compose up --build -d

# Or start individually
cd backend && uvicorn main:app --host 0.0.0.0 --port 8001
cd frontend && npm start
```

3. **Verify Deployment**
```bash
./scripts/test.sh
```

## 📋 Environment Configuration

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=qsp_compliance
EMERGENT_LLM_KEY=your-emergent-llm-key-here
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🔧 Production Deployment

### Prerequisites
- Docker and Docker Compose
- MongoDB 7.0+
- Emergent LLM API Key
- SSL Certificate (for HTTPS)

### Production Configuration

1. **Update Environment Variables**
```bash
# Backend production settings
MONGO_URL=mongodb://mongo-prod:27017
LOG_LEVEL=WARN
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=your-super-secure-production-key
```

2. **SSL Configuration**
   - Update docker-compose.yml with SSL certificates
   - Configure reverse proxy (nginx/traefik)
   - Update CORS origins to production domains

3. **Database Setup**
   - Use managed MongoDB service (MongoDB Atlas)
   - Configure backup and monitoring
   - Set up proper authentication

### Kubernetes Deployment

```yaml
# Example kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qsp-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qsp-backend
  template:
    metadata:
      labels:
        app: qsp-backend
    spec:
      containers:
      - name: backend
        image: qsp-compliance/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: qsp-secrets
              key: mongo-url
```

## 🛠️ Maintenance

### Backup
```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh /app/backups/qsp_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Monitoring
- Health checks: `GET /health`
- Metrics: `GET /metrics` (Prometheus compatible)
- Logs: `docker-compose logs -f`

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

## 🚨 Troubleshooting

### Common Issues

1. **Backend not starting**
```bash
# Check logs
docker-compose logs backend

# Common fixes
- Verify MongoDB connection
- Check EMERGENT_LLM_KEY configuration
- Ensure ports 8001 and 27017 are available
```

2. **Frontend build errors**
```bash
# Clear cache and rebuild
docker-compose down
docker system prune -f
docker-compose up --build --no-cache
```

3. **AI service not working**
```bash
# Verify API key
curl -H "Content-Type: application/json" \
  http://localhost:8001/api/test/ai

# Check configuration
docker-compose exec backend python -c "
from config import settings
print('LLM Key configured:', bool(settings.EMERGENT_LLM_KEY))
"
```

### Performance Optimization

1. **Database Indexing**
   - Ensure proper MongoDB indexes are created
   - Monitor query performance

2. **Caching**
   - Configure Redis for production caching
   - Implement CDN for static assets

3. **Load Balancing**
   - Use multiple backend instances
   - Configure load balancer (nginx/HAProxy)

## 📊 Monitoring & Observability

### Health Monitoring
- Endpoint: `GET /health`
- Checks: Database, AI service, disk space, memory

### Metrics Collection
- Prometheus metrics: `GET /metrics`
- Custom application metrics
- System resource monitoring

### Logging
- Structured JSON logging
- Log rotation and retention
- Error tracking (Sentry integration available)

## 🔐 Security Considerations

### Production Security Checklist
- [ ] Change default JWT secret key
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable MongoDB authentication
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] API key rotation

### Network Security
- Use private networks for database connections
- Implement API rate limiting
- Configure firewall rules
- Regular security audits

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Run health checks: `./scripts/test.sh`
3. Review configuration files
4. Check system requirements
5. Create issue with logs and configuration details