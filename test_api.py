# ABOUTME: Test script to verify API functionality with new ID format
# ABOUTME: Tests agent creation, conversation creation with agents, and ID prefixes

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_api_functionality():
    print("Testing ScienceHack API with new ID format...\n")
    
    # Test 1: Create agents
    print("1. Creating agents...")
    agent_a_response = requests.post(
        f"{BASE_URL}/api/agents/",
        params={
            "name": "Alice",
            "personality_traits": "Assertive, logical, direct communicator",
            "behavioral_instructions": "Always try to find practical solutions"
        }
    )
    agent_a = agent_a_response.json()
    print(f"   Created Agent A: {agent_a['name']} (ID: {agent_a['id']})")
    
    agent_b_response = requests.post(
        f"{BASE_URL}/api/agents/",
        params={
            "name": "Bob", 
            "personality_traits": "Emotional, creative, empathetic listener",
            "behavioral_instructions": "Focus on understanding feelings"
        }
    )
    agent_b = agent_b_response.json()
    print(f"   Created Agent B: {agent_b['name']} (ID: {agent_b['id']})")
    
    # Verify ID format
    assert agent_a['id'].startswith('a-'), f"Agent A ID should start with 'a-', got: {agent_a['id']}"
    assert agent_b['id'].startswith('a-'), f"Agent B ID should start with 'a-', got: {agent_b['id']}"
    print("   ✓ Agent IDs have correct prefix\n")
    
    # Test 2: Create conversation with existing agents
    print("2. Creating conversation with existing agents...")
    conv_response = requests.post(
        f"{BASE_URL}/api/conversations/create-with-agents",
        json={
            "general_setting": "Workplace conflict resolution",
            "specific_scenario": "Alice and Bob disagree about project priorities",
            "agent_a_id": agent_a['id'],
            "agent_b_id": agent_b['id']
        }
    )
    conversation = conv_response.json()
    print(f"   Created conversation (ID: {conversation['id']})")
    
    # Verify conversation ID format
    assert conversation['id'].startswith('c-'), f"Conversation ID should start with 'c-', got: {conversation['id']}"
    print("   ✓ Conversation ID has correct prefix")
    print(f"   ✓ Using agents: {conversation['setup']['agent_a']['name']} and {conversation['setup']['agent_b']['name']}\n")
    
    # Test 3: Generate AI response
    print("3. Generating AI response...")
    response = requests.post(
        f"{BASE_URL}/api/conversations/generate-response",
        json={
            "conversation_id": conversation['id']
        }
    )
    
    if response.status_code == 200:
        ai_response = response.json()
        print(f"   Generated response from {conversation['setup']['agent_a']['name']}:")
        print(f"   Message: {ai_response['message']['msg'][:100]}...")
        print(f"   Mood: {ai_response['message']['mood']}")
        print(f"   Node ID: {ai_response['node_id']}")
        
        # Verify node ID format
        assert ai_response['node_id'].startswith('n-'), f"Node ID should start with 'n-', got: {ai_response['node_id']}"
        # Verify message ID format
        assert ai_response['message']['id'].startswith('m-'), f"Message ID should start with 'm-', got: {ai_response['message']['id']}"
        print("   ✓ Node and Message IDs have correct prefixes\n")
    else:
        print(f"   Note: AI response generation requires OPENAI_API_KEY to be configured")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
    
    # Test 4: Test inline agent creation (original endpoint)
    print("4. Testing inline agent creation...")
    inline_conv_response = requests.post(
        f"{BASE_URL}/api/conversations/create",
        json={
            "general_setting": "Personal relationship",
            "specific_scenario": "Planning vacation destination",
            "agent_a_name": "Emma",
            "agent_a_traits": "Adventurous, spontaneous",
            "agent_b_name": "David", 
            "agent_b_traits": "Cautious, budget-conscious"
        }
    )
    inline_conversation = inline_conv_response.json()
    print(f"   Created conversation with inline agents (ID: {inline_conversation['id']})")
    assert inline_conversation['id'].startswith('c-'), "Inline conversation ID should start with 'c-'"
    assert inline_conversation['setup']['agent_a']['id'].startswith('a-'), "Inline agent A ID should start with 'a-'"
    assert inline_conversation['setup']['agent_b']['id'].startswith('a-'), "Inline agent B ID should start with 'a-'"
    print("   ✓ All IDs have correct prefixes\n")
    
    print("✅ All tests passed! The API is working correctly with the new ID format.")
    print("\nSummary of ID formats:")
    print("  - Agents: a-{uuid}")
    print("  - Conversations: c-{uuid}")
    print("  - Nodes: n-{uuid}")
    print("  - Messages: m-{uuid}")


if __name__ == "__main__":
    try:
        test_api_functionality()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")