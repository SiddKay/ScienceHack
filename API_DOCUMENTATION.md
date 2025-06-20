# ScienceHack API Documentation

## Overview

The ScienceHack backend provides a comprehensive API for managing AI-powered conflict simulations. The system allows users to create agents with specific personalities, initiate conversations between them, and explore different conversation paths through a branching tree structure.

## ID Format

All entities in the system use prefixed UUIDs for easy identification:

- **Agents**: `a-{uuid}` (e.g., `a-550e8400-e29b-41d4-a716-446655440000`)
- **Conversations**: `c-{uuid}` (e.g., `c-6ba7b810-9dad-11d1-80b4-00c04fd430c8`)
- **Nodes**: `n-{uuid}` (e.g., `n-6ba7b811-9dad-11d1-80b4-00c04fd430c8`)
- **Messages**: `m-{uuid}` (e.g., `m-6ba7b812-9dad-11d1-80b4-00c04fd430c8`)

## API Endpoints

### Agent Management

#### Create Agent
```
POST /api/agents/
```
Parameters:
- `name` (string): Agent's display name
- `personality_traits` (string): Description of personality traits
- `behavioral_instructions` (string, optional): Additional behavioral guidelines

Response: Created `AgentConfig` object with prefixed ID

#### Get Agent
```
GET /api/agents/{agent_id}
```
Returns the agent configuration for the specified ID.

#### List Agents
```
GET /api/agents/
```
Returns all available agents.

### Conversation Management

#### Create Conversation (with new agents)
```
POST /api/conversations/create
```
Creates a new conversation with inline agent definitions.

Request body:
```json
{
  "general_setting": "Workplace conflict",
  "specific_scenario": "Disagreement about project deadlines",
  "agent_a_name": "Alice",
  "agent_a_traits": "Detail-oriented, perfectionist",
  "agent_b_name": "Bob",
  "agent_b_traits": "Fast-paced, results-driven"
}
```

#### Create Conversation (with existing agents)
```
POST /api/conversations/create-with-agents
```
Creates a new conversation using previously created agents.

Request body:
```json
{
  "general_setting": "Workplace conflict",
  "specific_scenario": "Disagreement about project deadlines",
  "agent_a_id": "a-550e8400-e29b-41d4-a716-446655440000",
  "agent_b_id": "a-6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

#### Generate AI Response
```
POST /api/conversations/generate-response
```
Generates the next AI response in the conversation.

Request body:
```json
{
  "conversation_id": "c-6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "node_id": "n-optional-branch-point"  // Optional: continue from specific node
}
```

#### Add User Response
```
POST /api/conversations/user-response
```
Allows users to provide a custom response on behalf of an agent.

Request body:
```json
{
  "conversation_id": "c-6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "agent_id": "a-550e8400-e29b-41d4-a716-446655440000",
  "message": "Let's find a compromise that works for both of us.",
  "node_id": "n-optional-branch-point"  // Optional: continue from specific node
}
```

#### Get Conversation Tree
```
GET /api/conversations/{conversation_id}/tree
```
Returns the complete conversation tree structure with all branches.

#### Get Messages from Node
```
GET /api/conversations/{conversation_id}/messages/{node_id}
```
Returns all messages from the root to the specified node.

#### Branch from Node
```
POST /api/conversations/{conversation_id}/branch/{node_id}
```
Sets a specific node as the current branch point for continuing the conversation.

### Visualization

#### Get Tree Visualization Data
```
GET /api/visualization/{conversation_id}/tree-data
```
Returns hierarchical tree data formatted for D3.js visualization.

#### Get Graph Visualization Data
```
GET /api/visualization/{conversation_id}/graph-data
```
Returns nodes and edges formatted for graph visualization libraries.

## Mood System

Each message includes a mood indicator that determines its emotional tone:

- `happy` - Positive, joyful (green)
- `excited` - Enthusiastic, energetic (green)
- `neutral` - Balanced, objective (yellow)
- `calm` - Peaceful, composed (yellow)
- `sad` - Melancholic, disappointed (orange)
- `frustrated` - Annoyed, stressed (red)
- `angry` - Hostile, aggressive (red)

## Example Workflow

1. **Create Agents** (optional):
   ```bash
   curl -X POST "http://localhost:8000/api/agents/" \
     -d "name=Alice&personality_traits=Logical and direct"
   ```

2. **Create Conversation**:
   ```bash
   curl -X POST "http://localhost:8000/api/conversations/create-with-agents" \
     -H "Content-Type: application/json" \
     -d '{
       "general_setting": "Office meeting",
       "specific_scenario": "Budget allocation discussion",
       "agent_a_id": "a-123...",
       "agent_b_id": "a-456..."
     }'
   ```

3. **Generate Responses**:
   ```bash
   curl -X POST "http://localhost:8000/api/conversations/generate-response" \
     -H "Content-Type: application/json" \
     -d '{"conversation_id": "c-789..."}'
   ```

4. **Branch Conversation**:
   Users can click on any node in the tree and continue from that point, creating alternate conversation paths.

## Configuration

The backend requires the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI responses
- `ENVIRONMENT`: Set to "development" or "production"
- `PORT`: Server port (default: 8000)

## Running the Server

```bash
cd /home/maria/Projects/ScienceHack/ScienceHack
python3 main.py
```

Or with Docker:
```bash
docker-compose up
```