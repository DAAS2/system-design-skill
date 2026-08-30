"""Confirmation email worker.

Pops jobs from the `emails` list and sends email through SMTP.
"""

import json
import os
import smtplib
import time

import redis

r = redis.Redis.from_url(os.environ["REDIS_URL"])


def send(to: str, subject: str, body: str) -> None:
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost")) as s:
        s.sendmail("orders@shop.example", [to], f"Subject: {subject}\n\n{body}")


def main() -> None:
    while True:
        _, raw = r.blpop("emails")
        job = json.loads(raw)
        # look up the user's address from the orders table
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM orders WHERE id = %s", (job["order_id"],))
            row = cur.fetchone()
        conn.close()
        send(row[0], "Order confirmed", f"Thanks for order {job['order_id']}!")
        time.sleep(0.1)  # don't hammer the SMTP host


if __name__ == "__main__":
    main()
