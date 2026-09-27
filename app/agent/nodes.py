from datetime import datetime

from pydantic import BaseModel

from langgraph.types import interrupt

from app.agent.llm import llm
from app.agent.state import TripState

from app.tools.scooter_tool import get_scooter_option
from app.tools.currency_tool import convert_to_inr

from app.agent.utils import (
    resolve_user_choice,
    resolve_confirmation,
    resolve_edit_target,
)

from app.models.schemas import (
    TripIntent,
    TransportOption,
    HotelOption,
    DayPlan,
    BudgetItem,
    TripBudget,
)

from app.tools.transport_tool import search_transport
from app.tools.hotel_tool import search_hotels
from app.tools.weather_tool import get_weather_forecast


# ============================================================
# STRUCTURED LLMs
# ============================================================

structured_llm = llm.with_structured_output(TripIntent)


class ItineraryResult(BaseModel):
    days: list[DayPlan]


itinerary_llm = llm.with_structured_output(
    ItineraryResult,
    method="json_schema"
)


# ============================================================
# NODE 1 — PARSE USER INTENT
# ============================================================

def parse_intent(state: TripState) -> TripState:
    """
    Convert the user's natural-language request into
    a structured TripIntent object.
    """

    user_message = state["user_message"]

    prompt = f"""
    Extract the travel details from the user's request.

    User request:
    {user_message}

    Return:
    - origin
    - origin_state_or_region
    - destination
    - destination_state_or_region
    - start_date
    - end_date
    - budget_level
    - num_travelers

    Rules:
    - Dates must be YYYY-MM-DD.
    - If the year is missing, assume 2026.
    - budget_level must be one of:
      budget, moderate, luxury.
    - If budget is not mentioned, use moderate.
    - If number of travelers is not mentioned, use 1.
    - Identify the state or region for the origin and
      destination when possible.
    - If a place name is ambiguous, use the well-known
      intended location.
      Example: "Manali" means Manali, Himachal Pradesh.
    """

    intent = structured_llm.invoke(prompt)

    return {
        "intent": intent,
        "messages": state.get("messages", [])
        + [f"Parsed trip intent: {intent}"]
    }


# ============================================================
# NODE 2 — FIND TRANSPORT
# ============================================================

def find_transport(state: TripState) -> TripState:

    intent = state["intent"]

    options = search_transport(
        intent.origin,
        intent.destination,
        intent.start_date
    )

    options_sorted = sorted(
        options,
        key=lambda o: o.price
    )

    already_tried = state.get(
        "_rejected_transport_names",
        []
    )

    options_sorted = [
        o for o in options_sorted
        if o.name not in already_tried
    ] or options_sorted

    best = options_sorted[0]

    message = (
        f"The cheapest option is {best.name} "
        f"departing {best.departure}, "
        f"arriving {best.arrival}, "
        f"for ₹{best.price}. "
        f"Shall I go ahead with this?"
    )

    user_response = interrupt({
        "question": message,
        "options": [
            o.model_dump()
            for o in options_sorted
        ]
    })

    rejected, index = resolve_user_choice(
        user_response,
        options_sorted,
        context=(
            f"Choosing transport from "
            f"{intent.origin} to "
            f"{intent.destination}. "
            f"Option 0 ({best.name}) is cheapest "
            f"and recommended."
        )
    )

    if rejected:
        return {
            "transport_options": options_sorted,
            "_rejected_transport_names": (
                already_tried + [best.name]
            ),
            "_retry_transport": True,
            "messages": state.get("messages", []) + [
                message,
                f"User rejected: {user_response}"
            ]
        }

    chosen = options_sorted[index]

    return {
        "transport_options": options_sorted,
        "selected_transport": chosen,
        "_retry_transport": False,
        "messages": state.get("messages", []) + [
            message,
            f"User selected: {chosen.name}"
        ]
    }


# ============================================================
# NODE 3 — FIND HOTEL
# ============================================================

