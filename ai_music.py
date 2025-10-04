import numpy as np
import logging
from io import BytesIO
from pydub import AudioSegment
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
from functools import lru_cache
import hashlib
import os
import unicodedata

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa text: bỏ dấu, chuyển thành chữ thường
    """
    if not text:
        return ""
    
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'd')
    text = text.lower().strip()
    text = ' '.join(text.split())
    
    return text


class AIMusicGenerator:
    def __init__(self, device: str = None, use_cache: bool = True):
        """
        AI Music Generator dùng MusicGen với tối ưu
        :param device: 'cpu', 'cuda', hoặc None (auto-detect)
        :param use_cache: Bật cache cho audio đã generate
        """
        if device is None:
            device = self._detect_best_device()
        
        self.device = device
        self.use_cache = use_cache
        self.cache_dir = "audio_cache"
        self.use_fp16 = (device == "cuda")
        
        if self.use_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            logger.info(f"📄 Loading MusicGen on {device}...")
            self.processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                "facebook/musicgen-small"
            ).to(device)
            
            self.model.eval()
            
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
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"🎮 GPU detected: {gpu_name} ({gpu_memory:.1f} GB VRAM)")
            
            if gpu_memory >= 2.0:
                logger.info("✅ Using CUDA (GPU) - Expected 8-10x faster!")
                return "cuda"
            else:
                logger.warning(f"⚠️ GPU VRAM too low ({gpu_memory:.1f} GB), falling back to CPU")
                return "cpu"
        
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("🎯 Apple Silicon (MPS) detected - Expected 3-5x faster!")
            return "mps"
        
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
        """
        Xây dựng prompt cho MusicGen.
        instrument: đã được chuẩn hóa (không dấu, chữ thường)
        """
        # Mapping không dấu
        instrument_map = {
           "sao truc": "Vietnamese bamboo transverse flute Sáo Trúc, airy, soft timbre, capable of bending notes for expressive melodies",
  "sao tieu": "Vietnamese vertical bamboo flute Sáo Tiêu, mellow meditative low tone, ideal for soulful and introspective music",
  "ken bau": "Vietnamese conical oboe Kèn Bầu, reedy, buzzing, and powerful sound, used in traditional ceremonies",
  "dan tranh": "Vietnamese 16-string zither Đàn Tranh, bright, metallic cascading tones with glissando, versatile for classical and folk music",
  "dan bau": "Vietnamese monochord Đàn Bầu, expressive bending pitch, soulful vocal-like timbre, iconic in Vietnamese music",
  "dan nguyet": "Vietnamese moon lute Đàn Nguyệt, clear metallic tone, traditional opera instrument with a bright, resonant sound",
  "dan tinh": "Vietnamese lute Đàn Tính, gentle storytelling tone used in spiritual folk songs of ethnic minorities",
  "dan ty ba": "Vietnamese pear-shaped lute Đàn Tỳ Bà, delicate articulate plucking tone, rooted in classical traditions",
  "dan nhi": "Vietnamese two-string fiddle Đàn Nhị, nasal, emotional, expressive sound, often used in emotional ballads",
  "dan gao": "Vietnamese coconut-shell fiddle Đàn Gáo, rustic, folk tone with a warm, earthy quality",
  "dan co": "Vietnamese spike fiddle Đàn Cò, high-pitched crying timbre, evoking deep emotional resonance",
  "trong com": "Vietnamese barrel drum Trống Cơm, resonant deep bass sound, essential for rhythmic accompaniment",
  "phach": "Vietnamese wooden clappers Phách, dry sharp percussive click, used for rhythmic precision in ensembles",
  "song lang": "Vietnamese bamboo clapper Song Lang, sharp timing click, provides crisp rhythmic accents",
  "chieng": "Vietnamese gong Chiêng, metallic reverberant tone, central to ethnic rituals and ensembles",
  "t rung": "Vietnamese bamboo xylophone T'rưng, bright cascading mountain echo tones, popular in highland music",
  "k longput": "Vietnamese bamboo percussion K'longput, resonant airy tones from clapped air, unique to ethnic traditions",
  "dan kni": "Vietnamese mouth fiddle Đàn K'ni, haunting vocal-like resonance, played with mouth for expressive melodies",
  "sao": "Vietnamese bamboo flute Sáo, airy, soft timbre, capable of bending notes, versatile for various genres",
  "ken be": "Vietnamese small oboe Kèn Bè, reedy, buzzing, and powerful sound, compact yet impactful",
  "danh tranh": "Vietnamese 16-string zither Đàn Tranh, bright, metallic cascading tones with glissando, alternate name for Đàn Tranh",
  "dan da": "Vietnamese stone xylophone Đàn Đá, bright, resonant stone tones, unique to ancient traditions",
  "dan day": "Vietnamese long-necked lute Đàn Đáy, deep, resonant folk instrument, used in traditional ca trù music",
  "dan sen": "Vietnamese lotus lute Đàn Sen, delicate, floating tones, rare and poetic in sound",
  "dan tam thap luc": "Vietnamese 36-string zither Đàn Tam Thập Lục, extended range with versatile, cascading tones, ideal for complex melodies",
  "dan tam": "Vietnamese three-string lute Đàn Tam, bright, rhythmic plucking tones, used in traditional ensembles",
  "dan senh": "Vietnamese lute Đàn Sến, delicate, articulate plucking tones, popular in southern folk music",
  "senh tien": "Vietnamese coin clapper Sênh Tiền, metallic jingling percussion sound, adds rhythmic sparkle",
  "mo": "Vietnamese wooden fish Mõ, hollow resonant knocking tone for ceremonial and Buddhist rituals",
  "trong cai": "Vietnamese large drum Trống Cái, deep booming bass rhythm, leads traditional music ensembles",
  "trong chau": "Vietnamese temple drum Trống Châu, deep ceremonial tone with resonant beats, used in sacred settings",
  "cong chieng": "Vietnamese gong set Cồng Chiêng, varied metallic resonances, essential for ethnic rituals and festivals",
  "khen": "Vietnamese free reed mouth organ Khèn, polyphonic buzzing reed tones, expressive melodies for ethnic music",
  "dan goong": "Vietnamese bamboo tube zither Đàn Goong, earthy percussive tones from ethnic traditions",
  "litranh": "Vietnamese horn Litranh, natural horn sound with deep, calling timbre, used in ethnic ceremonies",
  "trong paranung": "Vietnamese ethnic drum Trống Paranưng, rhythmic patterns with vibrant beats, unique to minority groups",
  "chuong": "Vietnamese bell Chuông, clear ringing tone for signaling and ceremonies, adds melodic accents",
  "guitar": "Acoustic or electric stringed instrument Guitar, versatile warm or bright tones, used in folk, pop, rock, and classical music",
  "piano": "Keyboard instrument Piano, rich, dynamic range with resonant tones, ideal for classical, jazz, and contemporary music",
  "violin": "Stringed instrument Violin, expressive, singing tone, used in classical, folk, and modern genres",
  "drum set": "Percussion ensemble Drum Set, powerful rhythmic foundation with varied tones, essential for rock, jazz, and pop music",
  "flute": "Western transverse flute Flute, clear, bright, and airy tone, used in classical, jazz, and world music",
  "trumpet": "Brass instrument Trumpet, bold, piercing tone, versatile for jazz, classical, and marching bands",
  "saxophone": "Reed instrument Saxophone, smooth, soulful tone, prominent in jazz, pop, and classical music",
  "ukulele": "Small stringed instrument Ukulele, bright, cheerful plucking tones, popular in Hawaiian and folk music",
  "harmonica": "Free reed instrument Harmonica, compact, expressive sound, used in blues, folk, and country music",
        }

        # Chuẩn hóa instrument key
        normalized_key = normalize_text(instrument)
        desc = instrument_map.get(normalized_key, f"Vietnamese folk instrument {instrument}")

        return (
            f"A high-quality {style} solo performance played only with the {desc}. "
            f"Expressive and natural playing, clean audio recording, "
            f"authentic Vietnamese sound. "
            f"No accompaniment, no background, no drums, no percussion, "
            f"no other instruments."
        )

    def _get_cache_key(self, instrument: str, style: str, duration: float) -> str:
        """Tạo unique key cho cache"""
        # Chuẩn hóa trước khi tạo key để "đàn tranh" và "dan tranh" có cùng cache
        normalized_instrument = normalize_text(instrument)
        key_string = f"{normalized_instrument}_{style}_{duration}"
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
        """
        Generate audio cho nhạc cụ
        instrument: có thể có dấu hoặc không dấu
        """
        # Kiểm tra cache trước
        if self.use_cache:
            cache_key = self._get_cache_key(instrument, style, duration)
            cached_audio = self._load_from_cache(cache_key)
            if cached_audio:
                return cached_audio

        prompt = self._build_prompt(instrument, style)
        
        try:
            inputs = self.processor(
                text=[prompt],
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            if self.device == "cuda":
                inputs = {k: v.half() if v.dtype == torch.float32 else v 
                         for k, v in inputs.items()}

            max_new_tokens = int(duration * 40)
            
            with torch.no_grad():
                audio_values = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=1.0,
                    top_k=250,
                )

            sampling_rate = self.model.config.audio_encoder.sampling_rate
            audio_np = audio_values[0].cpu().numpy()

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
            
            if self.use_cache:
                self._save_to_cache(cache_key, audio_io)
                audio_io.seek(0)
            
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