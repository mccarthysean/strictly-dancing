**PRODUCT REQUIREMENTS DOCUMENT**

**Dance Partner**

*Global Dance Host Marketplace Platform*

Version 1.0 \| January 2026

Prepared for Claude Code Implementation

Test-Driven Development \| Bite-Sized Tasks \| Continuous Verification

**Table of Contents**

**1. Executive Summary**

**1.1 Product Vision**

Dance Partner is an Uber-style global marketplace mobile application that connects travelers, singles, and dance enthusiasts with qualified dance hosts for paid social dancing sessions. The platform enables users to book professional or semi-professional dance partners for events including salsa nights, ballroom events, swing dances, and other social dancing occasions worldwide.

**1.2 Problem Statement**

Many people who enjoy social dancing face barriers to participation: they may be traveling alone, lack a regular dance partner, feel intimidated at their skill level, or simply want to improve through dancing with more experienced partners. Currently, there is no global platform that safely and efficiently connects these individuals with vetted, qualified dance hosts.

**1.3 Solution Overview**

Dance Partner provides a two-sided marketplace with the following core value propositions:

-   For Clients: Easy discovery and booking of verified dance hosts by location, dance style, skill level, and availability with secure payment processing and quality assurance through ratings/reviews

-   For Hosts: A platform to monetize dance skills with flexible scheduling, secure payment collection, and professional profile management

-   For the Platform: Commission-based revenue model (15-20% per transaction) with opportunities for premium features and subscriptions

**1.4 Key Success Metrics**

  ---------------------------------------------------------------------------------------
  **Metric**                  **MVP Target (6 months)**   **Growth Target (18 months)**
  --------------------------- --------------------------- -------------------------------
  Registered Hosts            500                         10,000

  Registered Clients          2,000                       100,000

  Monthly Bookings            200                         15,000

  Average Rating              4.5+ stars                  4.7+ stars

  Host Retention (90-day)     60%                         75%

  Client Retention (90-day)   40%                         55%
  ---------------------------------------------------------------------------------------

**2. Technology Stack Specification**

**2.1 Frontend - Mobile Application**

  ---------------------------------------------------------------------------------------------------------------------
  **Component**      **Technology**                **Justification**
  ------------------ ----------------------------- --------------------------------------------------------------------
  Framework          React Native with Expo        Single codebase for iOS/Android, leverages React/TypeScript skills

  Language           TypeScript (strict mode)      Type safety improves AI-assisted development accuracy

  State Management   Zustand + React Query         Lightweight, TypeScript-native, excellent for real-time data

  Navigation         Expo Router                   File-based routing, deep linking support, type-safe

  UI Components      React Native Paper + Custom   Material Design compliance with custom theming

  Maps               react-native-maps             Native map integration for location features

  Forms              React Hook Form + Zod         Type-safe form validation with schema inference
  ---------------------------------------------------------------------------------------------------------------------

**2.2 Backend - API Server**

  ----------------------------------------------------------------------------------------------------------------
  **Component**       **Technology**                 **Justification**
  ------------------- ------------------------------ -------------------------------------------------------------
  Framework           FastAPI (Python 3.12+)         Async support, automatic OpenAPI docs, excellent type hints

  Database ORM        SQLAlchemy 2.0 + asyncpg       Async PostgreSQL support, type-safe queries

  Validation          Pydantic v2                    Request/response validation, JSON schema generation

  Task Queue          Celery + Redis                 Background job processing for emails, notifications

  WebSockets          FastAPI WebSockets             Native async WebSocket support for real-time features

  API Documentation   OpenAPI 3.1 (auto-generated)   Client SDK generation, contract-first development
  ----------------------------------------------------------------------------------------------------------------

**2.3 Database Layer**

  ----------------------------------------------------------------------------------------------------------------
  **Component**      **Technology**                   **Justification**
  ------------------ -------------------------------- ------------------------------------------------------------
  Primary Database   PostgreSQL 16 via Supabase       ACID compliance, PostGIS for geospatial, built-in realtime

  Geospatial         PostGIS Extension                Efficient location queries, distance calculations

  Cache Layer        Redis (Upstash)                  Session storage, rate limiting, pub/sub for WebSockets

  Search             PostgreSQL Full-Text + pg_trgm   Host search, fuzzy matching

  Migrations         Alembic                          Version-controlled schema changes, rollback support
  ----------------------------------------------------------------------------------------------------------------

**2.4 Real-Time Infrastructure**

  -----------------------------------------------------------------------------------------------------------
  **Feature**             **Technology**               **Implementation**
  ----------------------- ---------------------------- ------------------------------------------------------
  Chat/Messaging          Supabase Realtime            PostgreSQL change subscriptions for message delivery

  Location Tracking       FastAPI WebSockets + Redis   Low-latency streaming for active sessions

  Presence/Availability   Supabase Presence            Online status, typing indicators

  Push Notifications      Expo Push + FCM              Unified iOS/Android delivery through Firebase
  -----------------------------------------------------------------------------------------------------------

**2.5 Payment Processing**

  ---------------------------------------------------------------------------------------------------------------------
  **Component**      **Technology**                       **Purpose**
  ------------------ ------------------------------------ -------------------------------------------------------------
  Payment Platform   Stripe Connect (Express)             Marketplace split payments, host onboarding, global support

  Payment Flow       PaymentIntents with manual capture   Authorization hold at booking, capture on completion

  Payouts            Stripe automatic payouts             Configurable schedule to host bank accounts

  Mobile SDK         \@stripe/stripe-react-native         PCI-compliant card collection, Apple Pay, Google Pay
  ---------------------------------------------------------------------------------------------------------------------

**2.6 Infrastructure & DevOps**

  -----------------------------------------------------------------------------------------------------------
  **Component**      **Technology**                             **Purpose**
  ------------------ ------------------------------------------ ---------------------------------------------
  API Hosting        Railway (MVP) to AWS ECS Fargate (scale)   Managed containers, auto-scaling

  Database Hosting   Supabase (managed PostgreSQL)              Automatic backups, connection pooling

  File Storage       Supabase Storage (S3-compatible)           Profile images, verification documents

  CDN                Cloudflare                                 Static assets, API caching, DDoS protection

  CI/CD              GitHub Actions + EAS Build                 Automated testing, mobile builds

  Monitoring         Sentry + Axiom                             Error tracking, distributed tracing, logs

  Secrets            Doppler                                    Environment variables across environments
  -----------------------------------------------------------------------------------------------------------

