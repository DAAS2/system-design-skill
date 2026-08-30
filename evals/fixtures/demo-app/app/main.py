"""Shop API: create orders, read orders, charge cards."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import cache, db, payments
from .models import new_order

app = FastAPI(title="shop-api")


class OrderIn(BaseModel):
    user_id: str
    items: list[dict]


@app.on_event("startup")
def startup():
    db.init()


@app.post("/orders", status_code=201)
def create_order(body: OrderIn) -> dict:
    order = new_order(body.user_id, body.items)
    order_id = db.insert_order(order)
    return {"id": order_id, "status": order["status"]}


@app.get("/orders/{order_id}")
def read_order(order_id: int) -> dict:
    order = cache.get_order_cached(order_id)
    if order is None:
        order = db.get_order(order_id)
        if order is None:
            raise HTTPException(404)
        cache.put_order_cached(order)
    return order


@app.post("/orders/{order_id}/charge")
def charge_order(order_id: int) -> dict:
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)

    stripe_id = payments.charge(order["total"], order_id)
    db.insert_payment(order_id, order["total"], stripe_id, "captured")
    db.update_order_status(order_id, "paid")

    # tell the email worker
    import json
    import os

    import redis

    r = redis.Redis.from_url(os.environ["REDIS_URL"])
    r.lpush("emails", json.dumps({"order_id": order_id, "user_id": order["user_id"]}))

    return {"status": "paid", "stripe_id": stripe_id}
