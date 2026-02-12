from langgraph.graph import StateGraph, START, END
from src.graph.state import MessagesState
from src.agents.master import my_node
from src.agents.research import research_node
from src.agents.flights import flights_node

#create the graph
graph = StateGraph(MessagesState)

#add nodes and edges
graph.add_node("master", my_node)
graph.add_node("research", research_node)
graph.add_node("flights", flights_node)

def route_after_master(state: MessagesState) -> str:
    """Decide whether to route to research, flights, or end."""
    last_message = state["messages"][-1]
    content = last_message.content.lower() if last_message.content else ""
    
    if "route:research" in content:
        return "research"
    elif "route:flights" in content:
        return "flights"
    else:
        return "end"    


#creates flow START -> master node -> (routing) -> research -> master node -> (routing) -> flights -> master -> END
graph.add_edge(START, "master")
graph.add_edge("research", "master")
graph.add_edge("flights", "master")

# Master decides where to go
graph.add_conditional_edges("master", route_after_master, {
    "research": "research",
    "flights": "flights",
    "end": END
})




app = graph.compile()