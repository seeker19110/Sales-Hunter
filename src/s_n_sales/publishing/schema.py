"""Additive SQLite outbox tables; never use executescript inside a transaction."""

from __future__ import annotations

from s_n_sales.api.store_sqlite import SqliteOperatorStore


def initialize(store: SqliteOperatorStore) -> None:
    with store.transaction() as connection:
        statements = (
            """CREATE TABLE IF NOT EXISTS payload_approvals (
                scope_id TEXT PRIMARY KEY, publication_id TEXT NOT NULL,
                revision INTEGER NOT NULL, approval_id TEXT NOT NULL UNIQUE,
                scope_json TEXT NOT NULL,
                FOREIGN KEY(publication_id,revision)
                    REFERENCES candidate_revisions(publication_id,revision))""",
            """CREATE TABLE IF NOT EXISTS publish_intents (
                intent_id TEXT PRIMARY KEY, logical_key TEXT NOT NULL UNIQUE,
                scope_id TEXT NOT NULL REFERENCES payload_approvals(scope_id),
                publication_id TEXT NOT NULL, revision INTEGER NOT NULL,
                channel TEXT NOT NULL, source TEXT NOT NULL, business_key TEXT NOT NULL,
                payload_json TEXT NOT NULL, policy_json TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                available_at TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                lease_token TEXT, worker_id TEXT, lease_until TEXT,
                receipt_json TEXT, error_code TEXT, cooldown_until TEXT)""",
            "CREATE INDEX IF NOT EXISTS intents_due ON publish_intents(status,available_at)",
            "CREATE INDEX IF NOT EXISTS intents_business ON publish_intents(business_key,channel)",
            """CREATE TABLE IF NOT EXISTS publish_attempts (
                attempt_id TEXT PRIMARY KEY, intent_id TEXT NOT NULL
                    REFERENCES publish_intents(intent_id), attempt_number INTEGER NOT NULL,
                lease_token TEXT NOT NULL, worker_id TEXT NOT NULL, started_at TEXT NOT NULL,
                UNIQUE(intent_id,attempt_number))""",
            """CREATE TABLE IF NOT EXISTS publish_events (
                event_id TEXT PRIMARY KEY, intent_id TEXT REFERENCES publish_intents(intent_id),
                kind TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
                detail_json TEXT NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS publish_confirmations (
                intent_id TEXT PRIMARY KEY REFERENCES publish_intents(intent_id),
                receipt_json TEXT NOT NULL, confirmed_at TEXT NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS publish_pauses (
                scope TEXT NOT NULL, scope_key TEXT NOT NULL, paused INTEGER NOT NULL,
                actor TEXT NOT NULL, reason TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY(scope,scope_key))""",
            """CREATE TABLE IF NOT EXISTS approved_exports (
                export_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL
                    REFERENCES payload_approvals(scope_id), created_at TEXT NOT NULL,
                actor TEXT NOT NULL, export_json TEXT NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS recall_intents (
                intent_id TEXT PRIMARY KEY REFERENCES publish_intents(intent_id),
                status TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, receipt_json TEXT,
                lease_token TEXT, worker_id TEXT, lease_until TEXT)""",
            """CREATE TABLE IF NOT EXISTS worker_heartbeats (
                worker_id TEXT PRIMARY KEY, last_seen TEXT NOT NULL, mode TEXT NOT NULL)""",
        )
        for statement in statements:
            connection.execute(statement)
        for table in (
            "payload_approvals",
            "publish_attempts",
            "publish_events",
            "publish_confirmations",
            "approved_exports",
        ):
            for action in ("UPDATE", "DELETE"):
                connection.execute(
                    f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_{action} "
                    f"BEFORE {action} ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'immutable_publication_evidence'); END"
                )
        connection.execute(
            """CREATE TRIGGER IF NOT EXISTS intent_identity_immutable
            BEFORE UPDATE OF logical_key,scope_id,publication_id,revision,channel,source,
                business_key,payload_json,policy_json ON publish_intents
            BEGIN SELECT RAISE(ABORT, 'immutable_intent_identity'); END"""
        )
        connection.execute(
            "INSERT OR IGNORE INTO publish_pauses VALUES "
            "('global','*',1,'system:init','safe_default','1970-01-01T00:00:00.000000Z')"
        )