**3. Project Structure & Architecture**

**3.1 Monorepo Structure**

The project uses a monorepo with pnpm workspaces for frontend and separate Python package for backend:

> dance-partner/ ├── CLAUDE.md \# AI assistant context (CRITICAL) ├── CONTEXT.md \# Current state tracking ├── PRD.md \# This document in markdown ├── tasks/ │ ├── completed/ \# Completed task records │ ├── current.md \# Currently active task │ └── backlog.md \# Prioritized task queue ├── apps/ │ └── mobile/ \# React Native Expo app │ ├── app/ \# Expo Router pages │ ├── components/ \# Reusable UI components │ ├── hooks/ \# Custom React hooks │ ├── services/ \# API client, storage │ ├── stores/ \# Zustand state stores │ ├── types/ \# TypeScript definitions │ └── utils/ \# Helper functions ├── packages/ │ └── shared/ \# Shared types, constants ├── backend/ │ ├── alembic/ \# Database migrations │ ├── app/ │ │ ├── api/v1/ \# FastAPI route handlers │ │ ├── core/ \# Config, security, deps │ │ ├── models/ \# SQLAlchemy ORM models │ │ ├── schemas/ \# Pydantic schemas │ │ ├── services/ \# Business logic layer │ │ ├── repositories/ \# Data access layer │ │ └── workers/ \# Celery background tasks │ └── tests/ │ ├── unit/ \# Unit tests │ ├── integration/ \# Integration tests │ └── e2e/ \# End-to-end API tests ├── e2e/ \# Playwright browser tests └── docker-compose.yml \# Local development

**3.2 CLAUDE.md Specification**

The CLAUDE.md file is critical for AI-assisted development and must contain:

-   Project overview and current phase

-   All CLI commands for development, testing, deployment

-   Code style guidelines and patterns to follow

-   Architecture decisions and rationale

-   DO and DON\'T rules for code generation

-   Database schema overview

-   API endpoint summary

**3.3 CONTEXT.md Specification**

The CONTEXT.md file tracks current implementation state (updated after each task):

-   Current task ID and status

-   Recently completed tasks (last 5)

-   Known issues or blockers

-   Test coverage summary

-   Pending decisions or questions

-   Files modified in current session

**3.4 Modular Backend Architecture**

The backend follows clean architecture with clear separation of concerns:

> ┌────────────────────────────────────────────────────┐ │ API Layer │ │ (FastAPI Routes - HTTP handling only) │ └────────────────────────────────────────────────────┘ │ ▼ ┌────────────────────────────────────────────────────┐ │ Service Layer │ │ (Business Logic - orchestration, validation) │ └────────────────────────────────────────────────────┘ │ ▼ ┌────────────────────────────────────────────────────┐ │ Repository Layer │ │ (Data Access - database queries, external APIs) │ └────────────────────────────────────────────────────┘ │ ▼ ┌────────────────────────────────────────────────────┐ │ Model Layer │ │ (SQLAlchemy Models - schema, relationships) │ └────────────────────────────────────────────────────┘

**4. Database Schema Design**

**4.1 Core Entities Overview**

The database consists of the following primary tables:

  -----------------------------------------------------------------------------------------------------------------
  **Table**           **Purpose**             **Key Fields**
  ------------------- ----------------------- ---------------------------------------------------------------------
  users               Base user accounts      id, email, password_hash, user_type, first_name, last_name

  host_profiles       Extended host info      user_id, bio, hourly_rate_cents, location (PostGIS), rating_average

  dance_styles        Master list of styles   id, name, slug, category

  host_dance_styles   Host-style junction     host_profile_id, dance_style_id, skill_level (1-5)

  bookings            Session records         client_id, host_id, status, scheduled_start/end, amount, stripe_ids

  reviews             Post-session ratings    booking_id, reviewer_id, rating, comment

  conversations       Chat threads            participant_1_id, participant_2_id, last_message_at

  messages            Chat messages           conversation_id, sender_id, content, message_type

  host_availability   Schedule windows        host_profile_id, day_of_week, start_time, end_time
  -----------------------------------------------------------------------------------------------------------------

**4.2 Key Database Features**

-   PostGIS GEOGRAPHY(POINT) for host locations enabling radius-based search

-   Automatic rating_average calculation via database trigger

-   Soft delete pattern (is_active flag) for user accounts

-   TIMESTAMPTZ for all timestamps (timezone-aware)

-   Proper indexes for geospatial, booking status, and message queries

**5. API Specification**

**5.1 API Design Principles**

-   RESTful design with consistent resource naming

-   JSON error responses with error codes

-   Cursor-based pagination for infinite scroll

-   Rate limiting: 100 req/min authenticated, 20 anonymous

-   All timestamps in ISO 8601 UTC

-   Version prefix: /api/v1/

**5.2 Core Endpoints Summary**

  ---------------------------------------------------------------------------------------------------------------
  **Category**     **Key Endpoints**
  ---------------- ----------------------------------------------------------------------------------------------
  Authentication   POST /auth/register, /auth/login, /auth/refresh, /auth/logout, GET /auth/me

  Users            GET/PATCH /users/me, POST /users/me/become-host, GET/PATCH host-profile

  Host Discovery   GET /hosts (search/filter), /hosts/nearby, /hosts/{id}, /hosts/{id}/availability

  Bookings         POST /bookings, GET /bookings, POST /bookings/{id}/confirm\|decline\|cancel\|start\|complete

  Messaging        GET/POST /conversations, POST /conversations/{id}/messages, /conversations/{id}/read

  Payments         POST /payments/setup-intent, /hosts/stripe/onboard, GET /hosts/earnings

  Reviews          POST /bookings/{id}/review, GET /hosts/{id}/reviews
  ---------------------------------------------------------------------------------------------------------------

**5.3 WebSocket Endpoints**

  ------------------------------------------------------------------------------------
  **Endpoint**                            **Purpose**
  --------------------------------------- --------------------------------------------
  ws://api/v1/ws/chat/{conversation_id}   Real-time chat messages, typing indicators

  ws://api/v1/ws/notifications            Push notification stream

  ws://api/v1/ws/location/{booking_id}    Live location during active sessions
  ------------------------------------------------------------------------------------

**6. Implementation Tasks - Phase 1: Foundation**

