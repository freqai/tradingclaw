"""
Multi-Agent Coordinator using LangGraph
Orchestrates multiple trading agents and human-in-the-loop decision making
"""

from typing import Dict, Any, Optional, List, Annotated
from loguru import logger
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .base_agent import BaseAgent
from .pattern_agent import PatternAgent
from ..config.settings import settings


class AgentCoordinator:
    """Coordinate multiple trading agents with human-in-the-loop"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.graph = None
        self.state: Dict[str, Any] = {}
        self._initialize_agents()
        self._build_workflow()

    def _initialize_agents(self):
        """Initialize all trading agents"""
        
        # Pattern Analysis Agent (Multi-modal AI)
        pattern_agent = PatternAgent(agent_id="pattern_01")
        self.agents["pattern_agent"] = pattern_agent
        logger.info("Initialized pattern analysis agent")

        # TODO: Add more agents
        # - Trend Agent
        # - Mean Reversion Agent  
        # - Risk Management Agent
        # - Execution Agent

        logger.info(f"Initialized {len(self.agents)} agents")

    def _build_workflow(self):
        """Build LangGraph workflow for agent coordination"""

        # Define state schema
        class TradingState(dict):
            messages: List
            market_data: Dict
            agent_outputs: Dict
            human_decision: Optional[Dict]
            final_action: Optional[Dict]

        # Create graph
        workflow = StateGraph(TradingState)

        # Add nodes
        workflow.add_node("pattern_analysis", self._run_pattern_agent)
        workflow.add_node("aggregate_signals", self._aggregate_signals)
        workflow.add_node("human_review", self._human_review)
        workflow.add_node("execute_trade", self._execute_trade)

        # Define edges
        workflow.set_entry_point("pattern_analysis")
        
        # Pattern analysis -> Aggregate signals
        workflow.add_edge("pattern_analysis", "aggregate_signals")
        
        # Aggregate -> Human review (if approval required)
        if settings.REQUIRE_HUMAN_APPROVAL:
            workflow.add_edge("aggregate_signals", "human_review")
            workflow.add_edge("human_review", "execute_trade")
        else:
            workflow.add_conditional_edges(
                "aggregate_signals",
                self._should_execute,
                {
                    "execute": "execute_trade",
                    "hold": END,
                }
            )
        
        workflow.add_edge("execute_trade", END)

        self.graph = workflow.compile()
        logger.info("Agent workflow built successfully")

    async def _run_pattern_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run pattern analysis agent"""
        logger.info("Running pattern analysis agent...")
        
        market_data = state.get("market_data", {})
        agent = self.agents.get("pattern_agent")
        
        if not agent:
            return {"agent_outputs": {"pattern_agent": {"error": "Agent not found"}}}

        try:
            output = await agent.process(market_data)
            logger.info(f"Pattern agent completed: {output.get('signal', {}).get('action', 'unknown')}")
            
            return {
                "agent_outputs": {"pattern_agent": output},
                "messages": [AIMessage(content=f"Pattern analysis completed: {output.get('signal', {}).get('reason', '')}")]
            }
        except Exception as e:
            logger.error(f"Pattern agent failed: {e}")
            return {
                "agent_outputs": {"pattern_agent": {"error": str(e)}},
                "messages": [AIMessage(content=f"Pattern analysis failed: {str(e)}")]
            }

    async def _aggregate_signals(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate signals from all agents"""
        logger.info("Aggregating agent signals...")
        
        agent_outputs = state.get("agent_outputs", {})
        
        # Collect all signals
        signals = []
        for agent_name, output in agent_outputs.items():
            signal = output.get("signal", {})
            if signal:
                signals.append({
                    "agent": agent_name,
                    "action": signal.get("action"),
                    "confidence": signal.get("confidence", 0.0),
                    "reason": signal.get("reason"),
                })

        # Simple aggregation logic (can be enhanced)
        if not signals:
            aggregated_action = "hold"
            aggregated_confidence = 0.0
        else:
            # Weight by confidence
            buy_score = sum(s["confidence"] for s in signals if s["action"] == "buy")
            sell_score = sum(s["confidence"] for s in signals if s["action"] == "sell")
            
            if buy_score > sell_score:
                aggregated_action = "buy"
            elif sell_score > buy_score:
                aggregated_action = "sell"
            else:
                aggregated_action = "hold"
            
            aggregated_confidence = max(buy_score, sell_score) / len(signals) if signals else 0.0

        aggregated_signal = {
            "action": aggregated_action,
            "confidence": aggregated_confidence,
            "signals": signals,
            "recommendation": f"Aggregated recommendation: {aggregated_action.upper()} (confidence: {aggregated_confidence:.2f})",
        }

        logger.info(f"Aggregated signal: {aggregated_action} (confidence: {aggregated_confidence:.2f})")
        
        return {
            "agent_outputs": {**agent_outputs, "aggregated": aggregated_signal},
            "messages": [AIMessage(content=aggregated_signal["recommendation"])]
        }

    async def _human_review(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for human review and decision"""
        logger.info("Waiting for human review...")
        
        aggregated = state.get("agent_outputs", {}).get("aggregated", {})
        
        # In a real implementation, this would wait for user input via API/UI
        # For now, we'll simulate with a timeout
        
        human_decision = state.get("human_decision")
        
        if not human_decision:
            # Simulate timeout - in production, this would be async wait for user
            logger.warning("Human review timeout - defaulting to hold")
            human_decision = {
                "action": "hold",
                "reason": "No human response within timeout",
                "approved": False,
            }

        logger.info(f"Human decision: {human_decision.get('action', 'unknown')}")
        
        return {
            "human_decision": human_decision,
            "messages": [HumanMessage(content=f"Human decision: {human_decision.get('reason', '')}")]
        }

    async def _execute_trade(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade based on decision"""
        logger.info("Executing trade...")
        
        # Determine what to execute
        human_decision = state.get("human_decision")
        aggregated = state.get("agent_outputs", {}).get("aggregated", {})
        
        if human_decision and human_decision.get("approved"):
            action = human_decision.get("action", "hold")
            reason = f"Human approved: {human_decision.get('reason', '')}"
        else:
            action = aggregated.get("action", "hold")
            reason = aggregated.get("recommendation", "")

        # In production, this would call the execution agent/exchange
        execution_result = {
            "action": action,
            "status": "simulated",  # Would be "executed" in production
            "reason": reason,
            "timestamp": asyncio.get_event_loop().time(),
        }

        logger.info(f"Trade execution: {action} ({execution_result['status']})")
        
        return {
            "final_action": execution_result,
            "messages": [AIMessage(content=f"Trade {action} executed ({execution_result['status']})")]
        }

    def _should_execute(self, state: Dict[str, Any]) -> str:
        """Conditional edge: decide whether to execute or hold"""
        aggregated = state.get("agent_outputs", {}).get("aggregated", {})
        confidence = aggregated.get("confidence", 0.0)
        
        if confidence > 0.7 and aggregated.get("action") != "hold":
            return "execute"
        else:
            return "hold"

    async def process_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market data through the agent workflow"""
        
        initial_state = {
            "messages": [],
            "market_data": market_data,
            "agent_outputs": {},
            "human_decision": None,
            "final_action": None,
        }

        logger.info(f"Processing market data for {market_data.get('symbol', 'unknown')}")
        
        try:
            result = await self.graph.ainvoke(initial_state)
            logger.info("Workflow completed successfully")
            return result
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise

    async def start(self):
        """Start all agents"""
        for name, agent in self.agents.items():
            await agent.start()
        logger.info("All agents started")

    async def stop(self):
        """Stop all agents"""
        for name, agent in self.agents.items():
            await agent.stop()
        logger.info("All agents stopped")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            name: agent.get_state().dict()
            for name, agent in self.agents.items()
        }
