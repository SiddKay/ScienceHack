# ABOUTME: API endpoints for conversation management and AI responses
# ABOUTME: Handles conversation flow, agent responses, and tree operations

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional

from app.models import (
    CreateConversationRequest, CreateConversationWithAgentsRequest,
    GenerateResponseRequest, UserResponseRequest,
    ConversationTree, ConversationTreeResponse, Message, AgentConfig, 
    ConversationSetup, MoodEnum, InterventionRequest, InterventionResponse,
    InterventionType, AnalysisRequest, ConversationAnalysis, ModelProvider
)
from app.utils.convtree import conversation_tree_manager
from app.utils.id_generator import generate_id
from app.services.ai_provider_factory import AIProviderFactory
from app.services.analysis_service import analysis_service
from app.routers.agents import agents_store
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("/create", response_model=ConversationTree)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation with new inline agents."""
    try:
        # Set default model names if not provided
        agent_a_model_name = request.agent_a_model_name
        if not agent_a_model_name:
            default_models = {
                ModelProvider.openai: "gpt-4o",
                ModelProvider.mistral: "magistral-small-latest",
                ModelProvider.google: "gemini-2.5-flash-lite-preview-06-17"
            }
            agent_a_model_name = default_models.get(request.agent_a_model_provider, "gpt-4o")
        
        agent_b_model_name = request.agent_b_model_name
        if not agent_b_model_name:
            default_models = {
                ModelProvider.openai: "gpt-4o",
                ModelProvider.mistral: "magistral-small-latest",
                ModelProvider.google: "gemini-2.5-flash-lite-preview-06-17"
            }
            agent_b_model_name = default_models.get(request.agent_b_model_provider, "gpt-4o")
        
        agent_a = AgentConfig(
            id=generate_id("agent"),
            name=request.agent_a_name,
            personality_traits=request.agent_a_traits,
            model_provider=request.agent_a_model_provider,
            model_name=agent_a_model_name,
            temperature=request.agent_a_temperature
        )
        
        agent_b = AgentConfig(
            id=generate_id("agent"),
            name=request.agent_b_name,
            personality_traits=request.agent_b_traits,
            model_provider=request.agent_b_model_provider,
            model_name=agent_b_model_name,
            temperature=request.agent_b_temperature
        )
        
        setup = ConversationSetup(
            general_setting=request.general_setting,
            specific_scenario=request.specific_scenario,
            agent_a=agent_a,
            agent_b=agent_b
        )
        
        tree = conversation_tree_manager.create_tree(setup)
        logger.info(f"Created conversation tree: {tree.id}")
        
        return tree
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-with-agents", response_model=ConversationTree)
async def create_conversation_with_agents(request: CreateConversationWithAgentsRequest):
    """Create a new conversation using existing agents from the agents store."""
    try:
        agent_a = agents_store.get(request.agent_a_id)
        if not agent_a:
            raise HTTPException(status_code=404, 
                              detail=f"Agent with ID {request.agent_a_id} not found")
        
        agent_b = agents_store.get(request.agent_b_id)
        if not agent_b:
            raise HTTPException(status_code=404, 
                              detail=f"Agent with ID {request.agent_b_id} not found")
        
        setup = ConversationSetup(
            general_setting=request.general_setting,
            specific_scenario=request.specific_scenario,
            agent_a=agent_a,
            agent_b=agent_b
        )
        
        tree = conversation_tree_manager.create_tree(setup)
        logger.info(f"Created conversation tree: {tree.id} with existing agents")
        
        return tree
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation with agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-response")
async def generate_agent_response(request: GenerateResponseRequest):
    """Generate an AI response for the next agent in the conversation."""
    try:
        tree = conversation_tree_manager.get_tree(request.conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.node_id:
            conversation_tree_manager.set_current_branch(request.conversation_id, request.node_id)
            conversation_history = conversation_tree_manager.get_conversation_path(
                request.conversation_id, request.node_id
            )
        else:
            conversation_history = conversation_tree_manager.get_current_conversation(
                request.conversation_id
            )
        
        is_agent_a_turn = len(conversation_history) % 2 == 0
        current_agent = tree.setup.agent_a if is_agent_a_turn else tree.setup.agent_b
        
        # Get the appropriate AI service for the agent's model provider
        ai_service = AIProviderFactory.get_provider(current_agent.model_provider)
        
        response_data = await ai_service.generate_agent_response(
            agent=current_agent,
            setup=tree.setup,
            conversation_history=conversation_history,
            is_agent_a=is_agent_a_turn
        )
        
        message = Message(
            id=generate_id("message"),
            agent_id=current_agent.id,
            msg=response_data["msg"],
            mood=MoodEnum(response_data["mood"])
        )
        
        parent_node_id = tree.current_branch if conversation_history else None
        node = conversation_tree_manager.add_message(
            request.conversation_id, message, parent_node_id
        )
        
        return {
            "node_id": node.id,
            "message": message,
            "current_path": conversation_tree_manager.get_conversation_path(
                request.conversation_id, node.id
            )
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-response")
async def add_user_response(request: UserResponseRequest):
    """Add a user-provided response on behalf of an agent."""
    try:
        tree = conversation_tree_manager.get_tree(request.conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.node_id:
            conversation_tree_manager.set_current_branch(request.conversation_id, request.node_id)
        
        # Get the agent to determine which AI service to use
        agent = tree.setup.agent_a if request.agent_id == tree.setup.agent_a.id else tree.setup.agent_b
        ai_service = AIProviderFactory.get_provider(agent.model_provider)
        
        mood = await ai_service.analyze_mood(request.message)
        
        message = Message(
            id=generate_id("message"),
            agent_id=request.agent_id,
            msg=request.message,
            mood=MoodEnum(mood),
            is_user_override=True
        )
        
        parent_node_id = tree.current_branch
        node = conversation_tree_manager.add_message(
            request.conversation_id, message, parent_node_id
        )
        
        return {
            "node_id": node.id,
            "message": message,
            "current_path": conversation_tree_manager.get_conversation_path(
                request.conversation_id, node.id
            )
        }
        
    except Exception as e:
        logger.error(f"Error adding user response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/tree", response_model=ConversationTreeResponse)
async def get_conversation_tree(conversation_id: str):
    """Get the complete conversation tree structure."""
    tree = conversation_tree_manager.get_tree(conversation_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    current_path = []
    if tree.current_branch:
        current_path = conversation_tree_manager.get_conversation_path(
            conversation_id, tree.current_branch
        )
    
    return ConversationTreeResponse(tree=tree, current_path=current_path)


@router.get("/{conversation_id}/messages/{node_id}")
async def get_messages_from_node(conversation_id: str, node_id: str):
    """Get all messages from root to a specific node."""
    try:
        messages = conversation_tree_manager.get_conversation_path(conversation_id, node_id)
        return {"messages": messages, "node_id": node_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{conversation_id}/branch/{node_id}")
async def branch_from_node(conversation_id: str, node_id: str):
    """Set a node as the current branch point for continuing the conversation."""
    try:
        conversation_tree_manager.set_current_branch(conversation_id, node_id)
        messages = conversation_tree_manager.get_conversation_path(conversation_id, node_id)
        return {
            "message": "Branch point set successfully",
            "node_id": node_id,
            "current_path": messages
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/apply-intervention", response_model=InterventionResponse)
async def apply_intervention(request: InterventionRequest):
    """Apply an intervention (escalate or de-escalate) to generate the next response."""
    try:
        tree = conversation_tree_manager.get_tree(request.conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.node_id:
            conversation_tree_manager.set_current_branch(request.conversation_id, request.node_id)
            conversation_history = conversation_tree_manager.get_conversation_path(
                request.conversation_id, request.node_id
            )
        else:
            conversation_history = conversation_tree_manager.get_current_conversation(
                request.conversation_id
            )
        
        is_agent_a_turn = len(conversation_history) % 2 == 0
        current_agent = tree.setup.agent_a if is_agent_a_turn else tree.setup.agent_b
        
        # Get the appropriate AI service for the agent's model provider
        ai_service = AIProviderFactory.get_provider(current_agent.model_provider)
        
        response_data = await ai_service.apply_intervention(
            agent=current_agent,
            setup=tree.setup,
            conversation_history=conversation_history,
            is_agent_a=is_agent_a_turn,
            intervention_type=request.intervention_type
        )
        
        message = Message(
            id=generate_id("message"),
            agent_id=current_agent.id,
            msg=response_data["msg"],
            mood=MoodEnum(response_data["mood"])
        )
        
        parent_node_id = tree.current_branch if conversation_history else None
        node = conversation_tree_manager.add_message(
            request.conversation_id, message, parent_node_id
        )
        
        return InterventionResponse(
            node_id=node.id,
            message=message,
            current_path=conversation_tree_manager.get_conversation_path(
                request.conversation_id, node.id
            ),
            intervention_applied=request.intervention_type
        )
        
    except Exception as e:
        logger.error(f"Error applying intervention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ConversationTree])
async def list_conversations():
    """List all active conversations."""
    trees = conversation_tree_manager.get_all_trees()
    return list(trees.values())


@router.post("/{conversation_id}/analyze", response_model=ConversationAnalysis)
async def analyze_conversation(conversation_id: str):
    """Analyze a conversation using the third observer agent."""
    try:
        tree = conversation_tree_manager.get_tree(conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        all_messages = []
        if tree.current_branch:
            all_messages = conversation_tree_manager.get_conversation_path(
                conversation_id, tree.current_branch
            )
        
        if not all_messages:
            raise HTTPException(status_code=400, detail="No messages to analyze")
        
        analysis = await analysis_service.analyze_conversation(tree, all_messages)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))