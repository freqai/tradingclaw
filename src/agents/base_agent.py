"""
Base Agent class for all trading agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class AgentState(BaseModel):
    """Agent state representation"""
    agent_id: str
    agent_type: str
    status: str = "idle"  # idle, analyzing, waiting_approval, executing, completed
    current_task: Optional[Dict[str, Any]] = None
    last_action: Optional[str] = None
    metrics: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Abstract base class for all trading agents"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState(agent_id=agent_id, agent_type=agent_type)
        self.is_active = True

    @abstractmethod
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data and generate insights"""
        pass

    @abstractmethod
    async def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on analysis"""
        pass

    @abstractmethod
    async def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading action"""
        pass

    async def process(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full processing pipeline: analyze -> generate signal -> (optional) execute"""
        # Analyze
        analysis = await self.analyze(market_data)
        self.state.last_action = "analysis_completed"

        # Generate signal
        signal = await self.generate_signal(analysis)
        self.state.last_action = "signal_generated"

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "analysis": analysis,
            "signal": signal,
            "timestamp": market_data.get("timestamp"),
        }

    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state

    def update_state(self, **kwargs):
        """Update agent state"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

    async def start(self):
        """Start the agent"""
        self.is_active = True
        self.update_state(status="active")

    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        self.update_state(status="stopped")

    async def reset(self):
        """Reset agent state"""
        self.state = AgentState(agent_id=self.agent_id, agent_type=self.agent_type)
