from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List

from models.schemas import HealthResponse
from routers import calls, product

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Sarvam AI Voice Agent API",
    description="Backend API for AI-powered voice sales agent with Sarvam AI integration",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Demo/Simulation mode
app.include_router(calls.router)

# Real call mode (requires Sarvam AI + Twilio)
enable_real_calls = os.getenv("ENABLE_REAL_CALLS", "false").lower() == "true"
if enable_real_calls:
    required_env_vars: List[str] = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "WEBHOOK_BASE_URL"
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if not (os.getenv("SARVAM_AI_API_KEY") or os.getenv("SARVAM_API_KEY")):
        missing_vars.append("SARVAM_AI_API_KEY (or SARVAM_API_KEY)")

    if missing_vars:
        print("❌ Real call mode requested but missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("ℹ️  Falling back to simulation mode. Set ENABLE_REAL_CALLS=false or provide all required variables.")
        enable_real_calls = False
    else:
        from routers import real_calls, twilio_webhooks
        app.include_router(real_calls.router)
        app.include_router(twilio_webhooks.router)
        print("✅ Real call mode enabled (Sarvam AI + Twilio)")
else:
    print("ℹ️  Running in simulation mode (demo)")

# Product knowledge
app.include_router(product.router)

# Ensure static/audio directory exists for Sarvam AI TTS audio files
os.makedirs("static/audio", exist_ok=True)

# Mount static files for serving Sarvam AI TTS audio
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Sarvam AI Voice Agent API is running",
        timestamp=datetime.now()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        message="All systems operational",
        timestamp=datetime.now()
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*60)
    print("🚀 Starting Sarvam AI Voice Agent Backend")
    print("="*60)
    print(f"📡 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🎯 Mode: {'Real Calls (Sarvam AI + Twilio)' if enable_real_calls else 'Simulation (Demo)'}")
    print("="*60 + "\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
