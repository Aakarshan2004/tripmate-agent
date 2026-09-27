import json
from datetime import datetime, timedelta

from app.models.schemas import TransportOption
from app.agent.llm import llm


def search_transport(
    origin: str,
    destination: str,
    date: str
) -> list[TransportOption]:

    prompt = f"""
You are a travel transport planner.

Create realistic SIMULATED transport options for:

Origin: {origin}
Destination: {destination}
Date: {date}

Important:
- These are SIMULATED options, not live booking data.
- Think about the actual geography and railway/airport connectivity.
- If the destination does not have a railway station or direct practical train,
  suggest a realistic nearest railhead/airport route instead.
- Do NOT invent a direct train if the destination does not have one.
- Prefer well-known train/airline names where appropriate.
- Prices and timings are simulated estimates only.
- Return exactly 3 options.
- Include 2 train/rail options and 1 flight option when practical.
- For a train route involving a road connection, mention that connection in the name.
- Keep names concise.

Return ONLY valid JSON in this format:

[
  {{
    "mode": "train",
    "name": "train/route name",
    "price": 1500,
    "duration": "18h",
    "departure": "2026-11-05 20:00",
    "arrival": "2026-11-06 14:00"
  }}
]
"""

    try:
        result = llm.invoke(prompt)

        content = result.content.strip()

        # Remove markdown code fences if model adds them
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)

        options = [
            TransportOption(**item)
            for item in data
        ]

        # Clearly mark everything as simulated
        for option in options:
            option.name = f"[SIMULATED] {option.name}"

        return options[:3]

    except Exception as e:
        print(f"[transport_tool] LLM generation failed: {e}")

        # Safe fallback
        return _fallback_transport(origin, destination, date)


def _fallback_transport(
    origin: str,
    destination: str,
    date: str
) -> list[TransportOption]:

    return [
        TransportOption(
            mode="train",
            name=f"[SIMULATED] {origin} → {destination} rail route",
            price=1500,
            duration="20h",
            departure=f"{date} 20:00",
            arrival=_add_hours(date, 20),
        ),
        TransportOption(
            mode="train",
            name=f"[SIMULATED] {origin} → {destination} alternate rail route",
            price=2200,
            duration="22h",
            departure=f"{date} 18:00",
            arrival=_add_hours(date, 22),
        ),
        TransportOption(
            mode="flight",
            name=f"[SIMULATED] Flight {origin} → {destination}",
            price=4500,
            duration="2h 30m",
            departure=f"{date} 08:00",
            arrival=f"{date} 10:30",
        ),
    ]


def _add_hours(date_str: str, hours: int) -> str:

    dt = (
        datetime.strptime(date_str, "%Y-%m-%d")
        + timedelta(hours=hours)
    )

    return dt.strftime("%Y-%m-%d %H:%M")