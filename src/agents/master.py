from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from src.utils.config import API_KEY, MODEL_CONFIG

#create a model instance
model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)

def my_node(state: MessagesState) -> dict:
    #read from state
    messages = state["messages"]
    #call LLM
    response = model.invoke(messages)
    #return messages
    return {"messages": [response]}