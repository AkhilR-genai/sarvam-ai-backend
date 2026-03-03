"""
Real Call Router - Uses actual Sarvam AI and Twilio integration
This replaces the simulated call router when ENABLE_REAL_CALLS=true
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from models.schemas import InitiateCallRequest, CallResponse
from services.real_call_service import real_call_service

router = APIRouter(prefix="/api/real-calls", tags=["real-calls"])


@router.post("/initiate", response_model=CallResponse)
async def initiate_real_call(request: InitiateCallRequest):
    """
    Initiate a REAL phone call using Twilio + Sarvam AI
    
    This will:
    1. Create call session
    2. Make actual outbound call via Twilio
    3. Use Sarvam AI for speech recognition and generation
    """
    try:
        call = await real_call_service.create_call(request)
        return call
    except RuntimeError as e:
        message = str(e)
        if "Daily real-call limit reached" in message:
            raise HTTPException(status_code=429, detail=message)
        raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@router.get("/usage")
async def get_real_call_usage():
    """Get current daily usage and remaining real-call budget"""
    return real_call_service.get_usage_stats()


@router.post("/{call_id}/end")
async def end_real_call(call_id: str):
    """
    End a real call and get call details
    """
    success = await real_call_service.end_call(call_id)
    if not success:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call_data = real_call_service.get_call(call_id)
    
    return {
        "status": "success",
        "message": "Call ended",
        "call_id": call_id,
        "duration": call_data.get("timer", 0),
        "recording_url": call_data.get("recording_url"),
        "messages": call_data.get("messages", []),
        "deal_probability": call_data.get("deal_probability", 0)
    }


@router.get("/{call_id}")
async def get_real_call(call_id: str):
    """
    Get call details including all messages and analytics
    """
    call = real_call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return call


@router.websocket("/ws/{call_id}")
async def websocket_real_call(websocket: WebSocket, call_id: str):
    """
    WebSocket for real-time call updates
    In real implementation, this would stream live audio and transcriptions
    """
    await websocket.accept()
    
    call = real_call_service.get_call(call_id)
    if not call:
        await websocket.close(code=1008, reason="Call not found")
        return
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "call_id": call_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # In real implementation, this would:
        # 1. Stream audio from Twilio Media Streams
        # 2. Process with Sarvam AI STT in real-time
        # 3. Generate AI responses
        # 4. Send TTS audio back to Twilio
        
        # For now, keep connection alive for status updates
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            
    except WebSocketDisconnect:
        print(f"Client disconnected from real call {call_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
