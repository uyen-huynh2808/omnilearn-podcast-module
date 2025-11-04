from typing import Dict as _Dict, List as _List, Tuple as _Tuple, Optional
import os, re, math, time, tempfile, wave, base64, collections
from pydub import AudioSegment

# Google GenAI for TTS
from google import genai
from google.genai import types

# ===== Shared TTS Config =====
MODEL_TTS = "gemini-2.5-flash-preview-tts"
SAMPLE_RATE, CHANNELS, SAMPLE_W = 24000, 1, 2
LANG_CODE_TTS = None

# Free tier pacing (tùy chỉnh nếu cần)
MAX_RPM, WINDOW_S = 3, 60
SAFE_TOKS = 2400

# ---------- Helpers chung ----------
def approx_tokens_tts(s: str) -> int:
    return math.ceil(len(s) / 4.2)

def normalize_spaces(txt: str) -> str:
    return re.sub(r"[ \t]+", " ", (txt or "").strip())

def split_sentences(text: str):
    return [s.strip() for s in re.split(r'(?<=[\.\?\!…])\s+', text) if s.strip()]

def split_soft(s: str):
    parts = re.split(r'(?<=[,;:–—])\s+', s)
    return [p.strip() for p in parts if p.strip()]

def decode_pcm(inline_data):
    if isinstance(inline_data, bytes): return inline_data
    if isinstance(inline_data, str):   return base64.b64decode(inline_data)
    raise RuntimeError("PCM không hỗ trợ định dạng trả về này.")

def save_pcm_to_wav(path, pcm_bytes):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS); wf.setsampwidth(SAMPLE_W); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)

# pacing
_req_times = collections.deque()
def pace_rpm():
    now = time.time()
    while _req_times and now - _req_times[0] > WINDOW_S:
        _req_times.popleft()
    if len(_req_times) >= MAX_RPM:
        time.sleep(max(0.0, WINDOW_S - (now - _req_times[0]) + 0.05))
    _req_times.append(time.time())

# ---------- Monologue TTS ----------
def chunk_text_tts(text: str, max_tokens: int = SAFE_TOKS):
    text = normalize_spaces(text)
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, buf, cur_tok = [], [], 0

    def flush():
        nonlocal chunks, buf, cur_tok
        if buf:
            chunks.append(" ".join(buf).strip()); buf.clear(); cur_tok = 0

    for p in paras:
        for sent in split_sentences(p):
            st = approx_tokens_tts(sent)
            if st <= max_tokens:
                if cur_tok + st + (1 if buf else 0) <= max_tokens:
                    buf.append(sent); cur_tok += st + (1 if buf else 0)
                else:
                    flush(); buf.append(sent); cur_tok = st
                continue
            # soft split
            soft_parts = split_soft(sent)
            if len(soft_parts) == 1:
                flush(); chunks.append(sent); buf.clear(); cur_tok = 0
                continue
            tmp, tmp_tok = [], 0
            for sp in soft_parts:
                spt = approx_tokens_tts(sp) + (1 if tmp else 0)
                if tmp_tok + spt <= max_tokens:
                    tmp.append(sp); tmp_tok += spt
                else:
                    sub = " ".join(tmp).strip()
                    if sub:
                        sub_tok = approx_tokens_tts(sub)
                        if cur_tok + sub_tok + (1 if buf else 0) <= max_tokens:
                            buf.append(sub); cur_tok += sub_tok + (1 if buf else 0)
                        else:
                            flush(); buf.append(sub); cur_tok = sub_tok
                    tmp, tmp_tok = [sp], approx_tokens_tts(sp)
            sub = " ".join(tmp).strip()
            if sub:
                sub_tok = approx_tokens_tts(sub)
                if cur_tok + sub_tok + (1 if buf else 0) <= max_tokens:
                    buf.append(sub); cur_tok += sub_tok + (1 if buf else 0)
                else:
                    flush(); buf.append(sub); cur_tok = sub_tok
    flush()
    return chunks

def tts_once_monologue(client, text: str, voice_name: str = "Zephyr") -> bytes:
    pace_rpm()
    resp = client.models.generate_content(
        model=MODEL_TTS,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                ),
                language_code=LANG_CODE_TTS if LANG_CODE_TTS else None,
            ),
        ),
    )
    part = resp.candidates[0].content.parts[0]
    return decode_pcm(part.inline_data.data)

def synth_to_files(script_text: str, out_wav="monologue.wav", out_mp3="monologue.mp3", voice_name: str = "Zephyr"):
    api_key = (os.getenv("GEMINI_API_KEY_TTS")
               or os.getenv("GEMINI_API_KEY")
               or os.getenv("GEMINI_API_KEY_LLM"))
    if not api_key: raise RuntimeError("Thiếu API key.")
    script_text = normalize_spaces(script_text)
    if not script_text: raise RuntimeError("Input rỗng.")

    chunks = chunk_text_tts(script_text, SAFE_TOKS)
    client = genai.Client(api_key=api_key)

    segs = []
    with tempfile.TemporaryDirectory() as td:
        for i, ch in enumerate(chunks, 1):
            pcm = tts_once_monologue(client, ch, voice_name=voice_name)
            wpath = os.path.join(td, f"part_{i:03d}.wav")
            save_pcm_to_wav(wpath, pcm)
            segs.append(AudioSegment.from_wav(wpath))

    final = segs[0]
    for s in segs[1:]: final += s
    final = final.set_frame_rate(SAMPLE_RATE).set_channels(1)
    final.export(out_wav, format="wav")
    final.export(out_mp3, format="mp3")
    return {"wav": out_wav, "mp3": out_mp3, "chunks": len(chunks)}

