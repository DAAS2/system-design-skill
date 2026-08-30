"""Database access. One connection per query — fine for the demo."""

import os

import psycopg2

DDL = """
CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL,
    items       JSONB NOT NULL,
    total       NUMERIC(10, 2) NOT NULL,
    status      TEXT NOT NULL DEFAULT 'created',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS payments (
    id          SERIAL PRIMARY KEY,
    order_id    INT NOT NULL REFERENCES orders(id),
    stripe_id   TEXT,
    amount      NUMERIC(10, 2) NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
);
"""


def connect():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init():
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    conn.close()


def insert_order(order: dict) -> int:
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (user_id, items, total, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (order["user_id"], order["items"], order["total"], order["status"]),
        )
        order_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return order_id


def get_order(order_id: int) -> dict | None:
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SELECT id, user_id, items, total, status FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "user_id": row[1], "items": row[2], "total": float(row[3]), "status": row[4]}


def update_order_status(order_id: int, status: str) -> None:
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
    conn.commit()
    conn.close()


def insert_payment(order_id: int, amount: float, stripe_id: str, status: str) -> int:
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO payments (order_id, stripe_id, amount, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (order_id, stripe_id, amount, status),
        )
        pid = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return pid
