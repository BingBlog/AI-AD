# 真实用例测试指南

## 测试目标

打开小红书 https://www.xiaohongshu.com/explore 并检索10个新能源汽车的营销案例解析的帖子。

## 前置条件

1. **环境配置**
   - ✅ Python 3.12+
   - ✅ 已安装所有依赖（`pip install -r agent/requirements.txt`）
   - ✅ 已安装 Playwright 和 Chrome（Agent 使用系统 Chrome 以保持登录状态）
   - ✅ 已配置 DeepSeek API Key（在 `.env` 文件中）

2. **检查配置**
   ```bash
   cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
   cat .env | grep DEEPSEEK_API_KEY
   ```

## 测试步骤

### 步骤 1：启动 Agent 服务器

在一个终端窗口中运行：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 agent/main.py
```

或者使用便捷脚本：

```bash
./start_agent.sh
```

你应该看到类似输出：

```
============================================================
Ad Browser Agent 启动中...
============================================================
配置信息: Settings(...)
启动 WebSocket 服务器...
WebSocket 服务器已启动，监听 ws://localhost:8765
```

### 步骤 2：运行测试客户端

在另一个终端窗口中运行：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 agent/tests/test_real_case.py
```

或者使用便捷脚本：

```bash
./run_real_test.sh
```

### 步骤 3：观察执行过程

测试脚本会：
1. 连接到 Agent 服务器
2. 发送任务请求（关键词：["新能源汽车", "营销案例", "解析"]）
3. 实时显示状态更新和进度
4. 显示最终提取的营销案例结果

## 预期结果

1. **状态流程**：
   - IDLE → RECEIVED_TASK (10%)
   - RECEIVED_TASK → SEARCHING (30%)
   - SEARCHING → FILTERING (50%)
   - FILTERING → EXTRACTING (70%)
   - EXTRACTING → FINISHED (100%)

2. **提取结果**：
   - 最多 10 个营销案例
   - 每个案例包含：标题、品牌、主题、创意类型、策略、洞察、来源 URL

## 故障排查

### 问题 1：无法连接到服务器

**错误**：`ConnectionRefused`

**解决**：
- 确认 Agent 服务器已启动
- 检查端口 8765 是否被占用
- 检查防火墙设置

### 问题 2：浏览器无法打开

**错误**：`浏览器初始化失败` 或 `无法找到 Chrome`

**解决**：
- 确保系统已安装 Chrome 浏览器
- Agent 使用系统 Chrome 以保持登录状态
- 如果使用 Chromium，需要先安装：`uvx browser-use install`

### 问题 3：LLM 调用失败

**错误**：`LLM 调用失败` 或 `API Key 无效`

**解决**：
- 检查 `.env` 文件中的 `DEEPSEEK_API_KEY`
- 确认 API Key 有效且有足够余额
- 检查网络连接

### 问题 4：无法找到搜索结果

**可能原因**：
- 小红书页面结构变化
- 搜索功能需要登录
- 网络延迟或超时

**解决**：
- 查看 Agent 日志输出
- 检查浏览器是否正常打开页面
- 尝试手动访问 https://www.xiaohongshu.com/explore

## 测试数据示例

成功执行后，应该看到类似输出：

```
案例 1:
  标题: 特斯拉新能源汽车营销策略解析
  品牌: 特斯拉
  主题: 新能源汽车营销
  创意类型: 视频广告
  策略: 内容种草, KOL营销
  洞察: 抓住环保热点, 强调产品优势
  来源: https://www.xiaohongshu.com/...
```

## 注意事项

1. **执行时间**：完整任务可能需要 5-15 分钟（取决于网络和 LLM 响应速度）
2. **浏览器窗口**：Agent 会打开一个 Chrome 浏览器窗口，这是正常的。使用系统 Chrome 可以保持登录状态。
3. **弹层提取**：Agent 会在搜索结果页点击标题打开弹层，从弹层中提取案例详情（包括标题），避免导航到 404 页面。
4. **API 调用**：每个案例需要多次 LLM 调用（相关性判断、结构化提取、洞察生成），注意 API 配额
5. **网络要求**：需要稳定的网络连接访问小红书和 DeepSeek API

## 下一步

测试成功后，可以：
1. 修改关键词测试其他主题
2. 调整 `max_items` 参数
3. 查看提取结果的完整 JSON 格式
4. 集成到前端插件中
