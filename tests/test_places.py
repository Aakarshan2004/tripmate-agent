from app.tools.places_tool import get_places


places = get_places(
    destination="Goa",
    limit_per_kind=3
)

for place in places:
    print(place)