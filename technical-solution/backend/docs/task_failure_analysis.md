# 任务失败原因分析报告

## 任务信息
- **任务ID**: `task_49544538ae184203`
- **失败原因**: 未爬取到任何数据
- **失败时间**: 2026-01-24T02:24:37

## 失败判断逻辑

根据代码 `crawl_task_executor.py:269-279`，任务被标记为失败的条件是：

```python
total_processed = total_crawled + total_saved + total_failed
if total_processed == 0:
    # 标记为失败
```

这意味着：
- `total_crawled = 0` （没有爬取任何案例）
- `total_saved = 0` （没有保存任何案例）
- `total_failed = 0` （没有失败的案例）

## 数据文件检查结果

### 1. 断点续传文件 (`crawl_resume.json`)
```json
{
  "crawled_ids": [],
  "total_count": 0,
  "last_updated": "2026-01-24T02:24:37.198651"
}
```

**发现**：
- `crawled_ids` 为空数组，说明没有爬取到任何案例
- `total_count` 为 0，说明列表页返回的数据为空

### 2. 批次文件
- **未找到任何 `cases_batch_*.json` 文件**
- 说明没有保存任何批次数据

## 可能的原因分析

### 原因1: 列表页返回空数据（最可能）

**触发条件**：
- API 请求成功，但返回的 `items` 数组为空
- 代码位置：`crawl_stage.py:410-417` 或 `485-491`

**代码逻辑**：
```python
items = data['data'].get('items', [])
if not items:
    logger.info(f"第{page}页没有更多数据，停止获取")
    break
```

**可能的情况**：
1. **起始页码超出范围**：如果 `start_page` 设置过大，可能已经超出 API 的数据范围
2. **搜索条件无结果**：如果设置了 `search_value` 或 `case_type`，可能没有匹配的数据
3. **API 数据已更新**：目标页码的数据已被删除或移动

### 原因2: API 请求失败

**触发条件**：
- 网络连接问题
- API 认证失败（CSRF Token 失效）
- API 服务器错误
- 请求超时

**代码位置**：`crawl_stage.py:450-467`

**错误类型**：
- `network_error`: 网络连接问题
- `parse_error`: JSON 解析错误
- `timeout_error`: 请求超时

### 原因3: 数据格式异常

**触发条件**：
- API 返回的数据结构不符合预期
- 缺少 `data` 或 `data.items` 字段

**代码位置**：`crawl_stage.py:427-435` 或 `501-509`

### 原因4: 所有案例都被跳过

**触发条件**：
- 启用了断点续传 (`enable_resume=True`)
- 所有案例的 ID 都在 `crawled_ids` 中
- 所有案例都已保存到 JSON 文件

**代码位置**：`crawl_stage.py:148-158`

**注意**：根据 `crawl_resume.json`，`crawled_ids` 为空，所以这个原因不太可能。

## 诊断步骤

### 步骤1: 查看任务详情和日志

通过 API 或前端界面查看：
1. **任务配置**：
   - `start_page`: 起始页码
   - `end_page`: 结束页码
   - `case_type`: 案例类型
   - `search_value`: 搜索关键词
   - `enable_resume`: 是否启用断点续传

2. **任务日志**：
   - 查看 ERROR 和 WARNING 级别的日志
   - 查找 "第X页" 相关的日志信息
   - 查找 API 请求相关的错误信息

### 步骤2: 查看列表页记录

通过 API 端点 `/api/v1/crawl-tasks/{task_id}/list-pages` 查看：
- 是否有列表页记录
- 列表页的状态（success/failed/pending）
- 错误信息（如果有）

### 步骤3: 手动测试 API

使用测试脚本验证 API 是否正常工作：

```python
from services.spider.api_client import AdquanAPIClient

client = AdquanAPIClient()
# 测试获取第一页数据
data = client.get_creative_list(page=0)
print(f"返回数据: {data}")
```

## 解决方案

### 方案1: 检查任务配置

1. **验证起始页码**：
   - 如果 `start_page` 过大，调整为较小的值（如 0）
   - 使用 `/api/v1/crawl-tasks/last-page` 获取建议的起始页码

2. **检查搜索条件**：
   - 如果设置了 `search_value`，尝试清空后重试
   - 如果设置了 `case_type`，确认该类型是否有数据

### 方案2: 重试任务

如果确认配置正确，可以：
1. 使用 **重试** 功能：`POST /api/v1/crawl-tasks/{task_id}/retry`
2. 使用 **重新执行** 功能：`POST /api/v1/crawl-tasks/{task_id}/restart`

### 方案3: 检查网络和 API 状态

1. **验证网络连接**：确保可以访问 API 服务器
2. **检查 API 认证**：验证 CSRF Token 是否有效
3. **查看 API 响应**：手动测试 API 是否返回数据

### 方案4: 创建新任务

如果问题持续存在：
1. 删除当前失败的任务
2. 使用正确的配置创建新任务
3. 从较小的起始页码开始测试

## 预防措施

1. **任务创建前验证**：
   - 验证起始页码是否合理
   - 测试 API 连接和认证
   - 验证搜索条件是否有结果

2. **增强错误处理**：
   - 在列表页获取失败时，记录详细的错误信息
   - 区分不同类型的失败原因（空数据 vs 请求失败）

3. **添加监控**：
   - 监控 API 请求的成功率
   - 监控列表页返回的数据量
   - 设置告警，当连续多个任务失败时通知

## 相关代码位置

- 失败判断逻辑：`app/services/crawl_task_executor.py:269-279`
- 列表页获取：`services/pipeline/crawl_stage.py:366-590`
- API 客户端：`services/spider/api_client.py:75-167`
- 断点续传文件：`data/json/task_49544538ae184203/crawl_resume.json`
