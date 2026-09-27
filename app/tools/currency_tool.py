import requests

FRANKFURTER_URL = "https://api.frankfurter.app/latest"


def convert_to_inr(amount: float, from_currency: str) -> float:
    """Convert an amount to INR using Frankfurter exchange rates."""

    if from_currency.upper() == "INR":
        return amount

    try:
        response = requests.get(
            FRANKFURTER_URL,
            params={
                "from": from_currency,
                "to": "INR",
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()
        rate = data.get("rates", {}).get("INR")

        if rate is None:
            print(
                f"[currency_tool] No INR rate for {from_currency}. "
                "Using fallback."
            )
            return round(amount * 90, 2)

        return round(amount * rate, 2)

    except requests.RequestException as e:
        print(
            f"[currency_tool] Conversion failed: {e}. "
            "Using fallback."
        )
        return round(amount * 90, 2)