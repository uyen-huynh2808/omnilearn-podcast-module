from dataclasses import dataclass
from typing import Literal, Dict, Any, Optional

from core.llm_core import GeminiLLM
from models.storytelling_model import StorytellingModel, PodcastConfig as _PC1
from models.interview_model import InterviewModel, PodcastConfig as _PC2

@dataclass
class PodcastConfig:
    duration: str
    style: str
    characters: Literal[1, 2]

class PodcastOrchestrator:
    def __init__(self, llm_model=None, max_tokens_per_chunk: int = 2600):
        self.llm = llm_model or GeminiLLM(model_name="gemini-2.0-flash")
        self.story = StorytellingModel(self.llm, max_tokens_per_chunk)
        self.interview = InterviewModel(self.llm, max_tokens_per_chunk)

    def run(self, document: str, cfg: PodcastConfig, **kwargs) -> Dict[str, Any]:
        if cfg.characters == 1:
            return self.story.run(
                document,
                _PC1(duration=cfg.duration, style=cfg.style, characters=1),
                out_wav=kwargs.get("out_wav", "monologue_audio.wav"),
                out_mp3=kwargs.get("out_mp3", "monologue_audio.mp3"),
            )
        elif cfg.characters == 2:
            return self.interview.run(
                document,
                _PC2(duration=cfg.duration, style=cfg.style, characters=2),
                out_wav=kwargs.get("out_wav", "dialogue_audio.wav"),
                out_mp3=kwargs.get("out_mp3", "dialogue_audio.mp3"),
                speaker_voice=kwargs.get("speaker_voice"),
            )
        else:
            raise ValueError("`characters` phải là 1 hoặc 2.")
