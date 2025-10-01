# File: models.py
# Mở rộng với UserProfile để chat hiệu quả hơn
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    
class EnhancedChatRequest(BaseModel):
    """Request với thông tin người dùng rõ ràng hơn (optional)"""
    query: str
    history: Optional[List[Dict[str, str]]] = []
    user_profile: Optional[Dict[str, str]] = None  # {"level": "mới học", "budget": "500k", ...}

class ProductDemoRequest(BaseModel):
    product: str
    use_ai: bool = False
    style: str = "dân gian Việt Nam"
    duration: int = 5

class QuickConsultRequest(BaseModel):
    """Request nhanh cho consultation với thông tin đầy đủ"""
    level: str = Field(..., description="Trình độ: mới học/trung cấp/chuyên nghiệp")
    budget: str = Field(..., description="Ngân sách: dưới 500k/500k-1tr/trên 1tr")
    purpose: str = Field(..., description="Mục đích: học/biểu diễn/trang trí/sưu tầm")
    instrument_type: Optional[str] = Field(None, description="Loại nhạc cụ: hơi/dây/gõ")
    age: Optional[int] = Field(None, description="Độ tuổi người chơi")
    additional_info: Optional[str] = Field(None, description="Thông tin bổ sung")