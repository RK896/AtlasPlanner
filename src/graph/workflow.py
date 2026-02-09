from langgraph.graph import StateGraph, START, END
from src.graph.state import MessagesState
from src.agents.master import my_node

#create the graph
graph = StateGraph(MessagesState)

#add nodes and edges
graph.add_node("master", my_node)

#creates flow START -> master node -> END
graph.add_edge(START, "master")
graph.add_edge("master", END)

app = graph.compile()