Phase 1 establishes project infrastructure, authentication, and basic user management. All tasks follow TDD.

> **TASK 1.1: Initialize Monorepo Structure**

**Description:**

Create complete project directory structure with pnpm workspaces, TypeScript configs, and base configuration files.

**Acceptance Criteria:**

-   Directory structure matches Section 3.1 specification

-   pnpm workspace links apps/mobile and packages/shared

-   TypeScript strict mode enabled everywhere

-   ESLint and Prettier configurations consistent

-   CLAUDE.md and CONTEXT.md created with templates

**Test Requirements (TDD):**

-   Verify pnpm install completes without errors

-   Verify TypeScript compilation succeeds

-   Verify ESLint passes on template files

**Estimated Hours:** 2

> **TASK 1.2: Initialize Backend FastAPI Project**

**Description:**

Set up Python backend with FastAPI, UV for dependencies, and basic application bootstrap.

**Acceptance Criteria:**

-   pyproject.toml configured with UV, dependencies pinned

-   FastAPI app factory pattern in app/main.py

-   Health check at GET /health returns 200

-   OpenAPI docs at /docs and /redoc

-   CORS middleware configured for development

-   Logging configured with structlog JSON output

**Test Requirements (TDD):**

-   Unit test: Health endpoint returns correct schema

-   Unit test: Config loading from environment

-   Integration test: OpenAPI schema is valid

**Dependencies:** 1.1

**Estimated Hours:** 3

> **TASK 1.3: Configure Supabase Database Connection**

**Description:**

Set up Supabase project and SQLAlchemy 2.0 async connection with Alembic migrations.

**Acceptance Criteria:**

-   Supabase project with PostgreSQL database

-   SQLAlchemy async engine with asyncpg

-   Connection pooling (min=2, max=10 dev)

-   Alembic initialized with async support

-   Initial migration creates uuid-ossp and postgis extensions

**Test Requirements (TDD):**

-   Integration test: Can execute raw SQL query

-   Integration test: Alembic upgrade/downgrade works

-   Integration test: PostGIS functions available

**Dependencies:** 1.2

**Estimated Hours:** 3

> **TASK 1.4: Create User Database Model**

**Description:**

Implement User SQLAlchemy model with all required fields and migration.

**Acceptance Criteria:**

-   User model: id (UUID), email, password_hash, first_name, last_name, user_type, email_verified, is_active, timestamps

-   Email uniqueness at database level

-   Password hash never exposed in serialization

-   user_type ENUM (client, host, both)

**Test Requirements (TDD):**

-   Unit test: Model instantiation

-   Integration test: Migration creates table

-   Integration test: Unique constraint on email

**Dependencies:** 1.3

**Estimated Hours:** 2

> **TASK 1.5: Implement User Repository Layer**

**Description:**

Create UserRepository with async CRUD operations following repository pattern.

**Acceptance Criteria:**

-   create(), get_by_id(), get_by_email(), update(), soft_delete()

-   list() with pagination (limit/offset)

-   exists_by_email() for registration checks

-   All queries use async patterns

**Test Requirements (TDD):**

-   Unit test: Each method with mocked session

-   Integration test: Create and retrieve round-trip

-   Integration test: Soft delete preserves record

**Dependencies:** 1.4

**Estimated Hours:** 3

> **TASK 1.6: Implement Password Hashing Service**

**Description:**

Create secure Argon2id password hashing service.

**Acceptance Criteria:**

-   PasswordService using argon2-cffi

-   hash_password() with secure parameters

-   verify_password() with time-constant comparison

-   Minimum 8 character enforcement

**Test Requirements (TDD):**

-   Unit test: Hashing produces valid format

-   Unit test: Verification succeeds/fails correctly

-   Unit test: Different hashes for same password

**Dependencies:** 1.2

**Estimated Hours:** 2

> **TASK 1.7: Implement JWT Token Service**

**Description:**

Create JWT service for access/refresh tokens using RS256.

**Acceptance Criteria:**

-   Access tokens: 15-minute expiration

-   Refresh tokens: 7-day expiration, stored in DB

-   Payload: sub (user_id), exp, iat, jti

-   verify_token() validates signature and expiration

**Test Requirements (TDD):**

-   Unit test: Token creation and verification

-   Unit test: Expired token raises error

-   Integration test: Refresh token stored in database

**Dependencies:** 1.2

**Estimated Hours:** 3

> **TASK 1.8: Create Authentication Pydantic Schemas**

**Description:**

Define all request/response models for auth endpoints.

**Acceptance Criteria:**

-   RegisterRequest, LoginRequest, TokenResponse, RefreshRequest

-   ForgotPasswordRequest, ResetPasswordRequest, UserResponse

-   Email validation, password strength requirements

**Test Requirements (TDD):**

-   Unit test: Valid data passes validation

-   Unit test: Invalid email rejected

-   Unit test: Weak password rejected with requirements

**Dependencies:** 1.2

**Estimated Hours:** 2

> **TASK 1.9: Implement User Registration Endpoint**

**Description:**

Create POST /api/v1/auth/register with validation and email verification trigger.

**Acceptance Criteria:**

-   Validates email not registered (case-insensitive)

-   Hashes password, creates user

-   Queues email verification (Celery)

-   Returns 201 with UserResponse

-   Returns 409 if email exists

**Test Requirements (TDD):**

-   Unit test: Successful registration returns 201

-   Unit test: Duplicate email returns 409

-   Integration test: User created in database

**Dependencies:** 1.5, 1.6, 1.8

**Estimated Hours:** 3

> **TASK 1.10: Implement Login Endpoint**

**Description:**

Create POST /api/v1/auth/login returning JWT tokens.

**Acceptance Criteria:**

-   Verifies credentials (same error for email/password)

-   Returns 401 invalid, 403 deactivated

-   Returns TokenResponse with tokens

-   Updates last_login_at

**Test Requirements (TDD):**

-   Unit test: Valid credentials return tokens

-   Unit test: Invalid credentials return 401

-   Integration test: Refresh token stored

**Dependencies:** 1.5, 1.6, 1.7, 1.8

**Estimated Hours:** 3

> **TASK 1.11: Implement Token Refresh Endpoint**

**Description:**

Create POST /api/v1/auth/refresh for obtaining new access tokens.

**Acceptance Criteria:**

-   Validates refresh token signature/expiration

