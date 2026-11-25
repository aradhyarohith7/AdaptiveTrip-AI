
import json
from datetime import date

from agents.schemas import (
    DestinationAgentResult,
    BudgetAgentResult,
    ItineraryAgentResult,
    ReviewAgentResult
)

from gemini_client import generate_structured_response


def generate_itinerary_plan(
    trip: dict,
    destination_result: DestinationAgentResult,
    budget_result: BudgetAgentResult,
    previous_result: ItineraryAgentResult | None = None,
    review_feedback: ReviewAgentResult | None = None,
    route_context: dict | None = None,
    weather_context: dict | None = None
):

    start_date = date.fromisoformat(trip["startDate"])
    end_date = date.fromisoformat(trip["endDate"])

    trip_days = (end_date - start_date).days + 1

    if trip_days <= 0:
        raise ValueError("Return date must be after the departure date.")

    # Convert agent results into JSON.
    destination_data = destination_result.model_dump_json(indent=2)
    budget_data = budget_result.model_dump_json(indent=2)

    previous_itinerary_data = (
        previous_result.model_dump_json(indent=2)
        if previous_result
        else "No previous itinerary."
    )

    feedback_data = (
        review_feedback.model_dump_json(indent=2)
        if review_feedback
        else "No previous review feedback."
    )

    # Convert external travel information into JSON.
    route_data = (
        json.dumps(route_context, indent=2, ensure_ascii=False)
        if route_context
        else "Route information is not available."
    )

    weather_data = (
        json.dumps(weather_context, indent=2, ensure_ascii=False)
        if weather_context
        else "Weather information is not available."
    )

    prompt = f"""
    You are the Itinerary Planning Agent of AdaptiveTrip AI.

    Your responsibility is to create a practical,
    personalised, day-by-day travel itinerary.

    TRAVEL DETAILS:

    Origin: {trip["origin"]}
    Destination: {trip["destination"]}
    Departure: {trip["startDate"]}
    Return: {trip["endDate"]}
    Total days: {trip_days}
    Travellers: {trip["travellers"]}
    Travel style: {trip["travelStyle"]}
    Interests: {", ".join(trip.get("interests", []))}

    DESTINATION AGENT RESULTS:

    {destination_data}

    BUDGET AGENT RESULTS:

    {budget_data}

    REAL-WORLD ROUTE INFORMATION:

    {route_data}

    :

    {weather_data}

    PREVIOUS ITINERARY:

    {previous_itinerary_data}

    REVIEW AGENT FEEDBACK:

    {feedback_data}

    WHEN REVIEW FEEDBACK IS PROVIDED:

    - Correct the specific problems identified by the Review Agent.
    - Preserve activities that do not need correction.
    - Correct unrealistic travel durations and scheduling issues.
    - Respect the latest Budget Agent results.
    - Do not simply ignore review feedback.

    
    ROUTE PLANNING RULES:

    - Use the supplied OSRM driving distance and duration to plan inter-city travel.
    - Treat OSRM duration as a driving estimate, not a confirmed bus or train journey time.
    - Do not claim that OSRM provides live traffic information.
    - Allow reasonable additional time for breaks, delays and arrival activities.
    - On arrival days, account for the long journey before scheduling sightseeing.
    - Do not schedule a full day of sightseeing immediately after a long inter-city journey.
    - Keep arrival-day activities light and allow reasonable time for rest and check-in.
    - On departure days, prioritise the return journey and avoid scheduling activities that could delay departure.
    - Do not schedule sightseeing during the estimated inter-city travel period.
    - Do not assume the supplied route represents distances between individual tourist attractions.
    - Do not invent additional verified distances or journey times.
    - If route information is insufficient, clearly mention the limitation in the planning notes.
    
    
    DEPARTURE DAY RULES:

    - When a long inter-city return journey is required, prioritise the return journey over sightseeing.
    - Do not schedule tourist attractions or beach visits before a long return journey on the departure day.
    - Keep the return journey as one complete activity using the supplied route duration.
    - Never split one estimated route duration into multiple invented journey segments.
    - Do not invent separate travel durations to fill morning, afternoon or evening slots.
    - Allow reasonable time for checkout, preparation and travel delays.
    - If the trip duration is too short for both sightseeing and realistic return travel, clearly mention this limitation.
    - Do not sacrifice realistic travel planning just to fill all three time slots.



WEATHER PLANNING RULES:

- Check the weather forecast separately for every itinerary date.
- Consider the forecast condition, rain probability, and precipitation amount when selecting and scheduling activities.
- Prefer indoor sightseeing and flexible activities when moderate or heavy rain or thunderstorms are forecast.
- Prefer outdoor activities on days with clearer and more suitable weather.
- Light drizzle or a low chance of rain should not automatically prevent beach visits or outdoor sightseeing.
- When outdoor activities are planned during rainy conditions, mention that the activity is weather-dependent and should be checked before visiting.
- If multiple days have different weather conditions, distribute outdoor and indoor activities accordingly.
- Do not schedule all outdoor activities on a day with the highest expected rainfall when better alternatives exist.
- Do not automatically cancel activities because of moderate rain.
- Do not invent indoor alternatives or attractions that were not recommended by the Destination Agent.
- Use weather information only for dates actually present in the supplied forecast.
- Do not invent weather conditions for missing dates.
- Remember that a destination-level forecast may not describe the exact weather at every attraction.
- Make weather-related scheduling decisions practical and explain them briefly in the activity descriptions or planning notes.



COST RULES:

- The Budget Agent estimated the total trip cost as INR {budget_result.estimated_total_cost_inr}.
- Use this exact amount as the itinerary's estimated_total_cost_inr.
- Activity costs must include only additional activity-specific expenses for all travellers, such as entry fees, tickets and paid experiences.
- Never include inter-city transportation costs in individual activity costs.
- Never include accommodation or regular food expenses in individual activity costs.
- Transportation, accommodation and food must remain in the Budget Agent's expense breakdown.
- For travel activities such as arrival and departure, set estimated activity cost to INR 0.
- Do not count any expense twice.
- Do not change the Budget Agent's estimated total when creating the itinerary.


    IMPORTANT RULES:

    - Include exactly {trip_days} days.
    - Use dates in YYYY-MM-DD format.
    - Use only relevant recommended places.
    - Do not invent attractions.
    - Do not claim that bookings have been made.
    - Do not claim that routes include live traffic.
    - Do not invent unavailable weather information.
    - Keep the plan realistic and practical.

    Return the itinerary using the required structured format.
    """

    result = generate_structured_response(
        prompt,
        ItineraryAgentResult
    )

    return result