def find_hotel(state: TripState) -> TripState:

    intent = state["intent"]

    options = search_hotels(
        destination=intent.destination,
        region=intent.destination_state_or_region,
        check_in=intent.start_date,
        check_out=intent.end_date,
        budget_level=intent.budget_level,
        adults=intent.num_travelers,
    )

    already_tried = state.get(
        "_rejected_hotel_names",
        []
    )

    options = [
        o for o in options
        if o.name not in already_tried
    ]

    if not options:

        message = (
            f"I couldn't find more hotel options in "
            f"{intent.destination}. "
            f"Proceed without a hotel booking?"
        )

        user_response = interrupt({
            "question": message,
            "options": []
        })

        return {
            "hotel_options": [],
            "_retry_hotel": False,
            "messages": state.get("messages", []) + [
                message,
                f"User response: {user_response}"
            ]
        }

    best = max(
        options,
        key=lambda h: h.rating
    )

    options_sorted = (
        [best]
        + [
            o for o in options
            if o != best
        ]
    )

    message = (
        f"I found {best.name} in {best.location} "
        f"for {best.currency} "
        f"{best.price_per_night}/night "
        f"(total {best.currency} "
        f"{best.total_price} "
        f"for {best.nights} nights, "
        f"rated {best.rating}★). "
        f"Shall I book this?"
    )

    user_response = interrupt({
        "question": message,
        "options": [
            o.model_dump()
            for o in options_sorted
        ]
    })

    rejected, index = resolve_user_choice(
        user_response,
        options_sorted,
        context=(
            f"Choosing hotel in "
            f"{intent.destination}. "
            f"Option 0 ({best.name}) is best-rated "
            f"within the {intent.budget_level} "
            f"budget and recommended."
        )
    )

    if rejected:

        return {
            "hotel_options": options_sorted,
            "_rejected_hotel_names": (
                already_tried + [best.name]
            ),
            "_retry_hotel": True,
            "messages": state.get("messages", []) + [
                message,
                f"User rejected: {user_response}"
            ]
        }

    chosen = options_sorted[index]

    return {
        "hotel_options": options_sorted,
        "selected_hotel": chosen,
        "_retry_hotel": False,
        "messages": state.get("messages", []) + [
            message,
            f"User selected: {chosen.name}"
        ]
    }


# ============================================================
# NODE 4 — GENERATE ITINERARY
# ============================================================

def generate_itinerary(state: TripState) -> TripState:
    """
    Generate a day-by-day itinerary using:
    - Trip intent
    - Real weather forecast
    - LLM knowledge of the destination

    Places API is intentionally NOT used here.

    This node only generates the itinerary.
    It does NOT interrupt.
    """

    intent = state["intent"]

    # --------------------------------------------------------
    # Get real weather
    # --------------------------------------------------------

    weather = get_weather_forecast(
        intent.destination,
        intent.start_date,
        intent.end_date
    )

    # --------------------------------------------------------
    # Convert weather into text
    # --------------------------------------------------------

    weather_summary = "\n".join(
        f"{w.date}: {w.condition}, "
        f"{w.temp_min}-{w.temp_max}°C, "
        f"rain likely: {w.rain_likely}"
        for w in weather
    ) or (
        "No forecast available "
        "(trip dates beyond the available "
        "forecast window)."
    )

    # --------------------------------------------------------
    # Calculate number of trip days
    # --------------------------------------------------------

    trip_days = (
        datetime.strptime(
            intent.end_date,
            "%Y-%m-%d"
        )
        -
        datetime.strptime(
            intent.start_date,
            "%Y-%m-%d"
        )
    ).days + 1

    # --------------------------------------------------------
    # LLM prompt
    # --------------------------------------------------------

    prompt = f"""
    You are an expert travel itinerary planner.

    Create a practical {trip_days}-day itinerary for:

    Destination:
    {intent.destination}, {intent.destination_state_or_region}

    Trip dates:
    {intent.start_date} to {intent.end_date}

    Number of travelers:
    {intent.num_travelers}

    Budget level:
    {intent.budget_level}

    Real weather forecast:
    {weather_summary}

    IMPORTANT RULES:

    1. The itinerary MUST be specifically for
       {intent.destination}.

    2. Only suggest real attractions, activities,
       viewpoints, markets, temples, beaches,
       museums, trekking routes, local experiences,
       or other activities that are actually associated
       with {intent.destination}.

    3. Do NOT use attractions from another city,
       even if that city is in the same state or region.

    4. Do NOT invent fake attraction names.

    5. If you are not confident about a specific
       attraction, use a generic activity instead.

    6. Consider the weather when planning outdoor
       activities.

    7. Do not repeat the same attraction on multiple days.

    8. Keep travel between activities practical.

    9. The itinerary should be realistic for the
       number of days.

    10. Do not include hotel booking, transport booking,
        scooter booking, or return journey.
        Those are handled separately.

    11. Keep each day concise with 2-3 activities.

    12. Use the exact dates provided.

    13. For every day, provide:
        - date
        - weather_note
        - activities

    Return the itinerary as structured output.
    """

    # --------------------------------------------------------
    # Generate structured itinerary
    # --------------------------------------------------------

    result: ItineraryResult = itinerary_llm.invoke(
        prompt
    )

    # --------------------------------------------------------
    # Convert DayPlan objects into strings
    # --------------------------------------------------------

    itinerary_lines = [
        f"{day.date}: {', '.join(day.activities)}"
        for day in result.days
    ]

    # --------------------------------------------------------
    # Save itinerary
    # --------------------------------------------------------

    return {
        "itinerary": itinerary_lines,
        "messages": state.get("messages", []) + [
            "Generated draft itinerary:\n"
            + "\n".join(itinerary_lines)
        ]
    }