-   Checks token not revoked in database

-   Issues new access token

-   Returns 401 for invalid/expired/revoked

**Test Requirements (TDD):**

-   Unit test: Valid refresh returns new access

-   Unit test: Revoked token returns 401

-   Integration test: Token rotation works

**Dependencies:** 1.7, 1.8

**Estimated Hours:** 2

> **TASK 1.12: Implement Authentication Middleware**

**Description:**

Create FastAPI dependency for JWT auth extracting current user.

**Acceptance Criteria:**

-   get_current_user extracts Bearer token

-   Validates and loads user from DB

-   get_current_host_user requires host user_type

-   Token validation cached in Redis

**Test Requirements (TDD):**

-   Unit test: Valid token returns user

-   Unit test: Missing/invalid token returns 401

-   Integration test: Cache avoids DB query

**Dependencies:** 1.5, 1.7

**Estimated Hours:** 3

> **TASK 1.13: Implement Logout Endpoint**

**Description:**

Create POST /api/v1/auth/logout revoking refresh token.

**Acceptance Criteria:**

-   Revokes specific token or all user tokens

-   Returns 204 No Content

-   Idempotent operation

**Test Requirements (TDD):**

-   Unit test: Logout revokes token

-   Integration test: Revoked token cannot be used

**Dependencies:** 1.7, 1.12

**Estimated Hours:** 2

> **TASK 1.14: Implement Get Current User Endpoint**

**Description:**

Create GET /api/v1/auth/me returning authenticated user profile.

**Acceptance Criteria:**

-   Returns UserResponse with full profile

-   Response cached in Redis 1 minute

**Test Requirements (TDD):**

-   Unit test: Returns user data

-   Integration test: Cache populated

**Dependencies:** 1.8, 1.12

**Estimated Hours:** 1

> **TASK 1.15: Initialize React Native Expo Project**

**Description:**

Set up mobile app with Expo, TypeScript, and essential configs.

**Acceptance Criteria:**

-   Expo with TypeScript template

-   Expo Router file-based routing

-   Path aliases configured

-   EAS Build initialized

**Test Requirements (TDD):**

-   Verify expo start launches

-   Verify app renders on iOS/Android simulators

**Dependencies:** 1.1

**Estimated Hours:** 2

> **TASK 1.16: Set Up Mobile State Management**

**Description:**

Configure Zustand for global state and React Query for server state.

**Acceptance Criteria:**

-   Auth store (user, tokens, isAuthenticated)

-   Persisted to expo-secure-store

-   React Query with offline support

-   Custom useAuth hook

**Test Requirements (TDD):**

-   Unit test: Store state and actions

-   Unit test: Persistence saves/restores

**Dependencies:** 1.15

**Estimated Hours:** 3

> **TASK 1.17: Create API Client Service**

**Description:**

Build typed API client for backend communication.

**Acceptance Criteria:**

-   Axios with base URL from environment

-   Request interceptor adds auth header

-   Response interceptor handles 401 refresh

-   TypeScript types from OpenAPI spec

**Test Requirements (TDD):**

-   Unit test: Auth header included

-   Unit test: 401 triggers refresh

-   Unit test: Failed refresh triggers logout

**Dependencies:** 1.16

**Estimated Hours:** 3

> **TASK 1.18: Implement Login Screen**

**Description:**

Create login UI with form validation and API integration.

**Acceptance Criteria:**

-   Email/password inputs with validation

-   Loading state, error messages

-   Links to register and forgot password

-   Successful login navigates to home

**Test Requirements (TDD):**

-   Unit test: Form validation

-   Unit test: Error display

-   E2E test: Complete login flow

**Dependencies:** 1.10, 1.17

**Estimated Hours:** 4

> **TASK 1.19: Implement Registration Screen**

**Description:**

Create registration UI with comprehensive validation.

**Acceptance Criteria:**

-   Fields: email, password, confirm, names, user type

-   Password strength indicator

-   Terms checkbox required

-   Shows verification email sent message

**Test Requirements (TDD):**

-   Unit test: All validations

-   E2E test: Complete registration flow

**Dependencies:** 1.9, 1.17

**Estimated Hours:** 4

> **TASK 1.20: Implement Protected Route Navigation**

**Description:**

Set up navigation guards redirecting unauthenticated users.

**Acceptance Criteria:**

-   Auth layout for login/register

-   Protected layout for authenticated screens

-   Splash screen during auth check

-   Logout navigates to login

**Test Requirements (TDD):**

-   Unit test: Redirect logic

-   E2E test: Auth flow redirect

**Dependencies:** 1.16, 1.18

**Estimated Hours:** 3

**7. Implementation Tasks - Phase 2: Host Profiles**

Phase 2 implements host profile management, dance styles, and host discovery.

> **TASK 2.1: Create Dance Styles Model and Seed Data**

**Description:**

Implement DanceStyle model and seed initial styles.

**Acceptance Criteria:**

-   DanceStyle: id, name, slug, category, description

-   Seed 20+ styles (Salsa, Bachata, Tango, Waltz, etc.)

-   Categories: Latin, Ballroom, Swing, Social, Other

**Test Requirements (TDD):**

-   Integration test: Migration creates table

-   Integration test: Seed populates data

**Dependencies:** 1.3

**Estimated Hours:** 2

> **TASK 2.2: Create Host Profile Model**

**Description:**

Implement HostProfile with PostGIS location.

**Acceptance Criteria:**

-   One-to-one with User

-   PostGIS GEOGRAPHY(POINT) for location

-   hourly_rate_cents, rating_average, verification_status

-   Geospatial index on location

**Test Requirements (TDD):**

-   Integration test: Can insert/query location

-   Integration test: Geospatial index created

**Dependencies:** 1.4, 2.1

**Estimated Hours:** 3

> **TASK 2.3: Create Host Dance Styles Junction**

**Description:**

Implement many-to-many with skill levels.

**Acceptance Criteria:**

-   host_profile_id, dance_style_id, skill_level (1-5)

-   Unique constraint prevents duplicates

-   Cascade delete

**Test Requirements (TDD):**

-   Integration test: Unique constraint works

-   Integration test: Cascade delete works

**Dependencies:** 2.2

**Estimated Hours:** 2

> **TASK 2.4: Implement Host Profile Repository**

**Description:**

Create repository with CRUD and geospatial queries.

**Acceptance Criteria:**

