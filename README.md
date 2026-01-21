# RoleMirror: 游戏 NPC 对话自动化评测系统

RoleMirror 是一个基于 LLM（大语言模型）的自动化评测框架，旨在评估游戏 NPC（非玩家角色）的对话质量、角色一致性和互动体验。

通过使用两个独立的 LLM Agent —— 一个扮演 **NPC**，另一个扮演 **模拟玩家（Player Simulator）** —— 进行多轮对话，并由第三个 **Grader Agent** 对对话记录进行评分和证据提取。

## 核心特性

*   **自动化双 Agent 模拟**：
    *   **Mock NPC**：基于设定的人设（Persona）进行角色扮演，受 Token 限制以模拟真实游戏对话的简洁性。
    *   **Player Simulator**：基于特定的测试目标（如“激怒NPC”、“尝试砍价”）驱动对话发展。
*   **Model-Graded Evaluation（模型级评测）**：
    *   利用 LLM 作为裁判，对对话进行多维度打分（1-5分）。
    *   自动提取对话中的“证据”片段来支持评分理由。
    *   支持自定义评测标准（如：角色一致性、互动流畅度）。
*   **完全中文化**：
    *   支持中文 NPC 人设和对话。
    *   评测报告（理由、证据）全中文输出。
*   **配置灵活**：
    *   NPC 定义与测试场景分离，支持复用。
    *   支持通过 CLI 运行特定场景。

## 项目结构

```
RoleMirror/
├── src/
│   ├── agents/
│   │   ├── base.py           # Agent 基类
│   │   ├── npc.py            # NPC Agent 实现 (MockNPC)
│   │   └── simulator.py      # 玩家模拟器 Agent 实现 (PlayerSimulator)
│   ├── core/
│   │   ├── runner.py         # 评测运行器 (负责对话循环和调用打分)
│   │   ├── grader.py         # 打分引擎 (LLM-as-a-Judge)
│   │   └── log_evaluator.py  # 离线日志评测器
│   ├── data/
│   │   ├── npcs.json         # NPC 数据库 (定义人设)
│   │   ├── scenarios.json    # 测试场景库 (定义测试目标)
│   │   └── grader_config.json # 评测标准与裁判模型配置
│   └── llm_client.py         # LLM 客户端封装 (支持 OpenAI/DashScope)
├── reports/                  # 自动生成的评测报告目录
├── main.py                   # 在线评测入口
├── evaluate_logs.py          # 离线日志评测入口
├── requirements.txt          # 依赖列表
└── .env.example              # 环境变量配置模板
```

## 快速开始

### 1. 环境准备

确保安装了 Python 3.10+。

```bash
# 克隆仓库（略）

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，并填入你的 API Key（本项目默认使用阿里云 DashScope 的 `qwen-flash` 模型，兼容 OpenAI SDK）。

```ini
# .env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
LLM_MODEL=qwen-flash
```

### 3. 运行评测

#### 在线交互评测
直接运行 `main.py` 即可启动所有定义的测试场景（默认会自动生成 NPC x 场景 的全组合矩阵测试）：

```bash
# 默认串行运行
python main.py

# 指定并发数（例如 5 个线程并行）
python main.py --concurrency 5
```

程序运行结束后，会在 `reports/` 目录下生成一个包含时间戳的 JSON 报告文件。

#### 离线日志评测
如果你已经有现成的对话日志（JSON格式），可以使用 `evaluate_logs.py` 进行纯评测：

```bash
python evaluate_logs.py path/to/your/logs.json --output reports/ --concurrency 3
```

## 评测指标

报告中包含以下核心指标：

*   **维度评分 (1-5)**：由裁判模型根据配置的标准打分。
*   **性能指标**：
    *   `avg_latency_seconds`: NPC 平均响应时间。
    *   `avg_tokens_per_turn`: NPC 平均回复 Token 数。
    *   `total_tokens`: 总 Token 消耗。

## 如何自定义

### 添加新的 NPC

修改 `src/data/npcs.json`：

```json
{
  "id": "npc_new",
  "name": "新角色",
  "persona": "这里写详细的角色人设..."
}
```

### 配置评测标准与模型

修改 `src/data/grader_config.json` 可以自定义评测维度和使用的裁判模型：

```json
{
  "default_model": "qwen-plus", // 默认裁判模型
  "criteria": {
    "role_consistency": {
      "description": "角色一致性...",
      "model": "qwen-max",      // 针对该维度的特定模型（覆盖默认模型）
      "enabled": true
    }
  }
}
```

### 添加新的测试场景

修改 `src/data/scenarios.json`。注意：场景定义不再强制绑定特定 NPC，你可以让任意 NPC 跑任意场景。

```json
{
  "id": "scenario_bargain",
  "name": "砍价测试",
  "simulator_config": {
    "name": "砍价高手",
    "goal": "试图用最低价格买下商品",
    "context": "玩家是一个精明的商人..."
  }
}
```

如果想限制某个 NPC 只跑特定场景，可以在 `src/data/npcs.json` 中配置 `test_scenarios` 字段：

```json
{
  "id": "npc_blacksmith",
  "name": "铁匠",
  "persona": "...",
  "test_scenarios": ["scenario_bargain"] // 可选：指定白名单
}
```

## 评测报告示例

```json
{
  "npc_name": "格罗姆",
  "scenario_name": "砍价测试",
  "metrics": {
    "avg_latency_seconds": 1.2,
    "avg_tokens_per_turn": 45.5,
    "total_tokens": 520
  },
  "evaluations": {
    "role_consistency": {
      "score": 5,
      "reasoning": "NPC面对玩家的无理砍价表现出了极大愤怒，符合暴躁铁匠的人设。",
      "evidence": "NPC: '三折？你这口气比炉渣还贱！'"
    }
  }
}
```
