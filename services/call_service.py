import uuid
import asyncio
import random
from datetime import datetime
from typing import Dict, Optional
from models.schemas import (
    CallStatus, Sentiment, MessageRole, Message, 
    InitiateCallRequest, CallUpdate, CallResponse
)


class CallService:
    def __init__(self):
        self.active_calls: Dict[str, dict] = {}
        self.call_tasks: Dict[str, asyncio.Task] = {}

    def create_call(self, request: InitiateCallRequest) -> CallResponse:
        """Create a new call session"""
        call_id = str(uuid.uuid4())
        now = datetime.now()
        
        call_data = {
            "call_id": call_id,
            "status": CallStatus.CONNECTING,
            "lead_info": request,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "timer": 0,
            "sentiment": Sentiment.NEUTRAL,
            "confidence": 75,
            "deal_probability": 0
        }
        
        self.active_calls[call_id] = call_data
        
        return CallResponse(
            call_id=call_id,
            status=CallStatus.CONNECTING,
            lead_info=request,
            created_at=now,
            updated_at=now
        )

    def get_call(self, call_id: str) -> Optional[dict]:
        """Get call data by ID"""
        return self.active_calls.get(call_id)

    def end_call(self, call_id: str) -> bool:
        """End a call session"""
        if call_id in self.active_calls:
            self.active_calls[call_id]["status"] = CallStatus.ENDED
            self.active_calls[call_id]["updated_at"] = datetime.now()
            
            # Cancel the simulation task if it exists
            if call_id in self.call_tasks:
                self.call_tasks[call_id].cancel()
                del self.call_tasks[call_id]
            
            return True
        return False

    async def simulate_call_flow(self, call_id: str, websocket=None):
        """Simulate realistic call flow with status updates and messages"""
        if call_id not in self.active_calls:
            return

        call_data = self.active_calls[call_id]
        lead_name = call_data["lead_info"].lead_name
        purpose = call_data["lead_info"].purpose

        # Status flow with timing
        status_flow = [
            (CallStatus.CONNECTING, 2),
            (CallStatus.RINGING, 3),
            (CallStatus.AI_SPEAKING, 4),
            (CallStatus.LEAD_SPEAKING, 3),
            (CallStatus.AI_THINKING, 2),
            (CallStatus.AI_SPEAKING, 4),
        ]

        # Simulate conversation messages
        messages_data = [
            {
                "role": MessageRole.AI,
                "content": f"Hello {lead_name}! This is Sarvam AI calling on behalf of {purpose}. Am I speaking with the right person?",
                "delay": 5,
                "has_objection": False
            },
            {
                "role": MessageRole.LEAD,
                "content": "Yes, this is me. What's this about?",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.AI,
                "content": "Great! I'd love to tell you about our innovative AI solution that automates your entire sales process. Do you have a few minutes?",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.LEAD,
                "content": "Sure, but I'm quite busy. Make it quick.",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.AI,
                "content": "Absolutely! Our AI can handle hundreds of sales calls simultaneously with 95% accuracy. It learns from every conversation and improves over time.",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.LEAD,
                "content": "That sounds expensive. What's the pricing?",
                "delay": 4,
                "has_objection": True
            },
            {
                "role": MessageRole.AI,
                "content": "I understand budget is important. Our pricing starts at $499/month, but based on your scale, the ROI typically pays back within 2-3 months through increased efficiency.",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.LEAD,
                "content": "Interesting. How does it compare to competitors?",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.AI,
                "content": "Unlike competitors who use generic scripts, we use advanced NLP to understand context and adapt in real-time. Our objection handling success rate is 40% higher.",
                "delay": 4,
                "has_objection": False
            },
            {
                "role": MessageRole.LEAD,
                "content": "That's impressive. Can we schedule a demo?",
                "delay": 4,
                "has_objection": False
            },
        ]

        try:
            # Status flow simulation
            for status, duration in status_flow:
                if call_id not in self.active_calls or self.active_calls[call_id]["status"] == CallStatus.ENDED:
                    break

                call_data["status"] = status
                call_data["updated_at"] = datetime.now()

                if websocket:
                    await websocket.send_json({
                        "type": "status_update",
                        "status": status.value,
                        "timestamp": datetime.now().isoformat()
                    })

                await asyncio.sleep(duration)

            # Message simulation
            for msg_data in messages_data:
                if call_id not in self.active_calls or self.active_calls[call_id]["status"] == CallStatus.ENDED:
                    break

                await asyncio.sleep(msg_data["delay"])

                message = Message(
                    id=str(uuid.uuid4()),
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.now(),
                    has_objection=msg_data["has_objection"]
                )

                # Serialize message with datetime converted to ISO format
                message_dict = message.dict()
                message_dict["timestamp"] = message.timestamp.isoformat()
                call_data["messages"].append(message_dict)
                call_data["timer"] += msg_data["delay"]

                # Update sentiment based on objection
                if msg_data["has_objection"]:
                    call_data["sentiment"] = Sentiment.HESITANT
                    call_data["confidence"] = random.randint(50, 70)
                else:
                    # Gradually improve sentiment
                    sentiments = [Sentiment.NEUTRAL, Sentiment.POSITIVE]
                    call_data["sentiment"] = random.choice(sentiments)
                    call_data["confidence"] = random.randint(70, 90)

                # Gradually increase deal probability
                if call_data["deal_probability"] < 85:
                    call_data["deal_probability"] = min(
                        call_data["deal_probability"] + random.randint(5, 15), 
                        85
                    )

                # Update status based on message role
                if msg_data["role"] == MessageRole.AI:
                    call_data["status"] = CallStatus.AI_SPEAKING
                else:
                    call_data["status"] = CallStatus.LEAD_SPEAKING

                if websocket:
                    await websocket.send_json({
                        "type": "message",
                        "message": message_dict,
                        "sentiment": call_data["sentiment"].value,
                        "confidence": call_data["confidence"],
                        "deal_probability": call_data["deal_probability"],
                        "timer": call_data["timer"],
                        "status": call_data["status"].value
                    })

            # Continue with alternating statuses
            while call_id in self.active_calls and self.active_calls[call_id]["status"] != CallStatus.ENDED:
                statuses = [CallStatus.AI_SPEAKING, CallStatus.LEAD_SPEAKING, CallStatus.AI_THINKING, CallStatus.ANALYZING]
                call_data["status"] = random.choice(statuses)
                call_data["timer"] += 4
                
                if websocket:
                    await websocket.send_json({
                        "type": "status_update",
                        "status": call_data["status"].value,
                        "timer": call_data["timer"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(4)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in call simulation: {e}")


# Global instance
call_service = CallService()
