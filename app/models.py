from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    SCHEDULED = "scheduled"
    CONVERTED = "converted"
    LOST = "lost"

class Lead(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    company: str
    position: str
    industry: Optional[str] = None
    status: LeadStatus
    score: Optional[int] = None

class ConversationContext(BaseModel):
    tenant_id: str = "default"
    lead: Lead
    message_history: List[Dict[str, Any]] = []
    current_stage: str = "initial_outreach"

class AgentResponse(BaseModel):
    schema_version: str = "1.0"
    message: str
    suggested_action: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    requires_human: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WebhookEvent(BaseModel):
    event_type: str
    lead_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
