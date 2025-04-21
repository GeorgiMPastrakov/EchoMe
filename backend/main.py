from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from gradio_client import Client
import shutil, os, base64
from db import engine, SessionLocal, Base
import models, schemas

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "uploaded_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

Base.metadata.create_all(bind=engine)

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
    new_user = models.User(username=user.username, password=pwd_context.hash(user.password))
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
    file_path = os.path.join(UPLOAD_DIR, audio_file.filename)
    with open(file_path, "wb") as buf:
        shutil.copyfileobj(audio_file.file, buf)
    voice = models.Voice(user_id=user_id, voice_name=voice_name, audio_file=file_path, embedding_file="")
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice

@app.get("/voices")
def get_voices(user_id: int, db: Session = Depends(get_db)):
    voices = db.query(models.Voice).filter(models.Voice.user_id == user_id).all()
    return [schemas.VoiceResponse.from_orm(v) for v in voices]

@app.post("/generate_audio")
def generate_audio(
    voice_id: int = Body(...),
    text: str = Body(...),
    style: str = Body(...),
    db: Session = Depends(get_db),
):
    voice = db.query(models.Voice).get(voice_id)
    if not voice:
        raise HTTPException(404, "Voice not found")

    local_wav = voice.audio_file
    client = Client("https://myshell-ai-openvoice.hf.space/--replicas/pe0v7/")

    try:
        result = client.predict(
            text,
            f"{style}",
            local_wav,
            True,
            fn_index=1
        )
        print("OpenVoice response:", result)
    except Exception as e:
        raise HTTPException(502, f"TTS service error: {e}")

    if not isinstance(result, (list, tuple)) or len(result) != 3:
        raise HTTPException(502, "Unexpected TTS response format")

    _, audio_output_path, _ = result

    if not os.path.exists(audio_output_path):
        raise HTTPException(500, "Generated audio file not found")

    try:
        with open(audio_output_path, "rb") as f:
            audio_bytes = f.read()
            encoded = base64.b64encode(audio_bytes).decode("utf-8")
            audio_data_uri = f"data:audio/wav;base64,{encoded}"
            return JSONResponse(content={"audio": audio_data_uri})
    except Exception as e:
        raise HTTPException(500, f"Failed to read or encode audio: {e}")