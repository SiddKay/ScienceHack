# ABOUTME: Abstract base class for AI provider services
# ABOUTME: Defines common interface and shared logic for all AI providers

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.models import Message, MoodEnum, AgentConfig, ConversationSetup, InterventionType
from logging_config import get_logger

logger = get_logger(__name__)


class AIProviderService(ABC):
    """Abstract base class for AI provider services."""
    
    @abstractmethod
    async def generate_agent_response(self, agent: AgentConfig, setup: ConversationSetup,
                                    conversation_history: List[Message], 
                                    is_agent_a: bool) -> Dict[str, str]:
        """Generate an AI response for the agent."""
        pass
    
    @abstractmethod
    async def analyze_mood(self, message: str) -> str:
        """Analyze the mood of a given message."""
        pass
    
    @abstractmethod
    async def apply_intervention(self, agent: AgentConfig, setup: ConversationSetup,
                               conversation_history: List[Message], 
                               is_agent_a: bool, intervention_type: InterventionType) -> Dict[str, str]:
        """Apply an intervention to the agent's response."""
        pass
    
    def _build_system_prompt(self, agent: AgentConfig, setup: ConversationSetup, 
                           is_agent_a: bool) -> str:
        """Build the system prompt for the agent. Common across all providers."""
        other_agent = setup.agent_b if is_agent_a else setup.agent_a
        role = "Agent A" if is_agent_a else "Agent B"
        
        system_prompt = f"""You are {agent.name} ({role}) in a conflict simulation.

General Setting: {setup.general_setting}
Specific Scenario: {setup.specific_scenario}

Your personality traits: {agent.personality_traits}

The other agent is {other_agent.name} with these traits: {other_agent.personality_traits}

{agent.behavioral_instructions or ''}

You must respond to messages in character, considering the conversation history and your personality traits. Your response must be a JSON object with exactly these fields:
- "msg": Your response message (string)
- "mood": Your exact mood for this message, which must be one of these values: "happy", "excited", "neutral", "calm", "sad", "frustrated", "angry"

Always stay in character and respond appropriately to the situation and conversation flow."""
        
        return system_prompt
    
    def _build_intervention_prompt(self, base_prompt: str, intervention_type: InterventionType) -> str:
        """Add intervention instructions to the base prompt."""
        intervention_instruction = ""
        
        if intervention_type == InterventionType.escalate:
            intervention_instruction = """

IMPORTANT INTERVENTION DIRECTIVE: You must respond in a way that ESCALATES the conflict.
- Increase tension and disagreement
- Be more confrontational and assertive
- Focus on points of contention
- Express stronger emotions like frustration or anger
- Make the conflict more intense"""
        elif intervention_type == InterventionType.de_escalate:
            intervention_instruction = """

IMPORTANT INTERVENTION DIRECTIVE: You must respond in a way that DE-ESCALATES the conflict.
- Reduce tension and find common ground
- Be more understanding and empathetic
- Acknowledge the other person's perspective
- Use calming language
- Seek resolution and compromise"""
        
        return base_prompt + intervention_instruction
    
    def _validate_response(self, response: Dict[str, str]) -> Dict[str, str]:
        """Validate and normalize the AI response."""
        if "msg" not in response or "mood" not in response:
            raise ValueError("Invalid response format from AI")
        
        if response["mood"] not in [m.value for m in MoodEnum]:
            logger.warning(f"Invalid mood '{response['mood']}', defaulting to neutral")
            response["mood"] = MoodEnum.neutral.value
        
        return response
    
    def _get_fallback_response(self) -> Dict[str, str]:
        """Get a fallback response for error cases."""
        return {
            "msg": "I need a moment to collect my thoughts.",
            "mood": MoodEnum.neutral.value
        }