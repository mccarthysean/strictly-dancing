# Strictly Dancing

Global Dance Host Marketplace - connecting travelers and dance enthusiasts with qualified dance hosts for paid social dancing sessions worldwide.

## Tech Stack

- **PWA Web App**: React + Vite + TanStack Router/Query
- **Mobile Apps**: React Native + Expo (iOS/Android)
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Payments**: Stripe Connect
- **Database**: AWS RDS PostgreSQL with PostGIS
- **Real-time**: FastAPI WebSockets + Redis Pub/Sub

## Local Development Setup

### Prerequisites

- **Python 3.12+** - [python.org](https://www.python.org/downloads/)
- **Node.js 20+** or **Bun** (recommended) - [bun.sh](https://bun.sh/)
- **UV** - Python package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Docker & Docker Compose** - For local services
- **iOS Development** (macOS only):
  - Xcode 15+ from Mac App Store
  - iOS Simulator (included with Xcode)
  - Command Line Tools: `xcode-select --install`
- **Android Development**:
  - Android Studio with SDK 34+
  - Android Emulator configured
  - ANDROID_HOME environment variable set
- **Expo Go App** (for physical device testing):
  - [iOS App Store](https://apps.apple.com/app/expo-go/id982107779)
  - [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/strictly-dancing.git
cd strictly-dancing

# Start all services
./scripts/dev-setup.sh  # (coming soon)

# Or start individually (see below)
```

---

## Backend Development

### Setup

```bash
cd backend

# Install dependencies with UV
uv sync

# Copy environment template
cp .env.example .env  # Edit with your database credentials

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn app.main:app --reload --port 8001
```

### API Documentation

Once running, access the API docs at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- OpenAPI JSON: http://localhost:8001/openapi.json

### Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v --tb=short

# Run specific test file
uv run pytest tests/unit/test_auth_router.py

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Linting

```bash
cd backend
ruff check --fix .
ruff format .
```

---

## PWA Frontend Development

### Setup

```bash
cd frontend

# Install dependencies
bun install

# Start development server (hot reload enabled)
bun run dev
```

### Development Server

The PWA runs at **http://localhost:5175** with:
- Hot Module Replacement (HMR) for instant updates
- TanStack Router DevTools in development
- Service Worker registration in production build
- Strict port binding (fails if port is in use)

### Type Generation

After any backend API changes, regenerate TypeScript types:

```bash
cd frontend

# Requires backend running on port 8001
bun run generate-types
```

### Running Tests

```bash
cd frontend

# Run all tests
bun run test

# Run in watch mode
bun run test:watch

# Run with coverage
bun run test:coverage
```

### Building for Production

```bash
cd frontend

# Type check and build
bun run build

# Preview production build
bun run preview
```

---

## Mobile Development

### Setup

```bash
cd apps/mobile

# Install dependencies
bun install

# Start Expo development server
bun run start
```

### iOS Simulator Testing (macOS only)

1. **Ensure Xcode is installed** from the Mac App Store

2. **Open iOS Simulator**:
   ```bash
   # From Expo dev server, press 'i'
   # Or manually open Simulator.app
   open -a Simulator
   ```

3. **Start the app on iOS**:
   ```bash
   cd apps/mobile
   bun run ios
   # Or press 'i' in the Expo CLI menu
   ```

4. **Troubleshooting iOS Simulator**:
   - Clear Expo cache: `expo start --clear`
   - Reset Simulator: Device > Erase All Content and Settings
   - Rebuild: `expo prebuild --platform ios && expo run:ios`

### Android Emulator Testing

1. **Install Android Studio** from [developer.android.com](https://developer.android.com/studio)

2. **Configure SDK and Emulator**:
   - Open Android Studio > Tools > SDK Manager
   - Install Android SDK 34 (Android 14)
   - Install Intel HAXM (or Hypervisor Framework on M1+ Macs)
   - Create AVD: Tools > Device Manager > Create Device
   - Recommended: Pixel 6 with API 34

3. **Set environment variables** (add to ~/.bashrc or ~/.zshrc):
   ```bash
   export ANDROID_HOME=$HOME/Library/Android/sdk  # macOS
   # export ANDROID_HOME=$HOME/Android/Sdk       # Linux
   export PATH=$PATH:$ANDROID_HOME/emulator
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

4. **Start the emulator and app**:
   ```bash
   # Start emulator (if not already running)
   emulator -avd Pixel_6_API_34

   # Start app on Android
   cd apps/mobile
   bun run android
   # Or press 'a' in the Expo CLI menu
   ```

5. **Troubleshooting Android Emulator**:
   - Check ADB connection: `adb devices`
   - Clear app data: `adb shell pm clear com.strictlydancing.mobile`
   - Cold boot emulator: Device Manager > ... > Cold Boot Now

### Expo Go Testing (Physical Devices)

1. **Install Expo Go** on your device:
   - [iOS App Store](https://apps.apple.com/app/expo-go/id982107779)
   - [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. **Connect to same network** as your development machine

3. **Start the Expo server**:
   ```bash
   cd apps/mobile
   bun run start
   ```

4. **Scan the QR code**:
   - iOS: Open Camera app, scan QR code, tap the Expo Go link
   - Android: Open Expo Go app, tap "Scan QR Code"

5. **Troubleshooting Expo Go**:
   - If QR code doesn't work, switch to tunnel: `expo start --tunnel`
   - Clear Expo Go cache: Settings > Expo Go > Clear Expo Cache
   - Ensure firewall allows connections on port 8081

### Mobile Type Generation

After backend API changes:

```bash
cd apps/mobile

# Requires backend running on port 8001
bun run generate-types
```

### Running Mobile Tests

```bash
cd apps/mobile

# Run all tests
bun run test

# Run in watch mode
bun run test:watch

# Run with coverage
bun run test:coverage
```

---

## Development Workflow

### Starting All Services

For full-stack development, start services in this order:

```bash
# Terminal 1: Backend API
cd backend && uv run uvicorn app.main:app --reload --port 8001

# Terminal 2: PWA Frontend
cd frontend && bun run dev

# Terminal 3: Mobile (optional)
cd apps/mobile && bun run start
```

### Type Generation After API Changes

After modifying any FastAPI endpoint or Pydantic schema:

```bash
# Generate frontend types
cd frontend && bun run generate-types

# Generate mobile types
cd apps/mobile && bun run generate-types
```

### Pre-commit Checklist

Before committing changes:

```bash
# Backend
cd backend
ruff check --fix .
ruff format .
uv run pytest

# Frontend
cd frontend
bun run tsc
bun run test

# Mobile
cd apps/mobile
bun run tsc
bun run test
```

---

## Project Structure

```
strictly-dancing/
├── frontend/              # PWA Web App (React + Vite)
│   ├── src/
│   │   ├── routes/        # TanStack Router pages
│   │   ├── components/    # Reusable UI components
│   │   ├── contexts/      # React contexts (Auth)
│   │   ├── lib/api/       # OpenAPI client
│   │   └── types/         # Generated TypeScript types
│   └── vite.config.ts     # Vite + PWA configuration
│
├── apps/mobile/           # React Native Expo app
│   ├── app/               # Expo Router pages
│   ├── stores/            # Zustand state stores
│   ├── lib/               # API client, utilities
│   └── types/             # Generated TypeScript types
│
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py        # App entry point
│   │   ├── core/          # Config, database, deps
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── repositories/  # Data access layer
│   │   ├── services/      # Business logic
│   │   └── routers/       # API endpoints
│   ├── tests/             # pytest tests
│   └── alembic/           # Database migrations
│
├── ralph/                 # TDD development plans
└── mcp-postgres-server/   # PostgreSQL MCP server
```

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/strictly_dancing
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8001
```

### Mobile (.env)

```env
EXPO_PUBLIC_API_URL=http://localhost:8001
```

---

## Troubleshooting

### Common Issues

**Port 5175 already in use:**
```bash
# Find and kill the process
lsof -ti:5175 | xargs kill -9
```

**Backend can't connect to database:**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists: `psql -l`

**Type generation fails:**
- Ensure backend is running on port 8001
- Check for Python syntax errors
- Verify OpenAPI schema: http://localhost:8001/openapi.json

**Expo build issues:**
```bash
# Clear all caches
cd apps/mobile
rm -rf node_modules .expo
bun install
expo start --clear
```

**iOS Simulator not showing:**
- Open Xcode at least once to accept license
- Install iOS runtime: Xcode > Settings > Platforms > + iOS

**Android Emulator slow:**
- Enable hardware acceleration (HAXM or HVF)
- Allocate more RAM to emulator
- Use cold boot if emulator is stuck

---

## Documentation

- [PRD.md](./PRD.md) - Product Requirements Document
- [PLAN.md](./PLAN.md) - Technology Stack Plan
- [CLAUDE.md](./CLAUDE.md) - AI Assistant Instructions

---

## License

Proprietary - All rights reserved.