# ============================================================
# NODE 5 — APPROVE ITINERARY
# ============================================================

def approve_itinerary(state: TripState) -> TripState:
    """
    Show the generated itinerary and ask the user for approval.
    """

    itinerary_lines = state["itinerary"]

    message = (
        "Here's a draft itinerary:\n"
        + "\n".join(itinerary_lines)
    )

    user_response = interrupt({
        "question": (
            message
            + "\n\nDoes this work for you?"
        ),
        "options": []
    })

    confirmed = resolve_confirmation(
        user_response,
        context=(
            "The user is reviewing the proposed "
            "day-by-day trip itinerary. "
            "They can accept it or reject it "
            "and request a different itinerary."
        )
    )

    return {
        "_retry_itinerary": not confirmed,

        "messages": state.get("messages", []) + [
            message,
            f"User response: {user_response} "
            f"→ itinerary_confirmed={confirmed}"
        ]
    }


# ============================================================
# NODE 6 — PLAN LOCAL TRAVEL
# ============================================================

def plan_local_travel(state: TripState) -> TripState:
    """Propose scooter rental for local travel."""

    intent = state["intent"]

    scooter = get_scooter_option(
        intent.start_date,
        intent.end_date
    )

    message = (
        f"Scooter rentals are the most cost-effective way "
        f"to get around {intent.destination}. "
        f"Should I pre-book one at "
        f"₹{scooter.price_per_day}/day "
        f"(~₹{scooter.total_price} "
        f"for {scooter.days} days)?"
    )

    user_response = interrupt({
        "question": message,
        "options": []
    })

    confirmed = resolve_confirmation(
        user_response,
        context=(
            f"Asking whether to book a scooter rental "
            f"for {scooter.days} days in "
            f"{intent.destination}."
        )
    )

    return {
        "scooter_confirmed": confirmed,
        "selected_scooter": (
            scooter if confirmed else None
        ),
        "messages": state.get("messages", []) + [
            message,
            f"User response: {user_response} "
            f"→ confirmed={confirmed}"
        ]
    }


# ============================================================
# NODE 7 — FIND RETURN TRANSPORT
# ============================================================

