from typing import Dict, List, Optional
import logging
from pydantic_ai import Agent

from src.agents.models.base_agent import BaseAgent
from src.agents.models.agent import AgentBaseResponse
from src.memory.message_history import MessageHistory
from src.tools.blackpearl_tools import BlackPearlTools
from src.tools.omie_tools import OmieTools

logger = logging.getLogger(__name__)

# Backoffice agent system prompt
BACKOFFICE_PROMPT = (
    "You are the Backoffice agent for Solid, responsible for validating client information "
    "and managing client data in our systems.\n\n"
    
    "Your primary responsibilities are:\n"
    "1. Validating CNPJ numbers\n"
    "2. Searching for existing clients in our systems\n"
    "3. Updating client contact information\n\n"
    
    "Important guidelines:\n"
    "- Be thorough and accurate in your validation\n"
    "- Never mention internal tools like Omie or BlackPearl - refer to them generically as 'our system'\n"
    "- Always provide clear feedback about validation results\n"
    "- When a CNPJ is invalid, explain why it's invalid\n"
    "- When a client is found, provide all relevant information\n\n"
    
    "When responding, focus on providing factual information without unnecessary commentary."
)

class BackofficeAgent(BaseAgent):
    """Backoffice agent implementation for client validation and management."""
    
    def __init__(self, config: Dict[str, str]):
        """Initialize the backoffice agent with configuration."""
        # Validate required tokens
        if "blackpearl_token" not in config:
            raise ValueError("BlackPearl token is required for BackofficeAgent")
            
        if "omie_token" not in config:
            raise ValueError("Omie token is required for BackofficeAgent")
            
        # Store the tokens for later use by tools
        self.blackpearl_token = config["blackpearl_token"]
        self.omie_token = config["omie_token"]
        
        super().__init__(config, BACKOFFICE_PROMPT)

    def initialize_agent(self) -> Agent:
        """Initialize the backoffice agent with configuration."""
        return Agent(
            model=self.config.model,
            system_prompt=self.system_prompt,
            retries=self.config.retries
        )

    def register_tools(self):
        """Register Backoffice-specific tools with the agent."""
        # Initialize the tools
        blackpearl_tools = BlackPearlTools(self.blackpearl_token)
        omie_tools = OmieTools(self.omie_token)
        
        # Register BlackPearl tools for backoffice
        for tool in blackpearl_tools.get_backoffice_tools():
            self.agent.tool(tool)
            
        # Register Omie tools for backoffice
        for tool in omie_tools.get_backoffice_tools():
            self.agent.tool(tool)
            
    async def run(self, user_message: str, message_history: MessageHistory) -> AgentBaseResponse:
        """Run the agent with the given message and message history.
        
        Args:
            user_message: User message (already in message_history)
            message_history: Message history for this session
            
        Returns:
            Agent response
        """
        try:
            # Run the agent with the user message and message history
            result = await self.agent.run(
                user_message,
                message_history=message_history.messages
            )
            
            # Extract the response text
            response_text = result.data
            
            # Create and return the agent response
            return AgentBaseResponse.from_agent_response(
                message=response_text,
                history=message_history,
                error=None,
                session_id=message_history.session_id
            )
        except Exception as e:
            error_msg = f"Error running BackofficeAgent: {str(e)}"
            logger.error(error_msg)
            return AgentBaseResponse.from_agent_response(
                message="An error occurred while processing your request.",
                history=message_history,
                error=error_msg,
                session_id=message_history.session_id
            ) 