from fastmcp import FastMCP
from dotenv import load_dotenv
import os
import requests

mcp = FastMCP('flights')

load_dotenv()
rapidapi_key = os.getenv("RAPIDAPI_KEY")
rapidapi_host = os.getenv("RAPIDAPI_HOST")
headers = {
    "x-rapidapi-key": rapidapi_key,
    "x-rapidapi-host": rapidapi_host
}

#tools for flights agent
@mcp.tool
def search_roundtrip(origin: str, destination:str, departure_date:str, return_date:str) -> str:
    """
    Search for roundtrip flights from origin to destination with given departure and return date.
    """

    url = "https://google-flights4.p.rapidapi.com/flights/search-roundtrip"

    querystring = {
        "departureId": origin,
        "arrivalId": destination,
        "departureDate": departure_date,
        "returnDate": return_date
    }


    response = requests.get(url, headers=headers, params=querystring)
    return f"Flights available: {response.json()}"

@mcp.tool
def search_oneway(origin: str, destination: str, date: str) -> str:
    """Search for one-way flights."""
    url = "https://google-flights4.p.rapidapi.com/flights/search-one-way"
    querystring =  {
        "departureId": origin,
        "arrivalId": destination,
        "departureDate": date
    }
    # Call flights/search-one-way endpoint
    response=requests.get(url, headers=headers, params=querystring)
    return f"Flights available: {response.json()}"
    
# @tool  
# def get_booking_results(booking_id: str) -> str:
#     """Get details for a specific booking."""
#     # Call flights/get-booking-results endpoint

mcp.run()