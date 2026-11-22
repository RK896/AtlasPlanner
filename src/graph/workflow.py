"""The AtlasPlanner graph: a supervisor routing between four specialists.

    START → router ─┬─→ research   ─┐
                    ├─→ flights    ─┤
                    ├─→ hotels     ─┼─→ router (again, until it picks respond)
                    ├─→ activities ─┘
                    └─→ respond → END
"""
from langgraph.graph import END, START, StateGraph

from src.agents.activities import activities_node
from src.agents.flights import flights_node
from src.agents.hotels import hotels_node
from src.agents.master import RESPOND, respond_node, route_from_router, router_node
from src.agents.research import research_node
from src.graph.state import TravelState

SPECIALIST_NODES = {
    "research": research_node,
    "flights": flights_node,
    "hotels": hotels_node,
    "activities": activities_node,
}


def build_graph() -> StateGraph:
    graph = StateGraph(TravelState)
    graph.add_node("router", router_node)
    graph.add_node(RESPOND, respond_node)
    for name, node in SPECIALIST_NODES.items():
        graph.add_node(name, node)
        graph.add_edge(name, "router")  # every specialist reports back to the planner

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_from_router,
        {**{name: name for name in SPECIALIST_NODES}, RESPOND: RESPOND},
    )
    graph.add_edge(RESPOND, END)
    return graph


def compile_app(checkpointer=None):
    """Compile the graph; pass a checkpointer to remember conversations by thread_id."""
    return build_graph().compile(checkpointer=checkpointer)


app = compile_app()
