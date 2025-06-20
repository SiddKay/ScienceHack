# ABOUTME: API endpoints for agent configuration and management
# ABOUTME: Handles creating and retrieving agent configurations

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.models import AgentConfig
from app.utils.id_generator import generate_id
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])

agents_store: Dict[str, AgentConfig] = {}


@router.post("/", response_model=AgentConfig)
async def create_agent(name: str, personality_traits: str, 
                      behavioral_instructions: str = None):
    """Create a new agent configuration."""
    try:
        agent_id = generate_id("agent")
        agent = AgentConfig(
            id=agent_id,
            name=name,
            personality_traits=personality_traits,
            behavioral_instructions=behavioral_instructions
        )
        agents_store[agent_id] = agent
        
        logger.info(f"Created agent: {agent.name} (ID: {agent_id})")
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