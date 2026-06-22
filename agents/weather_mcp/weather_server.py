from fastmcp import FastMCP
import urllib.request, json

mcp = FastMCP("weather-radar")

@mcp.tool()
def get_precipitation(lat: float, lon: float) -> dict:
    headers = {"User-Agent": "pit-wall (capstone-project)"}
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    req = urllib.request.Request(points_url, headers=headers)
    with urllib.request.urlopen(req) as r:
        forecast_url = json.load(r)["properties"]["forecast"]
    req2 = urllib.request.Request(forecast_url, headers=headers)
    with urllib.request.urlopen(req2) as r:
        period = json.load(r)["properties"]["periods"][0]
    return {
        "short_forecast": period["shortForecast"],
        "precipitation_chance": period.get("probabilityOfPrecipitation", {}).get("value", 0),
        "confidence": 0.9
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
