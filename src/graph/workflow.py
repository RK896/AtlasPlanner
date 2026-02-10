from langgraph.graph import StateGraph, START, END
from src.graph.state import MessagesState
from src.agents.master import my_node
from src.agents.research import research_node

#create the graph
graph = StateGraph(MessagesState)

#add nodes and edges
graph.add_node("master", my_node)
graph.add_node("research", research_node)
#creates flow START -> master node -> (routing) -> research -> END
graph.add_edge(START, "master")

def route_after_master(state: MessagesState) -> str:
    """Decide whether to route to research or end."""
    return "research"

graph.add_conditional_edges(
    "master",
    route_after_master,
    {
        "research":"research",
        "end": END
    }
)
graph.add_edge("research", END)

app = graph.compile()