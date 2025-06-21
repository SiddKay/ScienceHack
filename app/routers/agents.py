# ABOUTME: API endpoints for agent configuration and management
# ABOUTME: Handles creating and retrieving agent configurations

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional

from app.models import AgentConfig, ModelProvider
from app.utils.id_generator import generate_id
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])

agents_store: Dict[str, AgentConfig] = {}


@router.post("/", response_model=AgentConfig)
async def create_agent(
    name: str, 
    personality_traits: str,
    behavioral_instructions: Optional[str] = None,
    model_provider: ModelProvider = ModelProvider.openai,
    model_name: Optional[str] = None,
    temperature: float = 0.8
):
    """Create a new agent configuration with model and temperature settings."""
    try:
        # Set default model name based on provider if not specified
        if not model_name:
            default_models = {
                ModelProvider.openai: "gpt-4o",
                ModelProvider.mistral: "magistral-small-latest",
                ModelProvider.google: "gemini-2.5-flash-lite-preview-06-17"
            }
            model_name = default_models.get(model_provider, "gpt-4o")
        
        agent_id = generate_id("agent")
        agent = AgentConfig(
            id=agent_id,
            name=name,
            personality_traits=personality_traits,
            behavioral_instructions=behavioral_instructions,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature
        )
        agents_store[agent_id] = agent
        
        logger.info(f"Created agent: {agent.name} (ID: {agent_id}) with {model_provider.value}/{model_name}")
        return agent
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentConfig)
async def get_agent(agent_id: str):
    """Get a specific agent configuration."""
    agent = agents_store.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/", response_model=List[AgentConfig])
async def list_agents():
    """List all available agents."""
    return list(agents_store.values())


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent configuration."""
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    del agents_store[agent_id]
    return {"message": "Agent deleted successfully"}