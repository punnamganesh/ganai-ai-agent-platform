import os
import logging
from typing import Dict, Any, Optional, List
from ..agents.assistant_agent import AssistantAgent
from ..agents.specialist_agent import SpecialistAgent
from ..agents.base_agent import BaseAgent
from ..models.llm_provider import LLMProvider
from ..models.model_config import ModelConfig

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        # router uses a separate (cheaper) model
        routing_model = os.getenv("ROUTING_MODEL", "gemini-1.5-flash")
        routing_config = ModelConfig(model=routing_model, temperature=0.1, max_tokens=10)
        self._routing_llm = LLMProvider(config=routing_config)
        self._initialize_agents()

    def _initialize_agents(self):
        self.register_agent(AssistantAgent())
        self.register_agent(SpecialistAgent(
            name="CodeExpert",
            description="Software development specialist",
            domain="Software Development",
            expertise_prompt="Expert in multiple programming languages, architecture, patterns, optimisation."
        ))
        self.register_agent(SpecialistAgent(
            name="DataScientist",
            description="Data science and analytics specialist",
            domain="Data Science",
            expertise_prompt="Expert in statistical analysis, machine learning, visualisation, modelling."
        ))

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [agent.get_metadata() for agent in self._agents.values()]

    # ---- Non‑streaming ----
    async def process_with_agent(self, agent_name: Optional[str], input_text: str,
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not agent_name:
            agent_name = await self.route_to_agent(input_text, context)
        agent = self.get_agent(agent_name)
        if not agent:
            return {"success": False, "error": f"Agent '{agent_name}' not found",
                    "available_agents": list(self._agents.keys())}
        return await agent.process(input_text, context)

    # ---- Streaming ----
    async def process_stream(self, agent_name: Optional[str], input_text: str,
                             context: Optional[Dict[str, Any]] = None):
        """Yields text chunks from the chosen agent."""
        if not agent_name:
            agent_name = await self.route_to_agent(input_text, context)
        agent = self.get_agent(agent_name)
        if not agent:
            yield f"Error: Agent '{agent_name}' not found"
            return
        # Try streaming method; fallback to non‑streaming if not implemented
        if hasattr(agent, 'process_stream'):
            async for chunk in agent.process_stream(input_text, context):
                yield chunk
        else:
            result = await agent.process(input_text, context)
            if result.get("success"):
                yield result.get("response", "")
            else:
                yield f"Error: {result.get('error', 'Unknown error')}"

    # ---- Router (LLM‑based) ----
    async def route_to_agent(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        agent_descriptions = []
        for name, agent in self._agents.items():
            desc = agent.get_metadata().get("description", agent.description)
            agent_descriptions.append(f"- {name}: {desc}")
        agents_list = "\n".join(agent_descriptions)
        agent_names = ", ".join(self._agents.keys())
        prompt = f"""You are a router. Select the best agent for this query.

Available agents:
{agents_list}



User query: "{input_text}"

Respond with ONLY the agent name (one of: {agent_names})."""
        resp = self._routing_llm.generate_response(prompt=prompt, temperature=0.1, max_tokens=10)
        if resp.get("success"):
            chosen = resp["response"].strip()
            if chosen in self._agents:
                return chosen
            else:
                logger.warning(f"Router returned invalid: '{chosen}', fallback to Assistant")
                return "Assistant"
        else:
            logger.error(f"Router failed: {resp.get('error')}, fallback to Assistant")
            return "Assistant"