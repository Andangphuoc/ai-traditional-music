# File: routes/consultation.py
from fastapi import APIRouter, HTTPException
from models import ChatRequest, QuickConsultRequest
from utils import process_chat_query, gemini_generate_text
import httpx
import json

router = APIRouter()

async def fetch_courses():
    """Lấy danh sách sản phẩm từ API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.music.3docorp.vn/api/Course###")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
    except Exception as e:
        print(f"Error fetching courses: {e}")
        return []

def format_courses_for_prompt(courses):
    """Format danh sách sản phẩm thành text cho Gemini"""
    formatted = "DANH SÁCH SẢN PHẨM CÓ SẴN:\n\n"
    for course in courses:
        price = course.get("discountPrice") or course.get("price", 0)
        
        # Xử lý category an toàn
        category = course.get('category')
        category_name = category.get('name') if category and isinstance(category, dict) else 'N/A'
        
        # Xử lý level an toàn
        level = course.get('level')
        level_name = level.get('name') if level and isinstance(level, dict) else 'N/A'
        
        formatted += f"""
ID: {course.get('courseId')}
Tên: {course.get('title')}
Giá: {price:,}đ
Danh mục: {category_name}
Trình độ: {level_name}
Tồn kho: {course.get('stock', 0)}
---
"""
    return formatted

async def extract_product_id_from_response(ai_response: str, courses: list) -> int:
    """
    Trích xuất product ID phù hợp nhất từ response của AI
    Sử dụng keyword matching với tên sản phẩm
    """
    ai_lower = ai_response.lower()
    
    # Danh sách từ khóa để mapping
    keywords_map = {
        1: ["sáo trúc", "sáo", "trúc", "tone d"],
        2: ["piano", "đàn piano", "donner", "ddp-200"],
        3: ["cajon", "trống", "meinl", "mcaj100"],
        4: ["guitar", "đờn guitar"]
    }
    
    # Tính điểm match cho mỗi sản phẩm
    scores = {}
    for course_id, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in ai_lower)
        if score > 0:
            scores[course_id] = score
    
    # Trả về ID có điểm cao nhất
    if scores:
        return max(scores, key=scores.get)
    
    # Fallback: trả về sản phẩm đầu tiên có trong danh sách
    return courses[0].get('courseId', 1) if courses else 1

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
    Endpoint tư vấn nhanh - tích hợp với API sản phẩm
    Trả về gợi ý + suggesstionProductId
    """
    # Lấy danh sách sản phẩm
    courses = await fetch_courses()
    
    if not courses:
        raise HTTPException(status_code=503, detail="Không thể lấy thông tin sản phẩm")
    
    # Format thông tin sản phẩm
    courses_info = format_courses_for_prompt(courses)
    
    prompt = f"""
🎯 QUY TẮC: Trả lời TỐI ĐA 3-4 câu (60-80 từ)

{courses_info}

THÔNG TIN KHÁCH HÀNG:
- Trình độ: {request.level}
- Ngân sách: {request.budget}
- Mục đích: {request.purpose}
- Loại nhạc cụ: {request.instrument_type or "Chưa xác định"}
- Độ tuổi: {request.age or "Không rõ"}
- Thêm: {request.additional_info or "Không có"}

Vai trò: Chuyên gia tư vấn nhạc cụ dân tộc Việt Nam

Nhiệm vụ:
1. Chọn 1 SẢN PHẨM CỤ THỂ từ danh sách trên phù hợp nhất
2. Gợi ý NGẮN GỌN theo format:

"Với [trình độ] và [mục đích], nên chọn [TÊN CHÍNH XÁC SẢN PHẨM] giá [X]k, [đặc điểm nổi bật], kèm [combo phụ kiện nếu có]."

Ví dụ tốt:
"Với người mới học và mục đích tự học tại nhà, nên chọn Sáo trúc cho người mới bắt đầu giá 299k, dễ thổi, âm ấm, kèm giáo trình PDF + túi vải + dây treo."

LƯU Ý: 
- Phải GHI RÕ TÊN SẢN PHẨM từ danh sách
- CHỈ gợi ý 1 sản phẩm duy nhất
- Ưu tiên sản phẩm còn hàng (stock > 0)
- Phù hợp với ngân sách
"""
    
    # Gọi Gemini để sinh gợi ý
    ai_suggestion = await gemini_generate_text(prompt)
    
    # Trích xuất product ID từ response
    suggested_product_id = await extract_product_id_from_response(ai_suggestion, courses)
    
    return {
        "suggestion": ai_suggestion,
        "suggesstionProductId": suggested_product_id,
        "user_profile": {
            "level": request.level,
            "budget": request.budget,
            "purpose": request.purpose,
            "instrument_type": request.instrument_type,
            "age": request.age
        }
    }