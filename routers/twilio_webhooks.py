"""
Twilio Webhook Router
Handles real-time voice call webhooks from Twilio
"""

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from services.real_call_service import real_call_service
from services.telephony_service import telephony_service
from services.sarvam_ai_service import sarvam_ai_service
import asyncio
import os
import uuid

router = APIRouter(prefix="/api/twilio", tags=["twilio"])


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhooks are reachable"""
    return {"status": "ok", "message": "Twilio webhooks are reachable"}

@router.post("/voice")
async def handle_generic_voice_webhook(request: Request):
    """
    Generic voice webhook for Twilio trial accounts
    Set this URL in Twilio Console: https://your-domain.com/api/twilio/voice
    """
    print(f"\n{'='*60}")
    print(f"🔔 GENERIC VOICE WEBHOOK CALLED")
    print(f"{'='*60}\n")
    
    form_data = await request.form()
    twilio_call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    print(f"Twilio Call SID: {twilio_call_sid}")
    print(f"Call Status: {call_status}")
    
    # Look up our call by Twilio SID
    call_data = real_call_service.get_call_by_twilio_sid(twilio_call_sid)
    
    if not call_data:
        print(f"⚠️ Call not found for Twilio SID: {twilio_call_sid}")
        return Response(
            content="<Response><Say voice='Polly.Aditi-Neural' language='en-IN'>Hello! This is a test call from Sarvam AI.</Say></Response>",
            media_type="application/xml"
        )
    
    call_id = call_data["call_id"]
    print(f"✅ Found call_id: {call_id}")
    
    # Generate greeting
    lead_name = call_data["lead_info"].lead_name
    
    try:
        print(f"🎤 Generating Sarvam AI TTS for greeting...")
        
        # Generate audio using Sarvam AI
        greeting_text = f"Hello {lead_name}! This is Sarvam AI calling. Am I speaking with the right person?"
        audio_bytes = await sarvam_ai_service.text_to_speech(
            text=greeting_text,
            language="en-IN"
        )
        
        # Save audio file
        audio_filename = f"{call_id}_greeting.wav"
        audio_path = os.path.join("static", "audio", audio_filename)
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Get webhook base URL
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        audio_url = f"{webhook_base}/static/audio/{audio_filename}"
        
        print(f"✅ Sarvam AI audio generated: {audio_url}")
        
        # Generate TwiML with Sarvam AI audio
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name,
            audio_url=audio_url
        )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Sarvam AI TTS failed: {e}, falling back to Twilio TTS")
        import traceback
        traceback.print_exc()
        
        # Fallback to Twilio TTS
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name
        )
        
        return Response(content=twiml, media_type="application/xml")

@router.post("/voice-generic")
async def handle_voice_webhook_generic(request: Request):
    """
    Generic voice webhook for Twilio Console configuration
    Works with trial accounts when URL is set in Twilio Console
    """
    print(f"\n{'='*60}")
    print(f"🔔 GENERIC VOICE WEBHOOK CALLED")
    print(f"{'='*60}\n")
    
    form_data = await request.form()
    twilio_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    print(f"Generic voice webhook: CallSid={twilio_sid}, Status={call_status}")
    print(f"All form data: {dict(form_data)}")
    
    # Find our call by Twilio SID
    call_id = None
    call_data = None
    for cid, cdata in real_call_service.active_calls.items():
        if cdata.get("twilio_call_sid") == twilio_sid:
            call_id = cid
            call_data = cdata
            print(f"✅ Found call by Twilio SID: {call_id}")
            break
    
    if not call_data:
        print(f"⚠️ Call not found in active calls, creating demo greeting")
        return Response(
            content="<Response><Say voice='Polly.Aditi-Neural' language='en-IN'>Hello! This is Sarvam AI calling. Unfortunately, I cannot find your call details. Please try again.</Say><Hangup/></Response>",
            media_type="application/xml"
        )
    
    # Generate greeting with Sarvam AI TTS
    lead_name = call_data["lead_info"].lead_name
    greeting_text = f"Hello {lead_name}! This is Sarvam AI calling. Am I speaking with the right person?"
    
    try:
        print(f"🎤 Generating Sarvam AI TTS for greeting...")
        
        # Generate audio using Sarvam AI
        audio_bytes = await sarvam_ai_service.text_to_speech(
            text=greeting_text,
            language="en-IN"
        )
        
        # Save audio file
        audio_filename = f"{call_id}_greeting.wav"
        audio_path = os.path.join("static", "audio", audio_filename)
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Get webhook base URL
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        audio_url = f"{webhook_base}/static/audio/{audio_filename}"
        
        print(f"✅ Sarvam AI audio generated: {audio_url}")
        
        # Generate TwiML with Sarvam AI audio
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name,
            audio_url=audio_url
        )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Sarvam AI TTS failed: {e}, falling back to Twilio TTS")
        import traceback
        traceback.print_exc()
        
        # Fallback to Twilio TTS
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name
        )
        
        return Response(content=twiml, media_type="application/xml")


@router.post("/voice/{call_id}")
async def handle_voice_webhook(call_id: str, request: Request):
    """
    Handle initial voice webhook when call connects
    Twilio calls this endpoint when the lead answers
    """
    print(f"\n{'='*60}")
    print(f"🔔 VOICE WEBHOOK CALLED FOR: {call_id}")
    print(f"{'='*60}\n")
    
    form_data = await request.form()
    call_status = form_data.get("CallStatus")
    
    # Log ALL form data for debugging
    print(f"Voice webhook for call {call_id}: Status={call_status}")
    print(f"All form data: {dict(form_data)}")
    
    call_data = real_call_service.get_call(call_id)
    if not call_data:
        # Try to find by Twilio SID as fallback
        twilio_sid = form_data.get("CallSid")
        print(f"⚠️ Call not found by ID, looking up by Twilio SID: {twilio_sid}")
        for cid, cdata in real_call_service.active_calls.items():
            if cdata.get("twilio_call_sid") == twilio_sid:
                call_id = cid
                call_data = cdata
                print(f"✅ Found call by Twilio SID: {call_id}")
                break
    
    if not call_data:
        return Response(content="<Response><Say>Call not found</Say></Response>", media_type="application/xml")
    
    # Generate greeting with Sarvam AI TTS
    lead_name = call_data["lead_info"].lead_name
    greeting_text = f"Hello {lead_name}! This is Sarvam AI calling. Am I speaking with the right person?"
    
    try:
        print(f"🎤 Generating Sarvam AI TTS for greeting...")
        
        # Generate audio using Sarvam AI
        audio_bytes = await sarvam_ai_service.text_to_speech(
            text=greeting_text,
            language="en-IN"
        )
        
        # Save audio file
        audio_filename = f"{call_id}_greeting.wav"
        audio_path = os.path.join("static", "audio", audio_filename)
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Get ngrok/webhook base URL
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        audio_url = f"{webhook_base}/static/audio/{audio_filename}"
        
        print(f"✅ Sarvam AI audio generated: {audio_url}")
        
        # Generate TwiML with Sarvam AI audio
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name,
            audio_url=audio_url
        )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Sarvam AI TTS failed: {e}, falling back to Twilio TTS")
        import traceback
        traceback.print_exc()
        
        # Fallback to Twilio TTS
        twiml = telephony_service.generate_greeting_twiml(
            call_id=call_id,
            lead_name=lead_name
        )
        
        return Response(content=twiml, media_type="application/xml")


@router.post("/process-speech")
async def process_speech_generic(
    CallSid: str = Form(None),
    SpeechResult: str = Form(None)
):
    """
    Generic speech processing endpoint for Twilio trial accounts
    """
    print(f"🗣️ Generic speech webhook - Twilio SID: {CallSid}, Speech: {SpeechResult}")
    
    # Look up call by Twilio SID
    call_data = real_call_service.get_call_by_twilio_sid(CallSid)
    
    if not call_data:
        print(f"⚠️ Call not found for Twilio SID: {CallSid}")
        return Response(content="<Response><Say>Call ended</Say><Hangup/></Response>", media_type="application/xml")
    
    call_id = call_data["call_id"]
    print(f"✅ Processing speech for call_id: {call_id}")
    
    # Use the existing process_speech_input logic
    return await process_speech_input(call_id, SpeechResult)


@router.post("/process-speech/{call_id}")
async def process_speech_input(
    call_id: str,
    SpeechResult: str = Form(None),
    RecordingUrl: str = Form(None),
    request: Request = None
):
    """
    Process speech input from lead
    This is called by Twilio after capturing lead's speech
    """
    print(f"🗣️ Speech from lead in call {call_id}: {SpeechResult}")
    
    call_data = real_call_service.get_call(call_id)
    
    # If call not found by ID, try finding by Twilio SID
    if not call_data and request:
        form_data = await request.form()
        twilio_sid = form_data.get("CallSid")
        print(f"⚠️ Call not found by ID, looking up by Twilio SID: {twilio_sid}")
        for cid, cdata in real_call_service.active_calls.items():
            if cdata.get("twilio_call_sid") == twilio_sid:
                call_id = cid
                call_data = cdata
                print(f"✅ Found call by Twilio SID: {call_id}")
                break
    
    if not call_data:
        return Response(content="<Response><Say>Call ended</Say><Hangup/></Response>", media_type="application/xml")
    
    # Use Twilio's transcription
    lead_speech = SpeechResult or "I didn't catch that"
    
    # Check if lead wants to end the call
    end_call_keywords = ['not interested', 'no thanks', 'goodbye', 'bye', 'hang up', 'stop calling', 'remove me', 'not now', 'busy']
    should_end_call = any(keyword in lead_speech.lower() for keyword in end_call_keywords)
    
    # Initialize conversation history if not exists
    if "conversation_history" not in call_data:
        call_data["conversation_history"] = []
    
    # Track conversation turns (to protect credits)
    max_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))  # Max 10 exchanges
    current_turns = len(call_data["conversation_history"]) // 2  # Each exchange = lead + AI
    
    if current_turns >= max_turns:
        print(f"⏰ Max conversation turns reached ({max_turns})")
        return Response(
            content="<Response><Say voice='Polly.Aditi-Neural' language='en-IN'>Thank you so much for your time today. I'll send you more information via email. Have a wonderful day!</Say><Hangup/></Response>",
            media_type="application/xml"
        )
    
    # Save lead's message to conversation history
    call_data["conversation_history"].append({
        "role": "lead",
        "content": lead_speech
    })
    
    try:
        print(f"🤖 Generating AI response for: {lead_speech}")
        
        # Generate AI response using Sarvam AI LLM
        product_info = {"description": real_call_service.product_knowledge or "AI voice agent platform"}
        ai_response_text = await sarvam_ai_service.generate_response(
            lead_message=lead_speech,
            conversation_history=call_data["conversation_history"],
            lead_info=call_data["lead_info"].dict(),
            product_info=product_info
        )
        
        print(f"💬 AI response text: {ai_response_text}")
        
        # Save AI response to conversation history
        call_data["conversation_history"].append({
            "role": "ai",
            "content": ai_response_text
        })
        
        # If lead wants to end call, prepare goodbye message
        if should_end_call:
            print(f"🔚 Lead requested to end call")
            ai_response_text = "I understand. Thank you for your time. If you change your mind, feel free to reach out to us. Have a great day!"
        
        # Generate Sarvam AI TTS audio
        try:
            print(f"🎤 Generating Sarvam AI TTS audio...")
            
            audio_bytes = await sarvam_ai_service.text_to_speech(
                text=ai_response_text,
                language="en-IN"
            )
            
            # Save audio file
            audio_filename = f"{call_id}_{uuid.uuid4().hex[:8]}.wav"
            audio_path = os.path.join("static", "audio", audio_filename)
            
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            
            # Get audio URL
            webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
            audio_url = f"{webhook_base}/static/audio/{audio_filename}"
            
            print(f"✅ Sarvam AI audio saved: {audio_url}")
            
            # Generate TwiML with Sarvam AI audio
            twiml = telephony_service.generate_response_twiml(
                call_id=call_id,
                ai_message=ai_response_text,
                audio_url=audio_url,
                end_call=should_end_call
            )
            
        except Exception as tts_error:
            print(f"⚠️ Sarvam AI TTS failed: {tts_error}, using Twilio TTS fallback")
            
            # Fallback to Twilio TTS
            twiml = telephony_service.generate_response_twiml(
                call_id=call_id,
                ai_message=ai_response_text,
                end_call=should_end_call
            )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response - keep conversation going
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        return Response(
            content=f"<Response><Gather input='speech' action='{webhook_base}/api/twilio/process-speech/{call_id}' method='POST' timeout='5' language='en-IN'><Say voice='Polly.Aditi-Neural' language='en-IN'>I'm sorry, I'm having trouble understanding. Could you please repeat that?</Say></Gather><Redirect method='POST'>{webhook_base}/api/twilio/process-speech/{call_id}</Redirect></Response>",
            media_type="application/xml"
        )


@router.post("/status/{call_id}")
async def handle_status_callback(call_id: str, request: Request):
    """
    Handle call status updates from Twilio
    Called when call status changes (ringing, answered, completed, etc.)
    """
    form_data = await request.form()
    call_status = form_data.get("CallStatus")
    call_duration = form_data.get("CallDuration")
    
    print(f"Status update for call {call_id}: {call_status}, Duration: {call_duration}")
    
    call_data = real_call_service.get_call(call_id)
    if call_data:
        # Map Twilio status to our CallStatus
        status_mapping = {
            "initiated": "connecting",
            "ringing": "ringing",
            "in-progress": "ai-speaking",
            "completed": "ended",
            "busy": "ended",
            "no-answer": "ended",
            "failed": "ended"
        }
        
        if call_status in status_mapping:
            from models.schemas import CallStatus
            call_data["status"] = CallStatus(status_mapping[call_status])
        
        if call_duration:
            call_data["timer"] = int(call_duration)
    
    return {"status": "received"}


@router.post("/recording/{call_id}")
async def handle_recording_callback(call_id: str, request: Request):
    """
    Handle recording callback from Twilio
    Called when call recording is ready
    """
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl")
    recording_sid = form_data.get("RecordingSid")
    
    print(f"Recording ready for call {call_id}: {recording_url}")
    
    call_data = real_call_service.get_call(call_id)
    if call_data:
        call_data["recording_url"] = recording_url
        call_data["recording_sid"] = recording_sid
    
    return {"status": "received"}
