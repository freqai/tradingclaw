"""
TDengine client for time-series data storage and retrieval
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import taos_ws


class TDengineClient:
    """Async TDengine client for K-line data storage"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6041,
        user: str = "root",
        password: str = "taosdata",
        database: str = "trading_data",
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    async def connect(self):
        """Establish connection to TDengine"""
        try:
            self.connection = taos_ws.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
            )
            await self._init_database()
            print(f"Connected to TDengine at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to TDengine: {e}")
            raise

    async def _init_database(self):
        """Initialize database and super tables"""
        if not self.connection:
            raise RuntimeError("Not connected to TDengine")

        cursor = self.connection.cursor()

        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} KEEP 3650")

        # Use database
        cursor.execute(f"USE {self.database}")

        # Create super table for K-line data
        cursor.execute("""
            CREATE STABLE IF NOT EXISTS kline_data (
                ts TIMESTAMP,
                symbol NCHAR(20),
                timeframe NCHAR(10),
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                amount DOUBLE
            ) TAGS (
                exchange NCHAR(20),
                symbol_tag NCHAR(20)
            )
        """)

        cursor.close()
        print("Database and super tables initialized")

    async def insert_kline(
        self,
        symbol: str,
        timeframe: str,
        exchange: str,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        amount: float,
    ):
        """Insert single K-line record"""
        if not self.connection:
            raise RuntimeError("Not connected to TDengine")

        cursor = self.connection.cursor()
        cursor.execute(f"USE {self.database}")

        # Create sub-table if not exists
        table_name = f"kline_{exchange}_{symbol.replace('/', '_').lower()}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            USING kline_data TAGS ('{exchange}', '{symbol}')
        """)

        # Insert data
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cursor.execute(f"""
            INSERT INTO {table_name} VALUES (
                '{ts_str}', '{symbol}', '{timeframe}',
                {open_price}, {high}, {low}, {close},
                {volume}, {amount}
            )
        """)

        cursor.close()

    async def insert_klines_batch(self, klines: List[Dict[str, Any]]):
        """Batch insert K-line records"""
        if not self.connection or not klines:
            return

        cursor = self.connection.cursor()

        for kline in klines:
            symbol = kline["symbol"]
            exchange = kline["exchange"]
            table_name = f"kline_{exchange}_{symbol.replace('/', '_').lower()}"

            # Ensure table exists
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name}
                USING kline_data TAGS ('{exchange}', '{symbol}')
            """)

        # Batch insert
        values = []
        for kline in klines:
            ts_str = kline["timestamp"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            values.append(
                f"('{ts_str}', '{kline['symbol']}', '{kline['timeframe']}', "
                f"{kline['open']}, {kline['high']}, {kline['low']}, {kline['close']}, "
                f"{kline['volume']}, {kline['amount']})"
            )

        if values:
            table_name = f"kline_{klines[0]['exchange']}_{klines[0]['symbol'].replace('/', '_').lower()}"
            cursor.execute(f"INSERT INTO {table_name} VALUES {' '.join(values)}")

        cursor.close()

    async def query_klines(
        self,
        symbol: str,
        timeframe: str,
        exchange: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query K-line data"""
        if not self.connection:
            raise RuntimeError("Not connected to TDengine")

        cursor = self.connection.cursor()
        cursor.execute(f"USE {self.database}")

        table_name = f"kline_{exchange}_{symbol.replace('/', '_').lower()}"
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        query = f"""
            SELECT ts, open, high, low, close, volume, amount
            FROM {table_name}
            WHERE ts >= '{start_str}' AND ts <= '{end_str}'
            ORDER BY ts DESC
            LIMIT {limit}
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "amount": row[6],
            })

        cursor.close()
        return result

    async def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
