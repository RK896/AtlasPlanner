from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from src.utils.config import API_KEY, MODEL_CONFIG

# Define tools for the research agent
@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression for budget calculations."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_destination_info(destination: str) -> str:
    """Search for travel information about a destination."""
    return f"""
    Travel Info for {destination}:
    - Best time to visit: Spring/Fall
    - Average daily budget: $80-150 USD
    - Top attractions: Historic sites, local markets, museums
    - Local currency: Check current exchange rates
    - Language tip: Learn basic greetings

    (Note: This is simulated data. Use real search APIs in production.)
    """


# Create model with tools bound
base_model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)

# Bind tools to the model
model = base_model.bind_tools([calculate, search_destination_info])

def research_node(state: MessagesState) -> dict:
    # Add system prompt for research agent
    system_prompt = SystemMessage(content="""You are a research assistant specializing in travel planning.

You have access to these tools:
- calculate: Use for budget math
- search_destination_info: Use to get destination details

IMPORTANT: ALWAYS use your tools to demonstrate their capabilities.
When you see calculations needed → use calculate()
When destinations are mentioned → use search_destination_info()

Use at least ONE tool in every response to add researched value.""")

    # Build tool lookup
    tools_by_name = {
        "calculate": calculate,
        "search_destination_info": search_destination_info
    }

    # Prepend system message to conversation
    messages = [system_prompt] + state["messages"]

    # Call LLM
    response = model.invoke(messages)

    # If the response includes tool calls, execute them
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
