
import asyncio

from agents.orchestrator import generate_travel_plan


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


async def main():

    result = await generate_travel_plan(sample_trip)

    print("\n========== FINAL RESULTS ==========")

    print("\nBUDGET:")
    print(result["budget"].model_dump_json(indent=2))

    print("\nITINERARY:")
    print(result["itinerary"].model_dump_json(indent=2))

    print("\nREVIEW:")
    print(result["review"].model_dump_json(indent=2))

    print("\nCORRECTION ATTEMPTS:")
    print(result["correction_attempts"])


if __name__ == "__main__":
    asyncio.run(main())
