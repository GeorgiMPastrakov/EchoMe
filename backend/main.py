from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import shutil, os, base64, uuid
import torch, soundfile as sf
from TTS.api import TTS

from db import engine, SessionLocal, Base
import models, schemas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "uploaded_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

Base.metadata.create_all(bind=engine)

device = "cuda" if torch.cuda.is_available() else "cpu"
tts_engine = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(400, "Username already registered")
    new_user = models.User(
        username=user.username,
        password=pwd_context.hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(400, "Invalid username or password")
    return db_user

@app.post("/upload_audio", response_model=schemas.VoiceResponse)
def upload_audio(
    user_id: int = Form(...),
    voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    public_name = f"{uuid.uuid4()}.wav"
    disk_path = os.path.join(UPLOAD_DIR, public_name)

    with open(disk_path, "wb") as buf:
        shutil.copyfileobj(audio_file.file, buf)

    voice = models.Voice(
        user_id=user_id,
        voice_name=voice_name,
        audio_file=f"/uploads/{public_name}",
        embedding_file="",
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice

@app.get("/voices", response_model=list[schemas.VoiceResponse])
def get_voices(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Voice).filter(
        models.Voice.user_id == user_id
    ).all()

class GenReq(BaseModel):
    voice_id: int
    text: str
    style: str | None = None

@app.post("/generate_audio")
def generate_audio(req: GenReq, db: Session = Depends(get_db)):
    voice = db.get(models.Voice, req.voice_id)
    if not voice:
        raise HTTPException(404, "Voice not found")

    if voice.audio_file.startswith("/uploads/"):
        filename = voice.audio_file.split("/uploads/")[-1]
        ref_path = os.path.join(UPLOAD_DIR, filename)
    else:
        ref_path = voice.audio_file

    if not os.path.exists(ref_path):
        raise HTTPException(500, "Reference WAV missing on disk")

    spoken_text = (
        f"[{req.style}] {req.text}"
        if req.style and req.style.lower() != "default"
        else req.text
    )

    wav = tts_engine.tts(
        text=spoken_text,
        speaker_wav=ref_path,
        language="en",
    )

    out_file = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.wav")
    sf.write(out_file, wav, samplerate=tts_engine.synthesizer.output_sample_rate)

    with open(out_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    os.remove(out_file)

    return JSONResponse(content={"audio": f"data:audio/wav;base64,{b64}"})
