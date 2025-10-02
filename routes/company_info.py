# File: routes/company_info.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

COMPANY_INFO_FILE = "company_info.txt"  # Đường dẫn file TXT (lưu JSON)

class CompanyInfo(BaseModel):
    company_name: str
    description: str
    purchase_policy: str
    return_policy: str
    contact: str
    chatbot_name: str

@router.get("/")
async def get_company_info():
    """
    Endpoint để xem nội dung file company_info.txt dưới dạng JSON
    """
    if not os.path.exists(COMPANY_INFO_FILE):
        raise HTTPException(status_code=404, detail="File company_info.txt không tồn tại.")
    
    try:
        with open(COMPANY_INFO_FILE, "r", encoding="utf-8") as f:
            content = json.load(f)
        logger.info("✅ Đã đọc nội dung file company_info.txt")
        return content
    except json.JSONDecodeError:
        logger.error("❌ File company_info.txt không chứa JSON hợp lệ")
        raise HTTPException(status_code=400, detail="File company_info.txt không chứa JSON hợp lệ")
    except Exception as e:
        logger.error(f"❌ Lỗi đọc file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi đọc file: {str(e)}")

@router.post("/update")
async def update_company_info(request: CompanyInfo):
    """
    Endpoint để cập nhật nội dung file company_info.txt từ JSON
    """
    try:
        with open(COMPANY_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(request.dict(), f, ensure_ascii=False, indent=2)
        logger.info("✅ Đã cập nhật nội dung file company_info.txt")
        return {"message": "Cập nhật thành công", "new_content": request.dict()}
    except Exception as e:
        logger.error(f"❌ Lỗi cập nhật file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật file: {str(e)}")