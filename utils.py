# File: utils.py
# Updated process_chat_query to use history for context (simulate learning)
import os
from dotenv import load_dotenv
import google.generativeai as genai
from transformers import pipeline
from functools import lru_cache
import asyncio
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    logger.error(f"❌ Lỗi khởi tạo Gemini API: {str(e)}")
    gemini_model = None

@lru_cache(maxsize=128)
def hf_generate_text(prompt: str) -> str:
    try:
        hf_generator = pipeline('text-generation', model='distilgpt2', device=-1)
        result = hf_generator(prompt, max_length=100, num_return_sequences=1, truncation=True)
        return result[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"❌ Lỗi tạo văn bản HF: {str(e)}")
        return f"Lỗi tạo văn bản: {str(e)}"

async def gemini_generate_text(prompt: str) -> str:
    if gemini_model is None:
        return "Gemini API chưa được cấu hình"
    try:
        response = await gemini_model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Lỗi tạo văn bản Gemini: {str(e)}")
        return f"Lỗi tạo văn bản: {str(e)}"
async def process_chat_query(query: str, history: List[Dict[str, str]], intent: str) -> str:
    """
    Xử lý câu hỏi với ngữ cảnh lịch sử chat + intent.
    Trả về câu trả lời ngắn gọn theo yêu cầu.
    """
    history_str = "\n".join(
        [f"Người dùng: {item['user']}\nAI: {item['ai']}" for item in history]
    ) if history else "Không có lịch sử chat trước."

    if intent == "consultation":
        prompt = (
            f"Dựa trên lịch sử chat: {history_str}\n"
            f"Câu hỏi: '{query}'\n"
            "Trả lời ngắn gọn. Gợi ý 1 nhạc cụ dân tộc Việt Nam phù hợp, kèm combo phụ kiện cơ bản. "
            "Format: “Bạn [mới học/biểu diễn/trang trí/sưu tầm] [tên nhạc cụ]? "
            "Nên chọn [phiên bản cụ thể: tone, chất liệu, giá tiền], kèm [phụ kiện cơ bản].”"
        )
    elif intent == "guide":
        prompt = (
        f"Dựa trên lịch sử chat: {history_str}\n"
        f"Câu hỏi: '{query}'\n"
        "Trả lời ngắn gọn. Hướng dẫn cách chơi hoặc bảo quản 1 nhạc cụ dân tộc Việt Nam. "
        "Kèm 1–2 gợi ý video YouTube (có tên video + đường link) phù hợp với người mới. "
        "Ví dụ: “Video: ‘Học sáo trúc cơ bản’ – https://youtube.com/…”"
        )
    elif intent == "story":
        prompt = (
            f"Dựa trên lịch sử chat: {history_str}\n"
            f"Câu hỏi: '{query}'\n"
            "Trả lời ngắn gọn. Kể nhanh nguồn gốc hoặc ý nghĩa văn hóa của 1 nhạc cụ dân tộc Việt Nam. "
            "Ví dụ: “Đàn bầu là nhạc cụ một dây độc đáo của Việt Nam, thường gắn với ca trù và nhạc dân gian Bắc Bộ…”"
        )
    elif intent == "support":
        prompt = (
            f"Dựa trên lịch sử chat: {history_str}\n"
            f"Câu hỏi: '{query}'\n"
            "Trả lời ngắn gọn, rõ ràng như chatbot chăm sóc khách hàng 24/7. "
            "Ví dụ: “Chọn đàn cho bé 8 tuổi: nên chọn đàn nhỏ, nhẹ.” "
            "Hoặc: “Bảo quản sáo khi trời nồm: cất nơi khô, dùng túi hút ẩm.”"
        )
    else:
        prompt = (
            f"Dựa trên lịch sử chat: {history_str}\n"
            f"Câu hỏi: '{query}'\n"
            "Trả lời ngắn gọn về nhạc cụ dân tộc Việt Nam."
        )

    return await gemini_generate_text(prompt)
