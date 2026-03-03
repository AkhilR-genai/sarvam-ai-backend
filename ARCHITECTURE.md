# 🏗️ **Sarvam AI Integration Architecture**

## **How Real Calls Work with Sarvam AI**

---

## **Current Implementation: Simulation Mode** ⚙️

Your current code is in **DEMO MODE** - it simulates conversations but doesn't make real calls.

**What it does:**
- ✅ Beautiful UI with animations
- ✅ Simulated conversation flow
- ✅ Mock sentiment analysis
- ✅ WebSocket real-time updates
- ❌ No actual phone calls
- ❌ No real voice synthesis
- ❌ No speech recognition

---

## **Enterprise Implementation: Real Calls** 🚀

### **Architecture Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  - User Interface                                               │
│  - WebSocket client for real-time updates                      │
│  - Audio player (for monitoring)                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS REST API
                             │ WebSocket
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Call Orchestration Service                              │  │
│  │  - Manages call lifecycle                                │  │
│  │  - Coordinates between APIs                              │  │
│  │  - Real-time WebSocket updates                           │  │
│  └─────────┬───────────────────────┬────────────────────────┘  │
│            │                       │                            │
│            ↓                       ↓                            │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │  Sarvam AI       │    │  Telephony       │                 │
│  │  Service         │    │  Service         │                 │
│  │  - TTS           │    │  - Call control  │                 │
│  │  - STT           │    │  - Audio routing │                 │
│  │  - LLM/Chat      │    │  - Recording     │                 │
│  └──────────────────┘    └──────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
            │                         │
            │ API Calls               │ API Calls
            ↓                         ↓
┌─────────────────────┐    ┌─────────────────────┐
│   SARVAM AI APIs    │    │    TWILIO APIs      │
│  ━━━━━━━━━━━━━━━━━  │    │  ━━━━━━━━━━━━━━━━━  │
│  • Text-to-Speech   │    │  • Voice Calls      │
│  • Speech-to-Text   │    │  • SIP Trunking     │
│  • Conversation AI  │    │  • Media Streams    │
│  • Language Models  │    │  • Call Recording   │
│  • Sentiment        │    │  • Number Routing   │
└─────────────────────┘    └──────────┬──────────┘
                                      │
                                      │ Phone Network
                                      ↓
                            ┌──────────────────────┐
                            │   LEAD'S PHONE       │
                            │   📱 +91 9876543210  │
                            └──────────────────────┘
```

---

## **🎯 Real Call Flow: Step-by-Step**

### **Phase 1: Call Initiation (0-3 seconds)**

```
1. User clicks "Initiate Call" in frontend
   └─→ Sends: POST /api/real-calls/initiate
       {
         "country_code": "+91",
         "mobile": "9876543210",
         "lead_name": "Rahul Kumar",
         "purpose": "sales",
         "crm_tag": "warm",
         "voice_personality": "professional"
       }

2. Backend (real_call_service.py):
   ├─→ Creates call session with unique ID
   ├─→ Stores lead information
   └─→ Calls Twilio API

3. Twilio API:
   ├─→ Makes outbound call to +91-9876543210
   ├─→ Returns: call_sid = "CA123456789"
   └─→ Lead's phone starts ringing 📱🔔

4. Backend responds to frontend:
   {
     "call_id": "uuid-abc-123",
     "status": "ringing",
     "twilio_call_sid": "CA123456789"
   }

5. Frontend:
   ├─→ Opens WebSocket connection
   ├─→ Shows "Ringing..." animation
   └─→ Displays orb pulsing
```

---

### **Phase 2: Lead Answers (3-7 seconds)**

```
6. Lead picks up phone
   │
   └─→ Twilio detects answer

7. Twilio → Your Backend Webhook:
   POST /api/twilio/voice/{call_id}
   {
     "CallStatus": "in-progress",
     "From": "+919876543210",
     "To": "+1234567890"
   }

8. Backend generates greeting:
   ├─→ Calls: telephony_service.generate_greeting_twiml()
   └─→ Returns TwiML:
       <Response>
         <Gather input="speech" language="en-IN">
           <Say voice="Polly.Aditi-Neural">
             Hello Rahul! This is Sarvam AI calling...
           </Say>
         </Gather>
       </Response>

