# ohra


## Quick Start

1. **Copy environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file with your actual values:**
   - AWS credentials
   - SageMaker endpoint names
   - Atlassian credentials

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Check service status:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f backend
   docker-compose logs -f worker
   ```

## Services

### Infrastructure Services

- **Qdrant** (ports 6333, 6334): Vector store for embeddings

### Application Services

- **Backend** (port 8000): FastAPI application
  - API: http://localhost:8000
  - Docs: http://localhost:8000/docs/openapi
  - Health: http://localhost:8000/health

- **Worker**: Document synchronization worker
  - Runs scheduled sync jobs for Confluence and Jira

## Environment Variables

See `env.example` for all required environment variables.

### Required Variables

1. **AWS Credentials:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`

2. **SageMaker Endpoints:**
   - `OHRA_SAGEMAKER__LLM_ENDPOINT`
   - `OHRA_SAGEMAKER__EMBEDDING_ENDPOINT`
   - `OHRA_SAGEMAKER__EMBEDDING_DIMENSION` (default: 768)

3. **Atlassian:**
   - `OHRA_ATLASSIAN__CONFLUENCE_URL`
   - `OHRA_ATLASSIAN__JIRA_URL`
   - `OHRA_ATLASSIAN__TOKEN`

## Database

- **SQLite**: Database file is created at `./projects/ohra-backend/data/ohra.db`
- No separate database service needed
- Database URL: `sqlite+aiosqlite:///./data/ohra.db`

## Database Migrations

Run migrations after starting services:

```bash
docker-compose exec backend uv run alembic upgrade head
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

## Troubleshooting

### Check service health:
```bash
docker-compose ps
```

### View specific service logs:
```bash
docker-compose logs backend
docker-compose logs worker
docker-compose logs qdrant
```

### Restart a service:
```bash
docker-compose restart backend
```

### Access service shell:
```bash
docker-compose exec backend bash
docker-compose exec worker bash
```
