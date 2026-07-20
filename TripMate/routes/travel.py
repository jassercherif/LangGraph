import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.travel_service import run_travel_agent

router = APIRouter()


class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None


@router.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    try:
        user_message = request_data.message.strip()

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty."},
            )

        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id,
        )

        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
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


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "AI Travel Planner API is Running"}


@router.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})
