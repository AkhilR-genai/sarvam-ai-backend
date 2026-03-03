"""
Telephony Service - Integrates with Twilio for real phone calls
This handles actual voice calling, audio streaming, and telephony functions
"""

import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from typing import Optional
import httpx


class TwilioConfig:
    """Configuration for Twilio"""
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")  # Your Twilio number
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")


class TelephonyService:
    """Service to handle real phone calls via Twilio"""
    
    def __init__(self):
        self.config = TwilioConfig()
        self.client = None
        if self.config.account_sid and self.config.auth_token:
            self.client = Client(self.config.account_sid, self.config.auth_token)

    def _ensure_client(self):
        if not self.client:
            raise RuntimeError(
                "Twilio credentials are missing. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
            )
        if not self.config.phone_number:
            raise RuntimeError("TWILIO_PHONE_NUMBER is missing.")
        if not self.config.webhook_base_url:
            raise RuntimeError("WEBHOOK_BASE_URL is missing.")
    
    def initiate_call(
        self,
        to_number: str,
        call_id: str,
        country_code: str = "+91"
    ) -> dict:
        """
        Initiate an outbound call to a lead
        
        Args:
            to_number: Lead's phone number
            call_id: Unique call identifier
            country_code: Country code (default +91 for India)
            
        Returns:
            Call details from Twilio
        """
        self._ensure_client()
        try:
            # Format phone number
            full_number = f"{country_code}{to_number}"
            
            print(f"📞 Initiating call to {full_number} with voice webhook URL")
            
            # Create call with URL webhook (ngrok is working based on status callbacks)
            call = self.client.calls.create(
                to=full_number,
                from_=self.config.phone_number,
                url=f"{self.config.webhook_base_url}/api/twilio/voice/{call_id}",  # Use URL for initial greeting
                method='POST',
                status_callback=f"{self.config.webhook_base_url}/api/twilio/status/{call_id}",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                record=True,
                recording_status_callback=f"{self.config.webhook_base_url}/api/twilio/recording/{call_id}"
            )
            
            return {
                "twilio_call_sid": call.sid,
                "status": call.status,
                "to": full_number,
                "from": self.config.phone_number
            }
            
        except Exception as e:
            print(f"Error initiating call: {e}")
            raise
    
    def generate_greeting_twiml(self, call_id: str, lead_name: str, audio_url: Optional[str] = None) -> str:
        """
        Generate TwiML for initial greeting
        
        This tells Twilio what to say when call connects
        
        Args:
            call_id: Call identifier
            lead_name: Name of the lead
            audio_url: Optional URL to Sarvam AI TTS audio
        """
        response = VoiceResponse()
        
        # Gather input from lead with speech recognition
        gather = Gather(
            input='speech',
            action=f"{self.config.webhook_base_url}/api/twilio/process-speech/{call_id}",
            method='POST',
            timeout=5,  # Wait 5 seconds after speech ends
            speech_timeout='auto',  # Auto-detect end of speech
            language='en-IN',
            hints='yes,no,interested,not interested,tell me more,demo,price,cost'
        )
        
        if audio_url:
            # Play Sarvam AI generated audio
            gather.play(audio_url)
        else:
            # Fallback to Twilio TTS
            gather.say(
                f"Hello {lead_name}! This is Sarvam AI calling. Am I speaking with the right person?",
                voice='Polly.Aditi-Neural',
                language='en-IN'
            )
        
        response.append(gather)
        
        # If no response after timeout, prompt again and redirect back to listen
        response.say("I didn't get that. Please say yes or no.", voice='Polly.Aditi-Neural', language='en-IN')
        response.redirect(f"{self.config.webhook_base_url}/api/twilio/voice/{call_id}", method='POST')
        
        return str(response)
    
    def generate_response_twiml(
        self,
        call_id: str,
        ai_message: str,
        audio_url: Optional[str] = None,
        end_call: bool = False
    ) -> str:
        """
        Generate TwiML for AI response
        
        Args:
            call_id: Call identifier
            ai_message: Text response from AI
            audio_url: URL to pre-generated Sarvam AI TTS audio (optional)
            end_call: Whether to end the call after this message
        """
        response = VoiceResponse()
        
        if end_call:
            # Just play message and hangup
            if audio_url:
                response.play(audio_url)
            else:
                response.say(ai_message, voice='Polly.Aditi-Neural', language='en-IN')
            response.say("Thank you for your time. Have a great day!", voice='Polly.Aditi-Neural', language='en-IN')
            response.hangup()
        else:
            # Continue conversation - gather more input
            gather = Gather(
                input='speech',
                action=f"{self.config.webhook_base_url}/api/twilio/process-speech/{call_id}",
                method='POST',
                timeout=5,  # Wait 5 seconds after speech ends
                speech_timeout='auto',
                language='en-IN',
                speech_model='phone_call',
                hints='yes,no,interested,not interested,tell me more,demo,price,cost,buy,schedule'
            )
            
            if audio_url:
                # Play pre-generated Sarvam AI TTS audio
                print(f"📢 Using Sarvam AI audio: {audio_url}")
                gather.play(audio_url)
            else:
                # Fallback to Twilio's TTS
                print(f"📢 Using Twilio TTS fallback")
                gather.say(ai_message, voice='Polly.Aditi-Neural', language='en-IN')
            
            response.append(gather)
            
            # If no response, ask again
            response.say("Are you still there? Please let me know your thoughts.", voice='Polly.Aditi-Neural', language='en-IN')
            # Redirect to continue listening
            response.redirect(f"{self.config.webhook_base_url}/api/twilio/process-speech/{call_id}", method='POST')
        
        return str(response)
    
    def end_call(self, twilio_call_sid: str) -> dict:
        """
        End an active call
        
        Args:
            twilio_call_sid: Twilio's call SID
        """
        self._ensure_client()
        try:
            call = self.client.calls(twilio_call_sid).update(status='completed')
            return {
                "status": call.status,
                "duration": call.duration
            }
        except Exception as e:
            print(f"Error ending call: {e}")
            raise
    
    def get_call_details(self, twilio_call_sid: str) -> dict:
        """Get details of a call from Twilio"""
        self._ensure_client()
        try:
            call = self.client.calls(twilio_call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
        except Exception as e:
            print(f"Error fetching call details: {e}")
            raise
    
    def get_recording_url(self, twilio_call_sid: str) -> Optional[str]:
        """Get URL of call recording"""
        self._ensure_client()
        try:
            recordings = self.client.recordings.list(call_sid=twilio_call_sid, limit=1)
            if recordings:
                recording = recordings[0]
                return f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
            return None
        except Exception as e:
            print(f"Error fetching recording: {e}")
            return None


# Global instance
telephony_service = TelephonyService()
