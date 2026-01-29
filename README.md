# Strictly Dancing

Global Dance Host Marketplace - connecting travelers and dance enthusiasts with qualified dance hosts for paid social dancing sessions worldwide.

## Tech Stack

- **PWA Web App**: React + Vite + TanStack Router/Query
- **Mobile Apps**: React Native + Expo (iOS/Android)
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Payments**: Stripe Connect
- **Database**: AWS RDS PostgreSQL with PostGIS
- **Real-time**: FastAPI WebSockets + Redis Pub/Sub

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+ or Bun
- Docker & Docker Compose
- AWS CLI configured

### Backend Setup

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

### Web Frontend Setup

```bash
cd frontend
bun install
bun run dev
```

### Mobile Setup

```bash
cd apps/mobile
bun install
bun run start
```

## Development

### Type Generation

After any FastAPI endpoint changes:

```bash
cd frontend && bun run generate-types
```

### Running Tests

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && bun run test
```

### Linting

```bash
# Python
cd backend && ruff check --fix . && ruff format .

# TypeScript
cd frontend && bun run tsc
```

## Project Structure

```
strictly-dancing/
├── frontend/              # PWA Web App
├── apps/mobile/           # React Native app
├── backend/               # FastAPI backend
├── ralph/                 # TDD development plans
└── mcp-postgres-server/   # PostgreSQL MCP server
```

## Documentation

- [PRD.md](./PRD.md) - Product Requirements Document
- [PLAN.md](./PLAN.md) - Technology Stack Plan
- [CLAUDE.md](./CLAUDE.md) - AI Assistant Instructions

## License

Proprietary - All rights reserved.
