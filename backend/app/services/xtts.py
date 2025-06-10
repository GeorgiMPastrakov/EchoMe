"""
Tiny wrapper around your XTTS inference code.

For now it just returns a placeholder file path.
Replace `synthesize()` with actual XTTS inference when ready.
"""
from uuid import uuid4
from pathlib import Path

AUDIO_OUT = Path("static/generated")
AUDIO_OUT.mkdir(parents=True, exist_ok=True)


async def synthesize(text: str, voice_path: str) -> str:
    # TODO: call your XTTS model here. For demo, copy source file.
    out_file = AUDIO_OUT / f"{uuid4().hex}.wav"
    with open(voice_path, "rb") as src, open(out_file, "wb") as dst:
        dst.write(src.read())
    return str(out_file)
