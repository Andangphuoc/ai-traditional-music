# File: routes/consultation.py
from fastapi import APIRouter
from models import ChatRequest, QuickConsultRequest
from utils import process_chat_query, gemini_generate_text

router = APIRouter()

@router.post("/")
async def consult_instrument(request: ChatRequest):
    """Endpoint chat thông thường với history"""
    response = await process_chat_query(request.query, request.history, intent="consultation")
    
    new_entry = {"user": request.query, "ai": response}
    updated_history = request.history.copy()
    updated_history.append(new_entry)
    
    return {
        "suggestion": response,
        "updated_history": updated_history
    }

@router.post("/quick")
async def quick_consult(request: QuickConsultRequest):
    """
    Endpoint tư vấn nhanh - không cần chat nhiều vòng
    User cung cấp đầy đủ thông tin ngay từ đầu
    """
    prompt = f"""
🎯 QUY TẮC: Trả lời TỐI ĐA 3-4 câu (60-80 từ)

THÔNG TIN KHÁCH HÀNG:
- Trình độ: {request.level}
- Ngân sách: {request.budget}
- Mục đích: {request.purpose}
- Loại nhạc cụ: {request.instrument_type or "Chưa xác định"}
- Độ tuổi: {request.age or "Không rõ"}
- Thêm: {request.additional_info or "Không có"}

Vai trò: Chuyên gia tư vấn nhạc cụ dân tộc Việt Nam

Hãy gợi ý NGẮN GỌN 1 nhạc cụ cụ thể theo format:
"Với [trình độ] và [mục đích], nên chọn [nhạc cụ cụ thể - model/tone/size] giá [X]k, [đặc điểm nổi bật], kèm [combo phụ kiện]."

Ví dụ tốt:
"Với người mới học và mục đích tự học tại nhà, nên chọn sáo trúc tone D (30cm), tre già giá 350k, dễ thổi, âm ấm, kèm giáo trình PDF + túi vải + dây treo."

KHÔNG liệt kê nhiều lựa chọn, CHỈ gợi ý 1 sản phẩm phù hợp nhất.
"""
    
    response = await gemini_generate_text(prompt)
    
    return {
        "suggestion": response,
        "user_profile": {
            "level": request.level,
            "budget": request.budget,
            "purpose": request.purpose,
            "instrument_type": request.instrument_type,
            "age": request.age
        }
    }