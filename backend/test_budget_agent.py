
from agents.budget_agent import generate_budget_plan

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

print("Testing Budget Agent...")

result = generate_budget_plan(sample_trip)

print("\nBUDGET AGENT RESULTS\n")
print(result.model_dump_json(indent=2))
