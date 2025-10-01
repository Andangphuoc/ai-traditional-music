import numpy as np
import logging
from io import BytesIO
from pydub import AudioSegment
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

logger = logging.getLogger(__name__)

class AIMusicGenerator:
    def __init__(self, device: str = "cpu"):
        """
        AI Music Generator dùng MusicGen
        :param device: 'cpu' hoặc 'cuda'
        """
        try:
            self.processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                "facebook/musicgen-small"
            ).to(device)
            self.device = device
            logger.info("✅ Loaded MusicGen successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load MusicGen: {str(e)}")
            raise

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
        "t_rung": "Vietnamese bamboo xylophone T’rưng, bright cascading mountain echo tones",
        "k_longput": "Vietnamese bamboo percussion K’longput, resonant airy tones from clapped air",
        "dan_kni": "Vietnamese mouth fiddle Đàn K’ni, haunting vocal-like resonance",
        }

        desc = instrument_map.get(instrument.lower(), f"Vietnamese folk instrument {instrument}")

        return (
            f"A high-quality {style} solo performance played only with the {desc}. "
            f"Expressive and natural playing, clean audio recording, "
            f"authentic Vietnamese sound. "
            f"No accompaniment, no background, no drums, no percussion, "
            f"no other instruments."
        )


    def generate(self, instrument: str, style: str, duration: float) -> BytesIO:
        prompt = self._build_prompt(instrument, style)
        try:
            inputs = self.processor(
                text=[prompt],
                padding=True,
                return_tensors="pt"
            ).to(self.device)

            # max_new_tokens quyết định độ dài -> approx 50 tokens ≈ 1 giây
            max_new_tokens = int(duration * 50)

            audio_values = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens
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
            return audio_io
        except Exception as e:
            logger.error(f"❌ Error generating audio for {instrument}: {str(e)}")
            raise
