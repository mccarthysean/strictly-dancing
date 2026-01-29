---
name: FastAPI Development
description: Build FastAPI endpoints with Pydantic models, async database operations, and proper error handling. Use when creating API endpoints, modifying routes, implementing CRUD operations, or working with the backend.
allowed-tools: [Read, Write, Edit, Bash]
---

# FastAPI Development Skill

## Purpose
Build FastAPI endpoints with proper patterns for the Strictly Dancing backend.

## When to Use This Skill
- Creating new API endpoints
- Modifying existing routes
- Implementing CRUD operations
- Working with Pydantic models
- Database operations with SQLAlchemy

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/             # API route handlers
│   │   ├── auth.py
│   │   ├── hosts.py
│   │   ├── bookings.py
│   │   └── messages.py
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── host_profile.py
│   │   └── booking.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── host_profile.py
│   │   └── booking.py
│   ├── services/            # Business logic
│   └── repositories/        # Data access layer
├── alembic/                 # Database migrations
├── tests/                   # Test files
└── pyproject.toml           # Dependencies
```

## Endpoint Patterns

### Basic CRUD Router
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.host_profile import HostProfile
from app.schemas.host_profile import HostProfileRead, HostProfileCreate, HostProfileUpdate

router = APIRouter(prefix="/hosts", tags=["hosts"])


@router.get("/", response_model=list[HostProfileRead])
async def list_hosts(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all host profiles."""
    result = await db.execute(
        select(HostProfile).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{host_id}", response_model=HostProfileRead)
async def get_host(
    host_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific host profile."""
    result = await db.execute(
        select(HostProfile).where(HostProfile.id == host_id)
    )
    host = result.scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@router.post("/", response_model=HostProfileRead, status_code=201)
async def create_host(
    host_in: HostProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new host profile."""
    host = HostProfile(**host_in.model_dump())
    db.add(host)
    await db.commit()
    await db.refresh(host)
    return host


@router.put("/{host_id}", response_model=HostProfileRead)
async def update_host(
    host_id: int,
    host_in: HostProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a host profile."""
    result = await db.execute(
        select(HostProfile).where(HostProfile.id == host_id)
    )
    host = result.scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    for field, value in host_in.model_dump(exclude_unset=True).items():
        setattr(host, field, value)

    await db.commit()
    await db.refresh(host)
    return host


@router.delete("/{host_id}", status_code=204)
async def delete_host(
    host_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a host profile."""
    result = await db.execute(
        select(HostProfile).where(HostProfile.id == host_id)
    )
    host = result.scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    await db.delete(host)
    await db.commit()
```

## Pydantic Schema Patterns

### Schema Definitions
```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class HostProfileBase(BaseModel):
    """Shared host profile properties."""
    display_name: str
    bio: str | None = None
    hourly_rate: float | None = None
    user_id: int


class HostProfileCreate(HostProfileBase):
    """Properties for creating a host profile."""
    pass


class HostProfileUpdate(BaseModel):
    """Properties for updating a host profile."""
    display_name: str | None = None
    bio: str | None = None
    hourly_rate: float | None = None


class HostProfileRead(HostProfileBase):
    """Properties returned to client."""
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
```

## SQLAlchemy Model Patterns

### Model Definition
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HostProfile(Base):
    __tablename__ = "host_profiles"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    bio = Column(String)
    hourly_rate = Column(Float)
    is_verified = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="host_profile")
    dance_styles = relationship("HostDanceStyle", back_populates="host_profile")
    bookings = relationship("Booking", back_populates="host")
```

## Database Queries

### Common Query Patterns
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Simple select
result = await db.execute(select(HostProfile))
hosts = result.scalars().all()

# With filter
result = await db.execute(
    select(HostProfile).where(HostProfile.is_verified == True)
)

# With relationship loading
result = await db.execute(
    select(HostProfile)
    .options(selectinload(HostProfile.dance_styles))
    .where(HostProfile.id == host_id)
)

# With ordering
result = await db.execute(
    select(HostProfile).order_by(HostProfile.rating.desc())
)

# With pagination
result = await db.execute(
    select(HostProfile)
    .offset(skip)
    .limit(limit)
)
```

## Error Handling

### HTTP Exceptions
```python
from fastapi import HTTPException

# Not found
if not host:
    raise HTTPException(status_code=404, detail="Host not found")

# Bad request
if invalid_data:
    raise HTTPException(status_code=400, detail="Invalid data")

# Unauthorized
if not current_user:
    raise HTTPException(status_code=401, detail="Not authenticated")

# Forbidden
if not has_permission:
    raise HTTPException(status_code=403, detail="Not authorized")
```

## Development Workflow

### Run Development Server
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run uvicorn app.main:app --reload --port 8001
```

### Run Tests
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run pytest
```

### Lint Code
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .
```

### Create Migration
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run alembic revision --autogenerate -m "Add host profile model"
uv run alembic upgrade head
```

## After Making Changes

### Regenerate Frontend Types
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

## Integration
This skill automatically activates when:
- Creating API endpoints
- Modifying FastAPI routes
- Working with Pydantic schemas
- Database operations
- Backend development
