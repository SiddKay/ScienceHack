# ABOUTME: API endpoints for conversation tree visualization
# ABOUTME: Provides structured data for frontend tree rendering

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional

from app.utils.convtree import conversation_tree_manager
from app.models import MoodEnum
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/visualization", tags=["visualization"])


def get_mood_color(mood: MoodEnum) -> str:
    """Map mood to color for visualization."""
    mood_colors = {
        MoodEnum.happy: "#4ade80",      # green-400
        MoodEnum.excited: "#22c55e",    # green-500
        MoodEnum.neutral: "#fbbf24",    # yellow-400
        MoodEnum.calm: "#fde047",       # yellow-300
        MoodEnum.sad: "#fb923c",        # orange-400
        MoodEnum.frustrated: "#f87171", # red-400
        MoodEnum.angry: "#ef4444"       # red-500
    }
    return mood_colors.get(mood, "#9ca3af")  # gray-400 as default


@router.get("/{conversation_id}/tree-data")
async def get_tree_visualization_data(conversation_id: str):
    """Get tree data formatted for D3.js or similar visualization libraries."""
    try:
        tree = conversation_tree_manager.get_tree(conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        def build_node_data(node_id: str, depth: int = 0) -> Dict:
            node = tree.nodes[node_id]
            agent_name = (tree.setup.agent_a.name 
                         if node.message.agent_id == tree.setup.agent_a.id 
                         else tree.setup.agent_b.name)
            
            return {
                "id": node.id,
                "name": f"{agent_name}: {node.message.msg[:50]}{'...' if len(node.message.msg) > 50 else ''}",
                "fullMessage": node.message.msg,
                "mood": node.message.mood.value,
                "color": get_mood_color(node.message.mood),
                "agent": agent_name,
                "agentId": node.message.agent_id,
                "timestamp": node.message.timestamp.isoformat(),
                "isUserOverride": node.message.is_user_override,
                "depth": depth,
                "isCurrentBranch": node.id == tree.current_branch,
                "children": [build_node_data(child_id, depth + 1) for child_id in node.children]
            }
        
        root_nodes = [build_node_data(node_id) for node_id in tree.root_nodes]
        
        return {
            "conversationId": conversation_id,
            "setup": {
                "generalSetting": tree.setup.general_setting,
                "specificScenario": tree.setup.specific_scenario,
                "agentA": tree.setup.agent_a.name,
                "agentB": tree.setup.agent_b.name
            },
            "treeData": root_nodes[0] if root_nodes else None,
            "totalNodes": len(tree.nodes),
            "maxDepth": max([node["depth"] for node in flatten_tree(root_nodes)]) if root_nodes else 0
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tree visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def flatten_tree(nodes: List[Dict]) -> List[Dict]:
    """Flatten tree structure for analysis."""
    result = []
    for node in nodes:
        result.append(node)
        if node.get("children"):
            result.extend(flatten_tree(node["children"]))
    return result


@router.get("/{conversation_id}/graph-data")
async def get_graph_visualization_data(conversation_id: str):
    """Get tree data formatted as nodes and edges for graph visualization."""
    try:
        tree = conversation_tree_manager.get_tree(conversation_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        nodes = []
        edges = []
        
        for node_id, node in tree.nodes.items():
            agent_name = (tree.setup.agent_a.name 
                         if node.message.agent_id == tree.setup.agent_a.id 
                         else tree.setup.agent_b.name)
            
            nodes.append({
                "id": node.id,
                "label": f"{agent_name}: {node.message.msg[:30]}...",
                "fullMessage": node.message.msg,
                "mood": node.message.mood.value,
                "color": get_mood_color(node.message.mood),
                "agent": agent_name,
                "isCurrentBranch": node.id == tree.current_branch,
                "isUserOverride": node.message.is_user_override
            })
            
            if node.parent_id:
                edges.append({
                    "from": node.parent_id,
                    "to": node.id
                })
        
        return {
            "conversationId": conversation_id,
            "nodes": nodes,
            "edges": edges
        }
        
    except Exception as e:
        logger.error(f"Error getting graph visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))