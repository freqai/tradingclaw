"""
Trend Strategy Agent - Analyzes market trends and momentum
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseAgent


class TrendAgent(BaseAgent):
    """Agent responsible for trend analysis and momentum strategies"""

    def __init__(self, agent_id: str = "trend_agent_01"):
        super().__init__(agent_id=agent_id, agent_type="trend_analysis")
        self.trend_history: List[Dict[str, Any]] = []

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends using technical indicators"""

        klines = market_data.get("klines", [])
        symbol = market_data.get("symbol", "BTC/USDT")
        timeframe = market_data.get("timeframe", "1h")

        if not klines or len(klines) < 50:
            logger.warning("Insufficient data for trend analysis")
            return {"error": "Insufficient data", "trend": "unknown"}

        # Extract prices
        closes = [k["close"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]

        # Calculate moving averages
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
        ma200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else closes[-1]

        current_price = closes[-1]

        # Determine trend
        if current_price > ma20 > ma50 > ma200:
            trend = "strong_bullish"
            confidence = 0.8
        elif current_price > ma20 > ma50:
            trend = "bullish"
            confidence = 0.7
        elif current_price > ma20:
            trend = "weak_bullish"
            confidence = 0.6
        elif current_price < ma20 < ma50 < ma200:
            trend = "strong_bearish"
            confidence = 0.8
        elif current_price < ma20 < ma50:
            trend = "bearish"
            confidence = 0.7
        elif current_price < ma20:
            trend = "weak_bearish"
            confidence = 0.6
        else:
            trend = "sideways"
            confidence = 0.5

        # Calculate momentum (simple RSI approximation)
        gains = []
        losses = []
        for i in range(1, min(14, len(closes))):
            change = closes[-i] - closes[-i-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))

        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 1
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        result = {
            "trend": trend,
            "confidence": confidence,
            "current_price": current_price,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "rsi": rsi,
            "rsi_signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
            "market_structure": self._analyze_market_structure(highs, lows),
            "momentum": "positive" if rsi > 50 else "negative",
        }

        self.trend_history.append(result)
        logger.info(f"Trend analysis completed: {trend} (RSI: {rsi:.1f})")
        return result

    def _analyze_market_structure(self, highs: List[float], lows: List[float]) -> Dict[str, Any]:
        """Analyze higher highs/lows structure"""
        if len(highs) < 10:
            return {"structure": "insufficient_data"}

        recent_highs = highs[-10:]
        recent_lows = lows[-10:]

        hh = all(recent_highs[i] >= recent_highs[i-1] for i in range(1, len(recent_highs), 2))
        hl = all(recent_lows[i] >= recent_lows[i-1] for i in range(1, len(recent_lows), 2))
        lh = all(recent_highs[i] <= recent_highs[i-1] for i in range(1, len(recent_highs), 2))
        ll = all(recent_lows[i] <= recent_lows[i-1] for i in range(1, len(recent_lows), 2))

        if hh and hl:
            return {"structure": "uptrend", "pattern": "HH+HL"}
        elif lh and ll:
            return {"structure": "downtrend", "pattern": "LH+LL"}
        else:
            return {"structure": "consolidation", "pattern": "mixed"}

    async def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on trend analysis"""

        trend = analysis.get("trend", "unknown")
        confidence = analysis.get("confidence", 0.0)
        rsi = analysis.get("rsi", 50)
        market_structure = analysis.get("market_structure", {})

        # Trend-following signals
        if "bullish" in trend and confidence > 0.6:
            if rsi < 70:  # Not overbought
                action = "buy"
                reason = f"Bullish trend confirmed ({analysis.get('market_structure', {}).get('pattern', '')}), RSI healthy at {rsi:.1f}"
            else:
                action = "hold"
                reason = f"Bullish trend but RSI overbought at {rsi:.1f}, wait for pullback"
        elif "bearish" in trend and confidence > 0.6:
            if rsi > 30:  # Not oversold
                action = "sell"
                reason = f"Bearish trend confirmed ({analysis.get('market_structure', {}).get('pattern', '')}), RSI healthy at {rsi:.1f}"
            else:
                action = "hold"
                reason = f"Bearish trend but RSI oversold at {rsi:.1f}, wait for bounce"
        else:
            action = "hold"
            reason = f"No clear trend direction ({trend})"

        signal = {
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "trend": trend,
            "rsi": rsi,
            "agent_type": "trend_analysis",
        }

        logger.info(f"Trend signal generated: {action} (confidence: {confidence:.2f})")
        return signal

    async def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Trend agent doesn't execute directly"""
        logger.info("Trend agent does not execute trades directly")
        return {
            "status": "forwarded",
            "message": "Signal forwarded to execution coordinator",
            "signal": signal,
        }

    def get_trend_bias(self) -> str:
        """Get current trend bias from history"""
        if not self.trend_history:
            return "unknown"
        return self.trend_history[-1].get("trend", "unknown")
