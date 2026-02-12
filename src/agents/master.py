from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from src.utils.config import API_KEY, MODEL_CONFIG
from langchain_core.messages import SystemMessage, ToolMessage

#create a model instance
model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)

def my_node(state: MessagesState) -> dict:
    system_prompt = SystemMessage(content="""You are a travel planning agent, who is orchestrating 2 other agents:
                                    Agents available to you:
                                        - Flight Agent, if the user needs a flight search, include route:flights in your response
                                        - Research Agent, if the user needs to research destinations, include route:research in your response
                                    - If the conversation is just casual chat, don't include any ROUTE tag
                                    - Always include the ROUTE tag at the END of your response on its own line.
                                  """)
    #read from state

    messages = [system_prompt] + state["messages"]
    #call LLM
    response = model.invoke(messages)
    #return messages
    return {"messages": [response]}
