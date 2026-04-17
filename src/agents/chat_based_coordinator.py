"""
Chat-based Multi-Agent System
Inspired by Claude Code architecture - agents converse in a shared chat context
No orchestration framework, just natural conversation and consensus building
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import asyncio
from loguru import logger


class ChatMessage(BaseModel):
    """Represents a message in the agent chat"""
    id: str
    sender: str  # agent_id or "human"
    sender_type: str  # "agent" or "human"
    content: str
    timestamp: datetime
    message_type: str = "discussion"  # discussion, proposal, vote, decision
    metadata: Dict[str, Any] = {}


class ChatRoom:
    """Shared chat context where all agents converse"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.messages: List[ChatMessage] = []
        self.participants: List[str] = []  # agent_ids
        self.human_present = False
        self.decision_reached = False
        self.final_decision: Optional[Dict[str, Any]] = None
        
    def add_message(self, message: ChatMessage):
        """Add message to chat history"""
        self.messages.append(message)
        logger.debug(f"[{self.room_id}] {message.sender}: {message.content[:100]}...")
        
    def get_recent_messages(self, limit: int = 50) -> List[ChatMessage]:
        """Get recent messages for context"""
        return self.messages[-limit:]
    
    def get_full_context(self) -> str:
        """Build full conversation context as string"""
        context_lines = []
        for msg in self.messages:
            prefix = "👤" if msg.sender_type == "human" else "🤖"
            context_lines.append(
                f"{prefix} [{msg.sender}] ({msg.message_type}): {msg.content}"
            )
        return "\n\n".join(context_lines)
    
    def add_participant(self, agent_id: str):
        """Add agent as participant"""
        if agent_id not in self.participants:
            self.participants.append(agent_id)
            
    def human_join(self):
        """Mark human as present"""
        self.human_present = True
        
    def reach_decision(self, decision: Dict[str, Any]):
        """Record final decision"""
        self.decision_reached = True
        self.final_decision = decision


class AgentPersona(BaseModel):
    """Defines an agent's personality and expertise"""
    agent_id: str
    name: str
    role: str
    expertise: List[str]
    communication_style: str  # "analytical", "cautious", "aggressive", "balanced"
    system_prompt: str
    
    @classmethod
    def create_default_personas(cls) -> List["AgentPersona"]:
        """Create default trading agent personas"""
        return [
            cls(
                agent_id="pattern_analyst",
                name="Pattern Analyst",
                role="Technical Pattern Recognition Specialist",
                expertise=["candlestick_patterns", "chart_formations", "support_resistance"],
                communication_style="analytical",
                system_prompt="""You are an expert technical analyst specializing in K-line pattern recognition.
Your role is to identify chart patterns (head & shoulders, triangles, engulfing, etc.) and explain their implications.
Be precise, cite specific price levels, and always mention your confidence level.
Speak concisely but thoroughly. Challenge assumptions if you see contradictory patterns."""
            ),
            cls(
                agent_id="trend_strategist",
                name="Trend Strategist", 
                role="Trend Analysis & Momentum Expert",
                expertise=["trend_following", "momentum", "moving_averages", "market_structure"],
                communication_style="balanced",
                system_prompt="""You are a trend-following specialist focused on market momentum and structure.
Analyze higher timeframe trends, moving average alignments, and momentum indicators.
Advocate for trading with the trend unless there's strong evidence of reversal.
Question counter-trend suggestions rigorously."""
            ),
            cls(
                agent_id="risk_manager",
                name="Risk Manager",
                role="Risk Assessment & Position Sizing",
                expertise=["risk_management", "position_sizing", "stop_loss", "portfolio_protection"],
                communication_style="cautious",
                system_prompt="""You are the risk management guardian. Your primary concern is capital preservation.
For every trade proposal, demand clear entry, stop-loss, take-profit levels and position size.
Challenge risky proposals. Calculate risk/reward ratios. Remind the team about drawdown limits.
It's better to miss a trade than lose money unnecessarily."""
            ),
            cls(
                agent_id="sentiment_analyst",
                name="Sentiment Analyst",
                role="Market Sentiment & On-Chain Data Expert",
                expertise=["sentiment_analysis", "on_chain_metrics", "funding_rates", "open_interest"],
                communication_style="analytical",
                system_prompt="""You analyze market sentiment, funding rates, open interest, and on-chain data.
Provide context about whether the market is overly bullish or bearish.
Warn about potential squeezes or crowded trades.
Help the team understand the broader market psychology."""
            ),
            cls(
                agent_id="execution_specialist",
                name="Execution Specialist",
                role="Trade Execution & Market Microstructure",
                expertise=["order_types", "slippage", "liquidity", "execution_timing"],
                communication_style="practical",
                system_prompt="""You focus on how to actually execute trades efficiently.
Advise on order types (limit vs market), timing, and liquidity considerations.
Estimate slippage and suggest optimal entry strategies.
Ensure proposed trades are executable in real market conditions."""
            ),
        ]


