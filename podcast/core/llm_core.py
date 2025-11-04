from typing import List, Optional
import json, os

# LLM (Gemini) cho text
try:
    from google import genai as genai_text
    from google.genai import types as text_types
except Exception:
    genai_text = None
    text_types = None


class GeminiLLM:
    """
    Simple wrapper: model.generate(prompt) -> str
    Dùng GEMINI_API_KEY_LLM / GEMINI_API_KEY / GEMINI_API_KEY_TTS cho LLM text.
    """
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        if api_key is None:
            api_key = (os.getenv("GEMINI_API_KEY_LLM")
                       or os.getenv("GEMINI_API_KEY")
                       or os.getenv("GEMINI_API_KEY_TTS"))
        if not api_key:
            raise RuntimeError("Thiếu API key cho LLM (GEMINI_API_KEY_LLM / GEMINI_API_KEY).")
        if genai_text is None:
            raise RuntimeError("Thiếu thư viện google-genai. Cài: pip install google-genai")
        self.client = genai_text.Client(api_key=api_key)
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        resp = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=text_types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.7,
            ),
        )
        out = []
        for c in getattr(resp, "candidates", []) or []:
            for p in getattr(getattr(c, "content", None), "parts", []) or []:
                if hasattr(p, "text"):
                    out.append(p.text)
        return "\n".join(out).strip() if out else ""


class ContentGenerator:
    """
    Generate text content từ input dài hoặc ngắn.
    CHỈ dùng 3 config: duration, style, characters
    """
    def __init__(self, llm_model, max_tokens_per_chunk: int = 2600):
        self.model = llm_model
        self.max_tokens_per_chunk = max_tokens_per_chunk

    # Utilities
    @staticmethod
    def approx_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def chunk_text(text: str, max_tokens: int) -> List[str]:
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        chunks, current, current_len = [], [], 0
        for sent in sentences:
            sent_len = ContentGenerator.approx_tokens(sent)
            if current_len + sent_len > max_tokens and current:
                chunks.append('. '.join(current) + '.')
                current, current_len = [], 0
            current.append(sent)
            current_len += sent_len
        if current:
            chunks.append('. '.join(current) + '.')
        return chunks

    # Prompt builders (chỉ 3 tham số)
    def build_prompt_short(self, text: str, duration: str, style: str, characters: int) -> str:
        cfg = {"duration": duration, "style": style, "characters": int(characters)}
        mode_note = (
            "Nếu 2 người nói chuyện, hãy viết theo định dạng:\n"
            "Speaker 1: ...\nSpeaker 2: ...\n"
            "Nếu 1 người thì viết dạng đoạn văn, KHÔNG gắn nhãn Speaker."
        )
        return f"""
Bạn là một nhà viết nội dung podcast.
Hãy chuyển đoạn văn sau thành nội dung phù hợp podcast, giữ kiến thức cốt lõi, không bịa đặt.
{mode_note}

text:
{text}

Yêu cầu (JSON):
{json.dumps(cfg, ensure_ascii=False, indent=2)}
""".strip()

    def build_prompt_long(self, text: str, duration: str, style: str, characters: int, context: str = "") -> str:
        cfg = {"duration": duration, "style": style, "characters": int(characters)}
        mode_note = (
            "Nếu 2 người nói chuyện, hãy viết theo định dạng:\n"
            "Speaker 1: ...\nSpeaker 2: ...\n"
            "Nếu 1 người thì viết dạng đoạn văn, KHÔNG gắn nhãn Speaker."
        )
        context_info = f"Context ngay trước đó để đảm bảo tính liền mạch:\n{context}" if context else "Không có context trước đó."
        return f"""
Bạn là một nhà viết nội dung podcast.
Hãy chuyển đoạn văn sau thành nội dung phù hợp podcast, giữ kiến thức cốt lõi, không bịa đặt.
{mode_note}

text:
{text}

Yêu cầu (JSON):
{json.dumps(cfg, ensure_ascii=False, indent=2)}

{context_info}
""".strip()

    def generate(self, document: str, duration: str, style: str, characters: int) -> str:
        if self.approx_tokens(document) <= self.max_tokens_per_chunk:
            prompt = self.build_prompt_short(document, duration, style, characters)
            return self.model.generate(prompt)

        chunks = self.chunk_text(document, self.max_tokens_per_chunk)
        prev_output, outputs = "", []
        for ch in chunks:
            prompt = self.build_prompt_long(ch, duration, style, characters, context=prev_output)
            resp = self.model.generate(prompt)
            outputs.append(resp)
            prev_output = resp
        return "\n".join(outputs)
