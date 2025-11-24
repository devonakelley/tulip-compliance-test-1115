# Certaro - Medical Device Compliance Platform

**AI-Powered Quality System Procedure (QSP) Compliance Checker**

Certaro is a multi-tenant SaaS platform designed for medical device companies to ensure compliance with ISO 13485:2024 and other regulatory standards. The system automatically detects gaps between internal Quality System Procedures (QSPs) and regulatory requirements using AI-powered semantic matching.

## Features

- **Regulatory Document Management**: Upload and compare regulatory standards (ISO 13485:2024, FDA 21 CFR Part 820, etc.)
- **QSP Document Analysis**: Parse and analyze company Quality System Procedures
- **AI-Powered Gap Analysis**: Two-stage matching system combining:
  - Explicit reference matching
  - Semantic similarity analysis using OpenAI embeddings
- **Change Impact Detection**: Identify which QSPs are affected by regulatory changes
- **RAG-Based Knowledge Base**: ChromaDB vector database for regulatory knowledge retrieval
- **Multi-Tenant Architecture**: Secure isolation for multiple organizations
- **JWT Authentication**: Secure user authentication and authorization

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: MongoDB (with Motor async driver)
- **AI/ML**: OpenAI API (text-embedding-3-large), LiteLLM, Emergent LLM
- **Vector Store**: ChromaDB for semantic search
- **File Processing**: PyMuPDF, PyPDF2, python-docx
- **Authentication**: JWT tokens with bcrypt password hashing

### Frontend
- **Framework**: React 19
- **Styling**: TailwindCSS
- **UI Components**: Shadcn/UI (Radix UI)
- **Build Tool**: CRACO (Create React App Configuration Override)
- **Routing**: React Router v7

## Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher
- **MongoDB**: 4.4 or higher
- **OpenAI API Key**: For embeddings and LLM capabilities

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tulip-compliance-test-1115
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env file with your credentials
# REQUIRED variables:
#   - MONGO_URL (MongoDB connection string)
#   - DB_NAME (Database name)
#   - JWT_SECRET_KEY (Generate with: openssl rand -hex 32)
#   - OPENAI_API_KEY (Your OpenAI API key)
#   - ADMIN_EMAIL (Initial admin email)
#   - ADMIN_PASSWORD (Initial admin password)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Create .env file from example
cp .env.example .env

# Edit .env file
# Set REACT_APP_BACKEND_URL to your backend URL (default: http://localhost:8001)
```

### 4. Database Initialization

```bash
# Ensure MongoDB is running
# Default: mongodb://localhost:27017

# Seed the database with admin user
cd backend
python seed_admin.py
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m uvicorn server:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

### Production Mode (Docker)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB connection string | Yes |
| `DB_NAME` | Database name | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ADMIN_EMAIL` | Initial admin email | Yes (for seeding) |
| `ADMIN_PASSWORD` | Initial admin password | Yes (for seeding) |
| `CORS_ORIGINS` | Allowed CORS origins | No (default: http://localhost:3000) |
| `ALGORITHM` | JWT algorithm | No (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | No (default: 1440) |

### Frontend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_BACKEND_URL` | Backend API URL | Yes |
| `REACT_APP_NAME` | Application name | No |

## Project Structure

```
.
├── backend/
│   ├── server.py                 # Main FastAPI application
│   ├── requirements.txt          # Python dependencies
│   ├── api/                      # API route modules
│   │   ├── auth_api.py          # Authentication endpoints
│   │   ├── change_impact.py     # Change impact analysis
│   │   ├── regulatory_upload.py # Regulatory document upload
│   │   └── rag.py               # RAG endpoints
│   ├── core/                    # Core business logic
│   │   ├── auth.py              # JWT authentication
│   │   ├── change_impact_service_mongo.py
│   │   ├── rag_service.py       # ChromaDB + RAG
│   │   └── storage_service.py   # File storage
│   ├── models/                  # Pydantic models
│   └── data/                    # QSP and regulatory documents
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main application
│   │   ├── components/          # React components
│   │   │   ├── GapAnalysisSimplified.js
│   │   │   ├── QSPUploadSimplified.js
│   │   │   └── ui/              # Shadcn/UI components
│   │   ├── context/             # React context
│   │   ├── pages/               # Page components
│   │   └── hooks/               # Custom hooks
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml           # Docker orchestration
└── README.md                    # This file
```

## API Documentation

Once the backend is running, visit http://localhost:8001/docs for interactive API documentation (Swagger UI).

## Key Workflows

### 1. Upload Regulatory Documents
1. Navigate to "Regulatory Upload"
2. Upload regulatory standard (PDF/DOCX)
3. System parses and stores clauses in MongoDB

### 2. Upload QSP Documents
1. Navigate to "QSP Upload"
2. Upload your company's QSP documents
3. System processes and maps sections

### 3. Run Gap Analysis
1. Navigate to "Gap Analysis"
2. Select regulatory standard and QSP documents
3. System performs two-stage matching:
   - Stage 1: Explicit reference matching
   - Stage 2: Semantic similarity analysis
4. Review identified gaps and recommendations

### 4. Change Impact Analysis
1. Upload new version of regulatory standard
2. System identifies changed clauses
3. System maps changes to affected QSPs
4. Generate change impact report

## Security Considerations

### Production Deployment Checklist

- [ ] Change default admin credentials immediately after first login
- [ ] Use a strong, randomly generated JWT secret key (min 32 characters)
- [ ] Set `CORS_ORIGINS` to your production domain only
- [ ] Enable HTTPS/TLS in production
- [ ] Use environment variables for all secrets (never commit .env files)
- [ ] Enable rate limiting on API endpoints
- [ ] Implement regular database backups
- [ ] Set up monitoring and alerting
- [ ] Review and update security headers
- [ ] Conduct security audit before production launch

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
yarn test
```

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `sudo systemctl status mongod`
- Verify `MONGO_URL` in .env file
- Check firewall settings

### Frontend Can't Connect to Backend
- Verify `REACT_APP_BACKEND_URL` in frontend/.env
- Check CORS settings in backend
- Ensure backend is running on correct port

### JWT Token Errors
- Ensure `JWT_SECRET_KEY` is set in backend/.env
- Check token expiration settings
- Clear browser localStorage and re-login

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact: [Your contact information]

## Acknowledgments

- ISO 13485:2024 regulatory framework
- OpenAI for embeddings and LLM capabilities
- ChromaDB for vector database functionality
- FastAPI and React communities
