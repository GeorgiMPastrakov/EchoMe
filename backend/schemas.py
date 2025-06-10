from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
            from_attributes = True

class VoiceResponse(BaseModel):
    id: int
    voice_name: str
    audio_file: str
    embedding_file: str

    class Config:
        from_attributes = True
