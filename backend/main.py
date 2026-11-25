
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId
from google.genai.errors import ServerError

from ai_service import generate_itinerary
from database import trips_collection


app = FastAPI(title="AdaptiveTrip AI API")


# Allow communication with React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define the trip information
class TripRequest(BaseModel):
    origin: str
    destination: str
    startDate: str
    endDate: str
    budget: float
    travellers: int
    travelStyle: str
    interests: list[str]


# Backend homepage
@app.get("/")
def home():
    return {
        "message": "AdaptiveTrip AI backend is running!"
    }


# Receive and save trip details
@app.post("/api/trips")
def create_trip(trip: TripRequest):

    trip_data = trip.model_dump()

    trip_data["createdAt"] = datetime.now(timezone.utc)

    try:
        result = trips_collection.insert_one(trip_data)

        return {
            "message": (
                f"Trip from {trip.origin} to "
                f"{trip.destination} saved successfully!"
            ),
            "trip_id": str(result.inserted_id)
        }

    except PyMongoError as error:
        print(f"Trip saving error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to save trip in MongoDB."
        )


# Retrieve saved trips
@app.get("/api/trips")
def get_trips():

    try:
        documents = trips_collection.find().sort(
            "createdAt", -1
        ).limit(20)

        saved_trips = []

        for document in documents:

            document["_id"] = str(document["_id"])

            if "createdAt" in document:
                document["createdAt"] = (
                    document["createdAt"].isoformat()
                )

            if "itineraryGeneratedAt" in document:
                document["itineraryGeneratedAt"] = (
                    document["itineraryGeneratedAt"].isoformat()
                )

            saved_trips.append(document)

        return {
            "trips": saved_trips
        }

    except PyMongoError as error:
        print(f"Trip retrieval error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve saved trips."
        )


# Generate an AI itinerary for a saved trip
@app.post("/api/trips/{trip_id}/generate-itinerary")
async def create_itinerary(trip_id: str):

    try:
        trip_object_id = ObjectId(trip_id)

    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID."
        )

    try:

        # Find the saved trip
        trip = trips_collection.find_one(
            {"_id": trip_object_id}
        )

        if not trip:
            raise HTTPException(
                status_code=404,
                detail="Trip not found."
            )

        # Generate the complete multi-agent travel plan
        generated_plan = await generate_itinerary(trip)

        # Prepare the structured agent results for MongoDB
        ai_plan = {
            "destination": generated_plan["destination"],
            "budget": generated_plan["budget"],
            "review": generated_plan["review"],
            "correction_attempts": generated_plan["correction_attempts"]
        }

        # Save the itinerary, structured activities, and agent results
        trips_collection.update_one(
            {"_id": trip_object_id},
            {
                "$set": {
                    "itinerary": generated_plan["itinerary"],
                    "itineraryData": generated_plan["itinerary_data"],
                    "aiPlan": ai_plan,
                    "itineraryGeneratedAt": datetime.now(timezone.utc)
                }
            }
        )

        return {
            "message": "AI itinerary generated successfully!",
            **generated_plan
        }

    except HTTPException:
        raise

    except ServerError as error:
        print(f"Gemini service error: {error}")

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again."
        )

    except PyMongoError as error:
        print(f"MongoDB itinerary saving error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to save the generated itinerary."
        )

    except Exception as error:
        print(f"Itinerary generation error: {error}")

        raise HTTPException(
            status_code=502,
            detail="Unable to generate itinerary. Please try again."
        )
