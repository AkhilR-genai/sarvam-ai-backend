from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class CallStatus(str, Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    RINGING = "ringing"
    AI_SPEAKING = "ai-speaking"
    LEAD_SPEAKING = "lead-speaking"
    AI_THINKING = "ai-thinking"
    ANALYZING = "analyzing"
    ENDED = "ended"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    HESITANT = "hesitant"
    NOT_INTERESTED = "not-interested"


class CRMTag(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class VoicePersonality(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"


class MessageRole(str, Enum):
    AI = "ai"
    LEAD = "lead"


class InitiateCallRequest(BaseModel):
    country_code: str = Field(..., example="+91")
    mobile: str = Field(..., example="9876543210")
    purpose: str = Field(..., example="sales")
    lead_name: str = Field(..., example="John Doe")
    crm_tag: CRMTag = Field(default=CRMTag.WARM)
    voice_personality: VoicePersonality = Field(default=VoicePersonality.PROFESSIONAL)
    objection_handling: bool = Field(default=True)


class Message(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    has_objection: Optional[bool] = False


class CallUpdate(BaseModel):
    status: CallStatus
    message: Optional[Message] = None
    sentiment: Optional[Sentiment] = None
    confidence: Optional[int] = None
    deal_probability: Optional[int] = None
    timer: Optional[int] = None


class CallResponse(BaseModel):
    call_id: str
    status: CallStatus
    lead_info: InitiateCallRequest
    created_at: datetime
    updated_at: datetime


class ProductKnowledgeRequest(BaseModel):
    description: str = Field(..., min_length=10)
    product_name: Optional[str] = None
    features: Optional[list[str]] = None
    pricing: Optional[str] = None


class ProductKnowledgeResponse(BaseModel):
    id: str
    description: str
    product_name: Optional[str]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime
