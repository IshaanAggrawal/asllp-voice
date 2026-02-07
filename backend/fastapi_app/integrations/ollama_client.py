import httpx
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with local Ollama instance
    
    This handles communication with Ollama for both:
    1. Orchestration layer (Qwen for intent classification)
    2. Conversational layer (LLaMA for response generation)
    """
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.conversational_model = os.getenv("OLLAMA_CONVERSATIONAL_MODEL", "llama3.2:1b")
        self.orchestration_model = os.getenv("OLLAMA_ORCHESTRATION_MODEL", "qwen2.5:1.5b")
        self.timeout = 30.0
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using Ollama
        
        Args:
            prompt: User input or conversation context
            model: Model to use (defaults to conversational model)
            system_prompt: Custom system prompt for agent personality
            temperature: Generation temperature (0-1)
        
        Returns:
            Generated text response
        """
        model = model or self.conversational_model
        
        logger.info(f"Generating response with model: {model}")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return data.get("message", {}).get("content", "")
                
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def classify_intent(self, transcript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use orchestration model to classify user intent
        
        This is where Qwen analyzes the transcript and determines:
        - What the user wants
        - How to route the conversation
        - What context to pass to the conversational layer
        
        TODO: Implement proper intent classification logic
        For assessment, you can create a simple classifier or use few-shot prompting
        """
        system_prompt = """You are an intent classifier for a voice agent system.
        Analyze the user's input and classify the intent. Return your response in JSON format with:
        - intent: The classified intent (greeting, question, command, etc.)
        - entities: Any relevant entities extracted
        - confidence: Confidence score 0-1
        """
        
        prompt = f"Classify this user input: '{transcript}'"
        
        response = await self.generate_response(
            prompt=prompt,
            model=self.orchestration_model,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for classification
        )
        
        # TODO: Parse JSON response properly
        # For now, return a simple structure
        return {
            "intent": "general_query",
            "entities": [],
            "confidence": 0.8,
            "raw_classification": response
        }
    
    async def health_check(self) -> bool:
        """Check if Ollama is reachable"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
