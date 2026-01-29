"""MCP PostgreSQL Server for Strictly Dancing.

Provides read-only database access for Claude Code via MCP protocol.
"""

import os
from pathlib import Path
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file (override=True to ensure .env takes precedence)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

# Create MCP server instance
mcp = FastMCP("Strictly Dancing PostgreSQL")

# Database configuration
DATABASES = {
    # Development database (AWS RDS ijack-dev)
    "dev": {
        "host": os.getenv("DB_HOST_DEV", "ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com"),
        "port": int(os.getenv("DB_PORT_DEV", "5432")),
        "user": os.getenv("DB_USER_DEV", "master"),
        "password": os.getenv("DB_PASSWORD_DEV", ""),
        "database": os.getenv("DB_NAME_DEV", "strictly_dancing"),
    },
    # Production database (AWS RDS ijack)
    "prod": {
        "host": os.getenv("DB_HOST_PROD", "ijack.c9lvkaunz4dq.us-west-2.rds.amazonaws.com"),
        "port": int(os.getenv("DB_PORT_PROD", "5432")),
        "user": os.getenv("DB_USER_PROD", "master"),
        "password": os.getenv("DB_PASSWORD_PROD", ""),
        "database": os.getenv("DB_NAME_PROD", "strictly_dancing"),
    },
}

# Print configuration for debugging (without passwords)
print("Database configurations:")
for db_name, config in DATABASES.items():
    print(f"\n{db_name}:")
    print(f"  host: {config['host']}")
    print(f"  port: {config['port']}")
    print(f"  user: {config['user']}")
    print(f"  database: {config['database']}")
    print(f"  has_password: {bool(config['password'])}")

# Connection pools for each database
pools: dict[str, Optional[asyncpg.Pool]] = {}


async def get_pool(db_name: str = "dev") -> asyncpg.Pool:
    """Get or create the connection pool for specified database."""
    global pools

    if db_name not in DATABASES:
        raise ValueError(
            f"Unknown database: {db_name}. Available databases: {list(DATABASES.keys())}"
        )

    if db_name not in pools or pools[db_name] is None:
        print(f"\nCreating new pool for database: {db_name}")
        config = DATABASES[db_name]
        print(f"Connection config: {config['host']}:{config['port']}")
        try:
            pools[db_name] = await asyncpg.create_pool(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            print(f"Pool created successfully for {db_name}")
        except Exception as e:
            print(f"Failed to create pool for {db_name}: {e}")
            raise

    return pools[db_name]


@mcp.tool()
async def query_data(sql: str, database: str = "dev") -> str:
    """
    Execute SQL queries safely (read-only access)

    Args:
        sql: SQL query to execute
        database: Database to query ("dev" or "prod", default: "dev")

    Returns:
        Formatted table output of query results
    """
    print(f"\n[query_data] Database: {database}, SQL: {sql[:50]}...")

    # Validate query is read-only
    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return "Error: Only SELECT and WITH queries are allowed for safety."

    try:
        db_pool = await get_pool(database)
        async with db_pool.acquire() as conn:
            current_db = await conn.fetchval("SELECT current_database()")
            print(f"[query_data] Connected to database: {current_db}")

            rows = await conn.fetch(sql)

            if not rows:
                return f"No results found in {database} database"

            columns = list(rows[0].keys())
            widths = {col: len(col) for col in columns}
            for row in rows:
                for col in columns:
                    val = str(row[col]) if row[col] is not None else "NULL"
                    widths[col] = max(widths[col], len(val))

            header = " | ".join(col.ljust(widths[col]) for col in columns)
            separator = "-+-".join("-" * widths[col] for col in columns)

            result_lines = [f"Database: {database}", header, separator]
            for row in rows:
                line = " | ".join(
                    (str(row[col]) if row[col] is not None else "NULL").ljust(widths[col])
                    for col in columns
                )
                result_lines.append(line)

            result_lines.append(f"\n({len(rows)} rows)")
            return "\n".join(result_lines)

    except asyncpg.PostgresError as e:
        return f"Database error in {database}: {e}"
    except Exception as e:
        return f"Error in {database}: {e}"


@mcp.tool()
async def list_tables(database: str = "dev") -> str:
    """List all tables in the database"""
    try:
        db_pool = await get_pool(database)
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """)

            if not rows:
                return f"No tables found in {database} database"

            result_lines = [f"Database: {database}", "Schema | Table", "-" * 30]
            for row in rows:
                result_lines.append(f"{row['table_schema']} | {row['table_name']}")

            result_lines.append(f"\n({len(rows)} tables)")
            return "\n".join(result_lines)

    except Exception as e:
        return f"Error in {database}: {e}"


@mcp.tool()
async def describe_table(table_name: str, schema: str = "public", database: str = "dev") -> str:
    """Get detailed information about a table"""
    try:
        db_pool = await get_pool(database)
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """,
                schema,
                table_name,
            )

            if not rows:
                return f"Table {schema}.{table_name} not found in {database} database"

            result_lines = [
                f"Database: {database}",
                f"Table: {schema}.{table_name}",
                "=" * 50,
                "Column | Type | Nullable | Default",
                "-" * 50,
            ]

            for row in rows:
                col_type = row["data_type"]
                if row["character_maximum_length"]:
                    col_type += f"({row['character_maximum_length']})"
                nullable = "YES" if row["is_nullable"] == "YES" else "NO"
                default = row["column_default"] or "NULL"
                result_lines.append(f"{row['column_name']} | {col_type} | {nullable} | {default}")

            result_lines.append(f"\n({len(rows)} columns)")
            return "\n".join(result_lines)

    except Exception as e:
        return f"Error in {database}: {e}"


if __name__ == "__main__":
    import asyncio

    mcp.settings.host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    mcp.settings.port = int(os.getenv("MCP_SERVER_PORT", "5005"))
    mcp.settings.streamable_http_path = "/mcp"

    asyncio.run(mcp.run(transport="streamable-http"))