def find_return_transport(state: TripState) -> TripState:

    intent = state["intent"]

    options = search_transport(
        intent.destination,
        intent.origin,
        intent.end_date
    )

    options_sorted = sorted(
        options,
        key=lambda o: o.price
    )

    already_tried = state.get(
        "_rejected_return_names",
        []
    )

    options_sorted = [
        o for o in options_sorted
        if o.name not in already_tried
    ] or options_sorted

    best = options_sorted[0]

    message = (
        f"For your return on {intent.end_date}, "
        f"the cheapest option is {best.name} "
        f"departing {best.departure} "
        f"for ₹{best.price}. "
        f"Shall I book this?"
    )

    user_response = interrupt({
        "question": message,
        "options": [
            o.model_dump()
            for o in options_sorted
        ]
    })

    rejected, index = resolve_user_choice(
        user_response,
        options_sorted,
        context=(
            f"Choosing return transport from "
            f"{intent.destination} to "
            f"{intent.origin}. "
            f"Option 0 ({best.name}) is cheapest "
            f"and recommended."
        )
    )

    if rejected:
        return {
            "return_options": options_sorted,
            "_rejected_return_names": (
                already_tried + [best.name]
            ),
            "_retry_return": True,
            "messages": state.get("messages", []) + [
                message,
                f"User rejected return transport: "
                f"{user_response}"
            ]
        }

    chosen = options_sorted[index]

    return {
        "return_options": options_sorted,
        "selected_return": chosen,
        "_retry_return": False,
        "messages": state.get("messages", []) + [
            message,
            f"User selected return transport: "
            f"{chosen.name}"
        ]
    }


# ============================================================
# NODE 8 — COMPUTE BUDGET
# ============================================================

def compute_budget(state: TripState) -> TripState:

    items = []

    # --------------------------------------------------------
    # Outbound transport
    # --------------------------------------------------------

    transport = state.get("selected_transport")

    if transport:
        items.append(
            BudgetItem(
                item=f"Transport ({transport.name})",
                cost=transport.price,
            )
        )

    # --------------------------------------------------------
    # Hotel
    # --------------------------------------------------------

    hotel = state.get("selected_hotel")

    if hotel:

        inr_total = convert_to_inr(
            hotel.total_price,
            hotel.currency,
        )

        items.append(
            BudgetItem(
                item=(
                    f"Stay ({hotel.name}, "
                    f"{hotel.nights} nights)"
                ),
                cost=int(inr_total),
            )
        )

    # --------------------------------------------------------
    # Scooter
    # --------------------------------------------------------

    scooter = state.get("selected_scooter")

    if scooter:

        items.append(
            BudgetItem(
                item=f"Scooter ({scooter.days} days)",
                cost=scooter.total_price,
            )
        )

    # --------------------------------------------------------
    # Return transport
    # --------------------------------------------------------

    return_transport = state.get(
        "selected_return"
    )

    if return_transport:

        items.append(
            BudgetItem(
                item=(
                    f"Return "
                    f"({return_transport.name})"
                ),
                cost=return_transport.price,
            )
        )

    # --------------------------------------------------------
    # Calculate total
    # --------------------------------------------------------

    total = sum(
        item.cost
        for item in items
    )

    budget = TripBudget(
        items=items,
        total=total,
    )

    summary_lines = "\n".join(
        f"{item.item}: ₹{item.cost}"
        for item in items
    )

    message = (
        f"Here's your trip budget:\n"
        f"{summary_lines}\n\n"
        f"Total: ₹{total}\n\n"
        f"Shall I finalize the bookings?"
    )

    user_response = interrupt({
        "question": message,
        "options": [],
    })

    confirmed = resolve_confirmation(
        user_response,
        context="Finalizing all trip bookings.",
    )

    # --------------------------------------------------------
    # User accepted
    # --------------------------------------------------------

    if confirmed:

        return {
            "budget": budget,
            "_booking_confirmed": True,
            "_edit_target": None,
            "messages": state.get("messages", []) + [
                message,
                f"User confirmed: {user_response}",
            ],
        }

    # --------------------------------------------------------
    # User rejected
    # --------------------------------------------------------

    followup = (
        "No problem — what would you like to change?\n"
        "Transport, hotel, itinerary, scooter, "
        "or the return journey?\n"
        "Or say 'cancel' to stop planning."
    )

    edit_response = interrupt({
        "question": followup,
        "options": [],
    })

    target = resolve_edit_target(
        edit_response
    )

    return {
        "budget": budget,
        "_booking_confirmed": False,
        "_edit_target": target,
        "messages": state.get("messages", []) + [
            message,
            f"User declined: {user_response}",
            followup,
            f"User wants to edit: {target}",
        ],
    }