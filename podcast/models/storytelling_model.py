from dataclasses import dataclass
from typing import Dict, Any

from core.llm_core import ContentGenerator
from core.tts_core import synth_to_files

@dataclass
class PodcastConfig:
    duration: str
    style: str
    characters: int  # 1 hoặc 2

class StorytellingModel:
    """characters = 1"""
    def __init__(self, llm_model, max_tokens_per_chunk: int = 2600):
        self.generator = ContentGenerator(llm_model, max_tokens_per_chunk=max_tokens_per_chunk)

    def run(self, document: str, cfg: PodcastConfig,
            out_wav: str = "monologue_audio.wav",
            out_mp3: str = "monologue_audio.mp3") -> Dict[str, Any]:
        script_text = self.generator.generate(
            document,
            duration=cfg.duration,
            style=cfg.style,
            characters=1,
        )
        audio_info = synth_to_files(script_text, out_wav=out_wav, out_mp3=out_mp3)
        return {"mode": "storytelling", "text": script_text, "audio": audio_info}
