# Agent 使用指南

## 快速开始

### 1. 启动 Agent 服务器

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 agent/main.py
```

服务器将在 `ws://localhost:8765` 上监听连接。

### 2. 使用 WebSocket 客户端连接

#### Python 客户端示例

```python
import asyncio
import json
import websockets

async def test_agent():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 发送启动任务消息
        message = {
            "type": "START_TASK",
            "task_id": "test-001",
            "payload": {
                "platform": "xiaohongshu",
                "keywords": ["春节营销", "汽车"],
                "max_items": 5
            }
        }
        await websocket.send(json.dumps(message))
        print("已发送任务请求")

        # 接收消息
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "STATUS_UPDATE":
                print(f"状态更新: {data['state']}, 进度: {data['progress']}%")
            elif msg_type == "TASK_RESULT":
                print(f"任务完成！结果数: {len(data.get('results', []))}")
                for i, result in enumerate(data.get('results', []), 1):
                    print(f"  案例 {i}: {result.get('brand')} - {result.get('theme')}")
                break
            elif msg_type == "ERROR":
                print(f"错误: {data['error']}")
                break

asyncio.run(test_agent())
```

#### JavaScript 客户端示例

```javascript
const ws = new WebSocket("ws://localhost:8765");

ws.onopen = () => {
  console.log("已连接到 Agent");

  // 发送启动任务消息
  const message = {
    type: "START_TASK",
    task_id: "test-001",
    payload: {
      platform: "xiaohongshu",
      keywords: ["春节营销"],
      max_items: 5,
    },
  };
  ws.send(JSON.stringify(message));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "STATUS_UPDATE") {
    console.log(`状态: ${data.state}, 进度: ${data.progress}%`);
  } else if (data.type === "TASK_RESULT") {
    console.log(`任务完成！结果数: ${data.results.length}`);
    data.results.forEach((result, i) => {
      console.log(`  案例 ${i + 1}: ${result.brand} - ${result.theme}`);
    });
    ws.close();
  } else if (data.type === "ERROR") {
    console.error(`错误: ${data.error}`);
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error("WebSocket 错误:", error);
};
```

## 消息协议

### 插件 → Agent：启动任务

```json
{
  "type": "START_TASK",
  "task_id": "uuid",
  "payload": {
    "platform": "xiaohongshu",
    "keywords": ["关键词1", "关键词2"],
    "max_items": 10
  }
}
```

### Agent → 插件：状态更新

```json
{
  "type": "STATUS_UPDATE",
  "state": "SEARCHING",
  "progress": 30,
  "message": "任务状态: SEARCHING"
}
```

### Agent → 插件：任务结果

```json
{
  "type": "TASK_RESULT",
  "results": [
    {
      "platform": "xiaohongshu",
      "brand": "品牌名",
      "theme": "营销主题",
      "creative_type": "创意类型",
      "strategy": ["策略1", "策略2"],
      "insights": ["洞察1", "洞察2"],
      "source_url": "https://..."
    }
  ]
}
```

### Agent → 插件：错误消息

```json
{
  "type": "ERROR",
  "error": "错误描述",
  "task_id": "uuid"
}
```

## 状态说明

| 状态          | 说明       | 进度 |
| ------------- | ---------- | ---- |
| IDLE          | 空闲       | 0%   |
| RECEIVED_TASK | 已接收任务 | 10%  |
| SEARCHING     | 搜索中     | 30%  |
| FILTERING     | 过滤中     | 50%  |
| EXTRACTING    | 提取中     | 70%  |
| FINISHED      | 已完成     | 100% |
| ABORTED       | 已中止     | 0%   |

## 停止服务器

按 `Ctrl+C` 发送 SIGINT 信号，服务器将优雅关闭：

- 取消所有运行中的任务
- 关闭所有客户端连接
- 清理资源

## 故障排查

### 问题：无法连接到服务器

**检查**：

1. Agent 是否已启动：`python3 agent/main.py`
2. 端口是否正确：默认 `8765`
3. 防火墙是否阻止连接

### 问题：任务执行失败

**检查**：

1. DeepSeek API Key 是否正确配置
2. Browser-Use 和 Chromium 是否已安装
3. 网络连接是否正常
4. 查看 Agent 日志输出

### 问题：消息解析失败

**检查**：

1. 消息格式是否符合协议规范
2. JSON 格式是否正确
3. 必需字段是否都存在