-   create(), get_by_user_id(), update()

-   add_dance_style(), remove_dance_style()

-   get_nearby() using PostGIS ST_DWithin

-   search() with filters: styles, rating, price

**Test Requirements (TDD):**

-   Integration test: Nearby query correct

-   Integration test: Search filters work

**Dependencies:** 2.2, 2.3

**Estimated Hours:** 4

> **TASK 2.5: Create Host Profile Schemas**

**Description:**

Define Pydantic schemas for host operations.

**Acceptance Criteria:**

-   CreateHostProfileRequest, UpdateHostProfileRequest, HostProfileResponse

-   HostSearchRequest with location, filters, pagination

-   Coordinate validation (lat/lng ranges)

**Test Requirements (TDD):**

-   Unit test: Valid schemas pass

-   Unit test: Invalid coordinates rejected

**Dependencies:** 2.2

**Estimated Hours:** 2

> **TASK 2.6: Implement Become Host Endpoint**

**Description:**

Create POST /api/v1/users/me/become-host.

**Acceptance Criteria:**

-   Creates HostProfile linked to user

-   Updates user.user_type to include host

-   Returns 409 if already host

**Test Requirements (TDD):**

-   Integration test: Host profile created

-   Integration test: User type updated

**Dependencies:** 2.4, 2.5, 1.12

**Estimated Hours:** 3

> **TASK 2.7: Implement Host Profile CRUD Endpoints**

**Description:**

Create endpoints for host profile management.

**Acceptance Criteria:**

-   GET/PATCH /users/me/host-profile

-   POST/DELETE dance-styles

-   PATCH location

-   All require host authentication

**Test Requirements (TDD):**

-   Unit test: Each endpoint

-   Integration test: Profile persisted

**Dependencies:** 2.4, 2.5, 1.12

**Estimated Hours:** 3

> **TASK 2.8: Implement Host Search Endpoint**

**Description:**

Create GET /api/v1/hosts with filtering and geospatial search.

**Acceptance Criteria:**

-   Query params: lat, lng, radius_km, styles\[\], min_rating, max_price

-   Paginated response with total count

-   Orders by distance or rating

-   Performance: \<100ms for 10K hosts

**Test Requirements (TDD):**

-   Integration test: Geospatial filtering

-   Performance test: Query time

**Dependencies:** 2.4, 2.5

**Estimated Hours:** 4

> **TASK 2.9: Implement Get Host Profile Endpoint**

**Description:**

Create GET /api/v1/hosts/{id} for public profile view.

**Acceptance Criteria:**

-   Full profile with dance styles, rating

-   Excludes sensitive data

-   Cached in Redis 5 minutes

**Test Requirements (TDD):**

-   Unit test: Excludes sensitive fields

-   Integration test: Cache used

**Dependencies:** 2.4, 2.5

**Estimated Hours:** 2

> **TASK 2.10: Implement Host Profile Screen (Mobile)**

**Description:**

Create host profile view for clients.

**Acceptance Criteria:**

-   Photo, name, headline, rating stars

-   Dance styles with skill badges

-   Hourly rate, bio, reviews

-   Message and Book buttons

**Test Requirements (TDD):**

-   Unit test: Renders all sections

-   E2E test: View host profile

**Dependencies:** 2.9, 1.17

**Estimated Hours:** 4

> **TASK 2.11: Implement Host Discovery Screen (Mobile)**

**Description:**

Create main discovery with search, filters, map.

**Acceptance Criteria:**

-   Toggle list/map view

-   Search bar, filter modal

-   Location-based results from GPS

-   Infinite scroll, pull-to-refresh

**Test Requirements (TDD):**

-   E2E test: Search and filter flow

-   E2E test: Map interaction

**Dependencies:** 2.8, 2.10

**Estimated Hours:** 6

> **TASK 2.12: Implement Host Profile Edit Screen (Mobile)**

**Description:**

Create profile management for hosts.

**Acceptance Criteria:**

-   Edit bio, headline, rate

-   Manage dance styles with skill levels

-   Update location with map picker

-   Photo upload with crop

**Test Requirements (TDD):**

-   E2E test: Complete profile edit

**Dependencies:** 2.7, 1.17

**Estimated Hours:** 5

**8. Implementation Tasks - Phase 3: Booking System**

Phase 3 implements booking workflow, availability, payment authorization, and session management.

> **TASK 3.1: Create Booking Model**

**Description:**

Implement Booking with all fields and relationships.

**Acceptance Criteria:**

-   FKs to User (client, host), HostProfile, DanceStyle

-   Status enum: pending, confirmed, in_progress, completed, cancelled, disputed

-   Amounts in cents, PostGIS location

**Test Requirements (TDD):**

-   Integration test: Migration creates table

-   Integration test: FK constraints work

**Dependencies:** 2.2

**Estimated Hours:** 3

> **TASK 3.2: Create Host Availability Model**

**Description:**

Implement availability schedule storage.

**Acceptance Criteria:**

-   Recurring weekly schedules

-   One-time overrides

-   Blocked time periods

**Test Requirements (TDD):**

-   Integration test: Time range queries

**Dependencies:** 2.2

**Estimated Hours:** 2

> **TASK 3.3: Implement Availability Repository**

**Description:**

Create schedule management methods.

**Acceptance Criteria:**

-   set_recurring_availability(), add_one_time()

-   block_time_slot(), get_availability_for_date()

-   is_available_for_slot() (accounts for bookings)

**Test Requirements (TDD):**

-   Integration test: Weekly schedule

-   Integration test: Booked times excluded

**Dependencies:** 3.2

**Estimated Hours:** 3

> **TASK 3.4: Implement Booking Repository**

**Description:**

Create booking CRUD and query methods.

**Acceptance Criteria:**

-   create(), get_by_id(), get_for_client(), get_for_host()

-   update_status(), get_overlapping()

-   get_upcoming()

**Test Requirements (TDD):**

-   Integration test: Status update

-   Integration test: Overlap detection

**Dependencies:** 3.1

**Estimated Hours:** 3

> **TASK 3.5: Create Booking Schemas**

**Description:**

Define request/response schemas.

**Acceptance Criteria:**

-   CreateBookingRequest, BookingResponse, BookingListResponse

-   AvailabilitySlot, HostAvailabilityResponse

-   Duration validation (30-240 minutes)

**Test Requirements (TDD):**

