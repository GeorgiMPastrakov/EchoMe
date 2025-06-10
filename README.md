# EchoMe

A lightweight **voice-cloning + text-to-speech** web app  
*Streamlit front-end · FastAPI back-end · Coquí-TTS XTTS v2 engine*

---

## ✨ Features

| Capability | Notes |
|------------|-------|
| **Sign up / Log in** | Stored in MySQL (`users` table) |
| **Upload or record a reference voice** | Any format accepted; server auto-converts to 16 kHz 16-bit mono WAV |
| **Clone + speak** | Multilingual XTTS v2 runs locally (CPU or CUDA) |
| **Browser playback** | Generated WAV returned as a Base-64 data URI |
| **REST API** | `/signup`, `/login`, `/upload_audio`, `/voices`, `/generate_audio` |

---

## 1  Prerequisites

| Component | Tested version |
|-----------|----------------|
| Python 3.11 | |
| MySQL 8.x   | Database **echome**, user **echo_user** |
| FFmpeg      | For audio conversion |
| (optional) NVIDIA GPU | CUDA 12.1 driver |

---

## 2  Clone & create a venv

```bash
git clone https://github.com/your-user/echo-me.git
cd echo-me
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
