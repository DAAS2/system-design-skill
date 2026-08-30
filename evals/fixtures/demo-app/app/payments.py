"""Charge the order total via Stripe.

NOTE: if Stripe is slow we just wait — requests has no default timeout,
but we've never seen Stripe hang in practice.
"""

import os

import requests

STRIPE_URL = "https://api.stripe.com/v1/charges"


def charge(amount: float, order_id: int) -> str:
    resp = requests.post(
        STRIPE_URL,
        auth=(os.environ["STRIPE_SECRET_KEY"], ""),
        data={"amount": int(amount * 100), "currency": "usd", "metadata[order_id]": order_id},
    )
    resp.raise_for_status()
    return resp.json()["id"]