class ChatBasedMultiAgentSystem:
    """
    Multi-agent system using chat-based conversation instead of orchestration.
    Agents discuss, debate, and build consensus naturally through conversation.
    """
    
    def __init__(self, personas: Optional[List[AgentPersona]] = None):
        self.personas = personas or AgentPersona.create_default_personas()
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self.chat_rooms: Dict[str, ChatRoom] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    def create_chat_room(self, room_id: str, topic: str, market_data: Dict[str, Any]) -> ChatRoom:
        """Create a new chat room for discussion"""
        room = ChatRoom(room_id=room_id)
        
        # Add initial context message
        context_msg = ChatMessage(
            id="context_001",
            sender="system",
            sender_type="agent",
            content=f"Discussion Topic: {topic}\n\nMarket Context:\n{self._format_market_context(market_data)}",
            timestamp=datetime.utcnow(),
            message_type="context",
            metadata={"market_data": market_data}
        )
        room.add_message(context_msg)
        
        # Add all agents as participants
        for persona in self.personas:
            room.add_participant(persona.agent_id)
            
        self.chat_rooms[room_id] = room
        logger.info(f"Created chat room '{room_id}' with {len(self.personas)} agents")
        return room
    
    def _format_market_context(self, market_data: Dict[str, Any]) -> str:
        """Format market data for chat context"""
        lines = []
        if "symbol" in market_data:
            lines.append(f"Symbol: {market_data['symbol']}")
        if "timeframe" in market_data:
            lines.append(f"Timeframe: {market_data['timeframe']}")
        if "latest_price" in market_data:
            lines.append(f"Current Price: ${market_data['latest_price']:,.2f}")
        if "price_change_24h" in market_data:
            change = market_data["price_change_24h"]
            lines.append(f"24h Change: {change:+.2f}%")
        if "klines" in market_data and market_data["klines"]:
            klines = market_data["klines"][-5:]  # Last 5 candles
            lines.append("\nRecent Candles:")
            for k in klines:
                lines.append(
                    f"  {k.get('timestamp', 'N/A')}: O:{k.get('open', 0):,.2f} "
                    f"H:{k.get('high', 0):,.2f} L:{k.get('low', 0):,.2f} "
                    f"C:{k.get('close', 0):,.2f} V:{k.get('volume', 0):,.0f}"
                )
        return "\n".join(lines)
    
    async def start_discussion(self, room_id: str, rounds: int = 3) -> Dict[str, Any]:
        """
        Run a multi-round discussion among agents.
        Each round, agents read the conversation and contribute based on their expertise.
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            raise ValueError(f"Chat room '{room_id}' not found")
        
        logger.info(f"Starting discussion in room '{room_id}' for {rounds} rounds")
        
        for round_num in range(1, rounds + 1):
            logger.info(f"--- Discussion Round {round_num} ---")
            
            # Each agent takes a turn to speak
            for persona in self.personas:
                if room.decision_reached:
                    break
                    
                # Get current conversation context
                context = room.get_full_context()
                
                # Generate agent's response
                response = await self._generate_agent_response(
                    persona=persona,
                    context=context,
                    round_num=round_num,
                    room=room
                )
                
                if response:
                    message = ChatMessage(
                        id=f"{room_id}_r{round_num}_{persona.agent_id}",
                        sender=persona.agent_id,
                        sender_type="agent",
                        content=response["content"],
                        timestamp=datetime.utcnow(),
                        message_type=response.get("message_type", "discussion"),
                        metadata=response.get("metadata", {})
                    )
                    room.add_message(message)
                    
                    # Check if agent is proposing a trade
                    if response.get("message_type") == "proposal":
                        # Trigger voting/consensus phase
                        await self._start_consensus_phase(room, persona, response)
            
            # Check if we have consensus
            if self._check_consensus(room):
                logger.info("Consensus reached!")
                break
        
        # Final synthesis
        if room.decision_reached:
            return room.final_decision
        else:
            return self._synthesize_final_decision(room)
    
    async def _generate_agent_response(
        self,
        persona: AgentPersona,
        context: str,
        round_num: int,
        room: ChatRoom
    ) -> Optional[Dict[str, Any]]:
        """Generate response for an agent based on context and persona"""
        # This would call the actual AI model
        # For now, we'll use a placeholder that demonstrates the pattern
        
        from ..ai_engine.multimodal_analyzer import MultiModalAnalyzer
        from ..agents.pattern_agent import PatternAgent
        
        # Build prompt for the agent
        prompt = f"""{persona.system_prompt}

