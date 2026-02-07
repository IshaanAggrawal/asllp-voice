from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting FastAPI WebSocket Server...")
    logger.info(f"Ollama URL: {os.getenv('OLLAMA_BASE_URL')}")
    logger.info(f"Model Provider: {os.getenv('MODEL_PROVIDER')}")
    yield
    logger.info("Shutting down FastAPI WebSocket Server...")


# Initialize FastAPI app
app = FastAPI(
    title="Voice Orchestration WebSocket Server",
    description="Real-time AI voice agent streaming service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import WebSocket handler
from websocket_handler import handle_voice_stream


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Voice Orchestration WebSocket Server",
        "model_provider": os.getenv("MODEL_PROVIDER", "ollama")
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "ollama_url": os.getenv("OLLAMA_BASE_URL"),
        "conversational_model": os.getenv("OLLAMA_CONVERSATIONAL_MODEL"),
        "orchestration_model": os.getenv("OLLAMA_ORCHESTRATION_MODEL")
    }


@app.websocket("/ws/voice/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice streaming
    
    Message Protocol:
    Client -> Server:
        - {"type": "audio_chunk", "data": "base64_audio", "timestamp": 123456}
        - {"type": "end_stream"}
    
    Server -> Client:
        - {"type": "transcript", "text": "...", "is_final": true}
        - {"type": "agent_response", "text": "...", "audio": "base64_audio"}
        - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        await handle_voice_stream(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection {session_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Internal server error: {str(e)}"
            })
        except:
            pass
    finally:
        logger.info(f"Closing WebSocket for session: {session_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", 8001)),
        reload=os.getenv("FASTAPI_RELOAD", "True") == "True"
    )
