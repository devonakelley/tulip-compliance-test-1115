# Enterprise QSP Compliance System

A robust, enterprise-grade QSP Compliance Checker that takes regulatory standard changes and alerts companies where their internal QSP documents need updates.

## 🎯 Overview

The Enterprise QSP Compliance System helps medical device companies:
- **Monitor regulatory changes** (like ISO 13485:2024 updates) 
- **Analyze internal QSP documents** for compliance gaps
- **Generate specific alerts** like "ISO change detected that impacts QSP doc X in section X"
- **Provide actionable recommendations** for compliance teams

## 🚀 Features

- **Document Processing**: Upload QSP documents (.docx, .txt, PDF) and regulatory change summaries
- **AI-Powered Analysis**: Multi-model AI integration (GPT, Claude, Gemini) for compliance assessment
- **Impact Detection**: Automated analysis of how regulatory changes affect existing QSP documents
- **Comprehensive Dashboard**: Real-time compliance metrics and gap analysis
- **Alert System**: Dashboard notifications, detailed reports, and email alerts
- **Enterprise Security**: Role-based access, audit logging, rate limiting

## 🏗️ Architecture

- **Backend**: FastAPI + MongoDB + Emergent LLM integration
- **Frontend**: React with professional UI components
- **Database**: MongoDB with optimized collections and indexing
- **AI Integration**: Multi-model support via emergentintegrations library
- **Deployment**: Docker-ready with Kubernetes support

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Emergent LLM API Key

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd qsp-compliance-system
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Environment Configuration

Create `backend/.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=qsp_compliance
EMERGENT_LLM_KEY=your-emergent-llm-key
CORS_ORIGINS=http://localhost:3000
```

Create `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🚀 Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Production Mode

```bash
# Build and run with Docker
docker-compose up --build
```

## 📊 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8001/api/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8001/health

## 🔧 Key Endpoints

- `POST /api/documents/upload` - Upload QSP documents
- `POST /api/regulatory/process-summary` - Process regulatory changes
- `POST /api/analysis/run` - Run compliance analysis
- `GET /api/analysis/{analysis_id}` - Get analysis results
- `GET /health` - System health check

## 📁 Project Structure

```
qsp-compliance-system/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── database/            # MongoDB integration
│   ├── core/               # Business logic
│   ├── middleware/         # Custom middleware
│   ├── auth/               # Authentication
│   └── requirements.txt    # Dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── components/     # UI components
│   │   └── services/       # API services
│   └── package.json        # Dependencies
├── docker-compose.yml      # Container orchestration
└── README.md              # This file
```

## 🔐 Security Features

- JWT-based authentication
- Rate limiting and request validation
- Audit logging for all operations
- Secure file upload with validation
- MongoDB injection protection

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

## 📈 Monitoring

The system includes comprehensive monitoring:
- Health checks for all services
- Performance metrics collection
- Error tracking and alerting
- Database connection monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs`
- Review the health status at `/health`