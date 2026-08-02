import psycopg
import re

FORBIDDEN_KEYWORDS = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke"]

def is_safe_sql(sql: str) -> bool:
    """Basic safety check before executing anything."""
    lowered = sql.lower()
    if not lowered.strip().startswith("select"):
        return False
    if any(kw in lowered for kw in FORBIDDEN_KEYWORDS):
        return False
    return True

def execute_sql(sql: str, connection_string: str) -> list[dict]:
    """
    Takes a validated SQL string, runs it, returns rows as a list of dicts.
    Assumes the connection is a read-only DB user.
    """
    if not is_safe_sql(sql):
        raise ValueError(f"Rejected unsafe SQL: {sql}")

    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]