import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from core.config import get_database_url
from graph.state import TravelState
from graph.nodes import flight_agent, hotel_agent, itinerary_agent, final_agent


def build_graph():
    g = StateGraph(TravelState)

    g.add_node("flight_agent", flight_agent)
    g.add_node("hotel_agent", hotel_agent)
    g.add_node("itinerary_agent", itinerary_agent)
    g.add_node("final_agent", final_agent)

    g.add_edge(START, "flight_agent")
    g.add_edge("flight_agent", "hotel_agent")
    g.add_edge("hotel_agent", "itinerary_agent")
    g.add_edge("itinerary_agent", "final_agent")
    g.add_edge("final_agent", END)

    return g


def create_travel_graph():
    database_url = get_database_url()
    conn = psycopg.connect(
        database_url,
        autocommit=True,
        row_factory=dict_row,
        sslmode="disable",
    )
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


# Module-level compiled graph (initialised once on import)
travel_graph = create_travel_graph()
