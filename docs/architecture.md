# AI Trading Agent System - 架构文档

## 系统概述

本项目是一个企业级多模态 AI 交易系统，通过多 Agent 协作实现加密货币交易决策和执行。系统核心特点：

1. **多模态 AI 分析**: 使用 GPT-4o/Claude 3.5 分析 K 线图形态
2. **多 Agent 架构**: 多个专业 Agent 分工协作
3. **人在回路**: 人类保留最终决策权
4. **企业级设计**: 高可用、可扩展、安全
5. **Chat-based 协作**: 参考 Claude Code 架构，Agent 通过自然对话达成共识（无编排框架）

## 技术架构

### 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 编程语言 | Python 3.10+ | 异步编程支持 |
| 时序数据库 | TDengine 3.x | 高性能 K 线数据存储 |
| 消息中间件 | Redis 7.x | 实时消息传递、发布订阅 |
| Agent 协作 | Chat-based (自研) | 自然对话式决策，无 LangGraph 编排 |
| 多模态模型 | GPT-4o / Claude 3.5 Sonnet | K 线图像分析 |
| 文本模型 | GPT-4o / Claude Sonnet 4 | Agent 对话生成 |
| 交易所接口 | CCXT | 统一交易所 API |
| 图表生成 | Plotly | 专业 K 线图 |

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Human Decision Layer                        │
│              (Web UI / API / Chat Interface)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Message Queue (Redis)                         │
│         Pub/Sub Channels: kline:*, trading:decisions            │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  Chat-based Multi-Agent System                   │
│         (No orchestration - Natural conversation flow)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Pattern      │  │ Trend        │  │ Risk         │          │
│  │ Analyst      │  │ Strategist   │  │ Manager      │          │
│  │ (K 线形态)    │  │ (趋势策略)    │  │ (风控管理)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Sentiment    │  │ Execution    │                             │
│  │ Analyst      │  │ Specialist   │                             │
│  │ (市场情绪)    │  │ (执行专家)    │                             │
│  └──────────────┘  └──────────────┘                             │
│                                                                  │
│  All agents converse in a shared ChatRoom context               │
│  Building consensus through natural dialogue                     │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    AI Analysis Engine                            │
│         MultiModalAnalyzer (OpenAI GPT-4o / Anthropic)           │
│         Text LLM for agent conversations                         │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│  TDengine                          Exchange Connector (CCXT)     │
│  - kline_data (super table)        - Binance                   │
│  - Real-time ingestion             - OKX                       │
│  - Historical queries              - Bybit                     │
└─────────────────────────────────────────────────────────────────┘
```

## Chat-based 多 Agent 协作模式

### 核心理念

参考 **Claude Code** 的架构设计，摒弃传统的工作流编排框架（如 LangGraph），采用**自然对话式**的多 Agent 协作模式：

1. **共享聊天室 (ChatRoom)**: 所有 Agent 在同一个上下文中对话
2. **角色化 Persona**: 每个 Agent 有明确的专业领域和沟通风格
3. **多轮讨论**: 通过多轮对话逐步建立共识
4. **投票机制**: Agent 对提案进行支持/反对投票
5. **人在回路**: 人类可以随时加入对话并影响决策

### 工作流程

```
1. 创建聊天室 → 注入市场数据上下文
       ↓
2. Round 1: 各 Agent 基于专业视角发表分析
       ↓
3. Round 2: Agent 互相回应、质疑、补充
       ↓
4. Round 3: 形成交易提案 → 投票表决
       ↓
