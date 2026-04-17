"""
Risk Management Agent - Evaluates trade risk and position sizing
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from .base_agent import BaseAgent


class RiskAgent(BaseAgent):
    """Agent responsible for risk assessment and position sizing"""

    def __init__(self, agent_id: str = "risk_agent_01", max_portfolio_risk: float = 0.02):
        super().__init__(agent_id=agent_id, agent_type="risk_management")
        self.max_portfolio_risk = max_portfolio_risk  # Max 2% risk per trade
        self.risk_history: List[Dict[str, Any]] = []
        self.current_drawdown = 0.0
        self.win_rate = 0.5

    async def analyze(self, market_data: Dict[str, Any], proposed_trade: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze risk parameters for a potential trade"""

        klines = market_data.get("klines", [])
        symbol = market_data.get("symbol", "BTC/USDT")

        if not klines or len(klines) < 20:
            logger.warning("Insufficient data for risk analysis")
            return {"error": "Insufficient data", "risk_level": "unknown"}

        # Calculate volatility (ATR approximation)
        highs = [k["high"] for k in klines[-20:]]
        lows = [k["low"] for k in klines[-20:]]
        closes = [k["close"] for k in klines[-20:]]

        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)

        atr = sum(true_ranges) / len(true_ranges) if true_ranges else 0
        current_price = closes[-1]
        volatility_pct = (atr / current_price) * 100 if current_price > 0 else 0

        # Determine risk level based on volatility
        if volatility_pct > 5:
            risk_level = "high"
            risk_multiplier = 0.5  # Reduce position size
        elif volatility_pct > 2:
            risk_level = "medium"
            risk_multiplier = 0.75
        else:
            risk_level = "low"
            risk_multiplier = 1.0

        # Analyze proposed trade if provided
        trade_assessment = None
        if proposed_trade:
            trade_assessment = self._assess_proposed_trade(proposed_trade, atr, current_price)

        result = {
            "volatility_atr": atr,
            "volatility_percent": volatility_pct,
            "risk_level": risk_level,
            "risk_multiplier": risk_multiplier,
            "max_position_size": self._calculate_max_position_size(risk_multiplier),
            "current_drawdown": self.current_drawdown,
            "win_rate": self.win_rate,
            "trade_assessment": trade_assessment,
            "risk_warnings": self._generate_risk_warnings(volatility_pct, proposed_trade),
        }

        self.risk_history.append(result)
        logger.info(f"Risk analysis completed: {risk_level} volatility ({volatility_pct:.2f}%)")
        return result

    def _assess_proposed_trade(self, trade: Dict[str, Any], atr: float, current_price: float) -> Dict[str, Any]:
        """Assess a proposed trade for risk parameters"""

        action = trade.get("action", "").lower()
        entry = trade.get("entry", current_price)
        stop_loss = trade.get("stop_loss")
        take_profit = trade.get("take_profit", [])

        assessment = {
            "valid": True,
            "warnings": [],
            "recommendations": [],
        }

        # Check if stop loss is provided
        if not stop_loss:
            assessment["valid"] = False
            assessment["warnings"].append("No stop loss defined - trade must have stop loss")
        else:
            # Calculate risk distance
            if action == "buy":
                risk_distance = entry - stop_loss
                if risk_distance <= 0:
                    assessment["valid"] = False
                    assessment["warnings"].append("Stop loss must be below entry for long positions")
                elif risk_distance < atr * 0.5:
                    assessment["warnings"].append("Stop loss too tight - consider wider stop based on ATR")
                    assessment["recommendations"].append(f"Suggested minimum stop distance: ${atr * 0.5:.2f}")
            elif action == "sell":
                risk_distance = stop_loss - entry
                if risk_distance <= 0:
                    assessment["valid"] = False
                    assessment["warnings"].append("Stop loss must be above entry for short positions")
                elif risk_distance < atr * 0.5:
                    assessment["warnings"].append("Stop loss too tight - consider wider stop based on ATR")
                    assessment["recommendations"].append(f"Suggested minimum stop distance: ${atr * 0.5:.2f}")

        # Check risk/reward ratio
        if take_profit and stop_loss:
            if action == "buy":
                reward_distance = min(take_profit) - entry if isinstance(take_profit, list) else take_profit - entry
            else:
                reward_distance = entry - max(take_profit) if isinstance(take_profit, list) else entry - take_profit

            if risk_distance > 0:
                rr_ratio = reward_distance / risk_distance
                assessment["risk_reward_ratio"] = rr_ratio

                if rr_ratio < 1.0:
                    assessment["warnings"].append(f"Poor risk/reward ratio ({rr_ratio:.2f}:1) - aim for at least 1:1")
                elif rr_ratio >= 2.0:
                    assessment["recommendations"].append(f"Good risk/reward ratio ({rr_ratio:.2f}:1)")

        # Check position size
        suggested_size = trade.get("position_size", 1.0)
        max_allowed = self._calculate_max_position_size(1.0)
        if suggested_size > max_allowed:
            assessment["warnings"].append(f"Position size ({suggested_size:.1f}%) exceeds maximum allowed ({max_allowed:.1f}%)")
            assessment["recommendations"].append(f"Reduce position size to {max_allowed:.1f}% or less")

        return assessment

    def _calculate_max_position_size(self, risk_multiplier: float = 1.0) -> float:
        """Calculate maximum allowed position size based on risk"""
        base_size = 10.0  # Base 10% of portfolio
        adjusted_size = base_size * risk_multiplier

        # Reduce size if in drawdown
        if self.current_drawdown > 0.1:  # Down more than 10%
            adjusted_size *= 0.5
        elif self.current_drawdown > 0.05:  # Down more than 5%
            adjusted_size *= 0.75

        # Adjust based on win rate
        if self.win_rate < 0.4:
            adjusted_size *= 0.7

        return min(adjusted_size, 20.0)  # Cap at 20%

    def _generate_risk_warnings(self, volatility_pct: float, proposed_trade: Optional[Dict]) -> List[str]:
        """Generate risk warnings based on market conditions"""
        warnings = []

        if volatility_pct > 8:
            warnings.append("⚠️ EXTREME VOLATILITY: Consider reducing position size significantly")
        elif volatility_pct > 5:
            warnings.append("⚠️ HIGH VOLATILITY: Use wider stops and smaller positions")

        if self.current_drawdown > 0.1:
            warnings.append("⚠️ SIGNIFICANT DRAWDOWN: Trading size reduced until recovery")

        if proposed_trade:
            action = proposed_trade.get("action", "").lower()
            if action not in ["buy", "sell", "hold"]:
                warnings.append("⚠️ INVALID ACTION: Trade action must be buy, sell, or hold")

        return warnings

    async def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk-based signal (usually veto or approval)"""

        risk_level = analysis.get("risk_level", "unknown")
        trade_assessment = analysis.get("trade_assessment", {})
        warnings = analysis.get("risk_warnings", [])

        # If trade assessment is invalid, veto
        if trade_assessment and not trade_assessment.get("valid", True):
            return {
                "action": "veto",
                "reason": f"Trade rejected by risk management: {', '.join(trade_assessment.get('warnings', []))}",
                "confidence": 1.0,
                "agent_type": "risk_management",
            }

        # High risk with warnings suggests caution
        if risk_level == "high" and warnings:
            return {
                "action": "caution",
                "reason": f"High risk environment: {'; '.join(warnings)}",
                "confidence": 0.8,
                "recommended_action": "reduce_size",
                "agent_type": "risk_management",
            }

        # All clear
        return {
            "action": "approved",
            "reason": "Risk parameters acceptable",
            "confidence": 0.9,
            "max_position_size": analysis.get("max_position_size", 10.0),
            "agent_type": "risk_management",
        }

    async def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Risk agent doesn't execute trades"""
        logger.info("Risk agent does not execute trades directly")
        return {
            "status": "advisory",
            "message": "Risk assessment provided to coordinator",
            "signal": signal,
        }

    def update_performance(self, win: bool, pnl_pct: float):
        """Update performance metrics after trade completion"""
        # Simple exponential moving average for win rate
        self.win_rate = self.win_rate * 0.9 + (1.0 if win else 0.0) * 0.1

        # Update drawdown
        if pnl_pct < 0:
            self.current_drawdown = max(self.current_drawdown, abs(pnl_pct))
        else:
            # Recovery
            self.current_drawdown = max(0, self.current_drawdown - abs(pnl_pct) * 0.5)

        logger.info(f"Performance updated: win_rate={self.win_rate:.2f}, drawdown={self.current_drawdown:.2%}")
