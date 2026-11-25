
from agents.destination_agent import generate_destination_recommendations
from agents.budget_agent import generate_budget_plan
from agents.itinerary_agent import generate_itinerary_plan


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

print("\nRunning Itinerary Agent...")
itinerary_result = generate_itinerary_plan(
    sample_trip,
    destination_result,
    budget_result
)

print("\nFINAL ITINERARY RESULTS\n")
print(itinerary_result.model_dump_json(indent=2))
