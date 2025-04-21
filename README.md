# 🎤 EchoMe — Real-Time Voice Cloning Web App

EchoMe is a real-time voice cloning web app that lets users upload or record their voice, type a message, and generate speech that sounds just like them. Designed for accessibility, emotional connection, and digital creativity, EchoMe brings your voice into the digital world.

## 🌟 Features

- 🔊 Upload or record your voice
- 💬 Type any text to generate AI speech in your voice
- 🎭 Choose from emotional styles: cheerful, whispering, sad, etc.
- 👁️‍🗨️ Great for blind users — they can hear who is "speaking"
- 📖 Read bedtime stories using your own voice, even remotely
- 🧠 Built with FastAPI, Streamlit, and OpenVoice

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** FastAPI + SQLAlchemy + MySQL
- **Voice Cloning:** OpenVoice (via Hugging Face Spaces) and RTVC (optional)
- **Authentication:** Custom user system with login/signup
- **Hosting:** Cloudflare Tunnel / Render / local

## 🚀 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/EchoMe.git
cd EchoMe
