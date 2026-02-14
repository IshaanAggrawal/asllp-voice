# 🎙️ Real-Time AI Voice Orchestration Platform

A production-grade system for creating and managing AI voice agents with real-time speech-to-speech interaction. Built with a dual-LLM architecture (Qwen + LLaMA) and ultra-low latency voice pipeline.

## 🚀 Key Features

### 🧠 Dual-Model Intelligence
*   **Orchestrator (Qwen 1.5B)**: Fast intent classification and routing.
*   **Responder (LLaMA 3.2 1B)**: Natural, context-aware conversational responses.

### ⚡ Ultra-Low Latency Pipeline
*   **Deepgram Nova-2**: Industry-leading Speech-to-Text (STT).
*   **Cartesia Sonic**: Hyper-realistic Text-to-Speech (TTS) with <100ms latency.
*   **WebSocket Streaming**: Full duplex audio for real-time interaction.
*   **Smart Timeout**: 15s post-speech timeout with barge-in support.

### 🛡️ Enterprise Architecture
*   **User Isolation**: Strict data segregation (agents, sessions, logs).
*   **Secure Auth**: JWT-based authentication with auto-refresh.
*   **Robust Backend**: Django (Data/User) + FastAPI (Real-time).

### 📊 Professional Dashboard
*   **Agent Management**: Create/Edit custom system prompts.
*   **Real-time Analytics**: Monitor session status and duration.
*   **Live Transcripts**: View logs as they happen.

## 🏗️ Technical Stack

- **Frontend**: Streamlit (Reactive UI)
- **Backend API**: Django REST Framework
- **Real-time Server**: FastAPI + Uvicorn
- **Database**: PostgreSQL (via Django ORM)
- **AI Inference**: Ollama (Local LLMs)
- **Voice APIs**: Deepgram, Cartesia

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) running locally
- Deepgram & Cartesia API Keys

### 1. Clone & Environment
```bash
git clone https://github.com/IshaanAggrawal/asllp-voice.git
cd asllp-voice

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`backend/.env`)
Create a `.env` file in `backend/`:
```ini
# Core
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Voice APIs
DEEPGRAM_API_KEY=your-deepgram-key
CARTESIA_API_KEY=your-cartesia-key

# AI Models (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_ORCHESTRATION_MODEL=qwen2.5:1.5b
OLLAMA_CONVERSATIONAL_MODEL=llama3.2:1b
```

### 3. Initialize Database
```bash
cd backend/django_app
python manage.py migrate
python manage.py createsuperuser
```

### 4. Pull AI Models
```bash
ollama pull qwen2.5:1.5b
ollama pull llama3.2:1b
```

## 🏃‍♂️ Running the Platform

Run these commands in **3 separate terminals**:

**Terminal 1: Django Backend** (User/Data)
```bash
cd backend/django_app
python manage.py runserver 8000
```

**Terminal 2: FastAPI Server** (Voice WebSockets)
```bash
cd backend/fastapi_app
uvicorn main:app --reload --port 8001
```

**Terminal 3: Streamlit Frontend** (UI)
```bash
cd streamlit_app
streamlit run app.py
```

Access the app at: **http://localhost:8501**

## 📖 Usage Guide

1.  **Login**: Use your superuser account or register a new one.
2.  **Create Agent**: Go to "Create Agent" -> Name it -> Set Prompt (e.g., "You are a helpful travel guide").
3.  **Start Call**: Go to "Voice Call" -> Select Agent -> "Start Session".
4.  **Speak**: Allow mic access and talk. Interrupt anytime (Barge-in supported).
5.  **Review**: Check the Dashboard for logs and session history.

## 🧩 Architecture Flow

```mermaid
graph TD
    User[User Microphone] -->|WebSocket Audio| FastAPI[FastAPI Server]
    FastAPI -->|Stream| Deepgram[Deepgram STT]
    Deepgram -->|Text| Orchestrator[Qwen 1.5B (Intent)]
    Orchestrator -->|Intent + Context| Responder[LLaMA 1B (Response)]
    Responder -->|Text Response| Cartesia[Cartesia TTS]
    Cartesia -->|Audio Stream| User
    
    FastAPI -.->|Async Log| Django[Django ORM]
    Django <-->|Persist| DB[(PostgreSQL/SQLite)]
```

## 📄 License
MIT License. Free to use and modify.
