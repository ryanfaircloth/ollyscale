import os

import asyncpg


class Storage:
    """Abstract storage interface for traces, logs, metrics."""

    async def upsert_service(self, conn, service_name: str) -> int:
        row = await conn.fetchrow(
            """
            INSERT INTO service_dim (service_name)
            VALUES ($1)
            ON CONFLICT (service_name) DO UPDATE SET service_name=EXCLUDED.service_name
            RETURNING service_id
            """,
            service_name,
        )
        return row["service_id"]

    async def upsert_operation(self, conn, operation_name: str) -> int:
        row = await conn.fetchrow(
            """
            INSERT INTO operation_dim (operation_name)
            VALUES ($1)
            ON CONFLICT (operation_name) DO UPDATE SET operation_name=EXCLUDED.operation_name
            RETURNING operation_id
            """,
            operation_name,
        )
        return row["operation_id"]

    async def upsert_resource(self, conn, resource_jsonb) -> int:
        row = await conn.fetchrow(
            """
            INSERT INTO resource_dim (resource_jsonb)
            VALUES ($1)
            ON CONFLICT (resource_jsonb) DO UPDATE SET resource_jsonb=EXCLUDED.resource_jsonb
            RETURNING resource_id
            """,
            resource_jsonb,
        )
        return row["resource_id"]

    def __init__(self):
        self.pg_dsn = os.environ.get("PG_DSN")
        self.pg_host = os.environ.get("PG_HOST", "localhost")
        self.pg_port = int(os.environ.get("PG_PORT", 5432))
        self.pg_user = os.environ.get("PG_USER", "postgres")
        self.pg_password = os.environ.get("PG_PASSWORD", "postgres")
        self.pg_db = os.environ.get("PG_DB", "postgres")

    async def store_trace(self, trace: dict) -> None:
        """
        Store a span/trace in spans_fact, mapping OTEL fields to columns.
        Upserts service, operation, resource dimensions as needed.
        Expects trace dict with OTEL fields and attributes.
        """
        dsn = (
            self.pg_dsn or f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )
        async with asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2) as pool, pool.acquire() as conn:
            service_id = await self.upsert_service(conn, trace["service_name"])
            operation_id = await self.upsert_operation(conn, trace["operation_name"])
            resource_id = await self.upsert_resource(conn, trace["resource_jsonb"])
            await conn.execute(
                """
                INSERT INTO spans_fact (
                    trace_id, span_id, parent_span_id, service_id, operation_id, resource_id,
                    start_time_unix_nano, end_time_unix_nano, status_code, kind, tenant_id, connection_id,
                    attributes, events, links
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11, $12,
                    $13, $14, $15
                )
                """,
                trace.get("trace_id"),
                trace.get("span_id"),
                trace.get("parent_span_id"),
                service_id,
                operation_id,
                resource_id,
                trace.get("start_time_unix_nano"),
                trace.get("end_time_unix_nano"),
                trace.get("status_code"),
                trace.get("kind"),
                trace.get("tenant_id"),
                trace.get("connection_id"),
                trace.get("attributes"),
                trace.get("events"),
                trace.get("links"),
            )

    async def store_log(self, log: dict) -> None:
        """
        Store a log in logs_fact, mapping OTEL fields to columns.
        Upserts service and resource dimensions as needed.
        Expects log dict with OTEL fields and attributes.
        """
        dsn = (
            self.pg_dsn or f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )
        async with asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2) as pool, pool.acquire() as conn:
            service_id = await self.upsert_service(conn, log["service_name"])
            resource_id = await self.upsert_resource(conn, log["resource_jsonb"])
            await conn.execute(
                """
                INSERT INTO logs_fact (
                    trace_id, span_id, service_id, resource_id, time_unix_nano, severity_text, body,
                    tenant_id, connection_id, attributes
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8, $9, $10
                )
                """,
                log.get("trace_id"),
                log.get("span_id"),
                service_id,
                resource_id,
                log.get("time_unix_nano"),
                log.get("severity_text"),
                log.get("body"),
                log.get("tenant_id"),
                log.get("connection_id"),
                log.get("attributes"),
            )

    async def store_metric(self, metric: dict) -> None:
        """
        Store a metric in metrics_fact, mapping OTEL fields to columns.
        Upserts service and resource dimensions as needed.
        Expects metric dict with OTEL fields and attributes.
        """
        dsn = (
            self.pg_dsn or f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )
        async with asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2) as pool, pool.acquire() as conn:
            service_id = await self.upsert_service(conn, metric["service_name"])
            resource_id = await self.upsert_resource(conn, metric["resource_jsonb"])
            await conn.execute(
                """
                INSERT INTO metrics_fact (
                    service_id, resource_id, name, time_unix_nano, value, tenant_id, connection_id, attributes
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8
                )
                """,
                service_id,
                resource_id,
                metric.get("name"),
                metric.get("time_unix_nano"),
                metric.get("value"),
                metric.get("tenant_id"),
                metric.get("connection_id"),
                metric.get("attributes"),
            )

    async def health(self) -> dict:
        dsn = (
            self.pg_dsn or f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )
        try:
            conn = await asyncpg.connect(dsn=dsn, timeout=2)
            await conn.execute("SELECT 1")
            await conn.close()
            return {"status": "ok", "db": self.pg_db, "host": self.pg_host}
        except Exception as e:
            return {"status": "error", "error": str(e)}
