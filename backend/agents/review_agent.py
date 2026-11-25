
import json
from datetime import date

from agents.schemas import (
    DestinationAgentResult,
    BudgetAgentResult,
    ItineraryAgentResult,
    ReviewAgentResult
)

from gemini_client import generate_structured_response


def review_travel_plan(
    trip: dict,
    destination_result: DestinationAgentResult,
    budget_result: BudgetAgentResult,
    itinerary_result: ItineraryAgentResult,
    route_context: dict | None = None,
    weather_context: dict | None = None
):

    start_date = date.fromisoformat(trip["startDate"])
    end_date = date.fromisoformat(trip["endDate"])

    expected_days = (end_date - start_date).days + 1

    destination_data = destination_result.model_dump_json(indent=2)
    budget_data = budget_result.model_dump_json(indent=2)
    itinerary_data = itinerary_result.model_dump_json(indent=2)

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
    You are the Review Agent of AdaptiveTrip AI.

    Your responsibility is to inspect a generated travel
    plan, identify problems, and classify whether each
    problem can be fixed by the AI agents or is an
    unavoidable user constraint.

    USER'S TRAVEL DETAILS:

    Origin: {trip["origin"]}
    Destination: {trip["destination"]}
    Departure date: {trip["startDate"]}
    Return date: {trip["endDate"]}
    Expected number of calendar days: {expected_days}
    Total budget: INR {trip["budget"]}
    Number of travellers: {trip["travellers"]}
    Travel style: {trip.get("travelStyle", "Not specified")}
    Interests: {", ".join(trip.get("interests", []))}

    DESTINATION AGENT RESULTS:

    {destination_data}

    BUDGET AGENT RESULTS:

    {budget_data}

    ITINERARY AGENT RESULTS:

    {itinerary_data}

    REAL-WORLD ROUTE INFORMATION:

    {route_data}

    WEATHER INFORMATION:

    {weather_data}

    REVIEW CHECKLIST:

    1. Check whether the itinerary contains exactly
       {expected_days} calendar days.

    2. Check whether the itinerary dates match the
       user's departure and return dates.

    3. Check whether the estimated total itinerary cost
       matches the Budget Agent's estimated total cost
       of INR {budget_result.estimated_total_cost_inr}.

    4. Check whether the estimated total cost exceeds
       the user's budget of INR {trip["budget"]}.

    5. Check whether the activities are relevant to the
       Destination Agent's recommendations.

    6. Identify repeated or duplicate activities.

    7. Check whether the daily schedule is practical.
       Flag days with excessive activity durations.

    8. Look for geographical inconsistencies using the
       available location and area information.

    9. Check whether the itinerary considers the user's
       interests and travel style.

    10. When route information is available, check whether
        the planned inter-city journey is reasonably
        consistent with the supplied driving distance
        and estimated driving duration.

    11. When weather information is available, check
        whether outdoor activities are reasonably planned
        around the forecast conditions.

    ROUTE REVIEW RULES:

    - Use the supplied OSRM route information as a reference.
    - Remember that OSRM duration does not include live traffic.
    - Do not assume the inter-city route distance represents
      distances between individual tourist attractions.
    - Do not invent route distances or travel durations.
    - Do not report missing route information as an error.

    WEATHER REVIEW RULES:

    - Compare itinerary dates only with matching forecast dates.
    - Check whether heavy rain or thunderstorms create
      obvious scheduling concerns for outdoor activities.
    - Do not flag every outdoor activity simply because
      there is a small chance of rain.
    - Do not invent weather conditions for dates without
      forecast information.
    - Do not report unavailable weather forecasts as
      itinerary errors.
    - Remember that destination-level weather may differ
      from the weather at individual attractions.

    ISSUE CLASSIFICATION RULES (CRITICAL):

    For every issue you add to `issues`, you must set:
    - `is_correctable`: true or false
    - `target_agent`: "budget", "itinerary", or "none"

    1. When `is_correctable` MUST be `true`:

       - The itinerary has wrong dates, wrong day count,
         duplicate attractions, or overcrowded daily hours
         (`target_agent`: "itinerary").

       - The itinerary total cost does not match the Budget
         Agent's realistic estimate (`target_agent`: "itinerary").

       - The plan is slightly over budget (e.g., within
         approximately 15-20%) and can realistically be fixed
         by replacing paid tours with free beaches or parks
         or trimming optional expenses
         (`target_agent`: "budget" or "itinerary").

       - Budget category math does not add up properly
         (`target_agent`: "budget").

       - The itinerary ignores available route or weather
         information in a way that creates a practical
         scheduling problem (`target_agent`: "itinerary").

    2. When `is_correctable` MUST be `false`
       (`target_agent`: "none"):

       - The user's total budget of INR {trip["budget"]} is
         fundamentally too low to cover basic inter-city
         transport, accommodation, and food for
         {trip["travellers"]} traveller(s) across
         {expected_days} days, and reducing costs further
         would require faking unrealistic prices.

       - The selected travel style (e.g., Luxury) conflicts
         severely with the available budget.

       - The trip duration ({expected_days} days) is too short
         to realistically travel from {trip["origin"]} to
         {trip["destination"]} and back.

    For every unavoidable issue (`is_correctable`: false), also
    add a clear, helpful explanation with practical alternatives
    (such as increasing the budget, reducing trip days, or
    changing travel style) into `unavoidable_constraints`.

    IMPORTANT REVIEW RULES:

    - Mark `approved` as false if there are ANY issues
      (whether correctable or unavoidable).
    - Never tell the Budget Agent to fake unrealistically low
      hotel or transport prices just to fit an impossible budget.
    - Use category values: budget, schedule, distance,
      duplicate, or requirements.
    - If no problems are found, return empty `issues` and
      `unavoidable_constraints` lists and set `approved` to true.
    - Do not invent actual travel distances or journey times.
    - Do not claim that prices or routes are live verified.
    - Do not invent problems just to fill the review.

    Return the review using the required structured format.
    """

    result = generate_structured_response(
        prompt,
        ReviewAgentResult
    )

    return result
