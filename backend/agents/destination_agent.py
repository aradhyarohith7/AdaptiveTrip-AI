
from agents.schemas import DestinationAgentResult
from gemini_client import generate_structured_response


def generate_destination_recommendations(trip: dict):

    interests = trip.get("interests", [])

    prompt = f"""
    You are the Destination Research Agent of AdaptiveTrip AI.

    Your responsibility is to recommend suitable tourist
    attractions and activities for the user's trip.

    TRAVEL DETAILS:

    Starting location: {trip["origin"]}
    Destination: {trip["destination"]}
    Departure date: {trip["startDate"]}
    Return date: {trip["endDate"]}
    Number of travellers: {trip["travellers"]}
    Travel style: {trip["travelStyle"]}
    Interests: {", ".join(interests)}

    YOUR TASK:

    1. Recommend 5 to 8 suitable attractions or activities.
    2. Select places that match the user's interests.
    3. Include a short description of each place.
    4. Mention the area or location of each place.
    5. Estimate the entry or activity cost per person in INR.
    6. Estimate the time needed to visit each place.
    7. Include useful notes about the destination.

    IMPORTANT RULES:

    - Recommend relevant and recognisable places.
    - Avoid recommending the same place more than once.
    - Do not create fictional attractions.
    - Costs must be approximate estimates, not verified prices.
    - If an entry fee is generally free, use zero.
    - Do not claim that opening hours or availability are live verified.
    - Do not create a complete day-wise itinerary.
    - Do not make hotel or transport budget decisions.
    - Focus only on destination research.

    Provide all estimated costs in Indian Rupees (INR).
    """

    result = generate_structured_response(
        prompt,
        DestinationAgentResult
    )

    return result
