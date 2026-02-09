from src.graph.workflow import app
from langchain_core.messages import HumanMessage

#create initial state with a user message
initial_state = {
    "messages": [HumanMessage(content="HELLO! Can you help me plan a trip?")]
}

# invoke graph
result = app.invoke(initial_state)

print("---- Agent Response ----")
print(result["messages"][-1].content)