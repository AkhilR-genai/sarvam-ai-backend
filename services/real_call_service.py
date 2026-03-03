"""
Real-time Call Service with Sarvam AI and Twilio Integration
This replaces the simulation with actual voice calling functionality
"""

import uuid
import asyncio
import os
from datetime import datetime
from typing import Dict, Optional
from models.schemas import (
    CallStatus, Sentiment, MessageRole, Message, 
    InitiateCallRequest, CallUpdate, CallResponse
)
from services.sarvam_ai_service import sarvam_ai_service
from services.telephony_service import telephony_service


class RealCallService:
    """Service that handles real voice calls using Sarvam AI + Twilio"""
    
    def __init__(self):
        self.active_calls: Dict[str, dict] = {}
        self.product_knowledge: str = ""
        self.max_real_calls_per_day = int(os.getenv("MAX_REAL_CALLS_PER_DAY", "2"))
        self.calls_today_count = 0
        self.calls_today_date = datetime.now().date()

    def _refresh_daily_counter(self):
        today = datetime.now().date()
        if self.calls_today_date != today:
            self.calls_today_date = today
            self.calls_today_count = 0

    def can_initiate_real_call(self) -> bool:
        self._refresh_daily_counter()
        return self.calls_today_count < self.max_real_calls_per_day

    def get_usage_stats(self) -> dict:
        self._refresh_daily_counter()
        remaining = max(self.max_real_calls_per_day - self.calls_today_count, 0)
        return {
            "date": str(self.calls_today_date),
            "used_calls": self.calls_today_count,
            "max_calls": self.max_real_calls_per_day,
            "remaining_calls": remaining
        }
    
    async def create_call(self, request: InitiateCallRequest) -> CallResponse:
        """Create a new call session and initiate real phone call"""
        if not self.can_initiate_real_call():
            usage = self.get_usage_stats()
            raise RuntimeError(
                f"Daily real-call limit reached ({usage['used_calls']}/{usage['max_calls']}). "
                "Increase MAX_REAL_CALLS_PER_DAY to continue."
            )

        call_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Initialize call data
        call_data = {
            "call_id": call_id,
            "status": CallStatus.CONNECTING,
            "lead_info": request,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "conversation_history": [],
            "timer": 0,
            "sentiment": Sentiment.NEUTRAL,
            "confidence": 75,
            "deal_probability": 0,
            "twilio_call_sid": None,
            "recording_url": None
        }
        
        self.active_calls[call_id] = call_data
        
        # Initiate real phone call via Twilio
        try:
            twilio_response = telephony_service.initiate_call(
                to_number=request.mobile,
                call_id=call_id,
                country_code=request.country_code
            )
            call_data["twilio_call_sid"] = twilio_response["twilio_call_sid"]
            call_data["status"] = CallStatus.RINGING
            self.calls_today_count += 1
        except Exception as e:
            print(f"Failed to initiate Twilio call: {e}")
            call_data["status"] = CallStatus.ENDED
            call_data["error"] = str(e)
        
        return CallResponse(
            call_id=call_id,
            status=call_data["status"],
            lead_info=request,
            created_at=now,
            updated_at=now
        )
    
    async def handle_speech_input(
        self,
        call_id: str,
        audio_data: bytes,
        websocket=None
    ) -> str:
        """
        Process speech input from lead
        
        Steps:
        1. Convert speech to text (Sarvam AI STT)
        2. Analyze sentiment
        3. Generate AI response (Sarvam AI LLM)
        4. Convert response to speech (Sarvam AI TTS)
        5. Send to Twilio to play to lead
        """
        if call_id not in self.active_calls:
            return ""
        
        call_data = self.active_calls[call_id]
        
        try:
            # Step 1: Speech-to-Text
            lead_text = await sarvam_ai_service.speech_to_text(
                audio_data=audio_data,
                language="en-IN"
            )
            
            # Create lead message
            lead_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.LEAD,
                content=lead_text,
                timestamp=datetime.now(),
                has_objection=False
            )
            
            # Step 2: Analyze sentiment
            sentiment_analysis = await sarvam_ai_service.analyze_sentiment(lead_text)
            call_data["sentiment"] = Sentiment(sentiment_analysis["sentiment"])
            call_data["confidence"] = sentiment_analysis["confidence"]
            lead_message.has_objection = sentiment_analysis["has_objection"]
            
            # Save lead message
            call_data["messages"].append(lead_message.dict())
            call_data["conversation_history"].append({
                "role": "lead",
                "content": lead_text
            })
            
            # Update status
            call_data["status"] = CallStatus.AI_THINKING
            
            # Send update via WebSocket
            if websocket:
                await websocket.send_json({
                    "type": "message",
                    "message": lead_message.dict(),
                    "sentiment": call_data["sentiment"].value,
                    "confidence": call_data["confidence"],
                    "status": "ai-thinking"
                })
            
            # Step 3: Generate AI response
            product_info = {"description": self.product_knowledge}
            ai_response_text = await sarvam_ai_service.generate_response(
                lead_message=lead_text,
                conversation_history=call_data["conversation_history"],
                lead_info=call_data["lead_info"].dict(),
                product_info=product_info
            )
            
            # Create AI message
            ai_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.AI,
                content=ai_response_text,
                timestamp=datetime.now(),
                has_objection=False
            )
            
            call_data["messages"].append(ai_message.dict())
            call_data["conversation_history"].append({
                "role": "ai",
                "content": ai_response_text
            })
            
            # Update deal probability
            if sentiment_analysis["sentiment"] == "positive":
                call_data["deal_probability"] = min(call_data["deal_probability"] + 15, 95)
            elif sentiment_analysis["has_objection"]:
                call_data["deal_probability"] = max(call_data["deal_probability"] - 5, 0)
            else:
                call_data["deal_probability"] = min(call_data["deal_probability"] + 5, 95)
            
            call_data["status"] = CallStatus.AI_SPEAKING
            
            # Send AI message via WebSocket
            if websocket:
                await websocket.send_json({
                    "type": "message",
                    "message": ai_message.dict(),
                    "sentiment": call_data["sentiment"].value,
                    "confidence": call_data["confidence"],
                    "deal_probability": call_data["deal_probability"],
                    "status": "ai-speaking"
                })
            
            # Step 4: Convert to speech (Sarvam AI TTS)
            audio_bytes = await sarvam_ai_service.text_to_speech(
                text=ai_response_text,
                language="en-IN"
            )
            
            # In production, upload audio to cloud storage and return URL
            # For now, return the text for Twilio TTS
            return ai_response_text
            
        except Exception as e:
            print(f"Error processing speech: {e}")
            return "I'm sorry, I didn't catch that. Could you please repeat?"
    
    async def end_call(self, call_id: str) -> bool:
        """End a real call"""
        if call_id not in self.active_calls:
            return False
        
        call_data = self.active_calls[call_id]
        
        # End Twilio call
        if call_data.get("twilio_call_sid"):
            try:
                telephony_service.end_call(call_data["twilio_call_sid"])
                
                # Get recording URL
                recording_url = telephony_service.get_recording_url(
                    call_data["twilio_call_sid"]
                )
                call_data["recording_url"] = recording_url
            except Exception as e:
                print(f"Error ending Twilio call: {e}")
        
        call_data["status"] = CallStatus.ENDED
        call_data["updated_at"] = datetime.now()
        
        return True
    
    def get_call(self, call_id: str) -> Optional[dict]:
        """Get call data by ID"""
        return self.active_calls.get(call_id)
    
    def set_product_knowledge(self, description: str):
        """Set product knowledge base for AI responses"""
        self.product_knowledge = description


# Global instance (use this for real calls)
real_call_service = RealCallService()