9. Twilio plays greeting to lead
   │
   └─→ Lead hears: "Hello Rahul! This is Sarvam AI calling..."

10. Backend → Frontend via WebSocket:
    {
      "type": "status_update",
      "status": "ai-speaking",
      "message": "Hello Rahul! This is Sarvam AI calling..."
    }

11. Frontend displays:
    ├─→ Orb animates (purple waves)
    ├─→ Shows message in conversation log
    └─→ Status: "AI Speaking"
```

---

### **Phase 3: Lead Responds (7-15 seconds)**

```
12. Lead speaks: "Yes, I'm interested"
    │
    └─→ Twilio captures audio

13. Twilio has TWO options for speech processing:

    OPTION A: Use Twilio's built-in STT
    ├─→ Twilio → Webhook: POST /api/twilio/process-speech/{call_id}
    │   {
    │     "SpeechResult": "Yes, I'm interested"
    │   }
    └─→ Get text directly

    OPTION B: Use Sarvam AI STT (Better for Indian accents)
    ├─→ Twilio → Webhook with RecordingUrl
    ├─→ Backend downloads audio
    ├─→ Backend → Sarvam AI STT API:
    │   {
    │     "file": audio_bytes,
    │     "language_code": "en-IN",
    │     "model": "saarika:v1"
    │   }
    └─→ Sarvam AI returns: "Yes, I'm interested"

14. Backend processes lead's response:
    ├─→ sarvam_ai_service.analyze_sentiment()
    │   Returns: {
    │     "sentiment": "positive",
    │     "confidence": 85,
    │     "has_objection": false
    │   }
    │
    ├─→ Creates message record
    └─→ Updates deal_probability: +15%

15. Backend → Frontend via WebSocket:
    {
      "type": "message",
      "message": {
        "role": "lead",
        "content": "Yes, I'm interested",
        "timestamp": "2026-03-03T10:30:15"
      },
      "sentiment": "positive",
      "confidence": 85,
      "deal_probability": 65,
      "status": "ai-thinking"
    }

16. Frontend updates:
    ├─→ Shows lead message (right side, cyan)
    ├─→ Displays 😊 positive sentiment
    ├─→ Updates deal probability: 65%
    └─→ Status changes to "AI Thinking"
```

---

### **Phase 4: AI Generates Response (15-20 seconds)**

```
17. Backend generates intelligent response:
    ├─→ sarvam_ai_service.generate_response()
    │   Parameters:
    │   - lead_message: "Yes, I'm interested"
    │   - conversation_history: [previous messages]
    │   - lead_info: {name, crm_tag, purpose}
    │   - product_info: {description, features, pricing}
    │
    └─→ Calls Sarvam AI LLM API:
        POST https://api.sarvam.ai/v1/chat/completions
        {
          "model": "sarvam-2b-v0.5",
          "messages": [
            {
              "role": "system",
              "content": "You are an AI sales agent for..."
            },
            {
              "role": "user",
              "content": "Yes, I'm interested"
            }
          ],
          "temperature": 0.7,
          "max_tokens": 150
        }

18. Sarvam AI LLM responds:
    {
      "choices": [{
        "message": {
          "content": "That's great to hear, Rahul! Let me tell you 
                     about our ROI. Most clients see 40% efficiency 
                     gains within the first month. Would you like 
                     to schedule a demo this week?"
        }
      }]
    }

19. Backend converts text to speech:
    ├─→ sarvam_ai_service.text_to_speech()
    │   POST https://api.sarvam.ai/v1/text-to-speech
    │   {
    │     "text": "That's great to hear, Rahul!...",
    │     "language_code": "en-IN",
    │     "speaker": "meera",
    │     "model": "bulbul:v1"
    │   }
    │
    └─→ Sarvam AI returns: audio_bytes (WAV format)

20. Backend uploads audio to S3:
    ├─→ boto3.client('s3').put_object()
    └─→ Gets public URL: https://s3.../audio-123.wav

21. Backend generates TwiML response:
    <Response>
      <Gather input="speech" language="en-IN">
        <Play>https://s3.../audio-123.wav</Play>
      </Gather>
    </Response>

22. Twilio plays Sarvam AI's voice to lead
    │
    └─→ Lead hears natural AI voice speaking

