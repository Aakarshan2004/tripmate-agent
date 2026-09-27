from app.agent.nodes import parse_intent


state = {
    "user_message": "Can you create a budget travel itinerary from Delhi to Goa from 1st to 7th May?"
}


result = parse_intent(state)

print(result["intent"])