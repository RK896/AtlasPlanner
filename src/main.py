from src.graph.workflow import app
from langchain_core.messages import HumanMessage

#create initial state with a user message
initial_state = {
    "messages": [HumanMessage(content="HELLO! Can you help me plan a trip?")]
}

# invoke graph
result = app.invoke(initial_state)

print("\n==== MASTER AGENT ====")
print(result["messages"][1].content)

print("\n==== RESEARCH AGENT ====")
print(result["messages"][2].content)