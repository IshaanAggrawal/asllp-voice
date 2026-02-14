"""
Voice Agent with Dual-Layer Architecture
- Orchestration Layer: Qwen 1.5B for intent classification
- Conversational Layer: LLaMA 1B for response generation
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# LangChain imports - updated for latest version
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Dual-layer AI agent for voice conversations
    - Orchestrator (Qwen): Intent classification and routing
    - Responder (LLaMA): Natural conversation generation
    """
    
    def __init__(self, session_id: str, agent_config: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.agent_config = agent_config or {}
        
        # Get models from environment
        self.orchestration_model = os.getenv("OLLAMA_ORCHESTRATION_MODEL", "qwen2.5:1.5b")
        self.conversational_model = os.getenv("OLLAMA_CONVERSATIONAL_MODEL", "llama3.2:1b")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Initialize LLMs
        self.orchestrator = OllamaLLM(
            model=self.orchestration_model,
            base_url=self.ollama_base_url,
            temperature=0.3  # Lower for consistent intent classification
        )
        
        self.responder = OllamaLLM(
            model=self.conversational_model,
            base_url=self.ollama_base_url,
            temperature=0.7  # Higher for natural conversation
        )
        
        # Simple conversation history (list of dicts)
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info(f"VoiceAgent initialized for session {session_id}")
        logger.info(f"Orchestrator: {self.orchestration_model}")
        logger.info(f"Responder: {self.conversational_model}")
    
    async def load_agent_config(self, agent_id: str):
        """Load agent configuration (system prompt, name, etc.)"""
        # In production, fetch from Django API
        # For now, use provided config or defaults
        if not self.agent_config:
            self.agent_config = {
                "name": "Voice Assistant",
                "system_prompt": "You are a helpful, friendly AI voice assistant.",
                "model": self.conversational_model
            }
        logger.info(f"Loaded config for agent: {self.agent_config.get('name')}")

    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration dynamically"""
        if not self.agent_config:
            self.agent_config = {}
        self.agent_config.update(config)
        logger.info(f"Updated agent config: {self.agent_config.get('name')}")
    
    async def classify_intent(self, user_input: str) -> Dict[str, str]:
        """
        Orchestration Layer: Classify user intent using Qwen
        """
        intent_prompt = PromptTemplate(
            input_variables=["user_input"],
            template="""Classify the user's intent into ONE category:
- greeting: Starting conversation
- question: Asking for information
- command: Requesting action
- farewell: Ending conversation
- clarification: Needs more info
- other: Anything else

User: "{user_input}"

Respond with ONLY the category name (one word):"""
        )
        
        # Use LCEL (modern approach for langchain v1.2)
        try:
            chain = intent_prompt | self.orchestrator | StrOutputParser()
            intent_raw = await chain.ainvoke({"user_input": user_input})
            
            # Parse and clean intent
            intent = intent_raw.strip().lower().split()[0]
            valid_intents = ["greeting", "question", "command", "farewell", "clarification", "other"]
            
            if intent not in valid_intents:
                intent = "other"
                
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            intent = "other"
            intent_raw = "error_fallback"
        
        logger.info(f"Classified intent: {intent}")
        
        return {
            "intent": intent,
            "raw_output": intent_raw
        }
    
    async def generate_response(self, user_input: str, intent: str) -> str:
        """
        Conversational Layer: Generate natural response using LLaMA
        """
        # Get agent's custom system prompt
        agent_persona = self.agent_config.get("system_prompt", 
            "You are a helpful AI voice assistant. Keep responses concise for voice.")
        
        # Build response prompt
        response_prompt = PromptTemplate(
            input_variables=["persona", "intent", "user_input", "history"],
            template="""You are: {persona}

User's intent: {intent}
Previous conversation: {history}

User: {user_input}

Respond naturally in 1-2 sentences (voice-friendly):
Assistant:"""
        )
        
        # Get chat history from simple list
        history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history[-5:]]) if self.conversation_history else "No previous conversation"
        
        # Use LCEL (modern approach for langchain v1.2)
        try:
            chain = response_prompt | self.responder | StrOutputParser()
            response = await chain.ainvoke({
                "persona": agent_persona,
                "intent": intent,
                "user_input": user_input,
                "history": history[:500]  # Limit history length
            })
            
            # Clean response
            response = response.strip()
            
            # Remove potential HTML artifacts from small models
            import re
            response = re.sub(r'<[^>]+>', '', response)
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            response = "I'm having trouble connecting to my brain right now. Please check if my models are running."
        
        logger.info(f"Generated response: {response[:100]}...")
        
        return response
    
    async def process_turn(self, user_input: str) -> str:
        """
        Main entry point: Process user input through dual-layer architecture
        
        Flow:
        1. Orchestrator classifies intent (Qwen)
        2. Responder generates answer (LLaMA)
        3. Update conversation memory
        4. Return response
        """
        logger.info(f"Processing: {user_input}")
        
        # OPTIMIZATION: Skip explicit intent classification to reduce latency
        # Local LLM inference is too slow for 2 passes (takes ~13s total).
        # We will let the responder handle intent implicitly.
        intent = "general"
        
        # Step 2: Generate response
        response = await self.generate_response(user_input, intent)
        
        # Step 3: Update conversation history (simple list)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep only last 20 messages to prevent memory overflow
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        logger.info(f"Response: {response}")
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Return conversation history"""
        return self.conversation_history
    
    async def clear_history(self):
        """Clear conversation memory"""
        self.conversation_history = []
        logger.info(f"Cleared history for session: {self.session_id}")
