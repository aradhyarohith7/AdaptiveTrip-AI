
import asyncio
from google.genai.errors import ServerError

from agents.destination_agent import generate_destination_recommendations
from agents.budget_agent import generate_budget_plan
from agents.itinerary_agent import generate_itinerary_plan
from agents.review_agent import review_travel_plan

from services.route_service import (
    get_route_between_places,
    geocode_place
)
from services.weather_service import get_weather


MAX_CORRECTION_ATTEMPTS = 2


async def generate_travel_plan(trip: dict):

    print("\nStarting AdaptiveTrip AI Orchestrator...")

    # STEP 1: Run Destination and Budget Agents in parallel
    print("\nRunning Destination and Budget Agents in parallel...")

    destination_task = asyncio.to_thread(
        generate_destination_recommendations,
        trip
    )

    budget_task = asyncio.to_thread(
        generate_budget_plan,
        trip
    )

    destination_result, budget_result = await asyncio.gather(
        destination_task,
        budget_task
    )

    print("Destination Agent completed.")
    print("Budget Agent completed.")

    # STEP 2: Fetch real-world route information
    route_context = None
    weather_context = None

    print("\nFetching real-world route information...")

    try:
        route_context = await asyncio.to_thread(
            get_route_between_places,
            trip["origin"],
            trip["destination"]
        )

        print("Route information retrieved successfully.")
        print(
            "Driving distance:",
            route_context["route"]["distance_km"],
            "km"
        )
        print(
            "Estimated driving duration:",
            route_context["route"]["duration_hours"],
            "hours"
        )

    except Exception as error:
        print("\nRoute information unavailable.")
        print("Reason:", error)

    # STEP 3: Fetch weather information for the trip dates
    print("\nFetching destination weather information...")

    try:
        if route_context:
            destination_location = route_context["destination"]

        else:
            # If route retrieval failed, find destination coordinates separately.
            await asyncio.sleep(1.1)

            destination_location = await asyncio.to_thread(
                geocode_place,
                trip["destination"]
            )

        weather_context = await asyncio.to_thread(
            get_weather,
            destination_location["latitude"],
            destination_location["longitude"],
            start_date=trip["startDate"],
            end_date=trip["endDate"]
        )

        if weather_context["available"]:
            print("Weather information retrieved successfully.")
            print("\nWeather forecast details:")
            for day in weather_context["forecast"]:
                print(day)
            print(
                "Forecast coverage:",
                weather_context["coverage_start"],
                "to",
                weather_context["coverage_end"]
            )
            print(
                "Full weather coverage:",
                weather_context["full_coverage"]
            )

            if weather_context["missing_dates"]:
                print(
                    "Weather unavailable for:",
                    weather_context["missing_dates"]
                )

        else:
            print("Weather forecast is unavailable for the trip dates.")
            print(weather_context["message"])

    except Exception as error:
        print("\nWeather information unavailable.")
        print("Reason:", error)

    # STEP 4: Generate the initial itinerary
    print("\nRunning Itinerary Agent...")

    itinerary_result = await asyncio.to_thread(
        generate_itinerary_plan,
        trip,
        destination_result,
        budget_result,
        route_context=route_context,
        weather_context=weather_context
    )

    # STEP 5: Review the initial itinerary
    print("\nRunning Review Agent...")

    review_result = await asyncio.to_thread(
        review_travel_plan,
        trip,
        destination_result,
        budget_result,
        itinerary_result,
        route_context=route_context,
        weather_context=weather_context
    )

    # STEP 6: Smart correction loop (only for correctable issues)
    correction_attempts = 0
    correction_history = []

    while (
        not review_result.approved
        and correction_attempts < MAX_CORRECTION_ATTEMPTS
    ):
        correctable_issues = [
            issue for issue in review_result.issues if issue.is_correctable
        ]

        unavoidable_issues = [
            issue for issue in review_result.issues if not issue.is_correctable
        ]

        # Stop immediately if there are no correctable issues left
        if not correctable_issues:
            print(
                "\nUnavoidable user constraints detected. "
                "Stopping correction loop so realistic costs are preserved."
            )
            correction_history.append(
                "Stopped automatic correction because remaining issues are unavoidable user constraints."
            )
            break

        correction_attempts += 1

        print(
            f"\nCorrection attempt "
            f"{correction_attempts}/{MAX_CORRECTION_ATTEMPTS} "
            f"for {len(correctable_issues)} correctable issue(s)..."
        )

        needs_budget_correction = any(
            issue.target_agent == "budget"
            or issue.category.lower() == "budget"
            for issue in correctable_issues
        )

        needs_itinerary_correction = any(
            issue.target_agent == "itinerary"
            or issue.category.lower() in {
                "schedule",
                "distance",
                "duplicate",
                "requirements"
            }
            for issue in correctable_issues
        )

        # Fallback if an issue was marked correctable without a specific target
        if not needs_budget_correction and not needs_itinerary_correction:
            needs_itinerary_correction = True

        try:
            # STEP 6A: Correct the budget if necessary
            if needs_budget_correction:
                print("\nRequesting Budget Agent correction...")

                previous_budget_result = budget_result

                budget_result = await asyncio.to_thread(
                    generate_budget_plan,
                    trip,
                    previous_budget_result,
                    review_result
                )

                print("Budget Agent correction completed.")

                correction_history.append(
                    f"Attempt {correction_attempts}: Revised budget allocations."
                )

                # A changed budget requires updating the itinerary
                needs_itinerary_correction = True

            # STEP 6B: Correct the itinerary if necessary
            if needs_itinerary_correction:
                print("\nRequesting Itinerary Agent correction...")

                previous_itinerary_result = itinerary_result

                itinerary_result = await asyncio.to_thread(
                    generate_itinerary_plan,
                    trip,
                    destination_result,
                    budget_result,
                    previous_itinerary_result,
                    review_result,
                    route_context=route_context,
                    weather_context=weather_context
                )

                print("Itinerary Agent correction completed.")

                correction_history.append(
                    f"Attempt {correction_attempts}: Revised day-by-day itinerary."
                )

            # STEP 6C: Review the corrected plan again
            print("\nReviewing corrected travel plan...")

            review_result = await asyncio.to_thread(
                review_travel_plan,
                trip,
                destination_result,
                budget_result,
                itinerary_result,
                route_context=route_context,
                weather_context=weather_context
            )

        except ServerError as error:
            print(
                "\nGemini is temporarily unavailable during correction."
            )
            print(f"Error: {error}")
            print(
                "Keeping the last successfully generated "
                "travel plan and review results."
            )

            correction_history.append(
                f"Attempt {correction_attempts}: Stopped early due to temporary Gemini server error (503)."
            )
            break

    # Safety check: Never mark an unresolved plan as approved
    if review_result.issues or review_result.unavoidable_constraints:
        review_result.approved = False

    # STEP 7: Return the final results
    if review_result.approved:
        print("\nTravel plan approved!")
    else:
        print(
            "\nTravel plan finished with unresolved constraints/issues after "
            f"{correction_attempts} correction attempt(s)."
        )

    return {
        "destination": destination_result,
        "budget": budget_result,
        "itinerary": itinerary_result,
        "review": review_result,
        "correction_attempts": correction_attempts,
        "correction_history": correction_history
    }