23. Backend → Frontend via WebSocket:
    {
      "type": "message",
      "message": {
        "role": "ai",
        "content": "That's great to hear, Rahul!...",
        "timestamp": "2026-03-03T10:30:18"
      },
      "status": "ai-speaking",
      "deal_probability": 75
    }

24. Frontend displays AI message
```

---

### **Phase 5: Conversation Continues (20+ seconds)**

This cycle repeats:
```
Lead speaks → Sarvam AI STT → 
Backend processes → Sarvam AI LLM generates response → 
Sarvam AI TTS creates audio → Twilio plays to lead →
Lead speaks → ...
```

Each exchange includes:
- ✅ Real-time transcription
- ✅ Sentiment analysis
- ✅ Objection detection
- ✅ Context-aware responses
- ✅ Deal probability updates
- ✅ Frontend updates via WebSocket

---

### **Phase 6: Call Ends (Variable time)**

```
25. Either party hangs up
    │
    └─→ Twilio detects disconnect

26. Twilio → Status Webhook:
    POST /api/twilio/status/{call_id}
    {
      "CallStatus": "completed",
      "CallDuration": "180"  // 3 minutes
    }

27. Backend finalizes call:
    ├─→ Updates call status to "ended"
    ├─→ Saves conversation to database
    ├─→ Calculates final metrics
    └─→ Triggers analytics

28. Twilio → Recording Webhook:
    POST /api/twilio/recording/{call_id}
    {
      "RecordingUrl": "https://api.twilio.com/...",
      "RecordingSid": "RE123456789"
    }

29. Backend downloads and stores recording:
    ├─→ Download from Twilio
    ├─→ Upload to S3
    └─→ Save URL to database

30. Backend → Frontend via WebSocket:
    {
      "type": "call_ended",
      "call_id": "uuid-abc-123",
      "duration": 180,
      "messages_count": 12,
      "final_deal_probability": 82,
      "recording_url": "https://s3.../recording.mp3"
    }

31. Frontend displays call summary:
    ├─→ Total duration: 3:00
    ├─→ Messages exchanged: 12
    ├─→ Deal probability: 82%
    ├─→ Download recording button
    └─→ CRM update button
```

---

## **🔑 Key Integration Points**

### **1. Sarvam AI APIs Used:**

| API | Purpose | Endpoint |
|-----|---------|----------|
| **TTS** | Convert AI text to natural Indian voice | `/v1/text-to-speech` |
| **STT** | Convert lead speech to text | `/v1/speech-to-text` |
| **LLM** | Generate intelligent responses | `/v1/chat/completions` |

### **2. Twilio APIs Used:**

| API | Purpose | Endpoint |
|-----|---------|----------|
| **Voice** | Make outbound calls | `/Calls.json` |
| **TwiML** | Control call flow | Webhooks |
| **Media Streams** | Real-time audio | WebSocket |
| **Recordings** | Save call audio | `/Recordings.json` |

---

## **📊 Data Flow Summary**

```
User Input → Frontend → Backend → Twilio → Lead's Phone
                ↓
         WebSocket updates
                ↓
           Real-time UI

Lead Speech → Twilio → Backend → Sarvam AI STT → Text
                                        ↓
                                  Sentiment Analysis
                                        ↓
                                  Sarvam AI LLM → Response
                                        ↓
                                  Sarvam AI TTS → Audio
                                        ↓
                Twilio plays → Lead hears AI
```

---

## **💡 Why This Architecture?**

✅ **Scalable**: Each service is independent  
✅ **Reliable**: Failover and retry logic  
✅ **Cost-effective**: Pay per use  
✅ **Low latency**: Optimized API calls  
✅ **Enterprise-ready**: Monitoring, logging, analytics  
✅ **Multi-language**: Sarvam handles Indian languages  
✅ **Natural voice**: Better than generic TTS  

---

## **🚀 To Go Live:**

1. ✅ Get Sarvam AI API key
2. ✅ Set up Twilio account  
3. ✅ Configure webhooks (must be HTTPS)
4. ✅ Deploy backend to cloud
5. ✅ Update environment variables
6. ✅ Test end-to-end
7. ✅ Monitor and optimize

**Your code is already structured for this - just need the API keys!** 🎯
