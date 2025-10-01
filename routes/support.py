from fastapi import APIRouter
from models import ChatRequest
from utils import process_chat_query

router = APIRouter()

@router.post("/")
async def customer_support(request: ChatRequest):
    response = await process_chat_query(request.query, request.history, intent="support")
    updated_history = request.history + [{"user": request.query, "ai": response}]
    return {"response": response, "updated_history": updated_history}  # Client stores updated_history in sessionStorage