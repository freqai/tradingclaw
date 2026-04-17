"""
Main entry point for AI Trading Agent System
"""

import asyncio
import signal
from typing import Optional
from loguru import logger
import sys

from .config.settings import settings
from .data.kline_collector import KlineCollector
from .agents.coordinator import AgentCoordinator
from .messaging.redis_client import RedisClient


class TradingAgentSystem:
    """Main system orchestrator"""

    def __init__(self):
        self.collector: Optional[KlineCollector] = None
        self.coordinator: Optional[AgentCoordinator] = None
        self.redis_client: Optional[RedisClient] = None
        self.is_running = False
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logger.remove()
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )
        logger.add(
            "logs/trading_agent.log",
            rotation="10 MB",
            retention="7 days",
            level=settings.LOG_LEVEL,
        )
        logger.info("Logging configured")

    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing AI Trading Agent System...")

        # Initialize Redis client
        self.redis_client = RedisClient(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )
        await self.redis_client.connect()
        logger.info("Redis client initialized")

        # Initialize K-line collector
        self.collector = KlineCollector()
        await self.collector.connect()
        logger.info("K-line collector initialized")

        # Initialize agent coordinator
        self.coordinator = AgentCoordinator()
        await self.coordinator.start()
        logger.info("Agent coordinator initialized")

        logger.info("System initialization completed")

    async def start(self):
        """Start the trading system"""
        if self.is_running:
            logger.warning("System is already running")
            return

        self.is_running = True
        logger.info("Starting AI Trading Agent System...")

        # Start data collection in background
        collect_task = asyncio.create_task(
            self.collector.collect_loop(
                symbols=[settings.DEFAULT_SYMBOL],
                timeframes=[settings.DEFAULT_TIMEFRAME, "4h", "1d"],
                interval_seconds=60,
            )
        )

        # Start agent processing loop
        process_task = asyncio.create_task(self._process_loop())

        # Wait for both tasks
        try:
            await asyncio.gather(collect_task, process_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")

    async def _process_loop(self):
        """Main processing loop for agent analysis"""
        logger.info("Starting agent processing loop...")

        while self.is_running:
            try:
                # Get latest market data from TDengine or Redis
                market_data = await self._get_latest_market_data()

                if market_data and market_data.get("klines"):
                    # Process through agent workflow
                    result = await self.coordinator.process_market_data(market_data)

                    # Log results
                    final_action = result.get("final_action", {})
                    logger.info(
                        f"Processing complete: {final_action.get('action', 'unknown')} "
                        f"({final_action.get('status', 'pending')})"
                    )

                    # Publish results to Redis
                    await self.redis_client.publish(
                        channel="trading:decisions",
                        message=result,
                    )

                await asyncio.sleep(300)  # Process every 5 minutes

            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(30)

    async def _get_latest_market_data(self) -> dict:
        """Get latest market data for analysis"""
        symbol = settings.DEFAULT_SYMBOL
        timeframe = settings.DEFAULT_TIMEFRAME

        # Fetch recent K-lines from TDengine
        from datetime import datetime, timedelta

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # Get 7 days of data

        klines = await self.collector.tdengine.query_klines(
            symbol=symbol,
            timeframe=timeframe,
            exchange=settings.EXCHANGE_NAME,
            start_time=start_time,
            end_time=end_time,
            limit=200,
        )

        if not klines:
            logger.warning("No K-line data available")
            return {}

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": settings.EXCHANGE_NAME,
            "klines": klines,
            "timestamp": datetime.now().isoformat(),
        }

    async def stop(self):
        """Stop the trading system"""
        if not self.is_running:
            return

        logger.info("Stopping AI Trading Agent System...")
        self.is_running = False

        # Stop coordinator
        if self.coordinator:
            await self.coordinator.stop()

        # Stop collector
        if self.collector:
            await self.collector.close()

        # Close Redis
        if self.redis_client:
            await self.redis_client.close()

        logger.info("System stopped")


async def main():
    """Main entry point"""
    system = TradingAgentSystem()

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(system.stop()),
        )

    try:
        await system.initialize()
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        raise
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
