from google.adk.agents.llm_agent import Agent
import urllib.request
import json

def get_precipitation(lat: float, lon: float) -> dict:
    """
    Fetches real precipitation data from the NOAA API.

    Returns a dictionary with:
    - short_forecast: brief text description
    - precipitation_chance: probability value (0‑100)
    - confidence: fixed confidence score (0.9)
    """
    headers = {"User-Agent": "pit-wall (capstone-project)"}
    # Step 1 – get the forecast endpoint for the given lat/lon
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    req = urllib.request.Request(points_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        forecast_url = json.load(r)["properties"]["forecast"]

    # Step 2 – fetch the actual forecast data
    req2 = urllib.request.Request(forecast_url, headers=headers)
    with urllib.request.urlopen(req2, timeout=10) as r:
        period = json.load(r)["properties"]["periods"][0]

    return {
        "short_forecast": period["shortForecast"],
        "precipitation_chance": period.get("probabilityOfPrecipitation", {}).get("value", 0),
        "confidence": 0.9,
    }

root_agent = Agent(
    model="groq/llama-3.1-8b-instant",
    name="weather_agent",
    description="Checks live weather using the NOAA API.",
    instruction="You check the weather forecast using the get_precipitation tool. Call it with the latitude and longitude provided.",
    tools=[get_precipitation]
)
