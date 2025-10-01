# File: models.py
# Updated to add history list for chat sessions (client-side session storage compatible)
from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    query: str  # e.g., "Tôi muốn tìm khóa học giá rẻ", "Cách chơi sáo trúc"
    history: Optional[List[Dict[str, str]]] = []  # Previous chat history: [{"user": "query", "ai": "response"}]

class ProductDemoRequest(BaseModel):
    product: str  # e.g., "sáo trúc", "đàn bầu"
    use_ai: bool = False  # True: AI-generated, False: Sample if available
    style: str = "dân gian Việt Nam"  # Default style
    duration: int = 5  # Duration in seconds