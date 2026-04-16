"""
Demo script for Chat-based Multi-Agent Trading System
Shows agents discussing and making trading decisions through conversation
"""

import asyncio
from datetime import datetime
from loguru import logger

from src.agents.chat_based_coordinator import ChatBasedMultiAgentSystem
from src.data.tdengine_client import TDengineClient


# Sample K-line data for demonstration
SAMPLE_KLINES = [
    {"timestamp": "2024-01-01 10:00:00", "open": 42000, "high": 42500, "low": 41800, "close": 42300, "volume": 1500},
    {"timestamp": "2024-01-01 11:00:00", "open": 42300, "high": 42800, "low": 42200, "close": 42700, "volume": 1800},
    {"timestamp": "2024-01-01 12:00:00", "open": 42700, "high": 43000, "low": 42500, "close": 42600, "volume": 2000},
    {"timestamp": "2024-01-01 13:00:00", "open": 42600, "high": 42900, "low": 42400, "close": 42800, "volume": 1600},
    {"timestamp": "2024-01-01 14:00:00", "open": 42800, "high": 43200, "low": 42700, "close": 43100, "volume": 2200},
    {"timestamp": "2024-01-01 15:00:00", "open": 43100, "high": 43500, "low": 43000, "close": 43400, "volume": 2500},
    {"timestamp": "2024-01-01 16:00:00", "open": 43400, "high": 43600, "low": 43200, "close": 43300, "volume": 1900},
    {"timestamp": "2024-01-01 17:00:00", "open": 43300, "high": 43500, "low": 43100, "close": 43450, "volume": 1700},
    {"timestamp": "2024-01-01 18:00:00", "open": 43450, "high": 43800, "low": 43400, "close": 43700, "volume": 2100},
    {"timestamp": "2024-01-01 19:00:00", "open": 43700, "high": 44000, "low": 43600, "close": 43900, "volume": 2400},
    {"timestamp": "2024-01-01 20:00:00", "open": 43900, "high": 44200, "low": 43800, "close": 44100, "volume": 2600},
    {"timestamp": "2024-01-01 21:00:00", "open": 44100, "high": 44300, "low": 43900, "close": 44000, "volume": 2000},
    {"timestamp": "2024-01-01 22:00:00", "open": 44000, "high": 44100, "low": 43700, "close": 43800, "volume": 1800},
    {"timestamp": "2024-01-01 23:00:00", "open": 43800, "high": 44000, "low": 43600, "close": 43900, "volume": 1600},
    {"timestamp": "2024-01-02 00:00:00", "open": 43900, "high": 44200, "low": 43850, "close": 44150, "volume": 1900},
]


