from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from gradio_client import Client
import shutil, os, base64, uuid
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
    unique_filename = f"{uuid.uuid4()}.wav"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
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
    style: str | None = Body(None),
    db: Session = Depends(get_db),
):
    # 1) fetch reference voice
    voice = db.get(models.Voice, voice_id)
    if not voice:
        raise HTTPException(404, "Voice not found")

    reference_wav = os.path.abspath(voice.audio_file)

    # 2) optional style tag at the front of the prompt
    if style and style.lower() != "default":
        text = f"[{style}] {text}"

    # 3) call the root Space URL (replica slug changes on every restart)
    client = Client(os.getenv("XTTS_SPACE_URL", "https://coqui-xtts.hf.space/"))

    try:
        # Space’s main fn (fn_index=0) returns 4 items; item 1 = WAV path
        result = client.predict(
            text,            # prompt
            "en",            # language code
            reference_wav,   # reference voice
            None,            # microphone wav (none)
            False,           # use_mic
            False,           # voice_cleanup
            True,            # no_lang_auto_detect
            True,            # agree to T&C
            fn_index=0
        )
    except Exception as e:
        raise HTTPException(502, f"TTS service error: {e}")

    if not isinstance(result, (list, tuple)) or len(result) < 2:
        raise HTTPException(502, "Unexpected TTS response format")

    wav_path = result[1]
    if not os.path.exists(wav_path):
        raise HTTPException(500, "Generated audio file not found")

    # 4) read → base64 → data-URI
    with open(wav_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
        audio_uri = f"data:audio/wav;base64,{encoded}"

    # tidy up temp file (optional)
    try:
        os.remove(wav_path)
    except OSError:
        pass

    return JSONResponse(content={"audio": audio_uri})