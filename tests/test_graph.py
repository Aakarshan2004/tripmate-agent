from langgraph.types import Command
from app.agent.graph import build_graph


graph = build_graph()


# ============================================================
# TEST 1 — TRANSPORT REJECTION / LOOPBACK
# ============================================================

retry_config = {
    "configurable": {
        "thread_id": "transport-retry-test"
    }
}


# Start trip → first transport pause
result = graph.invoke(
    {
        "user_message": (
            "Can you create a budget travel itinerary "
            "from Delhi to Goa from 1st to 7th October 2026?"
        )
    },
    config=retry_config
)

print(
    "\nPAUSE 1:",
    result["__interrupt__"][0].value["question"]
)


# Reject recommended transport
result = graph.invoke(
    Command(resume="none of these, show me something else"),
    config=retry_config
)

print(
    "\nPAUSE 2 (TRANSPORT RETRY):",
    result["__interrupt__"][0].value["question"]
)


# Accept new transport
result = graph.invoke(
    Command(resume="ok fine i'll take this one"),
    config=retry_config
)

print(
    "\nSelected transport:",
    result["selected_transport"]
)


# ============================================================
# TEST 2 — HOTEL REJECTION / LOOPBACK
# ============================================================

# Reject recommended hotel
result = graph.invoke(
    Command(resume="none of these, show me another hotel"),
    config=retry_config
)

print(
    "\nPAUSE 3 (HOTEL RETRY):",
    result["__interrupt__"][0].value["question"]
)


# If no unseen hotel exists, proceed without hotel
result = graph.invoke(
    Command(resume="yes, proceed without hotel"),
    config=retry_config
)

print(
    "\nHotel step completed."
)


# ============================================================
# TEST 3 — ITINERARY
# ============================================================

result = graph.invoke(
    Command(resume="looks great"),
    config=retry_config
)

print("\nItinerary:")
print("\n".join(result["itinerary"]))


# ============================================================
# TEST 4 — SCOOTER
# ============================================================

result = graph.invoke(
    Command(resume="yeah sure why not"),
    config=retry_config
)

print("\nScooter confirmed:", result["scooter_confirmed"])
print("Scooter details:", result["selected_scooter"])


# ============================================================
# TEST 5 — RETURN TRANSPORT
# ============================================================

# Scooter confirmation resumes the graph.
# Graph reaches return transport interrupt.
result = graph.invoke(
    Command(resume="take the cheapest one"),
    config=retry_config
)

print(
    "\nPAUSE 4 (BUDGET):",
    result["__interrupt__"][0].value["question"]
)


# ============================================================
# TEST 6 — FINAL BUDGET CONFIRMATION
# ============================================================

result = graph.invoke(
    Command(resume="yes finalize it"),
    config=retry_config
)

print("\nFinal Budget:")
print(result["budget"])