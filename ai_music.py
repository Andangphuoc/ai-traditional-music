import numpy as np
import logging
from io import BytesIO
from pydub import AudioSegment
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
from functools import lru_cache
import hashlib
import os

logger = logging.getLogger(__name__)

class AIMusicGenerator:
    def __init__(self, device: str = None, use_cache: bool = True):
        """
        AI Music Generator dùng MusicGen với tối ưu
        :param device: 'cpu', 'cuda', hoặc None (auto-detect)
        :param use_cache: Bật cache cho audio đã generate
        """
        # Auto-detect device tối ưu nhất
        if device is None:
            device = self._detect_best_device()
        
        self.device = device
        self.use_cache = use_cache
        self.cache_dir = "audio_cache"
        self.use_fp16 = (device == "cuda")  # Chỉ dùng FP16 khi có GPU
        
        if self.use_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            logger.info(f"🔄 Loading MusicGen on {device}...")
            self.processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                "facebook/musicgen-small"
            ).to(device)
            
            # Tối ưu cho inference
            self.model.eval()
            
            # Chỉ dùng FP16 khi có GPU và đủ VRAM
            if self.use_fp16:
                try:
                    self.model = self.model.half()
                    logger.info("✅ Enabled FP16 for faster inference")
                except Exception as e:
                    logger.warning(f"⚠️ Cannot use FP16: {str(e)}, using FP32")
                    self.use_fp16 = False
            
            logger.info(f"✅ Loaded MusicGen successfully on {device}")
        except Exception as e:
            logger.error(f"❌ Failed to load MusicGen: {str(e)}")
            raise
    
    def _detect_best_device(self) -> str:
        """
        Tự động phát hiện và chọn device tốt nhất
        """
        # Kiểm tra CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            logger.info(f"🎮 GPU detected: {gpu_name} ({gpu_memory:.1f} GB VRAM)")
            
            # Kiểm tra xem có đủ VRAM không (cần ít nhất 2GB cho musicgen-small)
            if gpu_memory >= 2.0:
                logger.info("✅ Using CUDA (GPU) - Expected 8-10x faster!")
                return "cuda"
            else:
                logger.warning(f"⚠️ GPU VRAM too low ({gpu_memory:.1f} GB), falling back to CPU")
                return "cpu"
        
        # Kiểm tra MPS (Apple Silicon M1/M2/M3)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("🍎 Apple Silicon (MPS) detected - Expected 3-5x faster!")
            return "mps"
        
        # Fallback về CPU
        else:
            logger.info("💻 Using CPU - Generation will be slower (~60s for 10s audio)")
            return "cpu"
    
    def get_device_info(self) -> dict:
        """
        Trả về thông tin về device đang sử dụng
        """
        info = {
            "device": self.device,
            "use_fp16": self.use_fp16,
            "cache_enabled": self.use_cache
        }
        
        if self.device == "cuda":
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            info["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated(0) / (1024**3)
        
        return info

    def _build_prompt(self, instrument: str, style: str) -> str:
        instrument_map = {
            "sao_truc": "Vietnamese bamboo transverse flute Sáo Trúc, airy, soft timbre, capable of bending notes",
            "sao_tieu": "Vietnamese vertical bamboo flute Sáo Tiêu, mellow meditative low tone",
            "ken_bau": "Vietnamese conical oboe Kèn Bầu, reedy, buzzing and powerful sound",
            "dan_tranh": "Vietnamese 16-string zither Đàn Tranh, bright, metallic cascading tones with glissando",
            "dan_bau": "Vietnamese monochord Đàn Bầu, expressive bending pitch, soulful vocal-like timbre",
            "dan_nguyet": "Vietnamese moon lute Đàn Nguyệt, clear metallic tone, traditional opera instrument",
            "dan_tinh": "Vietnamese lute Đàn Tính, gentle storytelling tone used in spiritual folk songs",
            "dan_ty_ba": "Vietnamese pear-shaped lute Đàn Tỳ Bà, delicate articulate plucking tone",
            "dan_nhi": "Vietnamese two-string fiddle Đàn Nhị, nasal, emotional, expressive",
            "dan_gao": "Vietnamese coconut-shell fiddle Đàn Gáo, rustic, folk tone",
            "dan_co": "Vietnamese spike fiddle Đàn Cò, high-pitched crying timbre",
            "trong_com": "Vietnamese barrel drum Trống Cơm, resonant deep bass sound",
            "phach": "Vietnamese wooden clappers Phách, dry sharp percussive click",
            "song_lang": "Vietnamese bamboo clapper Song Lang, sharp timing click",
            "chieng": "Vietnamese gong Chiêng, metallic reverberant tone",
            "t_rung": "Vietnamese bamboo xylophone T'rưng, bright cascading mountain echo tones",
            "k_longput": "Vietnamese bamboo percussion K'longput, resonant airy tones from clapped air",
            "dan_kni": "Vietnamese mouth fiddle Đàn K'ni, haunting vocal-like resonance",
        }

        desc = instrument_map.get(instrument.lower(), f"Vietnamese folk instrument {instrument}")

        return (
            f"A high-quality {style} solo performance played only with the {desc}. "
            f"Expressive and natural playing, clean audio recording, "
            f"authentic Vietnamese sound. "
            f"No accompaniment, no background, no drums, no percussion, "
            f"no other instruments."
        )

    def _get_cache_key(self, instrument: str, style: str, duration: float) -> str:
        """Tạo unique key cho cache"""
        key_string = f"{instrument}_{style}_{duration}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> BytesIO:
        """Load audio từ cache nếu có"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                audio_io = BytesIO(f.read())
                audio_io.seek(0)
                logger.info(f"💾 Loaded from cache: {cache_key}")
                return audio_io
        return None

    def _save_to_cache(self, cache_key: str, audio_io: BytesIO):
        """Lưu audio vào cache"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        with open(cache_path, 'wb') as f:
            f.write(audio_io.getvalue())
        logger.info(f"💾 Saved to cache: {cache_key}")

    def generate(self, instrument: str, style: str, duration: float) -> BytesIO:
        # Kiểm tra cache trước
        if self.use_cache:
            cache_key = self._get_cache_key(instrument, style, duration)
            cached_audio = self._load_from_cache(cache_key)
            if cached_audio:
                return cached_audio

        prompt = self._build_prompt(instrument, style)
        
        try:
            # Preprocessing
            inputs = self.processor(
                text=[prompt],
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Convert to FP16 nếu dùng GPU
            if self.device == "cuda":
                inputs = {k: v.half() if v.dtype == torch.float32 else v 
                         for k, v in inputs.items()}

            # Tối ưu số tokens: 40 tokens/giây thay vì 50
            max_new_tokens = int(duration * 40)
            
            # Generate với torch.no_grad() để tiết kiệm memory
            with torch.no_grad():
                audio_values = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,  # Thêm để âm thanh đa dạng hơn
                    temperature=1.0,  # Có thể điều chỉnh
                    top_k=250,  # Giảm từ default để nhanh hơn
                )

            sampling_rate = self.model.config.audio_encoder.sampling_rate
            audio_np = audio_values[0].cpu().numpy()

            # Normalize và convert sang int16
            audio_np = np.nan_to_num(audio_np)
            audio_np = (audio_np * 32767).astype(np.int16)

            audio_segment = AudioSegment(
                audio_np.tobytes(),
                frame_rate=sampling_rate,
                sample_width=2,
                channels=1
            )
            
            audio_io = BytesIO()
            audio_segment.export(audio_io, format="wav")
            audio_io.seek(0)
            
            # Lưu vào cache
            if self.use_cache:
                self._save_to_cache(cache_key, audio_io)
                audio_io.seek(0)  # Reset lại để đọc
            
            return audio_io
            
        except Exception as e:
            logger.error(f"❌ Error generating audio for {instrument}: {str(e)}")
            raise

    def clear_cache(self):
        """Xóa toàn bộ cache"""
        if os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
            logger.info("🗑️ Cache cleared")