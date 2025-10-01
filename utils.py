# File: utils.py
# Tối ưu cho chatbot trả lời ngắn gọn, đúng trọng tâm
import os
from dotenv import load_dotenv
import google.generativeai as genai
from functools import lru_cache
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    logger.error(f"❌ Lỗi khởi tạo Gemini API: {str(e)}")
    gemini_model = None

async def gemini_generate_text(prompt: str) -> str:
    if gemini_model is None:
        return "Gemini API chưa được cấu hình"
    try:
        response = await gemini_model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Lỗi tạo văn bản Gemini: {str(e)}")
        return f"Lỗi tạo văn bản: {str(e)}"

def extract_user_context(history: List[Dict[str, str]]) -> Dict[str, Optional[str]]:
    """
    Phân tích lịch sử để trích xuất thông tin người dùng đã cung cấp
    """
    context = {
        "level": None,      # Trình độ: mới học, trung cấp, chuyên nghiệp
        "budget": None,     # Ngân sách: dưới 500k, 500k-1tr, trên 1tr
        "purpose": None,    # Mục đích: học, biểu diễn, trang trí, sưu tầm
        "instrument": None, # Nhạc cụ đang quan tâm
        "age": None         # Độ tuổi (nếu có)
    }
    
    if not history:
        return context
    
    # Phân tích từ lịch sử (lấy thông tin từ câu hỏi người dùng)
    all_queries = " ".join([item['user'].lower() for item in history])
    
    # Trình độ
    if any(k in all_queries for k in ["mới", "chưa biết", "bắt đầu", "học lần đầu"]):
        context["level"] = "mới học"
    elif any(k in all_queries for k in ["đã biết", "biết cơ bản", "trung bình"]):
        context["level"] = "trung cấp"
    elif any(k in all_queries for k in ["chuyên nghiệp", "biểu diễn", "giỏi"]):
        context["level"] = "chuyên nghiệp"
    
    # Ngân sách
    if any(k in all_queries for k in ["rẻ", "dưới 500", "giá thấp"]):
        context["budget"] = "dưới 500k"
    elif any(k in all_queries for k in ["tầm 1 triệu", "500k", "giá vừa"]):
        context["budget"] = "500k-1tr"
    elif any(k in all_queries for k in ["cao cấp", "trên 1 triệu", "chất lượng tốt"]):
        context["budget"] = "trên 1tr"
    
    # Mục đích
    if any(k in all_queries for k in ["học", "tập", "luyện"]):
        context["purpose"] = "học"
    elif any(k in all_queries for k in ["biểu diễn", "trình diễn", "sân khấu"]):
        context["purpose"] = "biểu diễn"
    elif any(k in all_queries for k in ["trang trí", "treo tường", "decor"]):
        context["purpose"] = "trang trí"
    elif any(k in all_queries for k in ["sưu tầm", "sưu tập", "collection"]):
        context["purpose"] = "sưu tầm"
    
    # Nhạc cụ
    instruments = ["sáo", "đàn tranh", "đàn bầu", "đàn nguyệt", "đàn nhị", "trống"]
    for inst in instruments:
        if inst in all_queries:
            context["instrument"] = inst
            break
    
    # Độ tuổi
    import re
    age_match = re.search(r'(\d+)\s*tuổi', all_queries)
    if age_match:
        context["age"] = age_match.group(1)
    
    return context

def build_concise_history(history: List[Dict[str, str]], max_turns: int = 3) -> str:
    """
    Chỉ lấy thông tin quan trọng từ lịch sử, bỏ qua chi tiết dư thừa
    """
    if not history:
        return ""
    
    recent = history[-max_turns:] if len(history) > max_turns else history
    summary = []
    
    for item in recent:
        # Chỉ giữ lại câu hỏi ngắn gọn
        user_q = item['user'][:100]  # Giới hạn 100 ký tự
        summary.append(f"Q: {user_q}")
    
    return "\n".join(summary)

