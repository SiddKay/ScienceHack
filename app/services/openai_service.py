# ABOUTME: OpenAI service for generating agent responses with mood detection
# ABOUTME: Handles AI agent interactions and conversation generation

import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from config import settings
from app.models import Message, MoodEnum, AgentConfig, ConversationSetup, InterventionType
from logging_config import get_logger

logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
    
    def _build_system_prompt(self, agent: AgentConfig, setup: ConversationSetup, 
                           is_agent_a: bool) -> str:
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
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            if "msg" not in result or "mood" not in result:
                raise ValueError("Invalid response format from AI")
            
            if result["mood"] not in [m.value for m in MoodEnum]:
                logger.warning(f"Invalid mood '{result['mood']}', defaulting to neutral")
                result["mood"] = MoodEnum.neutral.value
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return {
                "msg": "I need a moment to collect my thoughts.",
                "mood": MoodEnum.neutral.value
            }
    
    async def analyze_mood(self, message: str) -> str:
        try:
            system_prompt = """Analyze the mood of the given message and return one of these moods:
            "happy", "excited", "neutral", "calm", "sad", "frustrated", "angry"
            
            Return only the mood word, nothing else."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
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
            
            system_prompt = base_prompt + intervention_instruction
            
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
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.9 if intervention_type == InterventionType.escalate else 0.6,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            if "msg" not in result or "mood" not in result:
                raise ValueError("Invalid response format from AI")
            
            if result["mood"] not in [m.value for m in MoodEnum]:
                logger.warning(f"Invalid mood '{result['mood']}', defaulting to neutral")
                result["mood"] = MoodEnum.neutral.value
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying intervention: {e}")
            return {
                "msg": "I need a moment to process this situation.",
                "mood": MoodEnum.neutral.value
            }


openai_service = OpenAIService()