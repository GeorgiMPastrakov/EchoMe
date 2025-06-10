from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_current_user, get_db
from ..models.voice import Voice
from ..services.xtts import synthesize

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate")
async def generate_audio(
    voice_id: str,
    text: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    res = await db.execute(
        select(Voice).where(Voice.id == voice_id, Voice.user_id == user.id)
    )
    voice = res.scalar_one_or_none()
    if not voice:
        raise HTTPException(404, "Voice not found")

    source_audio = Path("static/audio") / voice.filename
    audio_url = await synthesize(text, str(source_audio))

    # Return relative URL for frontend player
    return {"audio_url": f"/{audio_url.replace(Path('.').as_posix() + '/', '')}"}