# ---------- Dialogue TTS ----------
MODEL_TTS_INT = MODEL_TTS
LANG_CODE_INT = None

def approx_tokens_int(s: str) -> int:
    s = re.sub(r'(?mi)^\s*Speaker\s*\d+\s*[:：]\s*', '', s).strip()
    return math.ceil(len(s) / 4.2)

def normalize_int(txt: str) -> str:
    return re.sub(r"[ \t]+", " ", (txt or "")
                  .replace("\u00A0", " ")
                  .replace("\u202F", " ")
                  .replace("\uFEFF", " ")
                  ).strip()

def parse_turns(script: str) -> _List[_Tuple[str, str]]:
    lines = [l for l in script.splitlines() if l.strip()]
    turns, cur_spk, cur_buf = [], None, []
    pat = re.compile(r'^\s*(Speaker\s*\d+)\s*[:：]\s*(.*)$', re.I)
    for ln in lines:
        m = pat.match(ln)
        if m:
            if cur_spk is not None:
                full = f"{cur_spk}: " + " ".join(cur_buf).strip()
                turns.append((cur_spk, full))
            cur_spk = m.group(1).title().replace("  ", " ")
            cur_buf = [m.group(2)]
        else:
            if cur_spk is None: continue
            cur_buf.append(ln.strip())
    if cur_spk is not None:
        full = f"{cur_spk}: " + " ".join(cur_buf).strip()
        turns.append((cur_spk, full))
    return turns

def make_chunks_by_turn(turns: _List[_Tuple[str, str]], max_tokens: int = SAFE_TOKS) -> _List[str]:
    chunks, buf, tok = [], [], 0
    for spk, utt in turns:
        t = approx_tokens_int(utt)
        if t > max_tokens:
            raise RuntimeError(f"Lượt nói của {spk} vượt ngưỡng an toàn ~{t} > {max_tokens} tokens.")
        add = t + (1 if buf else 0)
        if tok + add <= max_tokens:
            buf.append(utt); tok += add
        else:
            chunks.append(" ".join(buf)); buf, tok = [utt], t
    if buf: chunks.append(" ".join(buf))
    return chunks

_req_times_int = collections.deque()
def pace_rpm_int():
    now = time.time()
    while _req_times_int and now - _req_times_int[0] > WINDOW_S:
        _req_times_int.popleft()
    if len(_req_times_int) >= MAX_RPM:
        time.sleep(max(0.0, WINDOW_S - (now - _req_times_int[0]) + 0.05))
    _req_times_int.append(time.time())

def tts_once_int(client, text: str, speaker_voice: _Dict[str, str]) -> bytes:
    pace_rpm_int()
    spk_cfgs = [
        types.SpeakerVoiceConfig(
            speaker=spk,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v)
            ),
        ) for spk, v in speaker_voice.items()
    ]
    resp = client.models.generate_content(
        model=MODEL_TTS_INT,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=spk_cfgs
                ),
                language_code=LANG_CODE_INT if LANG_CODE_INT else None,
            ),
        ),
    )
    part = resp.candidates[0].content.parts[0]
    return decode_pcm(part.inline_data.data)

def synth_dialogue(script_text: str,
                   out_wav="dialogue_audio.wav",
                   out_mp3="dialogue_audio.mp3",
                   speaker_voice: _Dict[str, str] | None = None):
    api_key = (os.getenv("GEMINI_API_KEY_TTS")
               or os.getenv("GEMINI_API_KEY")
               or os.getenv("GEMINI_API_KEY_LLM"))
    if not api_key: raise RuntimeError("Thiếu API key.")
    script = normalize_int(script_text)
    if not script: raise RuntimeError("Input rỗng.")

    if not speaker_voice:
        speaker_voice = {"Speaker 1": "Zephyr", "Speaker 2": "Puck"}

    turns = parse_turns(script)
    if not turns: raise RuntimeError("Không tìm thấy lượt nói 'Speaker X:' trong input.")
    chunks = make_chunks_by_turn(turns, SAFE_TOKS)

    client = genai.Client(api_key=api_key)
    segs = []
    with tempfile.TemporaryDirectory() as td:
        for i, ch in enumerate(chunks, 1):
            pcm = tts_once_int(client, ch, speaker_voice)
            wpath = os.path.join(td, f"part_{i:03d}.wav")
            save_pcm_to_wav(wpath, pcm)
            segs.append(AudioSegment.from_wav(wpath))

    final = segs[0]
    for s in segs[1:]: final += s
    final = final.set_frame_rate(SAMPLE_RATE).set_channels(1)
    final.export(out_wav, format="wav")
    final.export(out_mp3, format="mp3")
    return {"wav": out_wav, "mp3": out_mp3, "chunks": len(chunks), "turns": len(turns)}