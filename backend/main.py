from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uvicorn
import shutil, os
from db import engine, SessionLocal, Base
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return db_user

@app.post("/upload_audio", response_model=schemas.VoiceResponse)
async def upload_audio(
    user_id: int = Form(...),
    voice_name: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    audio_folder = "uploaded_audio"
    os.makedirs(audio_folder, exist_ok=True)
    file_path = os.path.join(audio_folder, audio_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    dummy_embedding = "not_generated_yet"
    
    voice = models.Voice(
        user_id=user_id,
        voice_name=voice_name,
        audio_file=file_path,
        embedding_file=dummy_embedding
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice

@app.post("/generate_audio")
def generate_audio(voice_id: int, text: str, db: Session = Depends(get_db)):
    voice = db.query(models.Voice).filter(models.Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    generated_folder = "generated_audio"
    os.makedirs(generated_folder, exist_ok=True)
    output_file = os.path.join(generated_folder, f"{voice_id}_output.wav")
    shutil.copy(voice.audio_file, output_file)
    
    return FileResponse(output_file, media_type="audio/wav")

@app.get("/voices")
def get_voices(user_id: int, db: Session = Depends(get_db)):
    voices = db.query(models.Voice).filter(models.Voice.user_id == user_id).all()
    return [schemas.VoiceResponse.from_orm(v) for v in voices]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)