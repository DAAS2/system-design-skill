"""Order cache. Cache-aside over Redis, 10-minute TTL."""

import json
import os

import redis

r = redis.Redis.from_url(os.environ["REDIS_URL"])

TTL_SECONDS = 600


def get_order_cached(order_id: int) -> dict | None:
    raw = r.get(f"order:{order_id}")
    if raw:
        return json.loads(raw)
    return None


def put_order_cached(order: dict) -> None:
    r.set(f"order:{order['id']}", json.dumps(order), ex=TTL_SECONDS)
