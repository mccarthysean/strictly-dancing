# Optimal tech stack for Dance Partner: a global marketplace mobile app

**React Native with Expo, FastAPI, Supabase, and Stripe Connect form the ideal foundation** for building an Uber-style dance marketplace. This stack maximizes your existing Python/React expertise while delivering cross-platform deployment, real-time capabilities, and scalable payment processing from day one. The critical insight: avoid over-engineering with microservices or Kubernetes—a modular monolith on managed platforms will scale to hundreds of thousands of users while keeping complexity manageable for AI-assisted development.

## PWAs cannot reach the App Store—React Native with Expo is the clear winner

Apple explicitly prohibits PWAs (Progressive Web Apps) in the App Store. Their Review Guidelines state that apps which are "repackaged websites" don't belong on the platform. While Google Play does accept PWAs via Trusted Web Activities, the iOS limitation alone disqualifies this approach for a marketplace requiring both platforms. Beyond store policies, PWAs lack critical features you need: **background location tracking** (impossible on iOS), reliable push notifications (requires manual "Add to Home Screen" on iOS), and native payment integrations.

**React Native with Expo** is the recommended framework for several reasons. Your existing React/TypeScript knowledge transfers directly—no new language to learn. Expo's managed workflow handles the painful parts of mobile development: code signing, app store submission, and native module configuration. The platform now supports all features Dance Partner requires:

- `expo-location` provides full background location tracking with proper iOS/Android permissions
- Expo Push Service offers unified push notifications across platforms at no additional cost
- Official Stripe SDK (`@stripe/stripe-react-native`) integrates seamlessly
- EAS Build compiles native binaries in the cloud; EAS Update enables over-the-air patches without App Store review

Flutter is a strong alternative with better built-in web support, but requires learning Dart. Given your React background and Claude Code's excellent JavaScript/TypeScript support, React Native provides the faster path to production.

| Approach | App Store | Background Location | Push Notifications | AI Development Support |
|----------|-----------|---------------------|-------------------|----------------------|
| PWA | ❌ iOS blocked | ❌ Impossible | ⚠️ Limited | ✅ Familiar |
| React Native/Expo | ✅ Both stores | ✅ Full support | ✅ Excellent | ✅ Excellent |
| Flutter | ✅ Both stores | ✅ Full support | ✅ Good | ⚠️ Dart learning curve |

## FastAPI plus Supabase delivers your entire backend stack

**Stick with FastAPI**—it's the right choice. The framework handles 45,000+ concurrent WebSocket connections per server, integrates naturally with your PostgreSQL expertise, and generates OpenAPI documentation automatically. Claude Code works exceptionally well with typed Python, making AI-assisted development highly productive. The async/await support matches modern real-time requirements without switching to Node.js or Go.

**Supabase becomes your force multiplier**, providing PostgreSQL database, real-time subscriptions, authentication, and file storage in one managed platform. The critical advantage: Supabase Realtime provides native database change subscriptions, eliminating the need to build a separate real-time infrastructure:

```javascript
// Chat messages arrive automatically when inserted into PostgreSQL
supabase.channel('room:123')
  .on('postgres_changes', 
      { event: 'INSERT', table: 'messages' },
      (payload) => handleNewMessage(payload)
  )
  .subscribe()
```

For **high-frequency location tracking**, bypass Supabase Realtime and use FastAPI's native WebSocket support with Redis Pub/Sub. Location updates every few seconds need minimal latency, and this direct path avoids database overhead:

```
Host GPS → FastAPI WebSocket → Redis Pub/Sub → Client WebSocket
                ↓
        PostGIS (for "hosts within 5km" queries)
```

**Redis serves multiple purposes**: caching (user profiles, search results), pub/sub for WebSocket coordination across server instances, geospatial queries via `GEOADD`/`GEORADIUS`, and simple job queues via Redis Streams with Celery. This consolidation reduces operational complexity compared to running separate cache, queue, and real-time systems.

The complete data layer stack:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Primary Database | Supabase PostgreSQL + PostGIS | Persistent data, geospatial queries |
| Real-time (chat/presence) | Supabase Realtime | Database change subscriptions |
| Real-time (location) | FastAPI WebSockets + Redis | Low-latency streaming |
| Cache/Sessions | Redis | Performance, authentication state |
| Background Jobs | Celery + Redis | Email, reports, async processing |

## Stripe Connect handles marketplace payments elegantly

