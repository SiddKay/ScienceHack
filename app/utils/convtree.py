# ABOUTME: Conversation tree management with branching support
# ABOUTME: Handles tree operations, path navigation, and conversation history

from typing import List, Optional, Dict
from datetime import datetime

from app.models import ConversationTree, ConversationNode, Message, ConversationSetup
from app.utils.id_generator import generate_id


class ConversationTreeManager:
    def __init__(self):
        self.trees: Dict[str, ConversationTree] = {}
    
    def create_tree(self, setup: ConversationSetup) -> ConversationTree:
        tree_id = generate_id("conversation")
        tree = ConversationTree(
            id=tree_id,
            setup=setup,
            nodes={},
            root_nodes=[],
            current_branch=None
        )
        self.trees[tree_id] = tree
        return tree
    
    def add_message(self, tree_id: str, message: Message, 
                   parent_node_id: Optional[str] = None) -> ConversationNode:
        tree = self.trees.get(tree_id)
        if not tree:
            raise ValueError(f"Tree {tree_id} not found")
        
        node_id = generate_id("node")
        
        if parent_node_id:
            parent = tree.nodes.get(parent_node_id)
            if not parent:
                raise ValueError(f"Parent node {parent_node_id} not found")
            path = f"{parent.path}:{node_id}"
            parent.children.append(node_id)
        else:
            path = node_id
            tree.root_nodes.append(node_id)
        
        node = ConversationNode(
            id=node_id,
            message=message,
            parent_id=parent_node_id,
            children=[],
            path=path
        )
        
        tree.nodes[node_id] = node
        tree.current_branch = node_id
        
        return node
    
    def get_conversation_path(self, tree_id: str, node_id: str) -> List[Message]:
        tree = self.trees.get(tree_id)
        if not tree:
            raise ValueError(f"Tree {tree_id} not found")
        
        node = tree.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        messages = []
        current = node
        
        while current:
            messages.insert(0, current.message)
            if current.parent_id:
                current = tree.nodes.get(current.parent_id)
            else:
                current = None
        
        return messages
    
    def get_tree(self, tree_id: str) -> Optional[ConversationTree]:
        return self.trees.get(tree_id)
    
    def get_all_trees(self) -> Dict[str, ConversationTree]:
        return self.trees
    
    def branch_from_node(self, tree_id: str, node_id: str, 
                        new_message: Message) -> ConversationNode:
        tree = self.trees.get(tree_id)
        if not tree:
            raise ValueError(f"Tree {tree_id} not found")
        
        node = tree.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        return self.add_message(tree_id, new_message, node_id)
    
    def get_current_conversation(self, tree_id: str) -> List[Message]:
        tree = self.trees.get(tree_id)
        if not tree or not tree.current_branch:
            return []
        
        return self.get_conversation_path(tree_id, tree.current_branch)
    
    def set_current_branch(self, tree_id: str, node_id: str):
        tree = self.trees.get(tree_id)
        if not tree:
            raise ValueError(f"Tree {tree_id} not found")
        
        if node_id not in tree.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        tree.current_branch = node_id


conversation_tree_manager = ConversationTreeManager()