
from agents.destination_agent import generate_destination_recommendations

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

print("Testing Destination Agent...")

result = generate_destination_recommendations(sample_trip)

print("\nDESTINATION AGENT RESULTS\n")
print(result.model_dump_json(indent=2))
