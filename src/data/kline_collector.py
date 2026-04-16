"""
K-line data collector from cryptocurrency exchanges
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
from loguru import logger

from ..config.settings import settings
from .tdengine_client import TDengineClient


class KlineCollector:
    """Collect K-line data from exchanges and store in TDengine"""

    def __init__(self):
        self.exchange = None
        self.tdengine = TDengineClient(
            host=settings.TDENGINE_HOST,
            port=settings.TDENGINE_PORT,
            user=settings.TDENGINE_USER,
            password=settings.TDENGINE_PASSWORD,
            database=settings.TDENGINE_DATABASE,
        )
        self.is_running = False

    async def connect(self):
        """Connect to exchange and TDengine"""
        # Initialize exchange
        exchange_class = getattr(ccxt, settings.EXCHANGE_NAME)
        self.exchange = exchange_class({
            "apiKey": settings.API_KEY,
            "secret": settings.API_SECRET,
            "sandbox": settings.TESTNET,
            "enableRateLimit": True,
        })

        # Connect to TDengine
        await self.tdengine.connect()
        logger.info(f"Connected to {settings.EXCHANGE_NAME} exchange")

    async def fetch_klines(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch K-line data from exchange"""
        if not self.exchange:
            raise RuntimeError("Not connected to exchange")

        try:
            # Convert timeframe to exchange format
            tf_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "6h": "6h", "12h": "12h",
                "1d": "1d", "1w": "1w", "1M": "1M"
            }
            exchange_tf = tf_map.get(timeframe, timeframe)

            # Fetch OHLCV data
            if since:
                timestamp = int(since.timestamp() * 1000)
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol, exchange_tf, since=timestamp, limit=limit
                )
            else:
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol, exchange_tf, limit=limit
                )

            # Convert to standardized format
            klines = []
            for candle in ohlcv:
                klines.append({
                    "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "exchange": settings.EXCHANGE_NAME,
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                    "amount": candle[6] if len(candle) > 6 else candle[5],
                })

            logger.info(f"Fetched {len(klines)} K-lines for {symbol}")
            return klines

        except Exception as e:
            logger.error(f"Failed to fetch K-lines: {e}")
            raise

    async def store_klines(self, klines: List[Dict[str, Any]]):
        """Store K-line data in TDengine"""
        await self.tdengine.insert_klines_batch(klines)
        logger.info(f"Stored {len(klines)} K-lines in TDengine")

    async def collect_loop(
        self,
        symbols: List[str],
        timeframes: List[str],
        interval_seconds: int = 60,
    ):
        """Continuous collection loop"""
        self.is_running = True
        logger.info(f"Starting K-line collection for {symbols}")

        while self.is_running:
            try:
                for symbol in symbols:
                    for timeframe in timeframes:
                        # Fetch latest K-lines
                        klines = await self.fetch_klines(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=50,
                        )

                        # Store in TDengine
                        await self.store_klines(klines)

                        # Publish to Redis for real-time processing
                        await self._publish_to_redis(klines[-1])

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Collection error: {e}")
                await asyncio.sleep(5)

    async def _publish_to_redis(self, kline: Dict[str, Any]):
        """Publish latest K-line to Redis"""
        import redis.asyncio as redis

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )

        channel = f"kline:{kline['exchange']}:{kline['symbol']}:{kline['timeframe']}"
        message = {
            "timestamp": kline["timestamp"].isoformat(),
            "symbol": kline["symbol"],
            "timeframe": kline["timeframe"],
            "exchange": kline["exchange"],
            "open": kline["open"],
            "high": kline["high"],
            "low": kline["low"],
            "close": kline["close"],
            "volume": kline["volume"],
        }

        await r.publish(channel, str(message))
        await r.close()

    async def close(self):
        """Close connections"""
        self.is_running = False
        if self.exchange:
            await self.exchange.close()
        await self.tdengine.close()
        logger.info("K-line collector closed")


async def main():
    """Main entry point"""
    collector = KlineCollector()

    try:
        await collector.connect()

        # Start collection
        await collector.collect_loop(
            symbols=[settings.DEFAULT_SYMBOL],
            timeframes=[settings.DEFAULT_TIMEFRAME],
            interval_seconds=60,
        )

    except KeyboardInterrupt:
        logger.info("Stopping collector...")
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
