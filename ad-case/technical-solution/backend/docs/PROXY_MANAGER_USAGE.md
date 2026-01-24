# 代理管理器使用说明

## ⚠️ 重要提示

**启动服务时，必须使用统一启动脚本**：

- macOS/Linux: `technical-solution/start.sh`
- Windows: `technical-solution/start.bat`

**禁止直接运行 `python run.py`**，必须通过启动脚本启动服务。

## 功能概述

代理管理器支持通过 Clash Verge API 自动切换代理节点，避免因请求过多而被封禁。

### 主要特性

1. **定时切换节点**

   - 基于请求次数：每 N 个请求后自动切换
   - 基于时间间隔：每 M 分钟后自动切换
   - 混合模式：同时考虑请求次数和时间

2. **错误自动切换**

   - 检测到代理错误时自动切换节点
   - 记录失败节点，暂时跳过

3. **智能节点选择**
   - 自动排除 DIRECT、REJECT 等系统节点
   - 随机选择可用节点
   - 避免重复使用失败节点

## 配置方法

### 1. 在 `.env` 文件中添加配置

```env
# Clash Verge API 配置
CLASH_API_URL=http://127.0.0.1:9097
CLASH_SECRET=123456
CLASH_PROXY_GROUP=GLOBAL

# 切换策略配置
CLASH_SWITCH_MODE=hybrid  # count/time/hybrid
CLASH_SWITCH_INTERVAL=50  # 每 50 个请求切换一次
CLASH_SWITCH_INTERVAL_MINUTES=10  # 每 10 分钟切换一次
CLASH_AUTO_SWITCH_ON_ERROR=true  # 错误时自动切换
```

### 2. 配置说明

#### CLASH_API_URL

- Clash Verge 的 API 地址
- 在 Clash Verge 设置中查看 "External Controller" 的端口
- 格式：`http://127.0.0.1:端口号`

#### CLASH_SECRET

- Clash API 的认证密钥
- 在 Clash Verge 设置中查看 "Secret" 字段
- 如果未设置，可以留空（但通常需要）

#### CLASH_PROXY_GROUP

- 要使用的代理组名称
- 通常是 `GLOBAL` 或 `Proxy`
- 可以在 Clash Verge 中查看可用的代理组

#### CLASH_SWITCH_MODE

- `count`: 仅基于请求次数切换
- `time`: 仅基于时间间隔切换
- `hybrid`: 混合模式（推荐），任一条件满足即切换

#### CLASH_SWITCH_INTERVAL

- 请求次数阈值
- 当请求次数达到此值时切换节点
- 适用于 `count` 和 `hybrid` 模式

#### CLASH_SWITCH_INTERVAL_MINUTES

- 时间间隔（分钟）
- 当时间间隔达到此值时切换节点
- 适用于 `time` 和 `hybrid` 模式

#### CLASH_AUTO_SWITCH_ON_ERROR

- 是否在请求失败时自动切换节点
- `true`: 启用（推荐）
- `false`: 禁用

## 使用示例

### 测试代理管理器

```bash
cd backend
python services/spider/proxy_manager.py
```

### 测试 Clash API 连接

```bash
cd backend
python tests/test_clash_api.py http://127.0.0.1:9097 123456
```

## 工作原理

1. **初始化**

   - 爬取任务启动时，自动检查是否配置了 Clash API
   - 如果配置了，初始化代理管理器
   - 加载可用节点列表

2. **请求记录**

   - 每次 HTTP 请求后，记录请求计数
   - 检查是否需要切换节点（基于次数或时间）

3. **自动切换**

   - 满足切换条件时，自动调用 Clash API 切换节点
   - 记录切换时间和当前节点

4. **错误处理**
   - 检测到代理相关错误时，立即切换节点
   - 将失败节点加入黑名单，暂时跳过

## 注意事项

1. **Clash Verge 必须运行**

   - 确保 Clash Verge 正在运行
   - 确保 API 端口可访问

2. **代理组配置**

   - 确保指定的代理组存在
   - 确保代理组中有足够的可用节点

3. **切换频率**

   - 不要设置过小的切换间隔，避免频繁切换
   - 建议：每 50 个请求或每 10 分钟切换一次

4. **节点选择**
   - 系统会自动排除 DIRECT、REJECT、Auto 等节点
   - 如果需要使用这些节点，需要修改代码

## 故障排查

### 问题：无法连接到 Clash API

**解决方案：**

1. 检查 Clash Verge 是否正在运行
2. 检查 API 端口是否正确
3. 检查是否设置了 Secret
4. 运行测试脚本：`python tests/test_clash_api.py http://127.0.0.1:9097 123456`

### 问题：切换节点失败

**解决方案：**

1. 检查代理组名称是否正确
2. 检查代理组中是否有可用节点
3. 查看日志中的错误信息

### 问题：仍然被封禁

**解决方案：**

1. 减小切换间隔（增加切换频率）
2. 增加请求延迟时间
3. 检查是否有足够的可用节点

## 日志示例

```
2026-01-24 05:03:28,871 - INFO - 代理管理器初始化完成
2026-01-24 05:03:28,871 - INFO -   API 地址: http://127.0.0.1:9097
2026-01-24 05:03:28,871 - INFO -   代理组: GLOBAL
2026-01-24 05:03:28,871 - INFO -   可用节点数: 49
2026-01-24 05:03:28,871 - INFO -   当前节点: Auto
2026-01-24 05:03:28,892 - INFO - ✓ 成功切换到节点: 荷兰-NL-3-流量倍率:1.0
```

## 相关文件

- `services/spider/proxy_manager.py` - 代理管理器实现
- `services/spider/api_client.py` - API 客户端（已集成）
- `services/spider/detail_parser.py` - 详情页解析器（已集成）
- `services/spider/csrf_token_manager.py` - Token 管理器（已集成）
- `services/pipeline/crawl_stage.py` - 爬取阶段（已集成）
- `app/config.py` - 配置文件
- `tests/test_clash_api.py` - API 测试脚本