5. 达成共识 → 输出决策 / 等待人工审批
```

### Agent 角色定义

| Agent | 职责 | 沟通风格 | 核心能力 |
|-------|------|----------|----------|
| Pattern Analyst | K 线形态识别 | 分析型 | 多模态 AI 图像分析 |
| Trend Strategist | 趋势与动量 | 平衡型 | 均线、RSI、市场结构 |
| Risk Manager | 风险评估 | 谨慎型 | 仓位管理、止损计算 |
| Sentiment Analyst | 市场情绪 | 分析型 | 资金费率、持仓量 |
| Execution Specialist | 交易执行 | 务实型 | 订单类型、滑点估算 |

### 消息类型

- **discussion**: 一般讨论、分析分享
- **proposal**: 正式交易提案（含入场、止损、止盈）
- **vote**: 对提案的投票（支持/反对/弃权）
- **decision**: 最终决策

## 模块设计

### 1. 数据层 (`src/data/`)

#### TDengineClient
- **职责**: K 线数据存储和查询
- **关键方法**:
  - `connect()`: 建立连接并初始化数据库
  - `insert_kline()`: 插入单条 K 线
  - `insert_klines_batch()`: 批量插入
  - `query_klines()`: 查询历史 K 线

#### KlineCollector
- **职责**: 从交易所采集 K 线数据
- **关键方法**:
  - `fetch_klines()`: 从 CCXT 获取 OHLCV 数据
  - `collect_loop()`: 持续采集循环
  - `_publish_to_redis()`: 发布到 Redis

#### ChartGenerator
- **职责**: 生成 K 线图供 AI 分析
- **关键方法**:
  - `create_candlestick_chart()`: 创建蜡烛图
  - `create_chart_for_ai()`: 生成 AI 分析用图表

### 2. Agent 层 (`src/agents/`)

#### BaseAgent (抽象基类)
```python
class BaseAgent(ABC):
    async def analyze(market_data) -> Dict
    async def generate_signal(analysis) -> Dict
    async def execute(signal) -> Dict
```

#### PatternAgent
- **职责**: K 线形态分析
- **特色**: 使用多模态 AI 识别图表模式
- **输出**: 识别的模式列表 + 置信度 + 交易信号

#### TrendAgent
- **职责**: 趋势分析与动量策略
- **特色**: 均线系统、RSI、市场结构分析
- **输出**: 趋势方向 + 强度 + 交易信号

#### RiskAgent
- **职责**: 风险评估与仓位管理
- **特色**: ATR 波动率分析、止损计算、风险/回报比评估
- **输出**: 风险等级 + 最大仓位 + 否决权

#### ChatBasedMultiAgentSystem (核心协调器)
- **职责**: 管理 ChatRoom，促进 Agent 对话
- **特色**: 无编排框架，自然对话达成共识
- **关键方法**:
  - `create_chat_room()`: 创建讨论室
  - `start_discussion()`: 启动多轮对话
  - `add_human_input()`: 人类加入对话
  - `_check_consensus()`: 检测共识达成

### 3. AI 引擎 (`src/ai_engine/`)

#### MultiModalAnalyzer
- **支持的模型**:
  - OpenAI GPT-4o (视觉理解)
  - Anthropic Claude 3.5 Sonnet (视觉理解)
- **功能**:
  - `analyze_chart()`: 单图表分析
  - `analyze_multiple_timeframes()`: 多时间周期综合分析

### 4. 消息层 (`src/messaging/`)

#### RedisClient
- **功能**:
  - Pub/Sub 实时消息
  - 键值缓存
  - 任务队列 (List)
  - 状态存储 (Hash)

### 5. 配置 (`src/config/`)

#### Settings
- **环境配置**: `.env` 文件加载
- **类型安全**: Pydantic 验证
- **配置项**:
  - TDengine 连接
  - Redis 连接
  - 交易所 API 密钥
  - AI 模型配置
  - 交易参数

## 数据流

### K 线数据采集流程
```
Exchange (Binance) 
    ↓ (CCXT API)
KlineCollector.fetch_klines()
    ↓
TDengineClient.insert_klines_batch()
    ↓
TDengine Database
    ↓
Redis.publish("kline:*")
```

### AI 分析流程
```
Market Data Request
    ↓
TDengine.query_klines()
    ↓
ChartGenerator.create_chart_for_ai()
    ↓
MultiModalAnalyzer.analyze_chart()
    ↓
