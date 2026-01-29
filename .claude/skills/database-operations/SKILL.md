---
name: Database Operations
description: Query and inspect PostgreSQL databases using MCP PostgreSQL tools. Execute SQL queries, list tables, describe schemas, check table structure, inspect data, analyze database schema, and troubleshoot database issues without leaving Claude Code. Supports runtime database selection between development (ijack-dev RDS) and production (ijack RDS) environments.
allowed-tools: [mcp__mcp-postgres__query_data, mcp__mcp-postgres__list_tables, mcp__mcp-postgres__describe_table, Read]
---

# Database Operations Skill

## Purpose
Query and inspect PostgreSQL databases using MCP PostgreSQL tools for safe, read-only database operations. Runtime database selection allows querying development (default) or production databases without container restart.

## When to Use This Skill
- Querying application data
- Listing database tables
- Inspecting table schemas
- Checking data for debugging
- Analyzing database structure
- Validating data integrity
- Database exploration
- Comparing dev vs prod data

## Available Databases

### Development Database (Default) - ijack-dev RDS
- **Connection**: AWS RDS (ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com)
- **Database**: strictly_dancing
- **Tables**: Application tables (users, host_profiles, bookings, etc.)
- **Usage**: `database="rds-dev"` (default parameter)
- **Default**: Queries without `database` parameter use development

### Production Database - ijack RDS
- **Connection**: AWS RDS (ijack.c9lvkaunz4dq.us-west-2.rds.amazonaws.com)
- **Database**: strictly_dancing
- **Tables**: Same schema as development
- **Usage**: `database="rds"`
- **Use When**: Checking production data, validating deployments, debugging production issues

## Core Operations

### List Tables
```python
# List Development tables (default)
mcp__mcp-postgres__list_tables(database="rds-dev")

# List Production tables
mcp__mcp-postgres__list_tables(database="rds")
```

### Describe Table Schema
```python
# Describe Development table (default)
mcp__mcp-postgres__describe_table(table_name="users", database="rds-dev")
mcp__mcp-postgres__describe_table(table_name="host_profiles", schema="public", database="rds-dev")

# Describe Production table
mcp__mcp-postgres__describe_table(
    table_name="bookings",
    database="rds"
)
```

### Execute SQL Queries
```python
# Query Development database (default)
mcp__mcp-postgres__query_data(
    sql="SELECT COUNT(*) FROM users WHERE is_active = true",
    database="rds-dev"
)

mcp__mcp-postgres__query_data(
    sql="SELECT id, email, created_at FROM users LIMIT 10",
    database="rds-dev"
)

# Query Production database
mcp__mcp-postgres__query_data(
    sql="SELECT * FROM host_profiles ORDER BY created_at DESC LIMIT 5",
    database="rds"
)
```

## Query Safety Guidelines

### Always Use LIMIT for Large Tables
```python
# CORRECT: Use LIMIT for safety
mcp__mcp-postgres__query_data(
    sql="SELECT * FROM bookings ORDER BY created_at DESC LIMIT 10",
    database="rds-dev"
)

# INCORRECT: No LIMIT on large table
mcp__mcp-postgres__query_data(
    sql="SELECT * FROM bookings"  # Could return many rows!
)
```

### Use Efficient Queries
```python
# CORRECT: Specific columns and conditions
mcp__mcp-postgres__query_data(
    sql="""
        SELECT id, display_name, user_id
        FROM host_profiles
        WHERE is_verified = true
        AND created_at > NOW() - INTERVAL '7 days'
        LIMIT 50
    """,
    database="rds-dev"
)

# INCORRECT: SELECT * without conditions
mcp__mcp-postgres__query_data(
    sql="SELECT * FROM host_profiles"
)
```

## Common Use Cases

### User Management
```python
# List active users
mcp__mcp-postgres__query_data(
    sql="SELECT id, email, created_at FROM users WHERE is_active = true LIMIT 20",
    database="rds-dev"
)

# Count users
mcp__mcp-postgres__query_data(
    sql="SELECT COUNT(*) as count FROM users",
    database="rds-dev"
)
```

### Host Profiles
```python
# Recent host profiles
mcp__mcp-postgres__query_data(
    sql="""
        SELECT id, display_name, created_at
        FROM host_profiles
        ORDER BY created_at DESC
        LIMIT 10
    """,
    database="rds-dev"
)

# Host with dance styles
mcp__mcp-postgres__query_data(
    sql="""
        SELECT hp.id, hp.display_name, ds.name as dance_style
        FROM host_profiles hp
        JOIN host_dance_styles hds ON hp.id = hds.host_profile_id
        JOIN dance_styles ds ON hds.dance_style_id = ds.id
        WHERE hp.id = 'some-host-id'
        LIMIT 20
    """,
    database="rds-dev"
)
```

### Bookings
```python
# Recent bookings
mcp__mcp-postgres__query_data(
    sql="""
        SELECT id, host_id, guest_id, status, created_at
        FROM bookings
        ORDER BY created_at DESC
        LIMIT 10
    """,
    database="rds-dev"
)

# Bookings by host
mcp__mcp-postgres__query_data(
    sql="""
        SELECT b.id, b.status, u.email as guest_email
        FROM bookings b
        JOIN users u ON b.guest_id = u.id
        WHERE b.host_id = 'some-host-id'
        LIMIT 20
    """,
    database="rds-dev"
)
```

## Schema Exploration

### Discover Table Structure
```python
# Get column information
mcp__mcp-postgres__describe_table(table_name="users", database="rds-dev")

# Explore relationships
mcp__mcp-postgres__query_data(
    sql="""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name='host_profiles'
    """,
    database="rds-dev"
)
```

### Find Tables by Pattern
```python
# Tables matching pattern
mcp__mcp-postgres__query_data(
    sql="""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE '%host%'
    """,
    database="rds-dev"
)
```

## Best Practices

1. **Always use LIMIT**: Especially on tables that could have many rows
2. **Select specific columns**: Avoid `SELECT *` when possible
3. **Use WHERE clauses**: Filter data at database level
4. **Aggregate when possible**: Use GROUP BY for summary data
5. **Read-only access**: MCP tools only execute SELECT queries
6. **Test queries**: Start with small LIMIT values
7. **Dev first**: Test queries on dev before running on prod

## Troubleshooting

### Connection Issues
MCP PostgreSQL server runs via the rcom container. If queries fail, check container status:
```bash
docker ps | grep mcp-postgres
docker logs rcom-mcp-postgres-1
```

### Slow Queries
- Add appropriate WHERE clauses
- Use smaller LIMIT values
- Check query execution plan

### Missing Tables
Use `list_tables()` to see available tables. Tables may be in different schemas (default: "public").

## Integration
This skill automatically activates when:
- Querying databases
- Listing or describing tables
- Running SQL queries
- Inspecting data
- Database exploration
- Validating data integrity
- Debugging data issues
