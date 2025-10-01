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
    "sáo": "sao.mp3",
    "đàn tranh": "dan_tranh.mp3",
    "đàn bầu": "dan_bau.mp3",
    "đàn nguyệt": "dan_nguyet.mp3",
    "đàn nhi": "dan_nhi.mp3",
    "đàn đá": "dan_da.mp3",
    "đàn day": "dan_day.mp3",
    "đàn sen": "dan_sen.mp3",
    "đàn tỳ bà": "dan_ty_ba.mp3",
    "danh tranh": "danh_tranh1.mp3",
    "kèn bé": "khen_be.mp3",
    "t'rưng": "t_rung.mp3",
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