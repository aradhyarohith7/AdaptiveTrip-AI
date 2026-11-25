
import json
import time
from difflib import SequenceMatcher
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

HEADERS = {
    "User-Agent": "AdaptiveTripAI/1.0 (educational travel planning project)",
    "Accept": "application/json"
}


# Common spelling variations of Sri Lanka.
LOCATION_ALIASES = {
    "srilnaka": "Sri Lanka",
    "srianka": "Sri Lanka",
    "srilanka": "Sri Lanka",
    "sri lanka": "Sri Lanka"
}


def correct_location_name(place_name):
    """Correct known spelling variations of location names."""

    cleaned_name = place_name.strip().lower()

    if cleaned_name in LOCATION_ALIASES:
        corrected_name = LOCATION_ALIASES[cleaned_name]

        if corrected_name.lower() != cleaned_name:
            print(
                f"Location spelling corrected: "
                f"{place_name} -> {corrected_name}"
            )

        return corrected_name

    return place_name.strip()


def geocode_place(place_name):
    """Find a location and return its coordinates and details."""

    corrected_name = correct_location_name(place_name)

    params = {
        "q": corrected_name,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    url = f"{NOMINATIM_URL}?{urlencode(params)}"
    request = Request(url, headers=HEADERS)

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if not data:
            raise ValueError(
                f"Location not found: {place_name}"
            )

        location = data[0]

        return {
            "name": location["display_name"],
            "searched_name": place_name,
            "corrected_name": corrected_name,
            "latitude": float(location["lat"]),
            "longitude": float(location["lon"]),
            "category": location.get("category"),
            "type": location.get("type"),
            "address": location.get("address", {})
        }

    except HTTPError as error:
        raise RuntimeError(
            f"Location service returned HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to location service: {error.reason}"
        ) from error


def get_route(origin, destination):
    """Calculate driving distance and duration using OSRM."""

    coordinates = (
        f"{origin['longitude']},{origin['latitude']};"
        f"{destination['longitude']},{destination['latitude']}"
    )

    url = f"{OSRM_URL}/{coordinates}?overview=false"
    request = Request(url, headers=HEADERS)

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError("OSRM could not find a driving route.")

        route = data["routes"][0]

        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_hours": round(route["duration"] / 3600, 2),
            "duration_minutes": round(route["duration"] / 60, 1),
            "source": "OSRM",
            "route_type": "Driving",
            "traffic_included": False
        }

    except HTTPError as error:
        raise RuntimeError(
            f"Routing service returned HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to routing service: {error.reason}"
        ) from error


def get_route_between_places(origin_name, destination_name):
    """Find two places and calculate the driving route."""

    origin = geocode_place(origin_name)

    # Respect Nominatim's public service request limit.
    time.sleep(1.1)

    destination = geocode_place(destination_name)

    route = get_route(origin, destination)

    return {
        "origin": origin,
        "destination": destination,
        "route": route
    }


if __name__ == "__main__":

    try:
        result = get_route_between_places(
            "Mysore Palace, Mysuru, Karnataka, India",
            "srilnaka"
        )

        print("\n========== ADAPTIVETRIP AI ROUTE TEST ==========")
        print("Origin:", result["origin"]["name"])
        print("Destination:", result["destination"]["name"])
        print("Original Input:", result["destination"]["searched_name"])
        print("Corrected Input:", result["destination"]["corrected_name"])
        print("Driving Distance:", result["route"]["distance_km"], "km")
        print("Driving Duration:", result["route"]["duration_hours"], "hours")
        print("Route Source:", result["route"]["source"])
        print("===============================================")

    except Exception as error:
        print("\nRoute test failed:", error)
