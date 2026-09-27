import os
import math
import requests

from dotenv import load_dotenv
from app.models.schemas import Place


load_dotenv()

OPENTRIPMAP_KEY = os.getenv("OPENTRIPMAP_KEY")

GEONAME_URL = "https://api.opentripmap.com/0.1/en/places/geoname"
RADIUS_URL = "https://api.opentripmap.com/0.1/en/places/radius"


KIND_CATEGORIES = [
    "beaches",
    "religion",
    "historic",
    "museums",
]


def get_places(
    destination: str,
    region: str = "",
    limit_per_kind: int = 3
) -> list[Place]:

    if not OPENTRIPMAP_KEY:
        raise RuntimeError(
            "OPENTRIPMAP_KEY not set in .env"
        )

    # Get coordinates of destination
    lat, lon = _geoname(destination, region)

    if lat is None or lon is None:
        return []

    print(
        f"[places_tool] Destination: {destination}, {region}"
    )
    print(
        f"[places_tool] Coordinates: lat={lat}, lon={lon}"
    )

    all_places = []

    for kind in KIND_CATEGORIES:

        try:
            resp = requests.get(
                RADIUS_URL,
                params={
                    "radius": 20000,
                    "lon": lon,
                    "lat": lat,
                    "kinds": kind,
                    "limit": limit_per_kind,
                    "apikey": OPENTRIPMAP_KEY,
                },
                timeout=10
            )

            resp.raise_for_status()

            features = resp.json().get(
                "features",
                []
            )

        except requests.RequestException as e:
            print(
                f"[places_tool] Request failed "
                f"for kind='{kind}': {e}"
            )
            continue

        for feature in features:

            props = feature.get(
                "properties",
                {}
            )

            geometry = feature.get(
                "geometry",
                {}
            )

            coords = geometry.get(
                "coordinates",
                [None, None]
            )

            name = props.get("name")

            if not name:
                continue

            # GeoJSON coordinates = [longitude, latitude]
            place_lat = (
                coords[1]
                if len(coords) > 1
                else None
            )

            place_lon = (
                coords[0]
                if len(coords) > 0
                else None
            )

            if place_lat is None or place_lon is None:
                continue

            # Calculate actual distance from destination
            distance = _distance_km(
                lat,
                lon,
                place_lat,
                place_lon
            )

            print(
                f"[PLACES] {name} | "
                f"distance={distance:.2f} km"
            )

            # Only keep places genuinely near destination
            if distance > 30:
                print(
                    f"[PLACES] SKIPPED: {name} "
                    f"({distance:.2f} km away)"
                )
                continue

            all_places.append(
                Place(
                    name=name,
                    kind=kind,
                    lat=place_lat,
                    lon=place_lon,
                    rating=props.get("rate", 0),
                )
            )

    print(
        f"[places_tool] Final places: "
        f"{[place.name for place in all_places]}"
    )

    return all_places


def _geoname(
    destination: str,
    region: str = ""
) -> tuple[float | None, float | None]:

    query = (
        f"{destination}, {region}"
        if region
        else destination
    )

    try:
        resp = requests.get(
            GEONAME_URL,
            params={
                "name": query,
                "country": "IN",
                "apikey": OPENTRIPMAP_KEY,
            },
            timeout=10
        )

        resp.raise_for_status()

        data = resp.json()

        return (
            data.get("lat"),
            data.get("lon")
        )

    except requests.RequestException as e:
        print(
            f"[places_tool] Geoname lookup failed: {e}"
        )
        return None, None


def _distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:

    R = 6371  # Earth radius in km

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return R * 2 * math.asin(
        math.sqrt(a)
    )