-   Unit test: Valid booking passes

-   Unit test: Past dates rejected

**Dependencies:** 3.1

**Estimated Hours:** 2

> **TASK 3.6: Integrate Stripe Connect**

**Description:**

Implement Stripe Connect Express for host onboarding.

**Acceptance Criteria:**

-   StripeService: create_connect_account(), create_account_link()

-   get_account_status(), handle_webhook()

-   Endpoints: POST/GET stripe/onboard, stripe/status

**Test Requirements (TDD):**

-   Integration test: Full onboarding flow (test mode)

**Dependencies:** 2.4

**Estimated Hours:** 4

> **TASK 3.7: Implement Booking Creation with Payment Hold**

**Description:**

Create POST /api/v1/bookings with Stripe authorization.

**Acceptance Criteria:**

-   Validates host available, time slot free

-   Calculates total, platform fee

-   Creates PaymentIntent with manual capture

-   Creates pending booking

**Test Requirements (TDD):**

-   Integration test: PaymentIntent created

-   Integration test: Concurrent booking prevention

**Dependencies:** 3.3, 3.4, 3.5, 3.6

**Estimated Hours:** 5

> **TASK 3.8: Implement Booking Confirmation**

**Description:**

Create POST /api/v1/bookings/{id}/confirm for host acceptance.

**Acceptance Criteria:**

-   Validates pending status

-   Updates to confirmed

-   Sends notifications to client

**Test Requirements (TDD):**

-   Integration test: Status persisted

-   Integration test: Notifications sent

**Dependencies:** 3.4, 3.5

**Estimated Hours:** 2

> **TASK 3.9: Implement Booking Cancellation**

**Description:**

Create POST /api/v1/bookings/{id}/cancel with refund.

**Acceptance Criteria:**

-   Client or host can cancel

-   Cancellation fee logic (within 24h)

-   Releases Stripe authorization

-   Notifications to other party

**Test Requirements (TDD):**

-   Integration test: PaymentIntent cancelled

**Dependencies:** 3.4, 3.6

**Estimated Hours:** 3

> **TASK 3.10: Implement Session Start**

**Description:**

Create POST /api/v1/bookings/{id}/start.

**Acceptance Criteria:**

-   Validates confirmed status, within 30min of start

-   Records actual_start, updates to in_progress

-   Initiates location tracking

**Test Requirements (TDD):**

-   Integration test: Status and timestamp persisted

**Dependencies:** 3.4

**Estimated Hours:** 2

> **TASK 3.11: Implement Session Completion with Capture**

**Description:**

Create POST /api/v1/bookings/{id}/complete with payment.

**Acceptance Criteria:**

-   Validates in_progress status

-   Captures PaymentIntent, creates Transfer to host

-   Updates to completed

-   Sends receipt, prompts review

**Test Requirements (TDD):**

-   Integration test: PaymentIntent captured

-   Integration test: Transfer created

**Dependencies:** 3.4, 3.6

**Estimated Hours:** 4

> **TASK 3.12: Implement Booking List Endpoint**

**Description:**

Create GET /api/v1/bookings with filters.

**Acceptance Criteria:**

-   Returns user\'s bookings (as client or host)

-   Filter by status, date range

-   Cursor-based pagination

**Test Requirements (TDD):**

-   Integration test: Filters work

**Dependencies:** 3.4, 3.5

**Estimated Hours:** 2

> **TASK 3.13: Implement Availability Endpoints**

**Description:**

Create host availability management endpoints.

**Acceptance Criteria:**

-   GET/PUT /host-profile/availability

-   POST/DELETE availability/override

-   GET /hosts/{id}/availability (public)

**Test Requirements (TDD):**

-   Integration test: Schedule persisted

-   Integration test: Bookings excluded

**Dependencies:** 3.3

**Estimated Hours:** 3

> **TASK 3.14: Implement Booking Flow Screen (Mobile)**

**Description:**

Create complete booking flow for clients.

**Acceptance Criteria:**

-   Calendar with available dates

-   Time slot selection, duration picker

-   Dance style selector, location input

-   Price breakdown, Stripe payment sheet

**Test Requirements (TDD):**

-   E2E test: Complete booking flow

**Dependencies:** 3.7, 3.13, 1.17

**Estimated Hours:** 6

> **TASK 3.15: Implement Bookings List Screen (Mobile)**

**Description:**

Create booking management screens.

**Acceptance Criteria:**

-   Tabs: Upcoming, Past, Cancelled

-   Booking cards with status

-   Pull-to-refresh, tap to detail

**Test Requirements (TDD):**

-   E2E test: Navigate booking list

**Dependencies:** 3.12, 1.17

**Estimated Hours:** 4

> **TASK 3.16: Implement Booking Detail Screen (Mobile)**

**Description:**

Create detailed view with actions.

**Acceptance Criteria:**

-   Full details, map showing location

-   Role-based actions (Confirm/Decline/Cancel/Complete)

-   Message button, Add to Calendar

**Test Requirements (TDD):**

-   E2E test: Confirm booking flow

-   E2E test: Cancel booking flow

**Dependencies:** 3.8, 3.9, 3.11, 3.15

**Estimated Hours:** 5

> **TASK 3.17: Implement Availability Management Screen (Mobile)**

**Description:**

Create host availability editor.

**Acceptance Criteria:**

-   Weekly schedule with time pickers

-   One-time overrides section

-   Blocked dates calendar

**Test Requirements (TDD):**

-   E2E test: Set availability

**Dependencies:** 3.13, 1.17

**Estimated Hours:** 5

**9. Implementation Tasks - Phase 4: Real-Time Features**

Phase 4 implements messaging, push notifications, and live location tracking.

> **TASK 4.1: Create Message and Conversation Models**

**Description:**

Implement messaging database models.

**Acceptance Criteria:**

-   Conversation: participant_1_id, participant_2_id, last_message_at

-   Message: conversation_id, sender_id, content, type, read_at

-   Unique constraint on participant pair

**Test Requirements (TDD):**

-   Integration test: Unique constraint works

**Dependencies:** 1.4

**Estimated Hours:** 2

> **TASK 4.2: Implement Messaging Repository**

**Description:**

Create conversation and message operations.

**Acceptance Criteria:**

-   get_or_create_conversation()

-   get_conversations_for_user(), get_messages() with cursor

-   create_message(), mark_as_read(), get_unread_count()

