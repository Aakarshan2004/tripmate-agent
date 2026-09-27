from app.models.schemas import ScooterOption
from datetime import datetime


def get_scooter_option(start_date: str, end_date: str) -> ScooterOption:
    """
    Mock scooter rental.
    """

    days = (
        datetime.strptime(end_date, "%Y-%m-%d")
        - datetime.strptime(start_date, "%Y-%m-%d")
    ).days

    days = max(days, 1)

    price_per_day = 300

    return ScooterOption(
        provider="LocalGo Rentals",
        price_per_day=price_per_day,
        total_price=price_per_day * days,
        days=days,
    )