PatternAgent.generate_signal()
```

### 交易决策流程 (Chat-based)
```
Agent 讨论开始
    ↓
Round 1: 各 Agent 发表专业分析
    ↓
Round 2: 互相回应、质疑、补充
    ↓
Round 3: 形成提案 → 投票
    ↓
共识检测 (>70% 支持且≤1 反对)
    ↓
达成共识？──否──→ 继续讨论 / HOLD
    │
   是
    ↓
Human Review (可选)
    ↓
执行交易
```

## LangGraph vs Chat-based 对比

### 原 LangGraph 方案 (已弃用)
```python
workflow = StateGraph(TradingState)
workflow.add_node("pattern_analysis", run_pattern_agent)
workflow.add_node("aggregate_signals", aggregate_signals)
workflow.add_edge("pattern_analysis", "aggregate_signals")
# 固定流程，缺乏灵活性
```

### 新 Chat-based 方案
```python
system = ChatBasedMultiAgentSystem()
room = system.create_chat_room("trade_001", topic, market_data)
decision = await system.start_discussion(room_id, rounds=3)
# 自然对话，动态共识
```

**优势**:
- ✅ 更灵活的决策过程
- ✅ Agent 可以主动质疑和补充
- ✅ 更接近真实投研团队的工作方式
- ✅ 人类可以自然加入对话
- ✅ 无需维护复杂的状态图

## 部署架构

### 开发环境
```yaml
# docker-compose.yml
version: '3.8'
services:
  tdengine:
    image: tdengine/tdengine:3.0
    ports:
      - "6041:6041"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 生产环境
```
Kubernetes:
  - tdengine-cluster (3 nodes)
  - redis-cluster (6 nodes)
  - trading-app (replicas: 3)
  - nginx-ingress
  
External Services:
  - OpenAI API
  - Anthropic API
  - Exchange APIs
```

## 安全考虑

### API 密钥管理
- 使用环境变量或密钥管理服务
- 绝不硬编码在代码中
- 定期轮换

### 风控措施
- 最大仓位限制
- 止损/止盈自动执行
- 每日最大亏损限制
- 人工审批大额交易

### 审计日志
- 所有交易决策记录
- Agent 行为追踪
- 人工干预记录

## 扩展点

### 新增 Agent
1. 继承 `BaseAgent`
2. 实现 `analyze()`, `generate_signal()`, `execute()`
3. 在 `AgentCoordinator._initialize_agents()` 注册

### 新交易所
1. CCXT 已支持 100+ 交易所
2. 配置 `EXCHANGE_NAME` 即可切换

### 新 AI 模型
1. 在 `MultiModalAnalyzer` 添加 provider
2. 实现对应的分析方法

## 监控与可观测性

### 指标收集
- K 线采集延迟
- AI 分析耗时
- Agent 决策准确率
- 交易执行成功率

### 日志
- 结构化日志 (JSON)
- 分级日志 (DEBUG/INFO/WARNING/ERROR)
- 日志聚合 (ELK/Loki)

### 告警
- 数据采集失败
- AI 服务不可用
- 异常交易行为
- 系统资源超限

## 快速开始

```bash
# 1. 克隆项目
git clone <repo>
cd ai-trading-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑 .env 填入配置

# 4. 启动基础设施
docker-compose up -d tdengine redis

# 5. 运行系统
python -m src.main
```

## 下一步开发计划

- [x] 实现 ChatBasedMultiAgentSystem (无编排框架)
- [x] 实现 PatternAgent (多模态 K 线分析)
- [x] 实现 TrendAgent (趋势策略)
- [x] 实现 RiskAgent (风控管理)
- [ ] 实现 SentimentAgent (市场情绪)
- [ ] 实现 ExecutionAgent (订单执行)
- [ ] 集成真实 LLM API 进行对话生成
- [ ] Web UI 人机交互界面
- [ ] Redis pub/sub 实时聊天流
- [ ] 回测系统
- [ ] 单元测试覆盖
