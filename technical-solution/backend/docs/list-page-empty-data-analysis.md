# 列表页空数据分析与改进

## 问题描述

日志显示任务 `task_65e78b3a478d4cdd` 在第 95 页数据为空，但实际通过 curl 请求可以获取到数据。

## 问题分析

### 1. 当前请求列表页数据的方法和参数

**位置**: `backend/services/spider/api_client.py` 的 `get_creative_list` 方法

**请求参数**:

- `page`: 页码（从 0 开始，API 实际使用 page+1）
- `case_type`: 案例类型（映射到 `typeclass` 参数）
- `industry`: 行业（默认 0）
- `typeclass`: 案例类型（默认使用 case_type）
- `area`: 地区（默认空字符串）
- `year`: 年份（默认 0）
- `filter`: 筛选条件（默认 0）
- `keyword`: 关键词（默认空字符串）

**请求 Headers**:

- `X-CSRF-TOKEN`: CSRF Token（通过 CSRFTokenManager 获取）
- `X-Requested-With`: XMLHttpRequest
- `User-Agent`: 浏览器 User-Agent
- `Referer`: https://www.adquan.com/case_library/index
- 其他标准浏览器 Headers

**改进前的问题**:

- 日志中只记录了部分请求信息，缺少完整的 URL 和关键 Headers
- 无法完整复现请求进行调试

**改进后**:

- ✅ 记录完整的请求 URL（包含所有参数）
- ✅ 记录关键 Headers（User-Agent, X-CSRF-TOKEN, X-Requested-With, Referer）
- ✅ 记录重试次数信息
- ✅ 记录请求方法和超时设置

### 2. 当前判断为空的方法及重试次数

**位置**: `backend/services/pipeline/crawl_stage.py` 的 `_get_list_items_streaming` 方法

**判断逻辑**:

```python
items = data['data'].get('items', [])
if not items:
    logger.info(f"第{page}页没有更多数据，停止获取")
    break
```

**问题**:

- ❌ 没有重试机制：一旦检测到空数据，立即停止
- ❌ 诊断信息不足：无法判断是网络问题、解析问题还是确实没有数据
- ❌ 没有记录完整的响应数据用于分析

**改进后**:

- ✅ 增加空数据重试机制（最多 3 次，每次间隔 5 秒）
- ✅ 记录完整的响应数据（限制长度避免日志过大）
- ✅ 记录响应数据的键结构用于诊断
- ✅ 在 HTML 解析阶段增加详细的诊断信息

### 3. 潜在问题分析

#### 3.1 HTML 解析失败

**可能原因**:

- HTML 结构变化，解析器无法找到 `article_1` 元素
- HTML 内容不完整（网络问题导致）
- HTML 格式错误

**改进**:

- ✅ 记录 HTML 内容长度和预览（前 500 字符）
- ✅ 检查 HTML 中是否包含 `article_1` 字符串
- ✅ 记录 HTML 中的 `<div>` 标签数量
- ✅ 记录解析失败的详细异常堆栈

#### 3.2 网络问题

**可能原因**:

- 请求超时但未抛出异常
- 响应不完整（部分数据丢失）
- 代理问题导致响应异常

**改进**:

- ✅ 记录 HTTP 状态码和响应大小
- ✅ 记录请求耗时
- ✅ 对于空数据增加重试机制（最多 3 次）

#### 3.3 API 返回格式变化

**可能原因**:

- API 返回的 `data` 字段格式变化
- API 返回空字符串而不是 HTML
- API 返回错误但状态码为 200

**改进**:

- ✅ 记录 API 状态码和消息
- ✅ 记录响应数据的完整结构
- ✅ 检查 `data` 字段的类型和内容

## 改进内容总结

### 1. API 请求日志增强 (`api_client.py`)

**新增日志信息**:

- 完整请求 URL（包含所有查询参数）
- 关键 Headers 信息（User-Agent, X-CSRF-TOKEN 等）
- 重试次数信息
- HTML 内容长度和预览
- HTML 解析失败的详细诊断信息

**示例日志输出**:

