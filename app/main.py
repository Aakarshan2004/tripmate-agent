from fastapi import FastAPI, HTTPException
from langgraph.types import Command
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import get_graph
from app.models.schemas import (
    StartTripRequest,
    ResumeTripRequest,
    TripResponse,
)


app = FastAPI(title="TripMate Agent API")
app = FastAPI(title="TripMate Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# START NEW TRIP
# ============================================================

@app.post("/trip/start", response_model=TripResponse)
def start_trip(req: StartTripRequest):

    graph = get_graph()

    config = {
        "configurable": {
            "thread_id": req.thread_id
        }
    }

    try:
        result = graph.invoke(
            {
                "user_message": req.message
            },
            config=config
        )

    except Exception as e:
        print("AGENT ERROR:", repr(e))
        raise

    return _build_response(
        req.thread_id,
        result
    )


# ============================================================
# RESUME EXISTING TRIP
# ============================================================

@app.post("/trip/resume", response_model=TripResponse)
def resume_trip(req: ResumeTripRequest):

    graph = get_graph()

    config = {
        "configurable": {
            "thread_id": req.thread_id
        }
    }

    try:
        result = graph.invoke(
            Command(resume=req.message),
            config=config
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )

    return _build_response(
        req.thread_id,
        result
    )


# ============================================================
# BUILD API RESPONSE
# ============================================================

def _build_response(thread_id: str, result: dict) -> TripResponse:
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value

        return TripResponse(
            thread_id=thread_id,
            status="waiting_for_input",
            question=interrupt_data.get("question"),
            options=interrupt_data.get("options", []),
        )

    status = (
        "completed"
        if result.get("_booking_confirmed")
        else "cancelled"
    )

    return TripResponse(
        thread_id=thread_id,
        status=status,
        final_state=_serialize_final_state(result),
    )


# ============================================================
# SERIALIZE PYDANTIC OBJECTS
# ============================================================

def _serialize_final_state(result: dict) -> dict:

    serialized = {}

    for key, value in result.items():

        if hasattr(value, "model_dump"):
            serialized[key] = value.model_dump()

        elif isinstance(value, list):
            serialized[key] = [
                v.model_dump()
                if hasattr(v, "model_dump")
                else v
                for v in value
            ]

        else:
            serialized[key] = value

    return serialized