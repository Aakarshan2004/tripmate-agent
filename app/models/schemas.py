from pydantic import BaseModel, Field
from typing import Optional, Literal


class TripIntent(BaseModel):

    """Structured representation of what the user wants."""

    origin: str = Field(
        description="City the user is travelling from"
    )

    origin_state_or_region: str = Field(
        description="State or region of the origin city"
    )

    destination: str = Field(
        description="City the user wants to travel to"
    )

    destination_state_or_region: str = Field(
        description="State or region of the destination city. "
                    "For ambiguous places, use the well-known intended location. "
                    "Example: Manali → Himachal Pradesh"
    )

    start_date: str = Field(
        description="Trip start date, format YYYY-MM-DD. Infer year 2026 if not given."
    )

    end_date: str = Field(
        description="Trip end date, format YYYY-MM-DD. Infer year 2026 if not given."
    )

    budget_level: Literal["budget", "moderate", "luxury"] = Field(
        default="moderate",
        description="Traveler's budget preference. Default to 'moderate' if not specified."
    )

    num_travelers: int = Field(
        default=1,
        description="Number of people travelling"
    )


class TransportOption(BaseModel):
    mode: str          # "train" or "flight"
    name: str          # e.g. "Goa Express"
    price: int
    duration: str
    departure: str
    arrival: str


class HotelOption(BaseModel):
    name: str
    price_per_night: float
    total_price: float
    currency: str
    nights: int
    location: str
    rating: float


class BudgetItem(BaseModel):
    item: str
    cost: int


class TripBudget(BaseModel):
    items: list[BudgetItem]
    total: int
    
class WeatherDay(BaseModel):
    date: str
    condition: str
    temp_min: float
    temp_max: float
    rain_likely: bool


class Place(BaseModel):
    name: str
    kind: str
    lat: float
    lon: float
    rating: int = 0


class DayPlan(BaseModel):
    date: str
    weather_note: str
    activities: list[str]
    
class ScooterOption(BaseModel):
    provider: str
    price_per_day: int
    total_price: int
    days: int
    
class StartTripRequest(BaseModel):
    message: str
    thread_id: str


class ResumeTripRequest(BaseModel):
    message: str
    thread_id: str


class TripResponse(BaseModel):
    thread_id: str
    status: Literal["waiting_for_input", "completed", "cancelled"]
    question: Optional[str] = None
    options: Optional[list[dict]] = None
    final_state: Optional[dict] = None