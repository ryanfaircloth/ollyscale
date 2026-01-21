import os
from typing import Any

import asyncpg


class Storage:
    """Abstract storage interface for traces, logs, metrics."""

    def __init__(self):
        self.pg_dsn = os.environ.get("PG_DSN")
        self.pg_host = os.environ.get("PG_HOST", "localhost")
        self.pg_port = int(os.environ.get("PG_PORT", 5432))
        self.pg_user = os.environ.get("PG_USER", "postgres")
        self.pg_password = os.environ.get("PG_PASSWORD", "postgres")
        self.pg_db = os.environ.get("PG_DB", "postgres")

    async def store_trace(self, trace: Any) -> None:
        # TODO: Implement Postgres logic
        pass

    async def store_log(self, log: Any) -> None:
        # TODO: Implement Postgres logic
        pass

    async def store_metric(self, metric: Any) -> None:
        # TODO: Implement Postgres logic
        pass

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
