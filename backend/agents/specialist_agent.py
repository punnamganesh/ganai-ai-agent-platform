import logging
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class SpecialistAgent(BaseAgent):
    """Specialized agent for specific domains"""
    
    def __init__(self, name: str, description: str, domain: str, expertise_prompt: str):
        super().__init__(name, description)
        self.domain = domain
        self.expertise_prompt = expertise_prompt
        self.llm = LLMProvider()
    
    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process input as a domain specialist"""
        try:
            self.add_to_history("user", input_text)
            
            # Create specialized system prompt
            system_prompt = f"""You are {self.name}, an expert in {self.domain}.
            
            Expertise: {self.expertise_prompt}
            
            Guidelines:
            1. Provide expert-level insights based on your domain knowledge
            2. Be specific and technical when appropriate
            3. Reference relevant concepts and best practices
            4. Stay within your domain of expertise
            5. If asked something outside your domain, politely redirect or suggest other specialists
            
            Respond with confidence and authority in your field."""
            
            response = self.llm.generate_response(
                prompt=input_text,
                system_prompt=system_prompt
            )
            
            if response["success"]:
                self.add_to_history("assistant", response["response"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SpecialistAgent: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request."
            }