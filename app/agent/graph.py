from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from app.agent.state import TripState

from app.agent.nodes import (
    parse_intent,
    find_transport,
    find_hotel,
    generate_itinerary,
    approve_itinerary,
    plan_local_travel,
    find_return_transport,
    compute_budget,
)


def route_after_transport(state: TripState) -> str:
    if state.get("_retry_transport"):
        return "find_transport"

    return "find_hotel"


def route_after_hotel(state: TripState) -> str:
    if state.get("_retry_hotel"):
        return "find_hotel"

    return "generate_itinerary"

def route_after_itinerary(state: TripState) -> str:
    if state.get("_retry_itinerary"):
        return "generate_itinerary"

    return "plan_local_travel"


def route_after_return(state: TripState) -> str:
    if state.get("_retry_return"):
        return "find_return_transport"

    return "compute_budget"


def route_after_budget(state: TripState) -> str:
    # User confirmed final booking
    if state.get("_booking_confirmed"):
        return END

    target = state.get("_edit_target")

    mapping = {
        "transport": "find_transport",
        "hotel": "find_hotel",
        "itinerary": "generate_itinerary",
        "scooter": "plan_local_travel",
        "return": "find_return_transport",
        "cancel": END,
    }

    return mapping.get(target, END)


def build_graph():
    builder = StateGraph(TripState)

    # --------------------------------------------------------
    # ADD NODES
    # --------------------------------------------------------

    builder.add_node(
        "parse_intent",
        parse_intent
    )

    builder.add_node(
        "find_transport",
        find_transport
    )

    builder.add_node(
        "find_hotel",
        find_hotel
    )

    builder.add_node(
        "generate_itinerary",
        generate_itinerary
    )

    # Separate approval node
    builder.add_node(
        "approve_itinerary",
        approve_itinerary
    )

    builder.add_node(
        "plan_local_travel",
        plan_local_travel
    )

    builder.add_node(
        "find_return_transport",
        find_return_transport
    )

    builder.add_node(
        "compute_budget",
        compute_budget
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    builder.add_edge(
        START,
        "parse_intent"
    )

    # --------------------------------------------------------
    # PARSE → TRANSPORT
    # --------------------------------------------------------

    builder.add_edge(
        "parse_intent",
        "find_transport"
    )

    # --------------------------------------------------------
    # TRANSPORT → HOTEL
    # --------------------------------------------------------

    builder.add_conditional_edges(
        "find_transport",
        route_after_transport,
        [
            "find_transport",
            "find_hotel"
        ]
    )

    # --------------------------------------------------------
    # HOTEL → ITINERARY GENERATION
    # --------------------------------------------------------

    builder.add_conditional_edges(
        "find_hotel",
        route_after_hotel,
        [
            "find_hotel",
            "generate_itinerary"
        ]
    )

    # --------------------------------------------------------
    # ITINERARY GENERATION → APPROVAL
    # --------------------------------------------------------

    builder.add_edge(
        "generate_itinerary",
        "approve_itinerary"
    )

    # --------------------------------------------------------
    # APPROVAL → LOCAL TRAVEL
    # --------------------------------------------------------

    builder.add_conditional_edges(
    "approve_itinerary",
    route_after_itinerary,
    [
        "generate_itinerary",
        "plan_local_travel",
    ]
)
    # --------------------------------------------------------
    # LOCAL TRAVEL → RETURN TRANSPORT
    # --------------------------------------------------------

    builder.add_edge(
        "plan_local_travel",
        "find_return_transport"
    )

    # --------------------------------------------------------
    # RETURN TRANSPORT → BUDGET
    # --------------------------------------------------------

    builder.add_conditional_edges(
        "find_return_transport",
        route_after_return,
        [
            "find_return_transport",
            "compute_budget"
        ]
    )

    # --------------------------------------------------------
    # BUDGET → EDIT / END
    # --------------------------------------------------------

    builder.add_conditional_edges(
        "compute_budget",
        route_after_budget,
        [
            "find_transport",
            "find_hotel",
            "generate_itinerary",
            "plan_local_travel",
            "find_return_transport",
            END,
        ]
    )

    # ========================================================
    # CHECKPOINT SERIALIZATION
    # ========================================================

    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("app.models.schemas", "TripIntent"),
            ("app.models.schemas", "TransportOption"),
            ("app.models.schemas", "HotelOption"),
            ("app.models.schemas", "BudgetItem"),
            ("app.models.schemas", "TripBudget"),
            ("app.models.schemas", "WeatherDay"),
            ("app.models.schemas", "Place"),
            ("app.models.schemas", "DayPlan"),
            ("app.models.schemas", "ScooterOption"),
        ]
    )

    checkpointer = InMemorySaver(
        serde=serde
    )

    return builder.compile(
        checkpointer=checkpointer
    )


# ============================================================
# GRAPH SINGLETON
# ============================================================

_graph_instance = None


def get_graph():
    global _graph_instance

    if _graph_instance is None:
        _graph_instance = build_graph()

    return _graph_instance