**Stripe Connect with Express accounts** is the definitive choice for Uber-style split payments. Express accounts let Stripe handle all KYC verification, identity checks, and compliance while giving you control over payout schedules—essential for escrow-like functionality.

The payment flow for Dance Partner works as follows:

1. **Client books session**: Create a PaymentIntent with `capture_method: 'manual'`—funds are authorized (held) on the card but not charged
2. **Session completes**: Capture the payment, triggering the actual charge
3. **Automatic split**: Platform fee is deducted; remainder transfers to host's connected account
4. **Payout**: Funds reach host's bank account per your configured schedule (daily/weekly)

```javascript
// Authorization at booking (escrow-like hold)
const paymentIntent = await stripe.paymentIntents.create({
  amount: 10000, // $100.00
  currency: 'usd',
  capture_method: 'manual',
  transfer_data: { destination: 'acct_host123' },
  application_fee_amount: 1500, // Platform keeps $15 (15%)
});

// Capture after session completion
await stripe.paymentIntents.capture('pi_xxx');
```

Authorization windows last **7 days** by default—sufficient for typical dance session bookings. For longer advance bookings, save the card and authorize closer to the session date.

Stripe Connect supports **47+ countries and 135 currencies**, enabling global expansion without switching providers. Host onboarding takes 2-5 minutes through Stripe's hosted flow, which you can brand with your colors and logo. Using Stripe Elements in your mobile app keeps you at **PCI SAQ-A compliance**—the simplest level, requiring only a 22-question self-assessment since card data never touches your servers.

## Start with a modular monolith, not microservices

"Infinitely scalable from day one" doesn't mean deploying Kubernetes with a service mesh. **It means clean architecture that CAN scale when needed.** Expert consensus is clear: below 10 developers, monoliths outperform microservices while Docker and Kubernetes add complexity without clear benefits.

A **modular monolith** organizes code into loosely-coupled modules (Users, Bookings, Matching, Payments) with clear boundaries and minimal cross-dependencies. Each module exposes a clean internal API. This provides the architectural foundation to extract services later while avoiding distributed systems complexity today:

```
┌─────────────────────────────────────────────────────┐
│           MODULAR MONOLITH (FastAPI)                │
├─────────────┬─────────────┬─────────────┬──────────┤
│   Users     │   Booking   │   Matching  │ Payments │
│   Module    │   Module    │   Module    │  Module  │
└─────────────┴─────────────┴─────────────┴──────────┘
```

**When to extract microservices**: when multiple teams (7+ developers) need deployment independence, when components have vastly different scaling requirements, or when you need different technology stacks for specific services. Uber started as a PHP monolith; they split into 500+ services only at massive scale with hundreds of engineers.

For infrastructure, **managed platforms beat AWS/GCP complexity** at startup scale:

| Phase | Infrastructure | Monthly Cost |
|-------|---------------|--------------|
| MVP (0-10K users) | Vercel + Supabase + Railway | $25-85 |
| Growth (10K-100K) | AWS ECS Fargate + RDS + ElastiCache | $200-1,000 |
| Scale (100K+) | Consider multi-region, read replicas | $1,000+ |

Avoid Kubernetes until you have 20+ services and a dedicated platform team. AWS ECS Fargate or GCP Cloud Run provide container orchestration without cluster management overhead.

## Real-time architecture requires thoughtful layering

Real-time features split into three categories, each with optimal implementation approaches:

**Chat and presence** use Supabase Realtime's PostgreSQL subscriptions. Messages persist to the database; subscribers receive changes automatically. Presence tracking uses Supabase's built-in presence channels with join/leave/sync events. This requires zero custom WebSocket infrastructure.

**Location tracking** needs lower latency than database round-trips provide. Implement this with FastAPI WebSockets coordinated through Redis Pub/Sub:

```python
# FastAPI WebSocket endpoint for location updates
@app.websocket("/ws/location/{booking_id}")
async def location_stream(websocket: WebSocket, booking_id: str):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"location:{booking_id}")
    
    async for message in pubsub.listen():
        await websocket.send_json(message['data'])
```

**Push notifications** flow through Firebase Cloud Messaging (FCM), which abstracts both APNs (iOS) and Android delivery. Your backend sends to FCM; FCM handles the platform-specific delivery. This unified approach simplifies implementation significantly.

