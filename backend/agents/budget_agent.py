
from datetime import date

from agents.schemas import BudgetAgentResult, ReviewAgentResult
from gemini_client import generate_structured_response


def generate_budget_plan(
    trip: dict,
    previous_result: BudgetAgentResult | None = None,
    review_feedback: ReviewAgentResult | None = None
):

    # Calculate the total number of trip days
    start_date = date.fromisoformat(trip["startDate"])
    end_date = date.fromisoformat(trip["endDate"])

    trip_days = (end_date - start_date).days + 1

    if trip_days <= 0:
        raise ValueError("Return date must be after the departure date.")

    budget = float(trip["budget"])

    if budget <= 0:
        raise ValueError("Travel budget must be greater than zero.")

    # Prepare previous results and review feedback
    previous_budget_data = (
        previous_result.model_dump_json(indent=2)
        if previous_result
        else "No previous budget plan."
    )

    feedback_data = (
        review_feedback.model_dump_json(indent=2)
        if review_feedback
        else "No previous review feedback."
    )

    prompt = f"""
    You are the Budget Planning Agent of AdaptiveTrip AI.

    Your responsibility is to plan realistic estimated travel
    expenses based on the user's budget and travel requirements.

    TRAVEL DETAILS:

    Starting location: {trip["origin"]}
    Destination: {trip["destination"]}
    Departure date: {trip["startDate"]}
    Return date: {trip["endDate"]}
    Total trip duration: {trip_days} calendar days
    Total budget: INR {budget}
    Number of travellers: {trip["travellers"]}
    Travel style: {trip["travelStyle"]}
    Interests: {", ".join(trip.get("interests", []))}

    PREVIOUS BUDGET PLAN:

    {previous_budget_data}

    REVIEW AGENT FEEDBACK:

    {feedback_data}

    When previous review feedback is provided, carefully
    revise the budget plan to address the identified issues.

    Do not artificially reduce expenses just to fit the budget.
    If the trip cannot realistically fit the budget, explain why.

    YOUR TASK:

    1. Estimate the overall travel cost for the entire group.
    2. Divide expenses into these categories:
       - Transportation between the starting location and destination
       - Accommodation
       - Food
       - Local transportation
       - Activities and attractions
       - Miscellaneous expenses
    3. Estimate the amount needed for each category.
    4. Calculate the daily budget by dividing the user's
       total budget by the number of trip days.
    5. Compare the estimated total expenses with the user's budget.
    6. Set is_within_budget to true only when the estimated
       total cost does not exceed the user's budget.
    7. If the budget is insufficient, explain why and suggest
       practical ways to reduce expenses.

    IMPORTANT RULES:

    - All amounts must be in Indian Rupees (INR).
    - Calculate expenses for all travellers together,
      not for just one person.
    - The category allocations should approximately add up
      to the estimated total cost.
    - Do not invent artificially low prices to fit the budget.
    - Consider the selected travel style.
    - Costs must be approximate estimates, not verified prices.
    - Do not claim that bookings or availability are verified.
    - Do not create a day-wise travel itinerary.
    - Focus only on budget planning.

    Return the budget plan using the required structured format.
    """

    result = generate_structured_response(
        prompt,
        BudgetAgentResult
    )

    return result
