
from agents.destination_agent import generate_destination_recommendations
from agents.budget_agent import generate_budget_plan
from agents.itinerary_agent import generate_itinerary_plan
from agents.review_agent import review_travel_plan


sample_trip = {
    "origin": "Mysuru",
    "destination": "Goa",
    "startDate": "2026-12-20",
    "endDate": "2026-12-24",
    "budget": 15000,
    "travellers": 2,
    "travelStyle": "Budget-friendly",
    "interests": ["Beaches", "Sightseeing"]
}

print("Running Destination Agent...")
destination_result = generate_destination_recommendations(sample_trip)

print("\nRunning Budget Agent...")
budget_result = generate_budget_plan(sample_trip)

print("\nBUDGET AGENT RESULT:")
print(budget_result.model_dump_json(indent=2))

print("\nRunning Itinerary Agent...")
itinerary_result = generate_itinerary_plan(
    sample_trip,
    destination_result,
    budget_result
)

print("\nRunning Review Agent...")
review_result = review_travel_plan(
    sample_trip,
    destination_result,
    budget_result,
    itinerary_result
)

print("\nREVIEW AGENT RESULTS:")
print(review_result.model_dump_json(indent=2))
