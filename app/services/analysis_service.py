# ABOUTME: Analysis service for third observer agent to analyze conversations
# ABOUTME: Provides conflict pattern analysis and improvement suggestions

import json
from typing import List, Dict, Tuple
from openai import AsyncOpenAI
from config import settings
from app.models import (
    ConversationTree, Message, MoodEnum, ConversationAnalysis,
    ObserverAgent
)
from logging_config import get_logger

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.observer = ObserverAgent()
    
    def _analyze_mood_transitions(self, messages: List[Message]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Analyze mood transitions to identify escalation and de-escalation points."""
        escalation_points = []
        de_escalation_points = []
        mood_progression = []
        
        mood_values = {
            MoodEnum.happy: 7,
            MoodEnum.excited: 6,
            MoodEnum.calm: 5,
            MoodEnum.neutral: 4,
            MoodEnum.sad: 3,
            MoodEnum.frustrated: 2,
            MoodEnum.angry: 1
        }
        
        for i, msg in enumerate(messages):
            mood_progression.append({
                "message_index": str(i),
                "agent_id": msg.agent_id,
                "mood": msg.mood.value,
                "snippet": msg.msg[:50] + "..." if len(msg.msg) > 50 else msg.msg
            })
            
            if i > 0:
                prev_mood_value = mood_values[messages[i-1].mood]
                curr_mood_value = mood_values[msg.mood]
                
                if curr_mood_value < prev_mood_value - 1:
                    escalation_points.append({
                        "from_index": str(i-1),
                        "to_index": str(i),
                        "from_mood": messages[i-1].mood.value,
                        "to_mood": msg.mood.value,
                        "message": msg.msg[:100] + "..." if len(msg.msg) > 100 else msg.msg
                    })
                elif curr_mood_value > prev_mood_value + 1:
                    de_escalation_points.append({
                        "from_index": str(i-1),
                        "to_index": str(i),
                        "from_mood": messages[i-1].mood.value,
                        "to_mood": msg.mood.value,
                        "message": msg.msg[:100] + "..." if len(msg.msg) > 100 else msg.msg
                    })
        
        return escalation_points, de_escalation_points, mood_progression
    
    def _format_conversation_for_analysis(self, tree: ConversationTree, messages: List[Message]) -> str:
        """Format conversation data for AI analysis."""
        conversation_text = f"**Conversation Setup:**\n"
        conversation_text += f"- General Setting: {tree.setup.general_setting}\n"
        conversation_text += f"- Specific Scenario: {tree.setup.specific_scenario}\n"
        conversation_text += f"- Agent A: {tree.setup.agent_a.name} - {tree.setup.agent_a.personality_traits}\n"
        conversation_text += f"- Agent B: {tree.setup.agent_b.name} - {tree.setup.agent_b.personality_traits}\n\n"
        
        conversation_text += "**Conversation Flow:**\n"
        for i, msg in enumerate(messages):
            agent_name = tree.setup.agent_a.name if msg.agent_id == tree.setup.agent_a.id else tree.setup.agent_b.name
            conversation_text += f"{i+1}. [{agent_name}] (Mood: {msg.mood.value}): {msg.msg}\n"
        
        return conversation_text
    
    async def analyze_conversation(self, tree: ConversationTree, messages: List[Message]) -> ConversationAnalysis:
        """Analyze a conversation for conflict patterns and provide insights."""
        try:
            escalation_points, de_escalation_points, mood_progression = self._analyze_mood_transitions(messages)
            
            conversation_formatted = self._format_conversation_for_analysis(tree, messages)
            
            system_prompt = f"""You are {self.observer.name}, a {self.observer.role}.
            
Analyze the given conversation for:
1. Overall conflict dynamics and patterns
2. Key turning points (escalations and de-escalations)
3. Communication effectiveness between agents
4. Specific suggestions for improvement

Provide your analysis in a structured JSON format with these fields:
- "summary": A comprehensive summary of the conflict dynamics (2-3 paragraphs)
- "suggestions": An array of specific, actionable suggestions for improving the conversation
- "analysis_markdown": A detailed markdown-formatted analysis report

The markdown report should include:
- Executive Summary
- Conflict Progression Analysis
- Key Turning Points
- Communication Patterns
- Recommendations for Each Agent
- Overall Conclusions"""
            
            analysis_data = f"{conversation_formatted}\n\n"
            analysis_data += f"**Identified Escalation Points:** {len(escalation_points)}\n"
            analysis_data += f"**Identified De-escalation Points:** {len(de_escalation_points)}\n"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_data}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=5000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return ConversationAnalysis(
                conversation_id=tree.id,
                total_messages=len(messages),
                escalation_points=escalation_points,
                de_escalation_points=de_escalation_points,
                mood_progression=mood_progression,
                summary=result.get("summary", "Analysis unavailable"),
                suggestions=result.get("suggestions", []),
                analysis_markdown=result.get("analysis_markdown", "# Analysis Report\n\nAnalysis unavailable")
            )
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return ConversationAnalysis(
                conversation_id=tree.id,
                total_messages=len(messages),
                escalation_points=escalation_points,
                de_escalation_points=de_escalation_points,
                mood_progression=mood_progression,
                summary="Error occurred during analysis",
                suggestions=["Unable to generate suggestions due to error"],
                analysis_markdown="# Analysis Report\n\nAn error occurred during analysis."
            )


analysis_service = AnalysisService()