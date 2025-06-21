# ABOUTME: OpenAI service for generating agent responses with mood detection
# ABOUTME: Handles AI agent interactions and conversation generation

import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from config import settings
from app.models import Message, MoodEnum, AgentConfig, ConversationSetup, InterventionType
from app.services.base_ai_service import AIProviderService
from logging_config import get_logger

logger = get_logger(__name__)


class OpenAIService(AIProviderService):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _build_conversation_history(self, messages: List[Message], 
                                  agent_a_id: str, agent_b_id: str) -> List[Dict]:
        history = []
        
        for msg in messages:
            role = "assistant" if msg.agent_id == agent_a_id else "user"
            history.append({
                "role": role,
                "content": msg.msg
            })
        
        return history
    
    async def generate_agent_response(self, agent: AgentConfig, setup: ConversationSetup,
                                    conversation_history: List[Message], 
                                    is_agent_a: bool) -> Dict[str, str]:
        try:
            system_prompt = self._build_system_prompt(agent, setup, is_agent_a)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                for msg in conversation_history:
                    if msg.agent_id == agent.id:
                        role = "assistant"
                    else:
                        role = "user"
                    messages.append({
                        "role": role,
                        "content": msg.msg
                    })
            else:
                initial_prompt = f"Start the conversation about: {setup.specific_scenario}"
                messages.append({"role": "user", "content": initial_prompt})
            
            response = await self.client.chat.completions.create(
                model=agent.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=agent.temperature,
                max_tokens=5000
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return self._validate_response(result)
            
        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return self._get_fallback_response()
    
    async def analyze_mood(self, message: str) -> str:
        try:
            system_prompt = """Analyze the mood of the given message and return one of these moods:
            "happy", "excited", "neutral", "calm", "sad", "frustrated", "angry"
            
            Return only the mood word, nothing else."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            mood = response.choices[0].message.content.strip().lower()
            
            if mood not in [m.value for m in MoodEnum]:
                return MoodEnum.neutral.value
            
            return mood
            
        except Exception as e:
            logger.error(f"Error analyzing mood: {e}")
            return MoodEnum.neutral.value
    
    async def apply_intervention(self, agent: AgentConfig, setup: ConversationSetup,
                               conversation_history: List[Message], 
                               is_agent_a: bool, intervention_type: InterventionType) -> Dict[str, str]:
        try:
            base_prompt = self._build_system_prompt(agent, setup, is_agent_a)
            system_prompt = self._build_intervention_prompt(base_prompt, intervention_type)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                for msg in conversation_history:
                    if msg.agent_id == agent.id:
                        role = "assistant"
                    else:
                        role = "user"
                    messages.append({
                        "role": role,
                        "content": msg.msg
                    })
            
            response = await self.client.chat.completions.create(
                model=agent.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=min(1.0, agent.temperature + 0.1) if intervention_type == InterventionType.escalate else max(0.1, agent.temperature - 0.2),
                max_tokens=5000
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return self._validate_response(result)
            
        except Exception as e:
            logger.error(f"Error applying intervention: {e}")
            return self._get_fallback_response()


openai_service = OpenAIService()