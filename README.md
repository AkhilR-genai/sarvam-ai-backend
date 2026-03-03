# Sarvam AI Voice Agent Backend

FastAPI backend for the Sarvam AI Voice Agent application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy .env.example to .env and configure:
```bash
cp .env.example .env
```

3. For real calls (Sarvam + Twilio), set:
- `ENABLE_REAL_CALLS=true`
- `SARVAM_AI_API_KEY` (or `SARVAM_API_KEY`)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `WEBHOOK_BASE_URL`
- Optional: `MAX_REAL_CALLS_PER_DAY=2` to protect credits

4. Run the server:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

## API Endpoints

### REST Endpoints
- `GET /` - Health check
- `POST /api/calls/initiate` - Initiate a new call
- `POST /api/calls/{call_id}/end` - End an active call
- `GET /api/calls/{call_id}` - Get call details
- `POST /api/product/save` - Save product knowledge base

### Real Call Endpoints (when `ENABLE_REAL_CALLS=true`)
- `POST /api/real-calls/initiate` - Initiate real Twilio + Sarvam call
- `POST /api/real-calls/{call_id}/end` - End real call
- `GET /api/real-calls/{call_id}` - Get real call details
- `GET /api/real-calls/usage` - See daily usage and remaining real-call budget

### WebSocket
- `WS /ws/{call_id}` - Real-time call updates

## Development

The backend is structured as follows:
- `main.py` - Main application entry point
- `models/` - Pydantic models
- `services/` - Business logic
- `routers/` - API route handlers
