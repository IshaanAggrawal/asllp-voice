import logging
from typing import Optional
from integrations.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Main voice agent orchestrator using Langchain/Langgraph
    
    TODO: This is a simplified implementation.
    For the full assessment, you should implement:
    1. Langgraph state machine for conversation flow
    2. Memory management for multi-turn conversations
    3. Tool/function calling if needed
    4. Proper error handling and retry logic
    
    Current implementation provides a basic structure.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.ollama_client = OllamaClient()
        self.conversation_history = []
        self.agent_config = None  # Will be fetched from Django API
        
        logger.info(f"Initialized VoiceAgent for session: {session_id}")
    
    async def load_agent_config(self, agent_id: str):
        """
        Load agent configuration from Django API
        
        TODO: Make HTTP request to Django to get:
        - Agent name
        - System prompt
        - Selected model
        """
        # Placeholder - in production, fetch from Django API
        self.agent_config = {
            "name": "Default Agent",
            "system_prompt": "You are a helpful voice assistant.",
            "model": "llama3.2:1b"
        }
    
    async def process_turn(self, user_input: str) -> str:
        """
        Process a single conversation turn
        
        Steps:
        1. Classify intent using orchestration layer (Qwen)
        2. Generate response using conversational layer (LLaMA)
        3. Update conversation history
        4. Return response
        """
        # Step 1: Intent classification (orchestration)
        intent_data = await self.ollama_client.classify_intent(
            transcript=user_input,
            context={"history": self.conversation_history}
        )
        
        logger.info(f"Classified intent: {intent_data.get('intent')}")
        
        # Step 2: Generate response (conversation)
        system_prompt = self.agent_config.get("system_prompt") if self.agent_config else None
        
        response = await self.ollama_client.generate_response(
            prompt=user_input,
            model=self.agent_config.get("model") if self.agent_config else None,
            system_prompt=system_prompt
        )
        
        # Step 3: Update history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "intent": intent_data.get("intent")
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def get_conversation_history(self):
        """Return conversation history"""
        return self.conversation_history
    
    async def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info(f"Cleared conversation history for session: {self.session_id}")
