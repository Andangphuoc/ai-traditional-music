from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from models import ProductDemoRequest
from ai_music import AIMusicGenerator
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

SAMPLE_DIR = "samples"
INSTRUMENT_SAMPLES = {
    "sáo trúc": "sao_truc_demo.wav",
    "đàn tranh": "dan_tranh_demo.wav",
    "đàn bầu": "dan_bau_demo.wav",
    "trống cơm": "trong_com_demo.wav",
    "đàn nguyệt": "dan_nguyet_demo.wav",
}

# Khởi tạo AI Generator
try:
    ai_generator = AIMusicGenerator()
except Exception as e:
    logger.error(f"❌ Lỗi khởi tạo AIMusicGenerator: {str(e)}")
    ai_generator = None

@router.post("/")
async def demo_audio(request: ProductDemoRequest):
    """
    API trả về demo âm thanh nhạc cụ
    - Nếu use_ai = False và có sample thật thì trả về file sample
    - Nếu use_ai = True hoặc không có sample thì dùng AI generator
    """
    instrument = request.product.lower()

    if not request.use_ai and instrument in INSTRUMENT_SAMPLES:
        file_path = os.path.join(SAMPLE_DIR, INSTRUMENT_SAMPLES[instrument])
        if os.path.exists(file_path):
            logger.info(f"✅ Trả file mẫu cho {instrument}")
            return FileResponse(
                file_path,
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename={instrument}_demo.wav"},
            )
        else:
            logger.warning(f"⚠️ Không tìm thấy file mẫu cho {instrument}, chuyển sang AI")

    if ai_generator is None:
        raise HTTPException(status_code=500, detail="Trình tạo âm thanh AI chưa được khởi tạo")

    try:
        audio_io = ai_generator.generate(
            instrument=instrument,
            style=request.style,
            duration=request.duration,
        )
        logger.info(f"🎶 Tạo âm thanh AI cho {instrument}")
        return StreamingResponse(
            audio_io,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={instrument}_ai_demo.wav"},
        )
    except Exception as e:
        logger.error(f"❌ Lỗi tạo âm thanh AI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tạo âm thanh thất bại: {str(e)}")