async def process_chat_query(query: str, history: List[Dict[str, str]], intent: str) -> str:
    """
    Xử lý câu hỏi với prompt ngắn gọn, đúng trọng tâm
    """
    # Trích xuất context từ history
    user_context = extract_user_context(history)
    history_summary = build_concise_history(history, max_turns=3)
    
    # Context string
    context_str = ""
    if any(user_context.values()):
        ctx_parts = []
        if user_context["level"]:
            ctx_parts.append(f"Trình độ: {user_context['level']}")
        if user_context["budget"]:
            ctx_parts.append(f"Ngân sách: {user_context['budget']}")
        if user_context["purpose"]:
            ctx_parts.append(f"Mục đích: {user_context['purpose']}")
        if user_context["instrument"]:
            ctx_parts.append(f"Nhạc cụ: {user_context['instrument']}")
        if user_context["age"]:
            ctx_parts.append(f"Độ tuổi: {user_context['age']}")
        context_str = " | ".join(ctx_parts)
    
    # Base instruction - QUAN TRỌNG: Bắt buộc trả lời ngắn gọn
    base_rules = """
🎯 QUY TẮC BẮT BUỘC:
- Trả lời TỐI ĐA 3-4 câu (60-80 từ)
- Đi thẳng vào vấn đề, không dài dòng
- Không giải thích quá chi tiết trừ khi được yêu cầu
- Format rõ ràng, dễ đọc
"""

    if intent == "consultation":
        prompt = f"""{base_rules}

Thông tin người dùng: {context_str if context_str else "Chưa có"}
Lịch sử: {history_summary if history_summary else "Không có"}
Câu hỏi: {query}

Vai trò: Chuyên gia tư vấn nhạc cụ dân tộc Việt Nam

Hãy trả lời NGẮN GỌN theo format:
"[Tình huống]? Nên chọn [nhạc cụ cụ thể - tone/size] giá [X]k, [1-2 đặc điểm nổi bật], kèm [phụ kiện cần thiết]."

Ví dụ tốt:
"Bạn mới học sáo trúc? Nên chọn sáo tone D, tre già giá 350k, dễ thổi, âm ấm, kèm giáo trình cơ bản + túi đựng."

KHÔNG viết dài dòng, KHÔNG liệt kê nhiều lựa chọn trừ khi được hỏi."""

    elif intent == "guide":
        # Kiểm tra nếu là follow-up question
        is_followup = any(k in query.lower() for k in ["chi tiết", "cụ thể", "rõ hơn", "thế nào", "như nào"])
        
        if is_followup and history:
            prompt = f"""{base_rules}

Lịch sử: {history_summary}
Câu hỏi follow-up: {query}

Người dùng muốn biết CHI TIẾT HƠN về câu trước. 
Hãy đi sâu vào KỸ THUẬT CỤ THỂ trong 4-5 bước ngắn gọn:

1. [Bước 1 - hành động cụ thể]
2. [Bước 2 - hành động cụ thể]
...

Tips quan trọng: [1 tips ngắn]

KHÔNG giải thích lý thuyết dài, CHỈ hướng dẫn hành động."""
        else:
            prompt = f"""{base_rules}

Câu hỏi: {query}
Thông tin: {context_str if context_str else "Không có"}

Vai trò: Giáo viên dạy nhạc

Trả lời ngắn gọn 3-4 bước cơ bản:
1. [Bước 1]
2. [Bước 2]
3. [Bước 3]

Video gợi ý: [Tên video ngắn] - [link]

KHÔNG mô tả chi tiết từng bước, CHỈ liệt kê hành động chính."""

    elif intent == "story":
        prompt = f"""{base_rules}

Câu hỏi: {query}

Vai trò: Người kể chuyện văn hóa

Kể nguồn gốc trong 3-4 câu:
- Câu 1: Nhạc cụ là gì
- Câu 2: Xuất xứ/lịch sử
- Câu 3: Ý nghĩa văn hóa

Ví dụ tốt:
"Đàn bầu là nhạc cụ độc tấu một dây của Việt Nam. Xuất hiện từ thế kỷ 10, gắn liền với ca trù. Âm thanh uốn lượn như giọng hát, thể hiện tâm hồn người Việt."

KHÔNG kể quá chi tiết lịch sử."""

    elif intent == "support":
        prompt = f"""{base_rules}

Câu hỏi: {query}
Thông tin: {context_str if context_str else "Không có"}

Vai trò: Nhân viên CSKH

Trả lời 2-3 câu ngắn gọn, thân thiện:
- Câu 1: Trả lời trực tiếp câu hỏi
- Câu 2: Gợi ý/lời khuyên cụ thể

Ví dụ tốt:
"Bảo quản sáo khi trời ẩm: cất nơi khô ráo, dùng túi hút ẩm silica gel. Tránh để gần cửa sổ hoặc nơi có nước."

KHÔNG giải thích dài lý do."""

    else:
        prompt = f"""{base_rules}

Câu hỏi: {query}

Trả lời ngắn gọn 2-3 câu về nhạc cụ dân tộc Việt Nam."""

    return await gemini_generate_text(prompt)