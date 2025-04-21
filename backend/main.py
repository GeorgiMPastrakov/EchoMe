#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uvicorn
import shutil
import os
import base64
from io import BytesIO
from gradio_client import Client
from db import engine, SessionLocal, Base
import models, schemas

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# File paths
UPLOAD_DIR = "uploaded_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ ROUTES ------------------------

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(400, "Username already registered")
    hashed = pwd_context.hash(user.password)
    new_user = models.User(username=user.username, password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(400, "Invalid username or password")
    return db_user

@app.post("/upload_audio", response_model=schemas.VoiceResponse)
async def upload_audio(
    user_id: int = Form(...),
    voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = audio_file.filename
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buf:
        shutil.copyfileobj(audio_file.file, buf)
    voice = models.Voice(
        user_id=user_id,
        voice_name=voice_name,
        audio_file=file_path,
        embedding_file=""
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice

@app.post("/generate_audio")
def generate_audio(
    voice_id: int = Body(...),
    text: str = Body(...),
    db: Session = Depends(get_db),
):
    # Step 1: Fetch user's stored WAV file
    voice = db.query(models.Voice).get(voice_id)
    if not voice:
        raise HTTPException(404, "Voice not found")
    local_wav = voice.audio_file

    # Step 2: Call OpenVoice Gradio API
    client = Client("https://myshell-ai-openvoice.hf.space/--replicas/pe0v7/")
    try:
        result = client.predict(
            text,
            "default",
            local_wav,
            True,
            fn_index=1
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(502, f"TTS service error: {e}")

    # Step 3: Validate result
    if not isinstance(result, (list, tuple)) or len(result) != 3:
        raise HTTPException(502, f"Unexpected TTS response: {result}")

    info_text, synthesized_audio_url, _ = result

    if not synthesized_audio_url:
        raise HTTPException(502, "TTS response missing audio output")

    # Step 4: Decode audio
    if isinstance(synthesized_audio_url, str) and synthesized_audio_url.startswith("data:audio"):
        try:
            _, b64 = synthesized_audio_url.split(",", 1)
            audio_bytes = base64.b64decode(b64)
            return StreamingResponse(BytesIO(audio_bytes), media_type="audio/wav")
        except Exception as e:
            raise HTTPException(500, f"Error decoding audio: {e}")
    else:
        # fallback: non-data URL result (rare, maybe a hosted URL)
        return {"info": info_text, "synthesized_audio_url": synthesized_audio_url}

@app.get("/voices")
def get_voices(user_id: int, db: Session = Depends(get_db)):
    voices = db.query(models.Voice).filter(models.Voice.user_id == user_id).all()
    return [schemas.VoiceResponse.from_orm(v) for v in voices]

# -------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
