# ABOUTME: Google Gemini AI service for generating agent responses with mood detection
# ABOUTME: Implements Google GenAI provider for conflict simulation agents

import json
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from config import settings
from app.models import Message, MoodEnum, AgentConfig, ConversationSetup, InterventionType
from app.services.base_ai_service import AIProviderService
from logging_config import get_logger

logger = get_logger(__name__)


class GoogleGeminiService(AIProviderService):
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set in environment variables")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    async def generate_agent_response(self, agent: AgentConfig, setup: ConversationSetup,
                                    conversation_history: List[Message], 
                                    is_agent_a: bool) -> Dict[str, str]:
        try:
            logger.info(f"Generating response with Google model: {agent.model_name}")
            logger.debug(f"API key present: {bool(settings.GOOGLE_API_KEY)}")
            
            system_prompt = self._build_system_prompt(agent, setup, is_agent_a)
            
            # Build conversation context for Gemini
            contents = f"{system_prompt}\n\n"
            
            if conversation_history:
                contents += "Conversation history:\n"
                other_agent = setup.agent_b if is_agent_a else setup.agent_a
                for msg in conversation_history:
                    speaker = "You" if msg.agent_id == agent.id else other_agent.name
                    contents += f"{speaker}: {msg.msg}\n"
                contents += "\nNow respond to continue this conversation."
            else:
                contents += f"Start the conversation about: {setup.specific_scenario}"
            
            contents += "\n\nIMPORTANT: Respond with a JSON object containing exactly two fields: 'msg' (your message) and 'mood' (one of: happy, excited, neutral, calm, sad, frustrated, angry)"
            
            # Use generate_content for JSON response
            response = await self.client.aio.models.generate_content(
                model=agent.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=agent.temperature,
                    max_output_tokens=5000
                )
            )
            
            # Log the raw response for debugging
            logger.debug(f"Google Gemini raw response: {response}")
            
            # Check if response has text attribute
            if not hasattr(response, 'text') or response.text is None:
                logger.error(f"Google Gemini response has no text attribute")
                # Try to access candidates if available
                if hasattr(response, 'candidates') and response.candidates:
                    logger.info(f"Found {len(response.candidates)} candidates")
                    try:
                        candidate = response.candidates[0]
                        
                        # Check if this is a MAX_TOKENS issue with empty parts
                        if (hasattr(candidate, 'finish_reason') and 
                            candidate.finish_reason.name == 'MAX_TOKENS' and
                            hasattr(candidate, 'content') and
                            candidate.content.parts is None):
                            logger.warning("MAX_TOKENS finish_reason with empty parts - retrying with higher token limit")
                            
                            # Retry with higher token limit
                            response_retry = await self.client.aio.models.generate_content(
                                model=agent.model_name,
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    response_mime_type='application/json',
                                    temperature=agent.temperature,
                                    max_output_tokens=5000  # Increased limit
                                )
                            )
                            
                            # Try to get text from retry
                            if hasattr(response_retry, 'text') and response_retry.text:
                                logger.info("Successfully retrieved response after retry")
                                result = json.loads(response_retry.text)
                                return self._validate_response(result)
                        
                        # Original candidate processing
                        if hasattr(candidate, 'content'):
                            content = candidate.content
                            if hasattr(content, 'parts') and content.parts:
                                part = content.parts[0]
                                if hasattr(part, 'text'):
                                    text = part.text
                                    logger.info(f"Extracted text from candidates: {text}")
                                    result = json.loads(text)
                                    return self._validate_response(result)
                                else:
                                    logger.error(f"Part has no text attribute: {part}")
                            else:
                                logger.error(f"Content has no parts: parts={content.parts if hasattr(content, 'parts') else 'no parts attr'} role='{content.role if hasattr(content, 'role') else 'no role'}'")
                        else:
                            logger.error(f"Candidate has no content: {candidate}")
                    except (IndexError, AttributeError) as e:
                        logger.error(f"Error accessing candidate content: {e}")
                else:
                    logger.error("No candidates in response")
                return self._get_fallback_response()
            
            result = json.loads(response.text)
            return self._validate_response(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for Google Gemini response. Error: {e}")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Error generating Google Gemini response: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._get_fallback_response()
    
    async def analyze_mood(self, message: str) -> str:
        try:
            contents = f"""Analyze the mood of this message and return only one of these moods:
            happy, excited, neutral, calm, sad, frustrated, angry
            
            Message: {message}
            
            Respond with a JSON object containing only a 'mood' field with one of the above values."""
            
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash-lite-preview-06-17",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.3,
                    max_output_tokens=10
                )
            )
            
            # Check if response has text attribute
            if not hasattr(response, 'text') or response.text is None:
                logger.error(f"Google Gemini mood analysis response has no text")
                return MoodEnum.neutral.value
            
            result = json.loads(response.text)
            mood = result.get("mood", "").strip().lower()
            
            if mood not in [m.value for m in MoodEnum]:
                return MoodEnum.neutral.value
            
            return mood
            
        except Exception as e:
            logger.error(f"Error analyzing mood with Google Gemini: {e}")
            return MoodEnum.neutral.value
    
    async def apply_intervention(self, agent: AgentConfig, setup: ConversationSetup,
                               conversation_history: List[Message], 
                               is_agent_a: bool, intervention_type: InterventionType) -> Dict[str, str]:
        try:
            logger.info(f"Applying {intervention_type.value} intervention with Google model: {agent.model_name}")
            logger.debug(f"API key present: {bool(settings.GOOGLE_API_KEY)}")
            
            base_prompt = self._build_system_prompt(agent, setup, is_agent_a)
            full_prompt = self._build_intervention_prompt(base_prompt, intervention_type)
            
            # Build conversation context
            contents = f"{full_prompt}\n\n"
            
            if conversation_history:
                contents += "Conversation history:\n"
                other_agent = setup.agent_b if is_agent_a else setup.agent_a
                for msg in conversation_history:
                    speaker = "You" if msg.agent_id == agent.id else other_agent.name
                    contents += f"{speaker}: {msg.msg}\n"
                contents += "\nNow respond following the intervention directive."
            else:
                contents += f"Start the conversation about: {setup.specific_scenario}"
            
            contents += "\n\nIMPORTANT: Respond with a JSON object containing exactly two fields: 'msg' (your message) and 'mood' (one of: happy, excited, neutral, calm, sad, frustrated, angry)"
            
            # Adjust temperature based on intervention type
            temperature = agent.temperature
            if intervention_type == InterventionType.escalate:
                temperature = min(1.0, temperature + 0.1)
            else:
                temperature = max(0.1, temperature - 0.2)
            
            response = await self.client.aio.models.generate_content(
                model=agent.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=temperature,
                    max_output_tokens=5000
                )
            )
            
            # Log the raw response for debugging
            logger.debug(f"Google Gemini intervention raw response: {response}")
            
            # Check if response has text attribute
            if not hasattr(response, 'text') or response.text is None:
                logger.error(f"Google Gemini intervention response has no text attribute")
                # Try to access candidates if available
                if hasattr(response, 'candidates') and response.candidates:
                    logger.info(f"Found {len(response.candidates)} candidates")
                    try:
                        candidate = response.candidates[0]
                        
                        # Check if this is a MAX_TOKENS issue with empty parts
                        if (hasattr(candidate, 'finish_reason') and 
                            candidate.finish_reason.name == 'MAX_TOKENS' and
                            hasattr(candidate, 'content') and
                            candidate.content.parts is None):
                            logger.warning("MAX_TOKENS finish_reason with empty parts - retrying with higher token limit")
                            
                            # Retry with higher token limit
                            response_retry = await self.client.aio.models.generate_content(
                                model=agent.model_name,
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    response_mime_type='application/json',
                                    temperature=temperature,
                                    max_output_tokens=5000  # Increased limit
                                )
                            )
                            
                            # Try to get text from retry
                            if hasattr(response_retry, 'text') and response_retry.text:
                                logger.info("Successfully retrieved response after retry")
                                result = json.loads(response_retry.text)
                                return self._validate_response(result)
                        
                        # Original candidate processing
                        if hasattr(candidate, 'content'):
                            content = candidate.content
                            if hasattr(content, 'parts') and content.parts:
                                part = content.parts[0]
                                if hasattr(part, 'text'):
                                    text = part.text
                                    logger.info(f"Extracted text from candidates: {text}")
                                    result = json.loads(text)
                                    return self._validate_response(result)
                                else:
                                    logger.error(f"Part has no text attribute: {part}")
                            else:
                                logger.error(f"Content has no parts: parts={content.parts if hasattr(content, 'parts') else 'no parts attr'} role='{content.role if hasattr(content, 'role') else 'no role'}'")
                        else:
                            logger.error(f"Candidate has no content: {candidate}")
                    except (IndexError, AttributeError) as e:
                        logger.error(f"Error accessing candidate content: {e}")
                else:
                    logger.error("No candidates in response")
                return self._get_fallback_response()
            
            result = json.loads(response.text)
            return self._validate_response(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for Google Gemini intervention response. Error: {e}")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Error applying intervention with Google Gemini: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._get_fallback_response()