async def demo_chat_based_trading():
    """Demonstrate chat-based multi-agent trading decision"""
    
    print("\n" + "="*80)
    print("🤖 CHAT-BASED MULTI-AGENT TRADING SYSTEM DEMO")
    print("="*80 + "\n")
    
    # Initialize the chat-based system
    system = ChatBasedMultiAgentSystem()
    
    # Prepare market data
    market_data = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "latest_price": 44150.0,
        "price_change_24h": 5.12,
        "klines": SAMPLE_KLINES,
        "exchange": "binance"
    }
    
    print("📊 Market Context:")
    print(f"   Symbol: {market_data['symbol']}")
    print(f"   Timeframe: {market_data['timeframe']}")
    print(f"   Current Price: ${market_data['latest_price']:,.2f}")
    print(f"   24h Change: {market_data['price_change_24h']:+.2f}%")
    print(f"   Data Points: {len(market_data['klines'])} candles\n")
    
    # Create a chat room for this trading decision
    room_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    topic = "Should we enter a LONG position on BTC/USDT?"
    
    print(f"💬 Creating chat room: {room_id}")
    print(f"   Topic: {topic}\n")
    
    room = system.create_chat_room(room_id, topic, market_data)
    
    # Start the agent discussion
    print("🚀 Starting multi-agent discussion (3 rounds)...\n")
    print("-"*80 + "\n")
    
    decision = await system.start_discussion(room_id, rounds=3)
    
    print("\n" + "-"*80)
    print("\n📋 DISCUSSION SUMMARY\n")
    
    # Display the conversation
    chat_history = system.get_chat_history(room_id)
    
    for msg in chat_history:
        emoji = "👤" if msg["sender_type"] == "human" else "🤖"
        sender_display = msg["sender"].replace("_", " ").title()
        
        print(f"{emoji} [{sender_display}]")
        print(f"   Type: {msg['type']}")
        # Show first 200 chars of content
        content_preview = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
        print(f"   Content: {content_preview}")
        print()
    
    # Display final decision
    print("\n" + "="*80)
    print("🎯 FINAL DECISION")
    print("="*80)
    print(f"\nAction: {decision.get('action', 'UNKNOWN').upper()}")
    print(f"Confidence: {decision.get('confidence', 0):.0%}")
    
    if decision.get("agent_support"):
        print(f"Agent Support: {decision.get('agent_support')} for, {decision.get('agent_oppose')} against")
    
    if decision.get("proposal"):
        print(f"\nProposal Summary:")
        proposal_preview = decision["proposal"][:300] + "..." if len(decision["proposal"]) > 300 else decision["proposal"]
        print(proposal_preview)
    
    if decision.get("requires_human_approval"):
        print("\n⚠️  Awaiting human approval before execution")
    else:
        print("\n✅ Decision ready for automatic execution")
    
    print("\n" + "="*80)
    
    return decision


async def demo_with_human_input():
    """Demonstrate human joining the agent conversation"""
    
    print("\n\n" + "="*80)
    print("👤 HUMAN-IN-THE-LOOP DEMO")
    print("="*80 + "\n")
    
    system = ChatBasedMultiAgentSystem()
    
    market_data = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "latest_price": 44150.0,
        "price_change_24h": 5.12,
        "klines": SAMPLE_KLINES,
        "exchange": "binance"
    }
    
    room_id = f"trade_human_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    room = system.create_chat_room(room_id, "BTC/USDT trade analysis", market_data)
    
    # Run initial discussion
    await system.start_discussion(room_id, rounds=2)
    
    # Human joins with input
    human_input = "I'm concerned about the upcoming Fed announcement tomorrow. Should we wait for more clarity before entering?"
    
    print(f"\n👤 Human joins the conversation:")
    print(f"   \"{human_input}\"\n")
    
    # Add human input
    decision = await system.add_human_input(room_id, human_input)
    
    # Show updated conversation
    chat_history = system.get_chat_history(room_id)[-5:]  # Last 5 messages
    
    print("💬 Recent conversation after human input:\n")
    for msg in chat_history:
        emoji = "👤" if msg["sender_type"] == "human" else "🤖"
        sender_display = msg["sender"].replace("_", " ").title()
        content_preview = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
        print(f"{emoji} [{sender_display}]: {content_preview}")
    
    print(f"\n🎯 Updated Decision: {decision.get('action', 'UNKNOWN').upper()}")
    
    return decision


async def main():
    """Main demo runner"""
    
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg), format="{message}")
    
    try:
        # Demo 1: Pure agent discussion
        decision1 = await demo_chat_based_trading()
        
        # Demo 2: With human input
        decision2 = await demo_with_human_input()
        
        print("\n\n" + "="*80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("  ✓ Multi-agent conversation without orchestration framework")
        print("  ✓ Specialized agent personas (Pattern, Trend, Risk, Sentiment, Execution)")
        print("  ✓ Consensus building through natural dialogue")
        print("  ✓ Human-in-the-loop capability")
        print("  ✓ Structured decision output")
        print("\nNext Steps:")
        print("  - Integrate with real LLM APIs (OpenAI/Anthropic)")
        print("  - Connect to live market data via TDengine")
        print("  - Add Redis pub/sub for real-time chat streaming")
        print("  - Build UI for human interaction")
        print()
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
