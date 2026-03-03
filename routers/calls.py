from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from models.schemas import (
    InitiateCallRequest, CallResponse, HealthResponse
)
from services.call_service import call_service

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/initiate", response_model=CallResponse)
async def initiate_call(request: InitiateCallRequest):
    """
    Initiate a new sales call with a lead
    """
    try:
        call = call_service.create_call(request)
        return call
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/end")
async def end_call(call_id: str):
    """
    End an active call
    """
    success = call_service.end_call(call_id)
    if not success:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return {"status": "success", "message": "Call ended", "call_id": call_id}


@router.get("/{call_id}")
async def get_call(call_id: str):
    """
    Get call details and current state
    """
    call = call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return call


@router.websocket("/ws/{call_id}")
async def websocket_endpoint(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time call updates
    """
    await websocket.accept()
    
    call = call_service.get_call(call_id)
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
        
        # Start call simulation
        await call_service.simulate_call_flow(call_id, websocket)
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
            
    except WebSocketDisconnect:
        print(f"Client disconnected from call {call_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
