
from uuid import uuid4

from agents.orchestrator import generate_travel_plan


def format_travel_plan(results: dict) -> str:

    destination = results["destination"]
    budget = results["budget"]
    itinerary = results["itinerary"]
    review = results["review"]

    lines = []

    # Itinerary title
    lines.append(f"# {itinerary.title}")
    lines.append("")

    # Daily itinerary
    lines.append("## DAY-BY-DAY ITINERARY")

    for day in itinerary.days:

        lines.append("")
        lines.append(f"### Day {day.day_number} - {day.date}")

        for period in ["morning", "afternoon", "evening"]:

            activities = getattr(day, period)

            lines.append("")
            lines.append(f"**{period.title()}**")

            if not activities:
                lines.append("- No activities planned.")
                continue

            for activity in activities:

                lines.append(f"- **{activity.title}**")
                lines.append(f"  {activity.description}")
                lines.append(f"  Location: {activity.location}")
                lines.append(
                    f"  Estimated activity cost: "
                    f"INR {activity.estimated_cost_inr_total:,.0f}"
                )
                lines.append(
                    f"  Duration: {activity.duration_hours} hours"
                )

    # Budget summary
    lines.append("")
    lines.append("## BUDGET SUMMARY")

    lines.append(
        f"User's budget: INR {budget.total_budget_inr:,.0f}"
    )

    lines.append(
        f"Estimated trip cost: "
        f"INR {budget.estimated_total_cost_inr:,.0f}"
    )

    lines.append(
        f"Daily budget: INR {budget.daily_budget_inr:,.0f}"
    )

    lines.append(
        f"Within budget: {'Yes' if budget.is_within_budget else 'No'}"
    )

    lines.append("")
    lines.append("### Expense Breakdown")

    for allocation in budget.allocations:

        lines.append(
            f"- {allocation.category}: "
            f"INR {allocation.estimated_amount_inr:,.0f}"
        )
        lines.append(f"  {allocation.explanation}")

    # Budget notes
    if budget.notes:

        lines.append("")
        lines.append("### Budget Notes")

        for note in budget.notes:
            lines.append(f"- {note}")

    # Destination recommendations
    lines.append("")
    lines.append("## DESTINATION RECOMMENDATIONS")

    for place in destination.places:

        lines.append(f"- **{place.name}** ({place.category})")
        lines.append(f"  {place.description}")
        lines.append(f"  Area: {place.area}")
        lines.append(
            f"  Estimated cost per person: "
            f"INR {place.estimated_cost_inr_per_person:,.0f}"
        )
        lines.append(
            f"  Visit duration: {place.visit_duration_hours} hours"
        )

    # Review Agent result
    lines.append("")
    lines.append("## AI REVIEW")

    lines.append(
        f"Review status: "
        f"{'Approved' if review.approved else 'Needs Attention'}"
    )

    lines.append(review.summary)

    if review.issues:

        lines.append("")
        lines.append("### Identified Issues")

        for issue in review.issues:

            lines.append(f"- Category: {issue.category}")
            lines.append(f"  Problem: {issue.description}")
            lines.append(
                f"  Suggested correction: {issue.suggested_correction}"
            )

    # Correction attempts
    lines.append("")
    lines.append(
        f"Correction attempts: {results['correction_attempts']}"
    )

    lines.append("")
    lines.append(
        "Note: Costs are estimates, not live-verified prices. "
        "Verify travel schedules, opening hours and availability "
        "before making arrangements."
    )

    return "\n".join(lines)


async def generate_itinerary(trip: dict) -> dict:

    # Run the four-agent Orchestrator
    results = await generate_travel_plan(trip)

    # Format the itinerary for the frontend
    itinerary_text = format_travel_plan(results)

    # Convert structured itinerary into JSON-compatible data
    itinerary_data = results["itinerary"].model_dump(mode="json")

    # Assign a unique ID and lock status to every activity
    for day in itinerary_data["days"]:

        for period in ["morning", "afternoon", "evening"]:

            for activity in day[period]:

                activity["activity_id"] = str(uuid4())
                activity["is_locked"] = False

    # Return both formatted text and structured itinerary data
    return {
        "itinerary": itinerary_text,
        "itinerary_data": itinerary_data,
        "destination": results["destination"].model_dump(mode="json"),
        "budget": results["budget"].model_dump(mode="json"),
        "review": results["review"].model_dump(mode="json"),
        "correction_attempts": results["correction_attempts"]
    }
