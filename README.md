# Enterprise AI Trading Agent System

企业级多模态 AI 交易代理系统，基于 K 线图分析的多 Agent 协作交易平台。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Human Decision Layer                        │
│                    (用户决策与交互界面)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Coordination                      │
│              (LangGraph 多 Agent 协调与任务分发)                   │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│ Pattern     │ Trend       │ Mean        │ Risk        │ Execution│
│ Agent       │ Agent       │ Reversion   │ Agent       │ Agent    │
│ (形态分析)   │ (趋势策略)   │ (均值回归)   │ (风控)       │ (执行)    │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    AI Analysis Engine                            │
│         (多模态大模型：GPT-4o/Claude 3.5 for K-line 图像分析)      │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Message Queue (Redis)                         │
│              (实时消息传递、任务队列、发布订阅)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
├─────────────────────┬───────────────────────────────────────────┤
│ TDengine            │ Exchange API (CCXT)                       │
│ (时序数据存储)        │ (币安/OKX/Bybit等交易所接口)                │
└─────────────────────┴───────────────────────────────────────────┘
```

## 技术栈

- **编程语言**: Python 3.10+
- **数据库**: TDengine 3.x (时序数据存储)
- **消息中间件**: Redis 7.x (消息队列、缓存、发布订阅)
- **Agent 框架**: LangGraph / AutoGen
- **多模态模型**: GPT-4o / Claude 3.5 Sonnet
- **交易所接口**: CCXT
- **图表生成**: Plotly / Matplotlib
- **异步框架**: asyncio / aiohttp

## 核心模块

### 1. 数据层 (data/)
- `kline_collector.py`: K 线数据采集
- `tdengine_client.py`: TDengine 数据存取
- `chart_generator.py`: K 线图生成

### 2. Agent 层 (agents/)
- `base_agent.py`: Agent 基类
- `pattern_agent.py`: K 线形态分析 Agent
- `trend_agent.py`: 趋势策略 Agent
- `mean_reversion_agent.py`: 均值回归 Agent
- `risk_agent.py`: 风控 Agent
- `execution_agent.py`: 交易执行 Agent
- `coordinator.py`: 多 Agent 协调器

### 3. AI 引擎 (ai_engine/)
- `multimodal_analyzer.py`: 多模态分析引擎
- `prompt_templates.py`: 提示词模板

### 4. 交易所接口 (exchanges/)
- `exchange_connector.py`: 交易所连接器
- `order_manager.py`: 订单管理

### 5. 消息队列 (messaging/)
- `redis_client.py`: Redis 客户端
- `message_bus.py`: 消息总线

### 6. 人机交互 (human_in_loop/)
- `decision_interface.py`: 决策接口
- `chat_handler.py`: 对话处理

### 7. 配置与工具 (config/, utils/)
- `settings.py`: 系统配置
- `logger.py`: 日志系统
- `security.py`: 安全管理

## 快速开始

### 环境要求
- Python 3.10+
- TDengine 3.x
- Redis 7.x

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库、Redis、API 密钥等
```

### 启动系统
```bash
# 启动数据采集服务
python -m src.data.kline_collector

# 启动 Agent 系统
python -m src.main

# 启动人机交互界面
python -m src.human_in_loop.interface
```

## 安全警告

⚠️ **交易风险**: 加密货币交易存在高风险，本系统仅供学习和研究使用
⚠️ **密钥管理**: 切勿将 API 密钥提交到版本控制系统
⚠️ **生产部署**: 生产环境需要额外的安全措施和风控机制

## 许可证

MIT License
