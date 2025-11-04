import os, json
from orchestrator import PodcastOrchestrator, PodcastConfig

if __name__ == "__main__":
    # ví dụ: đọc từ ENV hoặc file JSON/front-end ghi xuống
    duration   = os.getenv("CFG_DURATION", "ngắn (2-3 phút)")
    style      = os.getenv("CFG_STYLE", "học thuật")
    characters = int(os.getenv("CFG_CHARACTERS", "1"))

    # tài liệu đầu vào??
    with open("input.txt", "r", encoding="utf-8") as f:
        document = f.read()

    orch = PodcastOrchestrator(max_tokens_per_chunk=500)
    cfg = PodcastConfig(duration=duration, style=style, characters=characters)
    out = orch.run(document, cfg)
    print(json.dumps(out["audio"], ensure_ascii=False, indent=2))
