import os
import time
import requests
from dotenv import load_dotenv
from app.models.schemas import HotelOption

load_dotenv()

STAYINGAPI_KEY = os.getenv("STAYINGAPI_KEY")
STAYINGAPI_URL = "https://api.stayingapi.com/v1/search"
STAYINGAPI_JOBS_URL = "https://api.stayingapi.com/v1/jobs"

BUDGET_FILTERS = {
    "budget": (0, 80),
    "moderate": (80, 250),
    "luxury": (250, float("inf")),
}


def search_hotels(
    destination: str,
    region: str = "",
    check_in: str = "",
    check_out: str = "",
    budget_level: str = "moderate",
    adults: int = 1
) -> list[HotelOption]:

    if not STAYINGAPI_KEY:
        raise RuntimeError("STAYINGAPI_KEY not set in .env")

    location = (
        f"{destination}, {region}"
        if region
        else destination
    )

    params = {
        "location": location,
        "checkIn": check_in,
        "checkOut": check_out,
        "adults": adults,
        "platforms": "booking",
        "limit": 10,
    }

    headers = {
        "Authorization": f"Bearer {STAYINGAPI_KEY}"
    }

    try:
        response = requests.get(
            STAYINGAPI_URL,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()
        payload = response.json()

        # Live API may return 202 with an async job
        if response.status_code == 202:
            job_id = payload["data"]["jobId"]

            print(
                f"[hotel_tool] Live search started: {job_id}"
            )

            payload = _poll_job(
                job_id,
                headers
            )

        raw_results = payload.get("data", [])

        # Completed async jobs return the actual result
        # inside data.result
        if isinstance(raw_results, dict):
            raw_results = raw_results.get(
                "result",
                []
            )

        if not isinstance(raw_results, list):
            print(
                "[hotel_tool] Unexpected API response format"
            )
            return []

    except requests.RequestException as e:
        print(
            f"[hotel_tool] StayingAPI request failed: {e}"
        )
        return []

    except (ValueError, KeyError) as e:
        print(
            f"[hotel_tool] Invalid StayingAPI response: {e}"
        )
        return []

    hotels = [
        _to_hotel_option(item)
        for item in raw_results
    ]

    hotels = [
        h for h in hotels
        if h is not None
    ]

    low, high = BUDGET_FILTERS.get(
        budget_level,
        (0, float("inf"))
    )

    filtered = [
        h for h in hotels
        if low <= h.price_per_night <= high
    ]

    result = filtered if filtered else hotels

    return sorted(
        result,
        key=lambda h: h.price_per_night
    )


def _poll_job(
    job_id: str,
    headers: dict,
    max_wait: int = 300
) -> dict:

    start_time = time.time()

    while time.time() - start_time < max_wait:

        response = requests.get(
            f"{STAYINGAPI_JOBS_URL}/{job_id}",
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", {})

        status = data.get("status")

        print(
            f"[hotel_tool] Job {job_id}: {status}"
        )

        if status == "completed":
            return data.get(
                "result",
                {}
            )

        if status == "failed":
            print(
                f"[hotel_tool] Hotel search job failed: "
                f"{data.get('error')}"
            )
            return {}

        # API may provide Retry-After
        retry_after = response.headers.get(
            "Retry-After"
        )

        try:
            wait_seconds = int(
                retry_after
            ) if retry_after else 5
        except ValueError:
            wait_seconds = 5

        time.sleep(wait_seconds)

    print(
        f"[hotel_tool] Job {job_id} timed out"
    )

    return {}


def _to_hotel_option(
    item: dict
) -> HotelOption | None:

    try:

        price_block = item.get(
            "price",
            {}
        )

        location_block = item.get(
            "location",
            {}
        )

        return HotelOption(
            name=item.get(
                "name",
                "Unknown property"
            ),

            price_per_night=price_block.get(
                "nightlyPrice",
                0
            ),

            total_price=price_block.get(
                "totalPrice",
                0
            ),

            currency=price_block.get(
                "currency",
                "USD"
            ),

            nights=price_block.get(
                "nights",
                0
            ),

            location=location_block.get(
                "city",
                item.get("name", "")
            ),

            rating=item.get(
                "guestRating",
                0.0
            ),
        )

    except Exception as e:

        print(
            f"[hotel_tool] Skipping malformed result: {e}"
        )

        return None