For background location on mobile, use `expo-location` with proper permissions configuration. iOS requires "Always" location permission for background tracking—Apple scrutinizes this, so ensure your app's core functionality genuinely requires it. On Android, implement a foreground service to maintain tracking when the app isn't visible.

## Authentication and API design patterns matter

**OAuth 2.0 with PKCE** (Proof Key for Code Exchange) is mandatory for mobile authentication. Use the system browser (ASWebAuthenticationSession on iOS, Custom Tabs on Android) rather than embedded WebViews—this is both more secure and required by many OAuth providers.

JWT access tokens should expire in **15 minutes** with refresh token rotation: each refresh issues a new refresh token while invalidating the old one. Store tokens in iOS Keychain or Android EncryptedSharedPreferences—never in UserDefaults, SharedPreferences, or AsyncStorage.

**REST remains the right choice** for your primary API. Mobile clients benefit from HTTP caching, security patterns are mature, and implementation is straightforward. Reserve GraphQL for specific complex screens where you need to fetch multiple related entities in a single request to minimize cellular round-trips.

OpenAPI specification with FastAPI enables automatic documentation, client SDK generation, and clear API contracts. Structure your codebase around repository and service layers:

```
dance_partner/
├── api/routes/           # HTTP handlers only
├── services/             # Business logic orchestration
├── repositories/         # Database access patterns
├── models/
│   ├── domain/          # Business entities
│   └── schemas/         # Pydantic request/response models
└── CLAUDE.md            # AI assistant context
```

## Optimize for AI-assisted development with Claude Code

Create a comprehensive **CLAUDE.md** file in your project root. This becomes Claude Code's primary context for understanding your codebase:

```markdown
# Dance Partner API

## Commands
- `make dev`: Start development server
- `pytest tests/unit -v`: Run unit tests

## Code Style
- Type hints on ALL function parameters and returns
- Pydantic models for request/response validation
- Repository pattern for data access
- Services orchestrate business logic; routes only handle HTTP

DON'Ts:
- DON'T use `Any` type
- DON'T put business logic in route handlers
```

**Comprehensive type hints** dramatically improve Claude Code's suggestions. Pydantic models with Field descriptions and JSON schema examples provide additional context:

```python
class CreateBookingRequest(BaseModel):
    host_id: str = Field(..., description="The host's user ID")
    start_time: datetime = Field(..., description="Booking start in UTC")
    duration_minutes: int = Field(60, ge=30, le=240)
```

For testing, **Maestro** provides the best mobile E2E testing experience with YAML-based test definitions that work across iOS and Android. Backend tests use pytest with the repository/service pattern enabling clean unit test mocking.

## Recommended technology stack summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile** | React Native + Expo | Leverages React/TS skills, excellent Stripe SDK |
| **Web** | Next.js on Vercel | Code sharing with mobile, excellent DX |
| **Backend API** | FastAPI (Python) | Existing expertise, excellent for AI-assisted dev |
| **Database** | Supabase PostgreSQL + PostGIS | Managed Postgres with built-in realtime |
| **Real-time** | Supabase Realtime + FastAPI WebSockets | Chat via Supabase, location via direct WebSockets |
| **Cache/Pub-Sub** | Redis (Upstash or ElastiCache) | Caching, WebSocket coordination, geospatial |
| **Payments** | Stripe Connect Express | Marketplace splits, escrow, global support |
| **Auth** | Supabase Auth + OAuth 2.0 PKCE | Social logins, JWT, managed identity |
| **Push** | FCM (Firebase Cloud Messaging) | Unified iOS/Android delivery |
| **Hosting** | Vercel + Railway (MVP) → AWS ECS (scale) | Start managed, migrate when needed |
| **Monitoring** | Sentry + New Relic Free Tier | Error tracking, APM |
| **Mobile CI/CD** | EAS Build + Fastlane | Cloud builds, automated store submission |

## Conclusion

This architecture supports growth from zero to hundreds of thousands of users through incremental complexity additions rather than upfront over-engineering. The stack maximizes your existing Python and React expertise while providing a clear scaling path. Starting with Supabase and managed platforms keeps operational burden minimal during the critical MVP and product-market fit phases; AWS migration becomes straightforward when scale demands it.

The most important principle: **build for today's needs with tomorrow's architecture in mind**. A well-structured modular monolith with clean service boundaries, proper type annotations for AI-assisted development, and managed infrastructure will take Dance Partner further, faster than a premature microservices deployment ever could.