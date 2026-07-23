import uuid

from langchain_core.messages import HumanMessage
from fastapi import HTTPException

from core.database import get_db_connection
from graph.builder import travel_graph


def _upsert_session(session_id: str, user_id: int, title: str) -> None:
    """Save or update a session record for the user."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_sessions (id, user_id, title, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE
                    SET title = EXCLUDED.title,
                        updated_at = NOW()
                """,
                (session_id, user_id, title),
            )
        conn.commit()


def _assert_session_owner(session_id: str, user_id: int) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM user_sessions WHERE id = %s",
                (session_id,),
            )
            row = cur.fetchone()

    if row and row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user.")


def _save_session_answer(session_id: str, user_id: int, answer: str) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_sessions
                SET last_answer = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
                """,
                (answer, session_id, user_id),
            )
        conn.commit()


def run_travel_agent(
    user_input: str,
    user_id: int,
    session_id: str | None = None,
) -> dict:
    if not session_id:
        session_id = uuid.uuid4().hex
    else:
        _assert_session_owner(session_id, user_id)

    # Persist / refresh session with the query as title
    title = user_input[:80].strip()
    _upsert_session(session_id, user_id, title)

    config = {"configurable": {"thread_id": session_id}}

    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )

    final_answer = result["messages"][-1].content
    _save_session_answer(session_id, user_id, final_answer)

    return {
        "session_id": session_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }


def list_user_sessions(user_id: int) -> list[dict]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM user_sessions
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    return [
        {
            "session_id": r["id"],
            "title": r["title"],
            "created_at": r["created_at"].isoformat(),
            "updated_at": r["updated_at"].isoformat(),
        }
        for r in rows
    ]


def get_user_session_detail(session_id: str, user_id: int) -> dict | None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, last_answer, created_at, updated_at
                FROM user_sessions
                WHERE id = %s AND user_id = %s
                """,
                (session_id, user_id),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "session_id": row["id"],
        "title": row["title"],
        "answer": row.get("last_answer", "") or "",
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def delete_user_session(session_id: str, user_id: int) -> bool:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_sessions WHERE id = %s AND user_id = %s",
                (session_id, user_id),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted
