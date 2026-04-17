"""
Pattern Analysis Agent - Analyzes K-line chart patterns using multi-modal AI
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseAgent
from ..ai_engine.multimodal_analyzer import MultiModalAnalyzer
from ..data.chart_generator import ChartGenerator


class PatternAgent(BaseAgent):
    """Agent responsible for analyzing K-line chart patterns"""

    def __init__(self, agent_id: str = "pattern_agent_01"):
        super().__init__(agent_id=agent_id, agent_type="pattern_analysis")
        self.analyzer = MultiModalAnalyzer()
        self.chart_generator = ChartGenerator()
        self.pattern_history: List[Dict[str, Any]] = []

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze K-line chart for patterns using multi-modal AI"""

        klines = market_data.get("klines", [])
        symbol = market_data.get("symbol", "BTC/USDT")
        timeframe = market_data.get("timeframe", "1h")

        if not klines or len(klines) < 10:
            logger.warning("Insufficient K-line data for pattern analysis")
            return {"error": "Insufficient data", "patterns": []}

        # Generate chart for AI analysis
        chart_data = self.chart_generator.create_chart_for_ai(
            klines=klines,
            symbol=symbol,
            timeframe=timeframe,
        )

        # Use multi-modal AI to analyze chart patterns
        analysis_result = await self.analyzer.analyze_chart(
            image_base64=chart_data["image_base64"],
            market_summary=chart_data["summary"],
            context={
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_type": "pattern_recognition",
            },
        )

        # Extract identified patterns
        patterns = analysis_result.get("identified_patterns", [])
        confidence = analysis_result.get("confidence_score", 0.0)
        description = analysis_result.get("description", "")

        result = {
            "patterns": patterns,
            "confidence": confidence,
            "description": description,
            "chart_summary": chart_data["summary"],
            "ai_analysis": analysis_result,
            "data_points": len(klines),
        }

        # Store in history
        self.pattern_history.append({
            "timestamp": market_data.get("timestamp"),
            "patterns": patterns,
            "confidence": confidence,
        })

        logger.info(f"Pattern analysis completed: {len(patterns)} patterns identified")
        return result

    async def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on pattern analysis"""

        patterns = analysis.get("patterns", [])
        confidence = analysis.get("confidence", 0.0)

        if not patterns or confidence < 0.6:
            return {
                "action": "hold",
                "reason": "No high-confidence patterns detected",
                "confidence": confidence,
            }

        # Analyze pattern implications
        bullish_patterns = [p for p in patterns if p.get("type") == "bullish"]
        bearish_patterns = [p for p in patterns if p.get("type") == "bearish"]

        # Determine signal
        if len(bullish_patterns) > len(bearish_patterns):
            action = "buy"
            reason = f"Bullish patterns dominant: {[p['name'] for p in bullish_patterns]}"
        elif len(bearish_patterns) > len(bullish_patterns):
            action = "sell"
            reason = f"Bearish patterns dominant: {[p['name'] for p in bearish_patterns]}"
        else:
            action = "hold"
            reason = "Mixed signals from patterns"

        signal = {
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "patterns": patterns,
            "suggested_entry": analysis.get("chart_summary", {}).get("latest_price"),
            "agent_type": "pattern_analysis",
        }

        logger.info(f"Pattern signal generated: {action} (confidence: {confidence:.2f})")
        return signal

    async def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Pattern agent doesn't execute directly - sends to execution agent"""
        logger.info("Pattern agent does not execute trades directly")
        return {
            "status": "forwarded",
            "message": "Signal forwarded to execution coordinator",
            "signal": signal,
        }

    def get_recent_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pattern analysis history"""
        return self.pattern_history[-limit:]
