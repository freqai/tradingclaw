# Chat-based Multi-Agent Trading System

## 概述

这是一个参考 **Claude Code** 架构设计的多 Agent 交易系统，摒弃了传统的工作流编排框架（如 LangGraph），采用**自然对话式**的协作模式。多个专业 Agent 在共享聊天室中通过对话、辩论、投票来达成交易决策共识。

## 核心特性

- 🗣️ **自然对话**: Agent 像真实投研团队一样交流讨论
- 🎭 **角色化 Persona**: 每个 Agent 有明确的专业领域和沟通风格
- 🗳️ **投票共识**: 通过支持/反对投票达成决策
- 👤 **人在回路**: 人类可以随时加入对话影响决策
- 🚫 **无编排框架**: 没有固定的状态图，流程更灵活

## Agent 角色

| Agent | 职责 | 沟通风格 |
|-------|------|----------|
| Pattern Analyst | K 线形态识别 | 分析型 |
| Trend Strategist | 趋势与动量 | 平衡型 |
| Risk Manager | 风险评估 | 谨慎型 |
| Sentiment Analyst | 市场情绪 | 分析型 |
| Execution Specialist | 交易执行 | 务实型 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行演示

```bash
python -m src.demo_chat_agents
```

### 3. 代码示例

#### 基础用法

```python
from src.agents.chat_based_coordinator import ChatBasedMultiAgentSystem

# 初始化系统
system = ChatBasedMultiAgentSystem()

# 准备市场数据
market_data = {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "latest_price": 44150.0,
    "price_change_24h": 5.12,
    "klines": [...],  # K 线数据
}

# 创建聊天室
room = system.create_chat_room(
    room_id="trade_001",
    topic="Should we enter a LONG position on BTC/USDT?",
    market_data=market_data
)

# 启动多轮讨论
decision = await system.start_discussion(room_id, rounds=3)

# 查看结果
print(f"Action: {decision['action']}")
print(f"Confidence: {decision['confidence']:.0%}")
print(f"Conversation: {decision['full_conversation']}")
```

#### 人类加入对话

```python
# 人类提出问题或关切
human_input = "我担心明天的美联储 announcement，是否应该等待？"

# 将人类输入加入对话
updated_decision = await system.add_human_input(room_id, human_input)

# Agent 会回应人类的关切并重新评估决策
```

#### 查看聊天记录

```python
chat_history = system.get_chat_history(room_id)

for msg in chat_history:
    emoji = "👤" if msg["sender_type"] == "human" else "🤖"
    print(f"{emoji} [{msg['sender']}]: {msg['content']}")
```

## 架构设计

### ChatRoom (聊天室)

所有 Agent 在共享的 ChatRoom 中对话，维护完整的对话历史：

```python
class ChatRoom:
    messages: List[ChatMessage]      # 对话历史
    participants: List[str]          # 参与的 Agent
    human_present: bool              # 人类是否在场
    decision_reached: bool           # 是否已达成决策
    final_decision: Dict             # 最终决策
```

### ChatMessage (消息类型)

- `discussion`: 一般讨论、分析分享
- `proposal`: 正式交易提案（含入场、止损、止盈）
- `vote`: 对提案的投票（支持/反对/弃权）
- `decision`: 最终决策

### 共识机制

```python
def _check_consensus(room: ChatRoom) -> bool:
    # 需要 60% 以上的 Agent 参与投票
    # 支持率 > 70% 且反对票 ≤ 1 则达成共识
    support_ratio = support_count / total_voters
    return support_ratio > 0.7 and oppose_count <= 1
```

## 工作流程

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

## 对话示例

```
🤖 [Pattern Analyst]: 经过分析 K 线图，我识别出以下形态：
   - 上升三角形突破
   - 连续三根阳线
   置信度：75%，初步判断为看涨信号。

🤖 [Trend Strategist]: 同意 Pattern Analyst 的观点。从趋势角度看：
   - 价格位于 MA20/MA50/MA200 之上
   - RSI = 58，健康水平
   - 市场结构：HH+HL（上升趋势）
   建议：可以考虑做多。

🤖 [Risk Manager]: 我检查了风险参数：
   - 当前波动率：中等 (ATR = 2.3%)
   - 建议仓位：不超过 10%
   - 必须设置止损在三角形下沿
   如果满足以上条件，我支持这笔交易。

🤖 [Execution Specialist]: 从执行角度建议：
   - 使用限价单在 $44,000 附近入场
   - 预计滑点：0.1%
   - 最佳执行时间：下一个小时 K 线开盘
```

## 技术栈

- **Python 3.10+**: 异步编程
- **TDengine**: 时序数据存储
- **Redis**: 消息中间件
- **OpenAI GPT-4o / Anthropic Claude**: LLM 支持
- **Pydantic**: 数据验证

## 集成真实 LLM

要启用真实的 LLM 对话生成，需要配置 API 密钥：

```bash
# .env 文件
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

然后在代码中选择 provider：

```python
from src.ai_engine.multimodal_analyzer import MultiModalAnalyzer

# 使用 OpenAI
analyzer = MultiModalAnalyzer(provider="openai")

# 或使用 Anthropic
analyzer = MultiModalAnalyzer(provider="anthropic")
```

## 优势对比

### vs LangGraph 编排

| 特性 | LangGraph | Chat-based |
|------|-----------|------------|
| 灵活性 | 固定流程 | 动态对话 |
| Agent 互动 | 单向传递 | 多向辩论 |
| 人类参与 | 固定节点 | 随时加入 |
| 可解释性 | 状态转换 | 完整对话记录 |
| 维护成本 | 需维护状态图 | 简单直观 |

## 下一步

1. 集成真实 LLM API 进行对话生成
2. 实现 Redis pub/sub 实时聊天流
3. 构建 Web UI 供人类参与对话
4. 添加回测功能验证策略效果

## License

MIT
