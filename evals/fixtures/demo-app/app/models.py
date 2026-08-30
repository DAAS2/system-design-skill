"""Order and payment domain models (plain dicts; no ORM)."""


def new_order(user_id: str, items: list[dict]) -> dict:
    total = sum(i["price"] * i["qty"] for i in items)
    return {
        "user_id": user_id,
        "items": items,
        "total": total,
        "status": "created",  # created -> paid -> fulfilled
    }
