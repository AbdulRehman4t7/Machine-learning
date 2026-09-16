"""Wires the agents together into the LangGraph workflow."""

from langgraph.graph import END, START, StateGraph

from src.agents.final_agent import final_agent
from src.agents.flight_agent import flight_agent
from src.agents.hotel_agent import hotel_agent
from src.agents.itinerary_agent import itinerary_agent
from src.agents.weather_agent import weather_agent
from src.clients.checkpointer import get_checkpointer
from src.graph.state import TravelState


def build_graph() -> StateGraph:
    """Build the uncompiled graph. Useful for tests and for visualisation."""

    graph = StateGraph(TravelState)

    graph.add_node("flight_agent", flight_agent)
    graph.add_node("hotel_agent", hotel_agent)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("itinerary_agent", itinerary_agent)
    graph.add_node("final_agent", final_agent)

    graph.add_edge(START, "flight_agent")
    graph.add_edge("flight_agent", "hotel_agent")
    graph.add_edge("hotel_agent", "weather_agent")
    graph.add_edge("weather_agent", "itinerary_agent")
    graph.add_edge("itinerary_agent", "final_agent")
    graph.add_edge("final_agent", END)

    return graph


# Compiled once with the shared in-memory checkpointer
_compiled_graph = None


def get_travel_graph():
    """
    Return the compiled graph using MemorySaver (no database needed).
    The graph is compiled once and reused for all requests.
    """
    global _compiled_graph

    if _compiled_graph is None:
        _compiled_graph = build_graph().compile(checkpointer=get_checkpointer())

    return _compiled_graph

