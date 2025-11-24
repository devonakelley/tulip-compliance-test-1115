# Certaro Deployment Guide

This guide covers deploying the Certaro Medical Device Compliance Platform to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Database Management](#database-management)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure the following:

### Security
- [ ] Generated strong JWT secret key (min 32 characters)
- [ ] Changed default admin credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configured CORS to only allow production domains
- [ ] Reviewed and secured all API endpoints
- [ ] Enabled rate limiting (configured in backend)
- [ ] Set up secure environment variable management

### Infrastructure
- [ ] MongoDB instance is running and accessible
- [ ] Sufficient storage for uploads and ChromaDB data
- [ ] Network security groups/firewalls configured
- [ ] Load balancer configured (if needed)
- [ ] CDN set up for static assets (optional)

### Configuration
- [ ] All environment variables set in production
- [ ] OpenAI API key is valid and has sufficient quota
- [ ] Database backups configured
- [ ] Logging and monitoring tools set up

---

## Environment Setup

### Required Environment Variables

Create a `.env` file in both backend and frontend directories with the following variables:

#### Backend `.env`

```bash
# MongoDB Configuration
MONGO_URL=mongodb://your-mongo-host:27017
DB_NAME=compliance_checker_prod

# Security
JWT_SECRET_KEY=your-64-character-random-secret-key-generated-with-openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin Account (for initial seed only)
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=YourSecurePassword123!
COMPANY_NAME=Your Company Name

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key
EMERGENT_LLM_KEY=your-emergent-llm-key

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=https://app.yourcompany.com,https://www.yourcompany.com
DOMAIN=yourcompany.com

# Server Configuration
PORT=8001
HOST=0.0.0.0
LOG_LEVEL=INFO

# ChromaDB
CHROMA_PERSIST_DIRECTORY=/app/chromadb_data
```

#### Frontend `.env`

```bash
REACT_APP_BACKEND_URL=https://api.yourcompany.com
REACT_APP_NAME=Certaro
REACT_APP_VERSION=1.0.0
```

### Generating Secure Secrets

```bash
# Generate JWT secret key (64 characters recommended)
openssl rand -hex 32

# Generate admin password (or use a password manager)
openssl rand -base64 24
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended for Single-Server Deployments)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tulip-compliance-test-1115
   ```

2. **Set up environment variables:**
   ```bash
   # Copy example files
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env

   # Edit with your production values
   nano backend/.env
   nano frontend/.env
   ```

3. **Build and start services:**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

5. **Seed admin user (first time only):**
   ```bash
   docker-compose exec backend python seed_admin.py
   ```

### Option 2: Individual Docker Containers

1. **Build images:**
   ```bash
   # Backend
   cd backend
   docker build -t certaro-backend:latest .

   # Frontend
   cd ../frontend
   docker build -t certaro-frontend:latest .
   ```

2. **Run containers:**
   ```bash
   # MongoDB
   docker run -d --name certaro-mongo \
     -p 27017:27017 \
     -v certaro-mongo-data:/data/db \
     mongo:7.0

   # Backend
   docker run -d --name certaro-backend \
     -p 8001:8001 \
     --env-file backend/.env \
     -v certaro-uploads:/app/uploads \
     -v certaro-chromadb:/app/chromadb_data \
     certaro-backend:latest

   # Frontend
   docker run -d --name certaro-frontend \
     -p 3000:80 \
     certaro-frontend:latest
   ```

---

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS (Elastic Container Service)

1. **Push images to ECR:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Tag and push backend
   docker tag certaro-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/certaro-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/certaro-backend:latest

   # Tag and push frontend
   docker tag certaro-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/certaro-frontend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/certaro-frontend:latest
   ```

2. **Set up infrastructure:**
   - MongoDB: Use AWS DocumentDB or MongoDB Atlas
   - ECS Cluster: Create ECS cluster with Fargate or EC2
   - Load Balancer: Application Load Balancer (ALB)
   - Security Groups: Configure for services
   - Secrets: Use AWS Secrets Manager or Parameter Store

3. **Create ECS Task Definitions:**
   - Backend task with environment variables from Secrets Manager
   - Frontend task
   - Link to ALB target groups

### Google Cloud Platform (GCP)

1. **Push to Container Registry:**
   ```bash
   gcloud auth configure-docker
   docker tag certaro-backend:latest gcr.io/<project-id>/certaro-backend:latest
   docker push gcr.io/<project-id>/certaro-backend:latest
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy certaro-backend \
     --image gcr.io/<project-id>/certaro-backend:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Set up Cloud MongoDB:**
   - Use MongoDB Atlas
   - Or self-host on GCE instances

### Azure Deployment

1. **Push to Azure Container Registry:**
   ```bash
   az acr login --name <registry-name>
   docker tag certaro-backend:latest <registry-name>.azurecr.io/certaro-backend:latest
   docker push <registry-name>.azurecr.io/certaro-backend:latest
   ```

2. **Deploy to Azure Container Instances or App Service:**
   ```bash
   az container create \
     --resource-group certaro-rg \
     --name certaro-backend \
     --image <registry-name>.azurecr.io/certaro-backend:latest \
     --dns-name-label certaro-api \
     --ports 8001
   ```

---

## Database Management

### MongoDB Atlas (Recommended for Production)

1. **Create MongoDB Atlas cluster:**
   - Sign up at https://www.mongodb.com/cloud/atlas
   - Create M10+ cluster for production workloads
   - Configure network access (whitelist IPs)
   - Create database user with strong password

2. **Get connection string:**
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/compliance_checker_prod?retryWrites=true&w=majority
   ```

3. **Update backend .env:**
   ```bash
   MONGO_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net
   DB_NAME=compliance_checker_prod
   ```

### Self-Hosted MongoDB

1. **Install MongoDB:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y mongodb-org

   # Start service
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

2. **Enable authentication:**
   ```bash
   # Create admin user
   mongosh
   use admin
   db.createUser({
     user: "admin",
     pwd: "SecurePassword123!",
     roles: [ { role: "root", db: "admin" } ]
   })

   # Enable auth in /etc/mongod.conf
   security:
     authorization: enabled
   ```

3. **Configure backups:**
   ```bash
   # Daily backup script
   mongodump --uri="mongodb://admin:password@localhost:27017/compliance_checker_prod" --out=/backups/$(date +%Y%m%d)
   ```

---

## Security Hardening

### SSL/TLS Configuration

1. **Obtain SSL certificate:**
   - Use Let's Encrypt for free certificates
   - Or purchase from a certificate authority

2. **Configure Nginx reverse proxy:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name api.yourcompany.com;

       ssl_certificate /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/api.yourcompany.com/privkey.pem;

       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;

       location / {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS only
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# MongoDB should only be accessible from backend
# Do NOT expose port 27017 publicly
```

### Environment Variable Security

- **Never commit .env files to git**
- Use secrets management services:
  - AWS: Secrets Manager or Systems Manager Parameter Store
  - GCP: Secret Manager
  - Azure: Key Vault
  - HashiCorp Vault

---

## Monitoring & Logging

### Application Monitoring

1. **Sentry for error tracking:**
   ```bash
   pip install sentry-sdk
   ```

   Add to `server.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```

2. **Prometheus metrics:**
   ```bash
   pip install prometheus-fastapi-instrumentator
   ```

### Log Aggregation

1. **CloudWatch (AWS):**
   - Configure ECS tasks to send logs to CloudWatch
   - Set up log retention policies

2. **ELK Stack (Self-hosted):**
   - Elasticsearch for storage
   - Logstash for processing
   - Kibana for visualization

3. **Log file rotation:**
   ```bash
   # /etc/logrotate.d/certaro
   /var/log/certaro/*.log {
       daily
       rotate 14
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

---

## Backup & Recovery

### Database Backups

1. **Automated daily backups:**
   ```bash
   #!/bin/bash
   # /usr/local/bin/backup-mongo.sh

   BACKUP_DIR=/backups/mongodb
   DATE=$(date +%Y%m%d_%H%M%S)

   mongodump --uri="$MONGO_URL" --out="$BACKUP_DIR/$DATE"

   # Keep only last 30 days
   find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
   ```

2. **Cron job:**
   ```bash
   # Daily at 2 AM
   0 2 * * * /usr/local/bin/backup-mongo.sh
   ```

3. **Offsite backup:**
   ```bash
   # Sync to S3
   aws s3 sync /backups/mongodb s3://certaro-backups/mongodb/
   ```

### Disaster Recovery

1. **Restore from backup:**
   ```bash
   mongorestore --uri="$MONGO_URL" /backups/mongodb/20250124_020000
   ```

2. **Recovery Time Objective (RTO):** < 4 hours
3. **Recovery Point Objective (RPO):** < 24 hours

---

## Troubleshooting

### Backend Won't Start

1. **Check environment variables:**
   ```bash
   docker-compose exec backend env | grep -E 'MONGO_URL|JWT_SECRET'
   ```

2. **Check MongoDB connection:**
   ```bash
   docker-compose exec backend python -c "from pymongo import MongoClient; client = MongoClient('$MONGO_URL'); print(client.server_info())"
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

### Frontend Can't Connect to Backend

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8001/health
   ```

2. **Check CORS configuration:**
   - Ensure frontend URL is in `CORS_ORIGINS`

3. **Check browser console for errors**

### High Memory Usage

1. **Check ChromaDB data size:**
   ```bash
   du -sh /app/chromadb_data
   ```

2. **Increase container memory limits in docker-compose.yml:**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           memory: 4G
   ```

### Database Performance Issues

1. **Add indexes:**
   ```javascript
   db.qsp_documents.createIndex({ tenant_id: 1, filename: 1 })
   db.regulatory_documents.createIndex({ tenant_id: 1, framework: 1 })
   ```

2. **Monitor slow queries:**
   ```javascript
   db.setProfilingLevel(1, { slowms: 100 })
   db.system.profile.find().sort({ ts: -1 }).limit(5)
   ```

---

## Post-Deployment

### Initial Admin Setup

1. **Login with admin credentials**
2. **Change admin password immediately**
3. **Create additional user accounts**
4. **Upload initial regulatory documents**

### Health Checks

- Backend health: `https://api.yourcompany.com/health`
- Frontend: `https://app.yourcompany.com`
- Database: Monitor connection count and query performance

### Monitoring Alerts

Set up alerts for:
- API response time > 2 seconds
- Error rate > 1%
- Database connections > 80% of max
- Disk usage > 80%
- Memory usage > 90%

---

## Support

For deployment assistance:
- Review logs in `/var/log/certaro/`
- Check GitHub Issues
- Contact: [Your support contact]

---

**Last Updated:** 2025-11-24
