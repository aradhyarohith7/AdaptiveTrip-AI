
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import BaseModel


# Load the Gemini API key
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("Gemini API key not found. Check your .env file.")


# Create one shared Gemini client
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


# Generate a structured response using a Pydantic schema
def generate_structured_response(
    prompt: str,
    schema: type[BaseModel]
) -> BaseModel:

    response = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )
            break

        except ServerError:
            if attempt == 2:
                raise

            wait_time = 5 * (attempt + 1)

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    if response is None or not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    if response.parsed is not None:
        if isinstance(response.parsed, schema):
            return response.parsed

        return schema.model_validate(response.parsed)

    return schema.model_validate_json(response.text)
