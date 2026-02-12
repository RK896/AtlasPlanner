from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from src.utils.config import API_KEY, MODEL_CONFIG
from dotenv import load_dotenv
import os
import requests

load_dotenv()
rapidapi_key = os.getenv("RAPIDAPI_KEY")
rapidapi_host = os.getenv("RAPIDAPI_HOST")
headers = {
    "x-rapidapi-key": rapidapi_key,
    "x-rapidapi-host": rapidapi_host
}


#tools for flights agent
@tool
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

@tool
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




base_model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)
model = base_model.bind_tools([search_roundtrip, search_oneway])

def flights_node(state:MessagesState) -> dict:
    system_prompt = SystemMessage(content="""You a are a flight finding specialist
                                  You have access to these tools:
                                  - search_roundtrip: use to find flights for a roundtrip
                                  - search_oneway: use to find one way flights
                                  """)
    tools_by_name = {
        "search_roundtrip":search_roundtrip,
        "search_oneway": search_oneway
    }

    messages = [system_prompt] + state["messages"]

    response = model.invoke(messages)

    if hasattr(response, 'tool_calls') and response.tool_calls:
        # Execute each tool call
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Execute the tool
            tool_func = tools_by_name[tool_name]
            result = tool_func.invoke(tool_args)

            # Create tool message with result
            tool_messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_call["id"])
            )

        # Call LLM again with tool results to get final answer
        messages_with_tools = messages + [response] + tool_messages
        final_response = model.invoke(messages_with_tools)
        return {"messages": [response] + tool_messages + [final_response]}

    # No tools called - return the response as is
    return {"messages": [response]}
