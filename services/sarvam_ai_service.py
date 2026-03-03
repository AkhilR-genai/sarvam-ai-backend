"""
Sarvam AI API Integration Service
This service handles real-time speech-to-text, text-to-speech, and conversational AI
"""

import httpx
import asyncio
import os
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class SarvamAIConfig:
    """Configuration for Sarvam AI APIs"""
    def __init__(self):
        self.api_key = os.getenv("SARVAM_AI_API_KEY") or os.getenv("SARVAM_API_KEY")
        self.base_url = os.getenv("SARVAM_AI_BASE_URL", "https://api.sarvam.ai/v1")
        self.tts_url = f"{self.base_url}/text-to-speech"
        self.stt_url = f"{self.base_url}/speech-to-text"
        self.llm_url = f"{self.base_url}/chat/completions"
        

class TTSRequest(BaseModel):
    text: str
    language: str = "en-IN"  # English-India
    voice: str = "meera"  # Female voice
    speed: float = 1.0
    pitch: float = 1.0


class STTRequest(BaseModel):
    audio_data: bytes
    language: str = "en-IN"
    model: str = "saarika:v1"


class ConversationRequest(BaseModel):
    message: str
    context: dict
    lead_info: dict


class SarvamAIService:
    """Service to interact with Sarvam AI APIs"""
    
    def __init__(self):
        self.config = SarvamAIConfig()
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)

    def _ensure_config(self):
        if not self.config.api_key:
            raise RuntimeError(
                "Sarvam AI API key is missing. Set SARVAM_AI_API_KEY (or SARVAM_API_KEY)."
            )
    
    async def text_to_speech(self, text: str, language: str = "en-IN") -> bytes:
        """
        Convert text to speech using Sarvam AI TTS
        
        Args:
            text: Text to convert to speech
            language: Language code (en-IN, hi-IN, etc.)
            
        Returns:
            Audio bytes in WAV/MP3 format
        """
        self._ensure_config()
        try:
            payload = {
                "text": text,
                "language_code": language,
                "speaker": "meera",  # Use appropriate Sarvam AI voice
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.0,
                "speech_sample_rate": 8000,
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }
            
            print(f"🔵 Calling Sarvam AI TTS: {self.config.tts_url}")
            response = await self.client.post(
                self.config.tts_url,
                json=payload,
                timeout=15.0
            )
            
            print(f"🔵 Sarvam AI TTS Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Sarvam AI TTS Error: {response.text}")
                raise Exception(f"TTS failed with status {response.status_code}")
            
            response.raise_for_status()
            
            # Check if response is base64 encoded
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                # Response might be JSON with base64 audio
                import base64
                result = response.json()
                if "audio" in result:
                    audio_data = base64.b64decode(result["audio"])
                    print(f"✅ Sarvam AI TTS decoded base64 audio")
                    return audio_data
            
            # Direct binary audio
            audio_data = response.content
            print(f"✅ Sarvam AI TTS generated {len(audio_data)} bytes")
            return audio_data
            
        except httpx.TimeoutException as e:
            print(f"⏱️ Sarvam AI TTS timeout: {e}")
            raise
        except httpx.HTTPError as e:
            print(f"❌ Sarvam AI TTS HTTP Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Sarvam AI TTS Unexpected Error: {e}")
            raise
    
    async def speech_to_text(self, audio_data: bytes, language: str = "en-IN") -> str:
        """
        Convert speech to text using Sarvam AI STT
        
        Args:
            audio_data: Audio bytes
            language: Language code
            
        Returns:
            Transcribed text
        """
        self._ensure_config()
        try:
            # Sarvam AI speech-to-text endpoint
            files = {
                "file": ("audio.wav", audio_data, "audio/wav")
            }
            data = {
                "language_code": language,
                "model": "saarika:v1"
            }
            
            response = await self.client.post(
                self.config.stt_url,
                files=files,
                data=data
            )
            response.raise_for_status()
            
            result = response.json()
            transcript = result.get("transcript", "")
            return transcript
            
        except httpx.HTTPError as e:
            print(f"STT Error: {e}")
            raise
    
    async def generate_response(
        self,
        lead_message: str,
        conversation_history: list,
        lead_info: dict,
        product_info: dict
    ) -> str:
        """
        Generate AI response using Sarvam AI's conversational model
        
        Args:
            lead_message: What the lead said
            conversation_history: Previous messages
            lead_info: Lead details (name, CRM tag, etc.)
            product_info: Product knowledge base
            
        Returns:
            AI-generated response text
        """
        self._ensure_config()
        try:
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(lead_info, product_info)
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": "assistant" if msg["role"] == "ai" else "user",
                    "content": msg["content"]
                })
            
            # Add current lead message
            messages.append({
                "role": "user",
                "content": lead_message
            })
            
            # Call Sarvam AI LLM
            payload = {
                "model": "sarvam-2b-v0.5",  # Or appropriate Sarvam AI model
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150,
                "top_p": 0.9
            }
            
            print(f"🔵 Calling Sarvam AI LLM: {self.config.llm_url}")
            response = await self.client.post(
                self.config.llm_url,
                json=payload,
                timeout=10.0
            )
            
            print(f"🔵 Sarvam AI LLM Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Sarvam AI LLM Error: {response.text}")
                # Fallback to rule-based response
                return self._generate_fallback_response(lead_message, lead_info)
            
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            print(f"✅ Sarvam AI response generated successfully")
            return ai_response
            
        except httpx.TimeoutException:
            print(f"⏱️ Sarvam AI LLM timeout, using fallback")
            return self._generate_fallback_response(lead_message, lead_info)
        except httpx.HTTPError as e:
            print(f"❌ Sarvam AI LLM HTTP Error: {e}")
            return self._generate_fallback_response(lead_message, lead_info)
        except Exception as e:
            print(f"❌ Sarvam AI LLM Unexpected Error: {e}")
            return self._generate_fallback_response(lead_message, lead_info)
    
    def _generate_fallback_response(self, lead_message: str, lead_info: dict) -> str:
        """Generate rule-based response when Sarvam AI fails"""
        msg_lower = lead_message.lower()
        lead_name = lead_info.get("lead_name", "there")
        
        # Positive responses
        if any(word in msg_lower for word in ["yes", "yeah", "correct", "right", "sure"]):
            return f"Wonderful {lead_name}! I'm excited to share how our AI voice agent can transform your sales process. It handles calls 24/7, learns from every conversation, and has helped businesses increase their conversion rates by up to 40%. What's your biggest challenge with sales calls right now?"
        
        # Negative/wrong person
        elif any(word in msg_lower for word in ["no", "wrong", "not me", "mistake"]):
            return f"Oh I apologize for the confusion {lead_name}. May I know who would be the best person to discuss AI sales automation with? I'd be happy to call them instead."
        
        # Pricing questions
        elif any(word in msg_lower for word in ["price", "cost", "expensive", "budget", "afford", "how much"]):
            return "Great question! Our pricing starts at just 499 rupees per month. Most clients see ROI within the first 60 days through increased efficiency and more closed deals. We also offer a 14-day free trial so you can see the results yourself. Would you like to try it out?"
        
        # Interest/curiosity
        elif any(word in msg_lower for word in ["interested", "tell me more", "go ahead", "sounds good", "listening", "explain"]):
            return "Excellent! Our AI voice agent can make hundreds of simultaneous calls, never gets tired, and improves with every conversation. It handles objections intelligently and knows exactly when to escalate to a human. Plus, you get real-time analytics on every call. When would be convenient for a quick 15-minute demo?"
        
        # Too busy
        elif any(word in msg_lower for word in ["busy", "later", "not now", "bad time", "meeting"]):
            return f"I completely understand {lead_name}, your time is valuable. How about I send you a quick 2-minute video showing the platform, and we can schedule a proper demo for later this week? Does that work better?"
        
        # Demo request
        elif any(word in msg_lower for word in ["demo", "show", "see", "try", "test"]):
            return "Perfect! I can set up a live demo this week. We'll show you exactly how it works with your specific use case. Are mornings or afternoons generally better for you?"
        
        # Competitors/alternatives
        elif any(word in msg_lower for word in ["competitor", "using", "already have", "other"]):
            return "I understand you might be exploring options. What sets us apart is our focus on Indian languages and accents, plus our AI learns specifically from your sales methodology. Many clients who switched from alternatives saw a 30% improvement in call quality. Would you like to see a side-by-side comparison?"
        
        # Features/capabilities
        elif any(word in msg_lower for word in ["feature", "can it", "does it", "capability", "what does"]):
            return "Our platform offers speech recognition in 12 Indian languages, real-time sentiment analysis, automatic lead scoring, CRM integration, and detailed call analytics. The AI handles objections naturally and knows when to schedule callbacks. Which specific capability interests you most?"
        
        # Default - keep conversation going
        else:
            return f"I appreciate you taking the time {lead_name}. Let me ask you this - if you could automate just one part of your sales process, what would it be? Our AI specializes in the initial outreach and qualification, freeing up your team for closing deals."
    
    def _build_system_prompt(self, lead_info: dict, product_info: dict) -> str:
        """Build context-aware system prompt for sales conversation"""
        return f"""You are an AI sales agent for Sarvam AI voice platform. 

Lead Details:
- Name: {lead_info.get('lead_name')}
- Interest Level: {lead_info.get('crm_tag')}
- Purpose: {lead_info.get('purpose')}

Product Information:
{product_info.get('description', 'AI Voice Agent Platform')}

Your Goals:
1. Build rapport and trust
2. Understand lead's pain points
3. Present relevant product benefits
4. Handle objections professionally
5. Move towards scheduling a demo

Communication Style:
- {lead_info.get('voice_personality', 'professional')}
- Concise and clear
- Address objections with empathy
- Use value-based selling

Remember: Keep responses under 2-3 sentences. Ask questions to engage the lead.
"""
    
    async def analyze_sentiment(self, text: str) -> dict:
        """
        Analyze sentiment of lead's response
        
        Returns:
            dict with sentiment, confidence, and detected_objections
        """
        # This could use Sarvam AI's sentiment analysis or a custom model
        # For now, simple keyword-based detection
        
        objection_keywords = [
            "expensive", "cost", "price", "budget", "cant afford",
            "too much", "competitors", "already using", "not interested"
        ]
        
        positive_keywords = [
            "interested", "sounds good", "tell me more", "demo",
            "schedule", "yes", "great", "impressive"
        ]
        
        text_lower = text.lower()
        
        has_objection = any(keyword in text_lower for keyword in objection_keywords)
        is_positive = any(keyword in text_lower for keyword in positive_keywords)
        
        if has_objection:
            sentiment = "hesitant"
            confidence = 60
        elif is_positive:
            sentiment = "positive"
            confidence = 85
        else:
            sentiment = "neutral"
            confidence = 70
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "has_objection": has_objection
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
sarvam_ai_service = SarvamAIService()