=== CONVERSATION HISTORY ===
{context}

=== YOUR TURN ===
You are {persona.name} ({persona.role}).
Based on the conversation so far and your expertise, what would you like to contribute?

Consider:
1. Have you added unique value based on your expertise?
2. Do you agree or disagree with previous points? Why?
3. Is there enough information to make a trade proposal?
4. If others have made proposals, do you support or oppose them?

Respond in this format:
TYPE: [discussion|proposal|vote|question]
CONTENT: Your message to the group

If making a proposal, include:
PROPOSAL:
- Action: BUY/SELL/HOLD
- Entry: price
- Stop Loss: price  
- Take Profit: price(s)
- Position Size: % of portfolio
- Reasoning: brief explanation
- Confidence: 0-100%
"""
        
        # For demonstration, use pattern analyzer if available
        if persona.agent_id == "pattern_analyst" and round_num == 1:
            # First round: pattern analyst shares initial analysis
            try:
                # Extract market data from context
                last_msg = room.messages[0]  # Context message
                market_data = last_msg.metadata.get("market_data", {})
                
                if market_data.get("klines"):
                    pattern_agent = PatternAgent()
                    analysis = await pattern_agent.analyze(market_data)
                    signal = await pattern_agent.generate_signal(analysis)
                    
                    return {
                        "content": f"""After analyzing the K-line chart, I've identified the following patterns:

{analysis.get('description', 'No clear patterns detected')}

Key observations:
- Patterns found: {[p.get('name') for p in analysis.get('patterns', [])]}
- Overall confidence: {analysis.get('confidence', 0):.0%}

Based on this analysis, my initial assessment is {'bullish' if signal.get('action') == 'buy' else 'bearish' if signal.get('action') == 'sell' else 'neutral'}.

I'm interested to hear the trend strategist's view on the broader market structure.""",
                        "message_type": "discussion",
                        "metadata": {"analysis": analysis, "signal": signal}
                    }
            except Exception as e:
                logger.error(f"Pattern analysis failed: {e}")
        
        # Default response generation (would be replaced with actual LLM call)
        return await self._call_llm_for_agent(persona, prompt, context)
    
    async def _call_llm_for_agent(
        self,
        persona: AgentPersona,
        prompt: str,
        context: str
    ) -> Optional[Dict[str, Any]]:
        """Call LLM to generate agent response"""
        # This integrates with the existing MultiModalAnalyzer
        analyzer = MultiModalAnalyzer()
        
        try:
            # Use text-only analysis for chat responses
            if analyzer.provider == "openai":
                from openai import AsyncOpenAI
                client = AsyncOpenAI()
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": persona.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                
                content = response.choices[0].message.content
                return self._parse_agent_response(content)
                
            elif analyzer.provider == "anthropic":
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic()
                
                response = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system=persona.system_prompt,
                )
                
                content = response.content[0].text
                return self._parse_agent_response(content)
                
        except Exception as e:
            logger.error(f"LLM call failed for {persona.agent_id}: {e}")
            return None
    
    def _parse_agent_response(self, content: str) -> Dict[str, Any]:
        """Parse agent response into structured format"""
        lines = content.strip().split('\n')
        
        result = {
            "content": content,
            "message_type": "discussion",
            "metadata": {}
        }
        
        for line in lines:
            if line.startswith("TYPE:"):
                result["message_type"] = line.replace("TYPE:", "").strip()
            elif line.startswith("PROPOSAL:"):
                result["message_type"] = "proposal"
                # Parse proposal details
                result["metadata"]["has_proposal"] = True
        
        return result
    
    async def _start_consensus_phase(self, room: ChatRoom, proposer_persona: AgentPersona, proposal: Dict[str, Any]):
        """Initiate voting/consensus phase after a proposal"""
        logger.info(f"Starting consensus phase for proposal from {proposer_persona.agent_id}")
        
        # Ask each agent to vote
        for persona in self.personas:
            if persona.agent_id == proposer_persona.agent_id:
                continue  # Skip the proposer
                
            vote_prompt = f"""{persona.system_prompt}

A trade proposal has been made by {proposer_persona.name}:

{proposal.get('content', 'No details')}

