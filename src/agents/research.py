from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from src.utils.config import API_KEY, MODEL_CONFIG

model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)

def research_node(state: MessagesState) -> dict:
    # Add system prompt for research agent
    system_prompt = SystemMessage(content="""You are a research assistant specializing in travel planning.
Your job is to ALWAYS provide additional helpful information, research, or suggestions related to the conversation.
Even if the previous message seems complete, add value by providing:
- Destination ideas
- Travel tips
- Seasonal recommendations
- Popular attractions
- Budget insights

NEVER return an empty response. Always contribute something useful.""")

    # Prepend system message to conversation
    messages_with_system = [system_prompt] + state["messages"]

    # Call LLM
    response = model.invoke(messages_with_system)

    # Return response
    return {"messages": [response]}