**Test Requirements (TDD):**

-   Integration test: Conversation creation

-   Integration test: Message ordering

**Dependencies:** 4.1

**Estimated Hours:** 3

> **TASK 4.3: Configure Supabase Realtime**

**Description:**

Set up realtime subscriptions for messages.

**Acceptance Criteria:**

-   Enable Realtime on messages table

-   Row-level security for message access

-   Verify subscription receives INSERTs

**Test Requirements (TDD):**

-   Integration test: Message triggers subscription

**Dependencies:** 4.1

**Estimated Hours:** 2

> **TASK 4.4: Create Messaging Schemas**

**Description:**

Define schemas for messaging endpoints.

**Acceptance Criteria:**

-   ConversationResponse, MessageResponse

-   CreateMessageRequest, StartConversationRequest

**Test Requirements (TDD):**

-   Unit test: Schema validation

**Dependencies:** 4.1

**Estimated Hours:** 1

> **TASK 4.5: Implement Messaging Endpoints**

**Description:**

Create HTTP endpoints for messaging.

**Acceptance Criteria:**

-   GET/POST /conversations

-   GET /conversations/{id}, POST messages

-   POST /conversations/{id}/read

**Test Requirements (TDD):**

-   Integration test: Full conversation flow

**Dependencies:** 4.2, 4.4

**Estimated Hours:** 3

> **TASK 4.6: Implement Chat Screen (Mobile)**

**Description:**

Create real-time chat interface.

**Acceptance Criteria:**

-   Message list with infinite scroll

-   Real-time via Supabase subscription

-   Text input, typing indicator, read receipts

**Test Requirements (TDD):**

-   E2E test: Send and receive message

**Dependencies:** 4.3, 4.5, 1.17

**Estimated Hours:** 5

> **TASK 4.7: Implement Conversations List Screen (Mobile)**

**Description:**

Create inbox showing all conversations.

**Acceptance Criteria:**

-   Sorted by last message time

-   Other participant, preview, unread badge

-   Real-time updates

**Test Requirements (TDD):**

-   E2E test: Navigate to conversation

**Dependencies:** 4.5, 4.6

**Estimated Hours:** 4

> **TASK 4.8: Configure Push Notifications**

**Description:**

Set up Expo Push + FCM infrastructure.

**Acceptance Criteria:**

-   Push token registration on launch

-   Store tokens in users table

-   Backend service for sending

-   Handle notification tap navigation

**Test Requirements (TDD):**

-   Integration test: Push received

**Dependencies:** 1.4, 1.15

**Estimated Hours:** 4

> **TASK 4.9: Implement Push Notification Triggers**

**Description:**

Add notifications to relevant events.

**Acceptance Criteria:**

-   New message, booking requested/confirmed/cancelled

-   Session reminder (30 min before)

-   Review request (24h after completion)

**Test Requirements (TDD):**

-   Integration test: Notifications sent

**Dependencies:** 4.8

**Estimated Hours:** 3

> **TASK 4.10: Implement WebSocket Location Backend**

**Description:**

Create FastAPI WebSocket for live location.

**Acceptance Criteria:**

-   Endpoint /ws/location/{booking_id}

-   Authenticates, validates participant

-   Broadcasts via Redis Pub/Sub

**Test Requirements (TDD):**

-   Integration test: Location broadcast

**Dependencies:** 3.1

**Estimated Hours:** 4

> **TASK 4.11: Implement Location Tracking (Mobile)**

**Description:**

Create background location tracking.

**Acceptance Criteria:**

-   expo-location with proper permissions

-   Sends to WebSocket every 10 seconds

-   Arrival detection within 100m

**Test Requirements (TDD):**

-   E2E test: Location sharing

**Dependencies:** 4.10, 1.15

**Estimated Hours:** 5

> **TASK 4.12: Implement Active Session Screen (Mobile)**

**Description:**

Create in-progress session screen.

**Acceptance Criteria:**

-   Map with participant locations

-   Session timer, contact button

-   Complete session button (host)

**Test Requirements (TDD):**

-   E2E test: Active session flow

**Dependencies:** 4.11, 3.16

**Estimated Hours:** 5

**10. Implementation Tasks - Phase 5: Reviews & Polish**

Phase 5 implements reviews, verification, and final polish for MVP launch.

> **TASK 5.1: Create Review Model**

**Description:**

Implement Review for post-session ratings.

**Acceptance Criteria:**

-   booking_id (unique), reviewer_id, reviewee_id

-   rating (1-5), comment, host_response

-   Trigger updates host rating_average

**Test Requirements (TDD):**

-   Integration test: Rating average calculated

**Dependencies:** 3.1

**Estimated Hours:** 2

> **TASK 5.2: Implement Review Repository**

**Description:**

Create review operations.

**Acceptance Criteria:**

-   create(), get_for_booking(), get_for_user()

-   add_response(), calculate_rating_average()

**Test Requirements (TDD):**

-   Integration test: Review persisted

**Dependencies:** 5.1

**Estimated Hours:** 2

> **TASK 5.3: Implement Review Endpoints**

**Description:**

Create HTTP endpoints for reviews.

**Acceptance Criteria:**

-   POST /bookings/{id}/review

-   GET /hosts/{id}/reviews

-   POST /reviews/{id}/response

**Test Requirements (TDD):**

-   Integration test: Rating updates profile

**Dependencies:** 5.2

**Estimated Hours:** 3

> **TASK 5.4: Implement Review Screen (Mobile)**

**Description:**

Create post-session review interface.

**Acceptance Criteria:**

-   Star rating selector (1-5)

-   Written review textarea

-   Submit with confirmation

**Test Requirements (TDD):**

-   E2E test: Submit review flow

**Dependencies:** 5.3

**Estimated Hours:** 3

> **TASK 5.5: Implement Reviews Display (Mobile)**

**Description:**

Create reusable review list component.

**Acceptance Criteria:**

-   Reviewer name/avatar, stars, text

-   Host response section

-   Pagination

**Test Requirements (TDD):**

-   Unit test: Renders reviews

**Dependencies:** 5.3, 2.10

**Estimated Hours:** 2

> **TASK 5.6: Implement Host Verification (Backend)**

**Description:**

Create verification workflow.

**Acceptance Criteria:**

-   HostVerificationDocument model

-   Upload endpoint for documents

-   Admin approve/reject endpoints

-   Email notifications on status change

