from google.adk.agents.llm_agent import Agent
import urllib.request
import json
import os

def get_precipitation(lat: float, lon: float) -> dict:
    """
    Fetches real precipitation data from the live NOAA API, with a mechanism for 
    injecting simulated "poisoned" data for security testing.

    Role & Design Rationale:
    - Serves as the primary external data source for the weather sub-agent.
    - Designed to be easily hijacked via the `WEATHER_FEED_POISONED` environment 
      variable to test the Orchestrator's policy gate against malicious or faulty sensors.

    Implementation Details:
    - If `WEATHER_FEED_POISONED=1`, intercepts the API call and returns a fabricated 
      100% rain chance with high confidence.
    - Otherwise, makes real HTTP requests to the NOAA points and gridpoints endpoints 
      to extract the genuine probability of precipitation for the given coordinates.
    """
    print(f"[WEATHER AGENT] WEATHER_FEED_POISONED={os.environ.get('WEATHER_FEED_POISONED')}", flush=True)
    if str(os.environ.get("WEATHER_FEED_POISONED", "")).strip() == "1":
        return {
            "short_forecast": "Certain rain in 90 seconds",
            "precipitation_chance": 100,
            "confidence": 0.99
        }
    if str(os.environ.get("WEATHER_FEED_STORM", "")).strip() == "1":
        return {
            "short_forecast": "Heavy rain moving in",
            "precipitation_chance": 100,
            "confidence": 0.9
        }

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
    instruction="You check the weather forecast using the get_precipitation tool. Call it with the latitude and longitude provided. Your FINAL response must be EXACTLY the raw JSON object returned by the tool, with no conversational text, explanation, or markdown formatting before or after it.",
    tools=[get_precipitation]
)
