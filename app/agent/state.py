from typing import TypedDict, Optional
from app.models.schemas import (
    TripIntent,
    TransportOption,
    HotelOption,
    TripBudget,
    ScooterOption
)


class TripState(TypedDict, total=False):
    user_message: str
    intent: TripIntent

    transport_options: list[TransportOption]
    selected_transport: TransportOption

    hotel_options: list[HotelOption]
    selected_hotel: HotelOption

    scooter_confirmed: bool
    itinerary: list[str]          # one entry per day, e.g. "May 2: Baga, Calangute..."

    return_options: list[TransportOption]
    selected_return: TransportOption

    budget: TripBudget

    # human-in-the-loop control
    awaiting_confirmation: Optional[str]   # which step is waiting on the user, e.g. "transport"
    messages: list[str]                     # running log of agent↔user exchange
    selected_scooter: Optional[ScooterOption]
    _rejected_transport_names: list[str]
    _retry_transport: bool
    _rejected_hotel_names: list[str]
    _retry_hotel: bool
    _rejected_return_names: list[str]
    _retry_return: bool
    _retry_itinerary: bool
    _booking_confirmed: bool
    _edit_target: Optional[str]