Please review and cast your vote:
- SUPPORT: You agree with this trade
- OPPOSE: You have concerns (explain why)
- ABSTAIN: You don't have strong opinion

Respond with your vote and reasoning."""
            
            # Generate vote (would call LLM)
            vote_response = ChatMessage(
                id=f"{room.room_id}_vote_{persona.agent_id}",
                sender=persona.agent_id,
                sender_type="agent",
                content=f"[VOTE PENDING - Would call LLM]",
                timestamp=datetime.utcnow(),
                message_type="vote",
                metadata={"proposal_from": proposer_persona.agent_id}
            )
            room.add_message(vote_response)
    
    def _check_consensus(self, room: ChatRoom) -> bool:
        """Check if consensus has been reached"""
        recent_messages = room.get_recent_messages(20)
        
        votes = [m for m in recent_messages if m.message_type == "vote"]
        if len(votes) < len(self.personas) * 0.6:  # Need 60% participation
            return False
        
        # Count support vs oppose
        support_count = 0
        oppose_count = 0
        
        for vote in votes:
            content_lower = vote.content.lower()
            if "support" in content_lower or "agree" in content_lower:
                support_count += 1
            elif "oppose" in content_lower or "disagree" in content_lower:
                oppose_count += 1
        
        # Consensus if >70% support and minimal opposition
        total_voters = support_count + oppose_count
        if total_voters > 0:
            support_ratio = support_count / total_voters
            if support_ratio > 0.7 and oppose_count <= 1:
                return True
        
        return False
    
    def _synthesize_final_decision(self, room: ChatRoom) -> Dict[str, Any]:
        """Synthesize final decision from conversation"""
        # Find any proposals and votes
        proposals = [m for m in room.messages if m.message_type == "proposal"]
        votes = [m for m in room.messages if m.message_type == "vote"]
        
        if not proposals:
            return {
                "action": "hold",
                "reason": "No trade proposals reached sufficient support",
                "confidence": 0.0,
                "conversation_summary": room.get_full_context()[-2000:]
            }
        
        # Use the most recent proposal
        latest_proposal = proposals[-1]
        
        # Count final votes
        support = sum(1 for v in votes if "support" in v.content.lower())
        oppose = sum(1 for v in votes if "oppose" in v.content.lower())
        
        confidence = support / (support + oppose) if (support + oppose) > 0 else 0.5
        
        decision = {
            "action": "pending_review",  # Awaiting human input
            "proposal": latest_proposal.content,
            "agent_support": support,
            "agent_oppose": oppose,
            "confidence": confidence,
            "requires_human_approval": room.human_present,
            "full_conversation": room.get_full_context()
        }
        
        if not room.human_present:
            # Auto-decide based on agent consensus
            if confidence > 0.7:
                decision["action"] = "execute"
            else:
                decision["action"] = "hold"
        
        room.reach_decision(decision)
        return decision
    
    async def add_human_input(self, room_id: str, human_message: str) -> Dict[str, Any]:
        """Add human input to the conversation"""
        room = self.chat_rooms.get(room_id)
        if not room:
            raise ValueError(f"Chat room '{room_id}' not found")
        
        room.human_join()
        
        human_msg = ChatMessage(
            id=f"{room_id}_human_{len(room.messages)}",
            sender="human",
            sender_type="human",
            content=human_message,
            timestamp=datetime.utcnow(),
            message_type="discussion"
        )
        room.add_message(human_msg)
        
        # Let agents respond to human input
        for persona in self.personas[:2]:  # Only 2 agents respond to keep it concise
            response = await self._generate_agent_response(
                persona=persona,
                context=room.get_full_context(),
                round_num=99,  # Special round for human interaction
                room=room
            )
            if response:
                msg = ChatMessage(
                    id=f"{room_id}_response_{persona.agent_id}",
                    sender=persona.agent_id,
                    sender_type="agent",
                    content=response["content"],
                    timestamp=datetime.utcnow(),
                    message_type=response.get("message_type", "discussion")
                )
                room.add_message(msg)
        
        # Re-evaluate decision after human input
        if room.decision_reached:
            return room.final_decision
        else:
            return self._synthesize_final_decision(room)
    
    def get_chat_history(self, room_id: str) -> List[Dict[str, Any]]:
        """Get formatted chat history"""
        room = self.chat_rooms.get(room_id)
        if not room:
            return []
        
        return [
            {
                "id": msg.id,
                "sender": msg.sender,
                "sender_type": msg.sender_type,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "type": msg.message_type
            }
            for msg in room.messages
        ]
