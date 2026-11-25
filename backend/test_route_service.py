
from services.route_service import get_route_between_places


test_routes = [
    ("Mysuru, Karnataka, India", "Goa, India"),
    ("North Goa, India", "South Goa, India"),
    ("Goa, India", "Gokarna, Karnataka, India")
]


for origin, destination in test_routes:

    print("\n===================================")
    print(f"Testing: {origin} -> {destination}")
    print("===================================")

    try:
        result = get_route_between_places(origin, destination)

        route = result["route"]

        print("Distance:", route["distance_km"], "km")
        print("Driving Duration:", route["duration_hours"], "hours")
        print("Source:", route["source"])

    except Exception as error:
        print("Route test failed:", error)