```
API请求详情:
  - 完整URL: https://www.adquan.com/case_library/index?page=95&industry=0&typeclass=0&area=&year=0&filter=0&keyword=
  - 基础URL: https://www.adquan.com/case_library/index
  - 页码（内部）: 94 (API使用: 95)
  - 案例类型: 0
  - 请求参数: {'page': 94, 'industry': 0, 'typeclass': 0, 'area': '', 'year': 0, 'filter': 0, 'keyword': ''}
  - 请求方法: GET
  - 超时设置: 30 秒
  - 重试次数: 0/3
  - 关键Headers:
    * User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...
    * X-CSRF-TOKEN: rmTTA34nB8wIUmofcn3mXKWR6BuIJEN1JlShDTk9...
    * X-Requested-With: XMLHttpRequest
    * Referer: https://www.adquan.com/case_library/index
```

### 2. 空数据判断与重试机制 (`crawl_stage.py`)

**新增功能**:

- 空数据重试机制（最多 3 次，每次间隔 5 秒）
- 详细的响应数据诊断信息
- 重试计数管理（每页独立计数）

**重试逻辑**:

```python
if not items:
    # 记录诊断信息
    # ...

    # 重试机制
    if empty_retry_count < 3:
        empty_retry_count += 1
        logger.warning(f"检测到空数据，准备重试（第 {empty_retry_count}/3 次）...")
        time.sleep(5)
        continue  # 重新请求当前页
    else:
        # 达到最大重试次数，停止
        break
```

### 3. HTML 解析诊断增强 (`api_client.py`)

**新增诊断信息**:

- HTML 内容长度
- HTML 内容预览（前 500 字符）
- **完整 HTML 内容记录**（解析异常或结果为空时）
- 检查 HTML 中是否包含关键元素
- 解析失败的详细异常堆栈

**HTML 记录策略**:

- HTML ≤ 10000 字符：记录完整内容
- HTML > 10000 字符：记录前 5000 字符和后 5000 字符
- 使用分隔线标记，便于在日志中查找

**示例日志输出**:

```
⚠️ HTML 解析结果为空，可能的原因：
   1. HTML 结构已变化，未找到 article_1 元素
   2. HTML 内容不完整或格式错误
   3. 该页确实没有数据
   - 诊断: HTML中未找到 'article_1' 字符串
   - HTML中包含 50 个 <div> 标签
================================================================================
完整HTML内容（用于排查问题）:
================================================================================
HTML内容长度: 12345 字符
[完整的HTML内容]
================================================================================
```

## 使用建议

### 1. 查看完整请求信息

当遇到空数据问题时，查看日志中的"API 请求详情"部分，可以：

- 复制完整 URL 直接在浏览器或 curl 中测试
- 检查请求参数是否正确
- 检查 CSRF Token 是否有效

### 2. 分析响应数据

查看日志中的"响应数据"部分，可以：

- 检查 API 返回的数据结构
- 判断是解析问题还是 API 确实返回空数据
- 查看 HTML 内容预览判断 HTML 是否完整

### 4. 查看完整 HTML 内容

当解析异常或未解析到数据时，系统会自动记录完整的 HTML 内容到日志中：

- **HTML 长度 ≤ 10000 字符**：记录完整 HTML 内容
- **HTML 长度 > 10000 字符**：记录前 5000 字符和后 5000 字符（避免日志过大）

**记录时机**：

1. HTML 解析异常时（`list_page_html_parser.py`）
2. 未找到 `article_1` 元素时（`list_page_html_parser.py`）
3. 解析完成但未提取到任何案例时（`list_page_html_parser.py`）
4. API 返回空解析结果时（`api_client.py`）

**日志格式**：

```
================================================================================
完整HTML内容（用于排查问题）:
================================================================================
HTML内容长度: 12345 字符
[完整的HTML内容或前后各5000字符]
================================================================================
```

**使用建议**：

- 将日志中的 HTML 内容保存为 `.html` 文件，在浏览器中打开查看
- 检查 HTML 结构是否符合预期（是否包含 `article_1` 元素）
- 对比正常页面的 HTML 结构，找出差异

### 3. 重试机制

系统会自动对空数据进行重试（最多 3 次），如果：

- 3 次重试后仍为空：可能是该页确实没有数据，或 API/HTML 结构已变化
- 重试后成功获取数据：可能是临时网络问题或 API 响应延迟

**注意**：每次重试时都会记录完整的 HTML 内容，便于对比分析

## 后续优化建议

1. **增加响应时间监控**: 记录 API 响应时间，如果响应时间异常长，可能是网络问题
2. **增加 HTML 结构验证**: 在解析前验证 HTML 结构是否符合预期
3. **增加 API 健康检查**: 定期检查 API 是否正常，如果 API 异常，提前告警
4. **增加数据完整性检查**: 检查解析出的 items 是否包含必要字段（title, url 等）
