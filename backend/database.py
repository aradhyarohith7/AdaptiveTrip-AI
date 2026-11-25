
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Connect to the local MongoDB server
MONGO_URL = "mongodb://localhost:27017/"

client = MongoClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000
)

# Check whether MongoDB is reachable
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")

except PyMongoError as error:
    raise RuntimeError(f"MongoDB connection failed: {error}")

# Select our database and collection
db = client["AdaptiveTripDB"]
trips_collection = db["trips"]
