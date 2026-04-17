"""
K-line chart generator for multi-modal AI analysis
"""

import io
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import plotly.graph_objects as go
from plotly.io import to_image
from PIL import Image


class ChartGenerator:
    """Generate K-line charts for AI analysis"""

    def __init__(self, width: int = 1200, height: int = 600):
        self.width = width
        self.height = height

    def create_candlestick_chart(
        self,
        klines: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
        indicators: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Create candlestick chart with optional indicators"""

        # Prepare data
        timestamps = [k["timestamp"] for k in klines]
        opens = [k["open"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]

        # Create figure
        fig = go.Figure()

        # Candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=timestamps,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name="Price",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
            )
        )

        # Volume trace
        colors = [
            "#26a69a" if close >= open else "#ef5350"
            for open, close in zip(opens, closes)
        ]
        fig.add_trace(
            go.Bar(
                x=timestamps,
                y=volumes,
                name="Volume",
                marker_color=colors,
                opacity=0.3,
                yaxis="y2",
            )
        )

        # Add indicators if provided
        if indicators:
            if "ma" in indicators:
                for period, values in indicators["ma"].items():
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=values,
                            name=f"MA{period}",
                            line=dict(width=1),
                        )
                    )

            if "ema" in indicators:
                for period, values in indicators["ema"].items():
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=values,
                            name=f"EMA{period}",
                            line=dict(dash="dash"),
                        )
                    )

            if "bollinger" in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=indicators["bollinger"]["upper"],
                        name="Bollinger Upper",
                        line=dict(color="gray", width=1, dash="dot"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=indicators["bollinger"]["lower"],
                        name="Bollinger Lower",
                        line=dict(color="gray", width=1, dash="dot"),
                        fill="tonexty",
                        fillcolor="rgba(128,128,128,0.1)",
                    )
                )

        # Update layout
        fig.update_layout(
            title=f"{symbol} - {timeframe}",
            yaxis_title="Price (USDT)",
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0)"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=self.width,
            height=self.height,
            margin=dict(l=50, r=50, t=50, b=50),
        )

        fig.update_yaxes(
            gridcolor="lightgray",
            zerolinecolor="lightgray",
        )

        fig.update_xaxes(
            gridcolor="lightgray",
        )

        # Convert to image
        img_bytes = to_image(fig, format="png", width=self.width, height=self.height)
        return img_bytes

    def create_multi_timeframe_chart(
        self,
        klines_dict: Dict[str, List[Dict[str, Any]]],
        symbol: str,
    ) -> bytes:
        """Create multi-timeframe comparison chart"""

        fig = go.Figure()

        colors = ["#26a69a", "#1976d2", "#7b1fa2", "#fbc02d"]

        for idx, (timeframe, klines) in enumerate(klines_dict.items()):
            if not klines:
                continue

            timestamps = [k["timestamp"] for k in klines]
            closes = [k["close"] for k in klines]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=closes,
                    name=f"{timeframe}",
                    line=dict(color=colors[idx % len(colors)], width=2),
                )
            )

        fig.update_layout(
            title=f"{symbol} - Multi-Timeframe Analysis",
            yaxis_title="Price (USDT)",
            xaxis_rangeslider_visible=False,
            showlegend=True,
            plot_bgcolor="white",
            paper_bgcolor="white",
            width=self.width,
            height=self.height,
        )

        img_bytes = to_image(fig, format="png", width=self.width, height=self.height)
        return img_bytes

    def encode_image_to_base64(self, img_bytes: bytes) -> str:
        """Encode image bytes to base64 string"""
        return base64.b64encode(img_bytes).decode("utf-8")

    def create_chart_for_ai(
        self,
        klines: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
        indicators: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create chart and prepare for AI analysis"""

        # Generate chart
        img_bytes = self.create_candlestick_chart(
            klines=klines,
            symbol=symbol,
            timeframe=timeframe,
            indicators=indicators,
        )

        # Encode to base64
        img_base64 = self.encode_image_to_base64(img_bytes)

        # Prepare latest data summary
        latest = klines[-1] if klines else {}
        previous = klines[-2] if len(klines) > 1 else {}

        summary = {
            "symbol": symbol,
            "timeframe": timeframe,
            "latest_price": latest.get("close"),
            "price_change_24h": (
                ((latest.get("close", 0) - previous.get("close", 0)) / previous.get("close", 1) * 100)
                if previous.get("close") else 0
            ),
            "high_24h": max([k["high"] for k in klines[-24:]]) if len(klines) >= 24 else latest.get("high"),
            "low_24h": min([k["low"] for k in klines[-24:]]) if len(klines) >= 24 else latest.get("low"),
            "volume_24h": sum([k["volume"] for k in klines[-24:]]) if len(klines) >= 24 else latest.get("volume"),
            "trend": "up" if latest.get("close", 0) > previous.get("close", 0) else "down",
        }

        return {
            "image_base64": img_base64,
            "image_format": "png",
            "summary": summary,
            "data_points": len(klines),
        }
