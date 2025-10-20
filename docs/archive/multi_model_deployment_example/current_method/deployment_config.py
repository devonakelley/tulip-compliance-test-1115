"""
Multi-Model Deployment Configuration Generator
Creates all necessary configuration files for deploying across AI models
This shows the deployment complexity of the current method
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class MultiModelDeployment:
    def __init__(self, app_name: str, domain: str):
        self.app_name = app_name
        self.domain = domain
    
    def generate_claude_config(self) -> dict:
        """Generate Claude Desktop configuration"""
        return {
            "mcpServers": {
                self.app_name: {
                    "url": f"wss://{self.domain}/mcp",
                    "name": self.app_name.replace('-', ' ').title(),
                    "description": "Universal Task Manager with AI integration"
                }
            }
        }
    
    def generate_gpt_actions_config(self) -> dict:
        """Generate GPT Actions configuration"""
        return {
            "openapi_url": f"https://{self.domain}/api/gpt/openapi.json",
            "name": "Universal Task Manager",
            "description": "Comprehensive task management with AI assistance",
            "instructions": f"Use this API to manage tasks in {self.app_name}. You can create, list, update, and delete tasks, as well as upload files and get analytics.",
            "privacy_policy": f"https://{self.domain}/privacy",
            "auth": {"type": "none"},
            "capabilities": [
                "task_creation",
                "task_management", 
                "file_upload",
                "analytics"
            ]
        }
    
    def generate_gemini_config(self) -> dict:
        """Generate Gemini Extension configuration"""
        return {
            "extension_manifest": {
                "name": self.app_name,
                "display_name": "Universal Task Manager",
                "version": "1.0.0",
                "description": "AI-powered task management system",
                "functions_endpoint": f"https://{self.domain}/gemini/functions",
                "execute_endpoint": f"https://{self.domain}/gemini/execute",
                "schema_endpoint": f"https://{self.domain}/gemini/schema"
            },
            "deployment_settings": {
                "auto_scaling": True,
                "max_concurrent_requests": 100,
                "timeout_seconds": 30
            }
        }
    
    def generate_copilot_config(self) -> dict:
        """Generate Microsoft Copilot configuration"""
        return {
            "plugin_manifest": f"https://{self.domain}/copilot/.well-known/ai-plugin.json",
            "openapi_spec": f"https://{self.domain}/copilot/openapi.yaml",
            "capabilities": {
                "task_management": True,
                "file_handling": True,
                "analytics": True,
                "real_time_updates": False
            },
            "microsoft_365_integration": {
                "outlook_tasks": True,
                "teams_integration": True,
                "sharepoint_files": False
            }
        }
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose for all services"""
        return f"""version: '3.8'

services:
  main-api:
    build: .
    container_name: {self.app_name}-main
    ports:
      - "8001:8001"
    environment:
      - DOMAIN={self.domain}
      - NODE_ENV=production
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: python multi_model_server.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  gemini-service:
    build: .
    container_name: {self.app_name}-gemini
    ports:
      - "8002:8002"
    environment:
      - DOMAIN={self.domain}
      - SERVICE_TYPE=gemini
    depends_on:
      - main-api
    command: python gemini_extension.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  copilot-service:
    build: .
    container_name: {self.app_name}-copilot
    ports:
      - "8003:8003"
    environment:
      - DOMAIN={self.domain}
      - SERVICE_TYPE=copilot
    depends_on:
      - main-api
    command: python copilot_plugin.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/copilot/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  nginx:
    image: nginx:alpine
    container_name: {self.app_name}-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - main-api
      - gemini-service
      - copilot-service
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: {self.app_name}-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: {self.app_name}-network
"""

    def generate_nginx_config(self) -> str:
        """Generate Nginx configuration for routing"""
        return f"""events {{
    worker_connections 1024;
}}

http {{
    upstream main_api {{
        server main-api:8001;
        keepalive 32;
    }}
    
    upstream gemini_service {{
        server gemini-service:8002;
        keepalive 32;
    }}
    
    upstream copilot_service {{
        server copilot-service:8003;
        keepalive 32;
    }}

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=uploads:10m rate=2r/s;

    # Logging
    log_format detailed '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log detailed;
    error_log /var/log/nginx/error.log warn;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {{
        listen 80;
        server_name {self.domain};
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Main API and Claude MCP
        location /api/ {{
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://main_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }}
        
        # Claude MCP WebSocket
        location /mcp {{
            proxy_pass http://main_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }}
        
        # File uploads with larger body size
        location /api/upload {{
            limit_req zone=uploads burst=5 nodelay;
            client_max_body_size 100M;
            proxy_pass http://main_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_request_buffering off;
        }}
        
        # Gemini Extension
        location /gemini/ {{
            limit_req zone=api burst=15 nodelay;
            proxy_pass http://gemini_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}
        
        # Microsoft Copilot
        location /copilot/ {{
            limit_req zone=api burst=15 nodelay;
            proxy_pass http://copilot_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}
        
        # Health checks
        location /health {{
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }}
        
        # Static files (if any)
        location /static/ {{
            root /var/www;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
}}
"""

    def generate_dockerfile(self) -> str:
        """Generate Dockerfile for the application"""
        return """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Expose ports
EXPOSE 8001 8002 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8001/health || exit 1

# Default command
CMD ["python", "multi_model_server.py"]
"""

    def generate_requirements_txt(self) -> str:
        """Generate requirements.txt for the application"""
        return """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
websockets==12.0
aiofiles==23.2.1
python-multipart==0.0.6
pyyaml==6.0.1
redis==5.0.1
"""

    def save_all_configs(self, output_dir: Path):
        """Save all configuration files"""
        output_dir.mkdir(exist_ok=True)
        
        # AI Model configurations
        configs_dir = output_dir / "configs"
        configs_dir.mkdir(exist_ok=True)
        
        with open(configs_dir / "claude_config.json", "w") as f:
            json.dump(self.generate_claude_config(), f, indent=2)
        
        with open(configs_dir / "gpt_actions_config.json", "w") as f:
            json.dump(self.generate_gpt_actions_config(), f, indent=2)
        
        with open(configs_dir / "gemini_config.json", "w") as f:
            json.dump(self.generate_gemini_config(), f, indent=2)
        
        with open(configs_dir / "copilot_config.json", "w") as f:
            json.dump(self.generate_copilot_config(), f, indent=2)
        
        # Deployment files
        with open(output_dir / "docker-compose.yml", "w") as f:
            f.write(self.generate_docker_compose())
        
        with open(output_dir / "nginx.conf", "w") as f:
            f.write(self.generate_nginx_config())
            
        with open(output_dir / "Dockerfile", "w") as f:
            f.write(self.generate_dockerfile())
            
        with open(output_dir / "requirements.txt", "w") as f:
            f.write(self.generate_requirements_txt())
    
    def generate_deployment_script(self) -> str:
        """Generate deployment script"""
        return f"""#!/bin/bash
set -e

echo "🚀 Deploying {self.app_name} Multi-Model Application..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || {{ echo "Docker is required but not installed. Aborting." >&2; exit 1; }}
command -v docker-compose >/dev/null 2>&1 || {{ echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }}

# Create necessary directories
mkdir -p data logs ssl

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health checks
echo "🏥 Checking service health..."
curl -f http://localhost:8001/api/ || {{ echo "Main API health check failed"; exit 1; }}
curl -f http://localhost:8002/health || {{ echo "Gemini service health check failed"; exit 1; }}
curl -f http://localhost:8003/copilot/health || {{ echo "Copilot service health check failed"; exit 1; }}

echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Service URLs:"
echo "  Main API: http://{self.domain}/api/"
echo "  Claude MCP: ws://{self.domain}/mcp"
echo "  GPT Actions: http://{self.domain}/api/gpt/openapi.json"
echo "  Gemini: http://{self.domain}/gemini/functions"
echo "  Copilot: http://{self.domain}/copilot/.well-known/ai-plugin.json"
echo ""
echo "📋 Next steps:"
echo "  1. Configure Claude Desktop with the MCP endpoint"
echo "  2. Import GPT Actions schema in ChatGPT"
echo "  3. Set up Gemini Extension in AI Studio"
echo "  4. Configure Copilot plugin in Microsoft 365"
"""

def main():
    """Main function to generate all deployment configurations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate multi-model deployment configurations")
    parser.add_argument("--app-name", default="universal-task-manager", help="Application name")
    parser.add_argument("--domain", default="your-app.com", help="Domain name")
    parser.add_argument("--output", default="./deployment", help="Output directory")
    
    args = parser.parse_args()
    
    deployment = MultiModelDeployment(args.app_name, args.domain)
    output_path = Path(args.output)
    
    print(f"Generating deployment configurations for {args.app_name}...")
    deployment.save_all_configs(output_path)
    
    # Save deployment script
    with open(output_path / "deploy.sh", "w") as f:
        f.write(deployment.generate_deployment_script())
    os.chmod(output_path / "deploy.sh", 0o755)
    
    print(f"✅ Configurations generated in {output_path}")
    print(f"📁 Files created:")
    for file_path in output_path.rglob("*"):
        if file_path.is_file():
            print(f"  - {file_path.relative_to(output_path)}")

if __name__ == "__main__":
    main()
"""

This script generates all necessary configuration files for deploying
a multi-model AI application across GPT, Claude, Gemini, and Copilot.

Usage:
    python deployment_config.py --app-name my-app --domain my-domain.com
"""