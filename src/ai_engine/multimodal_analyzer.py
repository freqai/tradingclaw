"""
Multi-modal AI analyzer for K-line chart analysis
"""

import base64
from typing import Dict, Any, Optional, List
from loguru import logger

from ..config.settings import settings


class MultiModalAnalyzer:
    """Multi-modal AI analyzer for chart pattern recognition"""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AI client based on provider"""
        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = settings.OPENAI_MODEL
                logger.info("Initialized OpenAI multi-modal client")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                raise

        elif self.provider == "anthropic":
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.model = settings.ANTHROPIC_MODEL
                logger.info("Initialized Anthropic multi-modal client")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                raise

    async def analyze_chart(
        self,
        image_base64: str,
        market_summary: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze K-line chart using multi-modal AI"""

        prompt = self._build_analysis_prompt(market_summary, context)

        if self.provider == "openai":
            return await self._analyze_with_openai(image_base64, prompt)
        elif self.provider == "anthropic":
            return await self._analyze_with_anthropic(image_base64, prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _build_analysis_prompt(
        self,
        market_summary: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build analysis prompt for AI"""

        symbol = market_summary.get("symbol", "Unknown")
        timeframe = market_summary.get("timeframe", "Unknown")
        latest_price = market_summary.get("latest_price", 0)
        price_change = market_summary.get("price_change_24h", 0)
        trend = market_summary.get("trend", "unknown")

        prompt = f"""You are an expert cryptocurrency technical analyst. Analyze this K-line chart and identify trading patterns.

Market Context:
- Symbol: {symbol}
- Timeframe: {timeframe}
- Current Price: ${latest_price:.2f}
- 24h Change: {price_change:+.2f}%
- Trend: {trend}

Please analyze the chart and provide:

1. **Identified Patterns**: List all recognizable candlestick patterns and chart formations (e.g., head and shoulders, double top/bottom, triangles, flags, engulfing patterns, doji, hammer, etc.)

2. **Pattern Type**: For each pattern, specify if it's bullish, bearish, or neutral

3. **Confidence Score**: Rate your confidence in each pattern identification (0.0-1.0)

4. **Key Levels**: Identify support and resistance levels visible in the chart

5. **Volume Analysis**: Comment on volume trends and their implications

6. **Overall Assessment**: Provide a summary of the market structure and potential future movements

Respond in JSON format with the following structure:
{{
    "identified_patterns": [
        {{"name": "pattern name", "type": "bullish/bearish/neutral", "confidence": 0.0-1.0, "description": "brief description"}}
    ],
    "support_levels": [price1, price2, ...],
    "resistance_levels": [price1, price2, ...],
    "volume_analysis": "your analysis",
    "overall_assessment": "summary",
    "confidence_score": 0.0-1.0,
    "description": "comprehensive analysis description"
}}

Be precise and objective. Only identify patterns you can clearly see in the chart."""

        return prompt

    async def _analyze_with_openai(
        self,
        image_base64: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """Analyze using OpenAI GPT-4o"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
            )

            content = response.choices[0].message.content
            result = self._parse_ai_response(content)
            logger.info(f"OpenAI analysis completed: {len(result.get('identified_patterns', []))} patterns found")
            return result

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return {"error": str(e), "identified_patterns": [], "confidence_score": 0.0}

    async def _analyze_with_anthropic(
        self,
        image_base64: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """Analyze using Anthropic Claude 3.5"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            content = response.content[0].text
            result = self._parse_ai_response(content)
            logger.info(f"Anthropic analysis completed: {len(result.get('identified_patterns', []))} patterns found")
            return result

        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            return {"error": str(e), "identified_patterns": [], "confidence_score": 0.0}

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        import json
        import re

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # If no JSON found, create structured response from text
                return {
                    "identified_patterns": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "volume_analysis": content,
                    "overall_assessment": content,
                    "confidence_score": 0.5,
                    "description": content,
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return {
                "identified_patterns": [],
                "support_levels": [],
                "resistance_levels": [],
                "volume_analysis": content,
                "overall_assessment": content,
                "confidence_score": 0.5,
                "description": content,
            }

    async def analyze_multiple_timeframes(
        self,
        charts: Dict[str, str],  # timeframe -> image_base64
        market_summaries: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze multiple timeframe charts for comprehensive view"""

        results = {}
        for timeframe, image_base64 in charts.items():
            summary = market_summaries.get(timeframe, {})
            results[timeframe] = await self.analyze_chart(
                image_base64=image_base64,
                market_summary=summary,
                context={"analysis_type": "multi_timeframe"},
            )

        # Synthesize multi-timeframe analysis
        synthesis = self._synthesize_multi_timeframe(results)
        return {
            "timeframe_analyses": results,
            "synthesis": synthesis,
        }

    def _synthesize_multi_timeframe(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize analysis across multiple timeframes"""

        all_patterns = []
        confidence_scores = []

        for timeframe, analysis in results.items():
            patterns = analysis.get("identified_patterns", [])
            for pattern in patterns:
                pattern["timeframe"] = timeframe
                all_patterns.append(pattern)
            confidence_scores.append(analysis.get("confidence_score", 0.5))

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Check for pattern alignment across timeframes
        bullish_count = sum(1 for p in all_patterns if p.get("type") == "bullish")
        bearish_count = sum(1 for p in all_patterns if p.get("type") == "bearish")

        if bullish_count > bearish_count * 1.5:
            overall_bias = "bullish"
        elif bearish_count > bullish_count * 1.5:
            overall_bias = "bearish"
        else:
            overall_bias = "neutral"

        return {
            "total_patterns": len(all_patterns),
            "average_confidence": avg_confidence,
            "overall_bias": overall_bias,
            "bullish_patterns": bullish_count,
            "bearish_patterns": bearish_count,
            "recommendation": "Strong buy" if overall_bias == "bullish" and avg_confidence > 0.7
            else "Buy" if overall_bias == "bullish"
            else "Strong sell" if overall_bias == "bearish" and avg_confidence > 0.7
            else "Sell" if overall_bias == "bearish"
            else "Hold",
        }
