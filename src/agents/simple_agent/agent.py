import logging
from typing import Dict

from src.agents.models.base_agent import BaseAgent
from src.agents.simple_agent.prompts import SIMPLE_AGENT_PROMPT

class SimpleAgent(BaseAgent):
    def __init__(self, config: Dict[str, str]):
        super().__init__(config, SIMPLE_AGENT_PROMPT)

    def register_tools(self):
        """Register tools with the agent."""
        from src.tools.datetime_tools import get_current_date, get_current_time
        self.agent.tool(get_current_date)
        self.agent.tool(get_current_time)

# Remove the process_message method as it's now handled by BaseAgent
        