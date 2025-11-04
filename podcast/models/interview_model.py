from dataclasses import dataclass
from typing import Dict, Any, Optional

from core.llm_core import ContentGenerator
from core.tts_core import synth_dialogue

@dataclass
class PodcastConfig:
    duration: str
    style: str
    characters: int  # 1 hoặc 2

class InterviewModel:
    """characters = 2"""
    def __init__(self, llm_model, max_tokens_per_chunk: int = 2600):
        self.generator = ContentGenerator(llm_model, max_tokens_per_chunk=max_tokens_per_chunk)

    def run(self, document: str, cfg: PodcastConfig,
            out_wav: str = "dialogue_audio.wav",
            out_mp3: str = "dialogue_audio.mp3",
            speaker_voice: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        script_text = self.generator.generate(
            document,
            duration=cfg.duration,
            style=cfg.style,
            characters=2,
        )
        audio_info = synth_dialogue(
            script_text,
            out_wav=out_wav,
            out_mp3=out_mp3,
            speaker_voice=speaker_voice,
        )
        return {"mode": "interview", "text": script_text, "audio": audio_info}
