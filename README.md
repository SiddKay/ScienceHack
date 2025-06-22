# ScienceHack Backend API

FastAPI backend for ScienceHack application with Google Cloud Platform deployment support.

> Info: The code for the frontend is available at [ScienceHack Frontend](https://github.com/SiddKay/conflict-orchestrator-playground).

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Docker** (optional, for containerized development)
- **Git**

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ScienceHack
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# Required: Set your OPENAI_API_KEY
```

**Important:** Update `.env` with your actual API keys:
```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

## Development Setup

### Option A: Docker Development (Recommended)

#### macOS/Linux
```bash
# Start development server with hot reload
docker-compose up api

# Or run in background
docker-compose up -d api
```

#### Windows (WSL2)
```bash
# Ensure Docker permissions (run once)
sudo usermod -aG docker $USER
newgrp docker

# Start development server
docker-compose up api
```

#### Windows (PowerShell/CMD)
```bash
# Start development server
docker-compose up api
```

### Option B: Local Python Development

#### macOS/Linux
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

#### Windows (PowerShell)
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

#### Windows (Command Prompt)
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

## API Endpoints

- **GET /** - Root endpoint
- **GET /health** - Health check with system metrics

## Access Your API

- **Local Development:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** http://localhost:8000/health

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `PORT` | No | `8000` | Server port |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `MISTRAL_API_KEY` | Yes | - | Mistral API key |
| `GOOGLE_API_KEY` | Yes | - | Google API key |
| `LOG_LEVEL` | No | `DEBUG` | Logging level |

## Deployment

### Google Cloud Platform
```bash
# Deploy to GCP App Engine
gcloud app deploy

# Or build Docker image
docker build -t sciencehack-api .
```

### Production Environment
Set `ENVIRONMENT=production` in your deployment environment.

## Troubleshooting

### Docker Permission Issues (Linux/WSL)
```bash
sudo usermod -aG docker $USER
newgrp docker
# OR restart your terminal/WSL
```

### Import Errors
```bash
# Rebuild Docker image
docker-compose build --no-cache

# Or update local dependencies
pip install -r requirements.txt --upgrade
```

### Port Already in Use
```bash
# Kill process on port 8000
# Linux/Mac:
sudo lsof -t -i:8000 | xargs kill -9
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Development Commands

```bash
# Stop all containers
docker-compose down

# Rebuild and start
docker-compose up --build api

# View logs
docker-compose logs -f api

# Run production mode locally
docker-compose up api-prod
```