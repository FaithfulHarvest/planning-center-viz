# Planning Center Visualization

A multi-tenant SaaS web app for churches to visualize their Planning Center check-in data.

## Features

- 2-week free trial for new churches
- Secure Planning Center API credential storage
- On-demand data synchronization
- Dashboard with canned charts:
  - Attendance over time (line chart)
  - Check-ins by event (bar chart)
  - Demographics (age groups + gender distribution)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Azure SQL Server
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **Deployment**: Fly.io

## Project Structure

```
planning-center-viz/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── etl/          # PCO data sync
│   ├── Dockerfile
│   └── fly.toml
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── context/      # Auth context
│   ├── Dockerfile
│   └── fly.toml
└── docker-compose.yml
```

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional, for local SQL Server)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your database credentials

# Run the server
uvicorn app.main:app --reload --port 8080
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:5173 and will proxy API requests to http://localhost:8080.

## Deployment to Fly.io

### Initial Setup

1. Install the Fly CLI: https://fly.io/docs/hands-on/install-flyctl/

2. Login to Fly.io:
   ```bash
   fly auth login
   ```

3. Create the apps:
   ```bash
   cd backend
   fly apps create pco-viz-backend

   cd ../frontend
   fly apps create pco-viz-frontend
   ```

### Configure Secrets

```bash
# Backend secrets
fly secrets set -a pco-viz-backend \
    DATABASE_URL="mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+18+for+SQL+Server" \
    SECRET_KEY="your-jwt-secret-key" \
    ENCRYPTION_KEY="your-fernet-key" \
    CORS_ORIGINS="https://pco-viz-frontend.fly.dev"
```

### Deploy

```bash
# Deploy backend
cd backend
fly deploy

# Deploy frontend
cd ../frontend
fly deploy
```

## Environment Variables

### Backend

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Azure SQL Server connection string |
| `SECRET_KEY` | JWT signing key |
| `ENCRYPTION_KEY` | Fernet key for encrypting PCO credentials |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `TRIAL_DURATION_DAYS` | Trial length (default: 14) |

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL |

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create tenant + admin user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user info

### Tenant
- `GET /api/tenant` - Get tenant info
- `PUT /api/tenant/credentials` - Update PCO credentials
- `POST /api/tenant/test-credentials` - Test PCO connection

### Data
- `POST /api/data/refresh` - Start data refresh
- `GET /api/data/refresh/status` - Get refresh status

### Charts
- `GET /api/charts/attendance` - Attendance over time
- `GET /api/charts/events` - Event breakdown
- `GET /api/charts/demographics` - Demographics data
- `GET /api/charts/summary` - Summary statistics

## License

Private - All rights reserved.
