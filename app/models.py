# ABOUTME: Data models for agents, conversations, messages and tree nodes
# ABOUTME: Defines the structure for conflict simulation entities

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum


class MoodEnum(str, Enum):
    happy = "happy"
    excited = "excited"
    neutral = "neutral"
    calm = "calm"
    sad = "sad"
    frustrated = "frustrated"
    angry = "angry"


class AgentConfig(BaseModel):
    id: str
    name: str
    personality_traits: str
    behavioral_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationSetup(BaseModel):
    general_setting: str
    specific_scenario: str
    agent_a: AgentConfig
    agent_b: AgentConfig


class Message(BaseModel):
    id: str
    agent_id: str
    msg: str
    mood: MoodEnum
    timestamp: datetime = Field(default_factory=datetime.now)
    is_user_override: bool = False


class ConversationNode(BaseModel):
    id: str
    message: Message
    parent_id: Optional[str] = None
    children: List[str] = []
    path: str


class ConversationTree(BaseModel):
    id: str
    setup: ConversationSetup
    nodes: Dict[str, ConversationNode] = {}
    root_nodes: List[str] = []
    current_branch: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class CreateConversationRequest(BaseModel):
    general_setting: str
    specific_scenario: str
    agent_a_name: str
    agent_a_traits: str
    agent_b_name: str
    agent_b_traits: str


class CreateConversationWithAgentsRequest(BaseModel):
    general_setting: str
    specific_scenario: str
    agent_a_id: str
    agent_b_id: str


class GenerateResponseRequest(BaseModel):
    conversation_id: str
    node_id: Optional[str] = None


class UserResponseRequest(BaseModel):
    conversation_id: str
    node_id: Optional[str] = None
    message: str
    agent_id: str


class ConversationTreeResponse(BaseModel):
    tree: ConversationTree
    current_path: List[Message]


class InterventionType(str, Enum):
    escalate = "escalate"
    de_escalate = "de_escalate"


class InterventionRequest(BaseModel):
    conversation_id: str
    node_id: Optional[str] = None
    intervention_type: InterventionType


class InterventionResponse(BaseModel):
    node_id: str
    message: Message
    current_path: List[Message]
    intervention_applied: InterventionType


class ObserverAgent(BaseModel):
    id: str = Field(default="observer-agent")
    name: str = Field(default="Conflict Analysis Observer")
    role: str = Field(default="Analyze conversations for conflict patterns and provide insights")


class ConversationAnalysis(BaseModel):
    conversation_id: str
    total_messages: int
    escalation_points: List[Dict[str, str]]
    de_escalation_points: List[Dict[str, str]]
    mood_progression: List[Dict[str, str]]
    summary: str
    suggestions: List[str]
    analysis_markdown: str


class AnalysisRequest(BaseModel):
    conversation_id: str