**Test Requirements (TDD):**

-   Integration test: Full verification flow

**Dependencies:** 2.4

**Estimated Hours:** 4

> **TASK 5.7: Implement Host Onboarding Flow (Mobile)**

**Description:**

Create guided multi-step onboarding.

**Acceptance Criteria:**

-   Steps: Profile, Dance styles, Rate, Availability, Stripe, Verification

-   Progress indicator, save and resume

**Test Requirements (TDD):**

-   E2E test: Complete onboarding

**Dependencies:** 2.6, 2.12, 3.6, 3.17, 5.6

**Estimated Hours:** 6

> **TASK 5.8: Implement Settings Screen (Mobile)**

**Description:**

Create user settings and preferences.

**Acceptance Criteria:**

-   Account, notifications, payment, privacy sections

-   Support, legal links

-   Logout, delete account

**Test Requirements (TDD):**

-   E2E test: Change settings

**Dependencies:** 1.18

**Estimated Hours:** 4

> **TASK 5.9: Implement Error Handling and Offline**

**Description:**

Add comprehensive error handling.

**Acceptance Criteria:**

-   Global error boundary

-   Retry logic, offline indicator

-   Queue actions while offline

-   Sentry integration

**Test Requirements (TDD):**

-   Integration test: Sync on reconnect

**Dependencies:** 1.17

**Estimated Hours:** 4

> **TASK 5.10: Implement Analytics and Logging**

**Description:**

Add tracking and structured logging.

**Acceptance Criteria:**

-   Backend: JSON logging, request metrics

-   Mobile: Screen views, user actions, Sentry

-   Privacy-compliant

**Test Requirements (TDD):**

-   Integration test: Logs contain required fields

**Dependencies:** 1.2, 1.15

**Estimated Hours:** 3

> **TASK 5.11: Implement E2E Test Suite**

**Description:**

Create comprehensive Playwright tests.

**Acceptance Criteria:**

-   Registration, login, host profile

-   Booking flow with payment

-   Messaging, session completion, reviews

-   CI/CD integration

**Test Requirements (TDD):**

-   All E2E tests pass

-   Tests run in CI on every PR

**Dependencies:** All previous

**Estimated Hours:** 8

> **TASK 5.12: Performance Optimization**

**Description:**

Optimize and verify scalability.

**Acceptance Criteria:**

-   Database query optimization

-   API p95 \<200ms, app cold start \<3s

-   Redis caching, image optimization

-   Load test: 1000 concurrent users

**Test Requirements (TDD):**

-   Performance test: Response times

-   Load test: Concurrent handling

**Dependencies:** All previous

**Estimated Hours:** 5

> **TASK 5.13: App Store Preparation**

**Description:**

Prepare for iOS and Android submission.

**Acceptance Criteria:**

-   Icons, splash screen, screenshots

-   App descriptions, keywords

-   Privacy policy, terms of service

-   EAS Build production config

**Test Requirements (TDD):**

-   Production build succeeds

-   TestFlight upload successful

**Dependencies:** All previous

**Estimated Hours:** 4

**11. Testing Strategy**

**11.1 TDD Workflow**

Every task follows strict TDD:

1.  Write failing tests defining expected behavior

2.  Implement minimum code to pass

3.  Refactor while keeping tests green

4.  Commit test and implementation together

**11.2 Testing Stack**

  -----------------------------------------------------------------------------------
  **Layer**                  **Tools**
  -------------------------- --------------------------------------------------------
  Backend Unit/Integration   pytest, pytest-asyncio, pytest-cov, httpx, factory_boy

  Frontend Unit              Jest, React Native Testing Library, MSW

  E2E                        Playwright
  -----------------------------------------------------------------------------------

**11.3 Coverage Requirements**

-   Backend: Minimum 80% line coverage

-   Frontend: Minimum 70% line coverage

-   Critical paths (auth, payments): 100% coverage

**12. Context Tracking Protocol**

**12.1 CONTEXT.md Template**

> \# Dance Partner - Current Context \## Active Task - \*\*ID\*\*: \[Task ID\] - \*\*Title\*\*: \[Title\] - \*\*Status\*\*: \[in_progress \| blocked \| completed\] \## Recently Completed (Last 5) 1. \[ID\] - \[Title\] - \[Timestamp\] \## Test Status - Unit: X passing, Y failing - Integration: X passing, Y failing - Coverage: Backend X%, Frontend Y% \## Files Modified This Session - \[file paths\] \## Next Task - \*\*ID\*\*: \[Next ID\] - \*\*Dependencies\*\*: \[Required completed tasks\]

**12.2 Task Completion Checklist**

-   All acceptance criteria met

-   All tests written and passing

-   Code follows style guidelines

-   No type/lint errors

-   CONTEXT.md updated

-   Changes committed

**13. Appendix**

**13.1 Environment Variables**

  -----------------------------------------------------------------------
  **Variable**               **Description**
  -------------------------- --------------------------------------------
  DATABASE_URL               PostgreSQL connection string

  REDIS_URL                  Redis connection string

  JWT_SECRET_KEY             RSA private key for JWT

  STRIPE_SECRET_KEY          Stripe API secret

  STRIPE_WEBHOOK_SECRET      Stripe webhook signing

  SUPABASE_URL               Supabase project URL

  SUPABASE_ANON_KEY          Supabase anonymous key

  EXPO_PUBLIC_API_URL        Backend API URL for mobile

  SENTRY_DSN                 Sentry error tracking DSN
  -----------------------------------------------------------------------

**13.2 Error Response Format**

> { \"error\": { \"code\": \"BOOKING_CONFLICT\", \"message\": \"The requested time slot is no longer available\", \"details\": { \"field\": \"scheduled_start\" } } }

**13.3 Standard Error Codes**

  -------------------------------------------------------------------------
  **Code**              **HTTP**   **Description**
  --------------------- ---------- ----------------------------------------
  VALIDATION_ERROR      422        Request validation failed

  UNAUTHORIZED          401        Authentication required

  FORBIDDEN             403        Insufficient permissions

  NOT_FOUND             404        Resource not found

  CONFLICT              409        Resource conflict

  BOOKING_CONFLICT      409        Time slot unavailable

  PAYMENT_FAILED        402        Payment processing failed

  RATE_LIMITED          429        Too many requests
  -------------------------------------------------------------------------

*--- End of Document ---*
