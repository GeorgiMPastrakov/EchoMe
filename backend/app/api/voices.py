import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_db, get_current_user
from ..models.voice import Voice
from ..schemas.voice import VoiceRead

AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.post("/upload", response_model=VoiceRead, status_code=201)
async def upload_voice(
    label: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    uid = uuid.uuid4().hex
    ext = Path(file.filename).suffix or ".wav"
    filename = f"{uid}{ext}"
    dest = AUDIO_DIR / filename

    # Save to disk
    with dest.open("wb") as f:
        f.write(await file.read())

    voice = Voice(user_id=user.id, label=label, filename=filename)
    db.add(voice)
    await db.commit()
    await db.refresh(voice)
    return voice


@router.post("/record", response_model=VoiceRead, status_code=201)
async def record_voice(
    label: str = Form(...),
    file: UploadFile = File(...),          # browser recording blob arrives same way
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await upload_voice(label, file, db, user)  # reuse same logic


@router.get("/", response_model=list[VoiceRead])
async def list_voices(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    res = await db.execute(select(Voice).where(Voice.user_id == user.id))
    return res.scalars().all()
