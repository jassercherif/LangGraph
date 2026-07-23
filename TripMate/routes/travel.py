import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from schemas.travel import TravelRequest
from services.auth_service import get_current_user
from services.travel_service import (
    delete_user_session,
    get_user_session_detail,
    list_user_sessions,
    run_travel_agent,
)

router = APIRouter()


@router.post("/api/travel")
async def travel_planner(
    request_data: TravelRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        user_message = request_data.message.strip()
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty."},
            )

        result = run_travel_agent(
            user_input=user_message,
            user_id=current_user["user_id"],
            session_id=request_data.session_id,
        )

        return JSONResponse(
            content={
                "success": True,
                "session_id": result["session_id"],
                "answer": result["answer"],
                "flight_results": result["flight_results"],
                "hotel_results": result["hotel_results"],
                "itinerary": result["itinerary"],
                "llm_calls": result["llm_calls"],
            }
        )

    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@router.get("/api/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    sessions = list_user_sessions(current_user["user_id"])
    return {"success": True, "sessions": sessions}


@router.get("/api/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = get_user_session_detail(session_id, current_user["user_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, **session}


@router.delete("/api/sessions/{session_id}")
async def remove_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = delete_user_session(session_id, current_user["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True}


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "AI Travel Planner API is Running"}


@router.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})
