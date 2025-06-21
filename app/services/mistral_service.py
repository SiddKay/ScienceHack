# ABOUTME: Mistral AI service for generating agent responses with mood detection
# ABOUTME: Implements MistralAI provider for conflict simulation agents

import json
from typing import List, Dict, Optional
from mistralai import Mistral
from config import settings
from app.models import Message, MoodEnum, AgentConfig, ConversationSetup, InterventionType
from app.services.base_ai_service import AIProviderService
from logging_config import get_logger

logger = get_logger(__name__)


class MistralService(AIProviderService):
    def __init__(self):
        if not settings.MISTRAL_API_KEY:
            logger.warning("MISTRAL_API_KEY is not set in environment variables")
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
    
    async def generate_agent_response(self, agent: AgentConfig, setup: ConversationSetup,
                                    conversation_history: List[Message], 
                                    is_agent_a: bool) -> Dict[str, str]:
        try:
            logger.info(f"Generating response with Mistral model: {agent.model_name}")
            logger.debug(f"API key present: {bool(settings.MISTRAL_API_KEY)}")
            
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
            
            # Ensure there's a user message at the end for the model to respond to
            if messages[-1]["role"] != "user":
                messages.append({
                    "role": "user", 
                    "content": "Continue the conversation."
                })
            
            response = await self.client.chat.complete_async(
                model=agent.model_name,
                messages=messages,
                temperature=agent.temperature,
                max_tokens=5000,
                response_format={"type": "json_object"}
            )
            
            # Log the raw response for debugging
            logger.debug(f"Mistral raw response: {response}")
            
            if not response or not response.choices or not response.choices[0].message:
                logger.error(f"Invalid response structure from Mistral: {response}")
                return self._get_fallback_response()
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty content from Mistral response")
                return self._get_fallback_response()
            
            logger.debug(f"Mistral response content: {content}")
            
            # Mistral might include markdown code blocks, so extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return self._validate_response(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for Mistral response. Content: '{content}', Error: {e}")
            # Try to extract a plain text response
            if content and isinstance(content, str):
                return {
                    "msg": content,
                    "mood": MoodEnum.neutral.value
                }
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Error generating Mistral response for model {agent.model_name}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            if hasattr(e, 'response'):
                logger.error(f"API response: {getattr(e, 'response', 'No response attribute')}")
            return self._get_fallback_response()
    
    async def analyze_mood(self, message: str) -> str:
        try:
            system_prompt = """Analyze the mood of the given message and return one of these moods:
            "happy", "excited", "neutral", "calm", "sad", "frustrated", "angry"
            
            Return only the mood word, nothing else."""
            
            response = await self.client.chat.complete_async(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            mood = response.choices[0].message.content.strip().lower().replace('"', '').replace("'", "")
            
            if mood not in [m.value for m in MoodEnum]:
                return MoodEnum.neutral.value
            
            return mood
            
        except Exception as e:
            logger.error(f"Error analyzing mood with Mistral: {e}")
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
            
            # Add user message to continue conversation with intervention
            messages.append({
                "role": "user", 
                "content": "Continue the conversation following the intervention directive."
            })
            
            # Adjust temperature based on intervention type
            temperature = agent.temperature
            if intervention_type == InterventionType.escalate:
                temperature = min(1.0, temperature + 0.1)
            else:
                temperature = max(0.1, temperature - 0.2)
            
            response = await self.client.chat.complete_async(
                model=agent.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=5000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return self._validate_response(result)
            
        except Exception as e:
            logger.error(f"Error applying intervention with Mistral: {e}")
            return self._get_fallback_response()