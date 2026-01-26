# 重试机制与 JSON 文件存储关系分析

## 1. 问题分析

**核心问题**：如果爬取失败后，对失败的列表页和案例进行重试，数据是否还会保存在 JSON 文件中？

## 2. 当前实现分析

### 2.1 失败时的数据保存

根据当前代码实现（`crawl_stage.py`），当案例爬取失败时：

```python
except Exception as e:
    logger.error(f"[案例 {i}/{len(list_items)}] 处理失败: {case_title} (case_id={case_id}) - {e}")
    self.stats['total_failed'] += 1

    # 保存失败信息
    failed_case = {
        'case_id': case_id,
        'url': case_url,
        'title': case_title,
        'error': str(e),
        'crawl_time': datetime.now().isoformat()
    }
    current_batch.append(failed_case)  # 失败案例也会添加到批次中
```

**关键发现**：

- ✅ 失败的案例**会保存到 JSON 文件**，但只包含错误信息
- ❌ 失败的案例**不包含完整的案例数据**（title, description, images 等）
- ✅ 失败案例会被标记为 `error` 字段

### 2.2 成功时的数据保存

当案例爬取成功时：

```python
try:
    # 解析详情页
    detail_data = self.detail_parser.parse(case_url)

    # 合并数据
    case_data = merge_case_data(item, detail_data)

    # 验证数据
    is_valid, error = self.validator.validate_case(case_data)
    if not is_valid:
        case_data['validation_error'] = error

    # 添加到批次
    current_batch.append(case_data)  # 包含完整数据

    # 达到批次大小，保存JSON
    if len(current_batch) >= self.batch_size:
        self._save_batch(current_batch, batch_num)
```

**关键发现**：

- ✅ 成功的案例会保存**完整的案例数据**到 JSON 文件
- ✅ 验证失败的案例也会保存，但包含 `validation_error` 字段

---

## 3. 重试机制分析

### 3.1 当前重试方式（retry_task）

**当前实现**（`crawl_task_service.py`）：

```python
async def retry_task(self, task_id: str) -> bool:
    """重试任务"""
    # 清除统计信息，准备重新开始
    await self.repo.update_task_progress(
        task_id=task_id,
        completed_pages=0,
        current_page=task_data.get("start_page", 0),
        total_crawled=0,
        total_saved=0,
        total_failed=0,
        batches_saved=0
    )

    # 自动开始执行
    await self.start_task(task_id)
```

**特点**：

- ❌ 这是**全量重试**，会重新爬取整个任务
- ❌ 不会利用新表（`crawl_list_pages`、`crawl_case_records`）的失败记录
- ✅ 重试成功后，数据会正常保存到 JSON 文件

### 3.2 优化后的精确重试（待实现）

根据优化方案（`crawl-task-optimization.md`），将实现精确重试：

#### 3.2.1 重试失败的列表页

```python
async def retry_failed_list_pages(self, task_id: str) -> bool:
    """重试失败的列表页"""
    # 1. 查询失败的列表页
    failed_pages = await self.list_page_repo.get_failed_list_pages(task_id)

    # 2. 重试每个失败的列表页
    for page_info in failed_pages:
        page_number = page_info['page_number']
        # 重新爬取该列表页
        await self._retry_single_list_page(task_id, page_number)
```

**流程**：

1. 查询 `crawl_list_pages` 表中 `status='failed'` 的记录
2. 重新调用 `get_creative_list(page_number)` 获取列表页数据
3. 如果成功，更新 `crawl_list_pages` 状态为 `success`
4. 遍历列表页中的案例，爬取每个案例
5. **成功的案例会保存到 JSON 文件**（通过 `_save_batch` 方法）

#### 3.2.2 重试失败的案例

```python
async def retry_failed_cases(self, task_id: str, case_ids: Optional[List[int]] = None) -> bool:
    """重试失败的案例"""
    # 1. 查询失败的案例
    failed_cases = await self.case_repo.get_failed_cases(task_id)

    # 2. 重试每个失败的案例
    for case_info in failed_cases:
        # 重新爬取该案例
        await self._retry_single_case(task_id, case_info)
```

**流程**：

1. 查询 `crawl_case_records` 表中 `status IN ('failed', 'validation_failed')` 的记录
2. 获取案例的 `case_url` 和 `case_id`
3. 重新调用 `detail_parser.parse(case_url)` 解析详情页
4. 如果成功，更新 `crawl_case_records` 状态为 `success`
5. **成功的案例会保存到 JSON 文件**（通过 `_save_batch` 方法）

---

## 4. 重试后的数据保存流程

### 4.1 重试列表页后的数据流

```
重试失败的列表页
  ↓
重新获取列表页数据（get_creative_list）
  ↓
成功 → 更新 crawl_list_pages.status = 'success'
  ↓
遍历列表页中的案例
  ↓
爬取每个案例（detail_parser.parse）
  ↓
成功 → 合并数据 → 添加到 current_batch
  ↓
达到批次大小 → _save_batch → 保存到JSON文件 ✅
```

### 4.2 重试案例后的数据流

```
重试失败的案例
  ↓
重新解析详情页（detail_parser.parse）
  ↓
成功 → 合并数据 → 添加到 current_batch
  ↓
达到批次大小 → _save_batch → 保存到JSON文件 ✅
```

### 4.3 关键代码路径

无论是一次性爬取还是重试，只要案例爬取成功，都会经过以下代码路径：

```python
# services/pipeline/crawl_stage.py

try:
    # 解析详情页
    detail_data = self.detail_parser.parse(case_url)

    # 合并数据
    case_data = merge_case_data(item, detail_data)

    # 验证数据
    is_valid, error = self.validator.validate_case(case_data)
    if not is_valid:
        case_data['validation_error'] = error

    # 添加到批次（包含完整数据）
    current_batch.append(case_data)

    # 达到批次大小，保存JSON
    if len(current_batch) >= self.batch_size:
        self._save_batch(current_batch, batch_num)  # ✅ 保存到JSON文件
        current_batch = []
        batch_num += 1
```

---

## 5. 结论

### 5.1 核心答案

**是的，重试成功后数据会保存到 JSON 文件中。**

**原因**：

1. ✅ 重试机制会重新调用爬取流程（`detail_parser.parse`）
2. ✅ 爬取成功的案例会经过正常的数据处理流程
3. ✅ 成功的案例会添加到 `current_batch`，然后通过 `_save_batch` 保存到 JSON 文件
4. ✅ 保存的 JSON 文件包含**完整的案例数据**（title, description, images 等）

### 5.2 数据保存的两种情况

#### 情况 1：首次爬取失败

**JSON 文件内容**：

```json
{
  "batch_num": 0,
  "cases": [
    {
      "case_id": 12345,
      "url": "https://...",
      "title": "案例标题",
      "error": "网络请求失败",
      "crawl_time": "2024-01-01T00:00:00"
    }
  ]
}
```

**特点**：

- ❌ 不包含完整的案例数据
- ✅ 包含错误信息
- ✅ 记录在 `crawl_case_records` 表中，状态为 `failed`

#### 情况 2：重试成功后

**JSON 文件内容**：

```json
{
  "batch_num": 1,
  "cases": [
    {
      "case_id": 12345,
      "title": "案例标题",
      "description": "完整的案例描述",
      "images": ["url1", "url2", ...],
      "tags": ["tag1", "tag2", ...],
      // ... 完整的案例数据
    }
  ]
}
```

**特点**：

- ✅ 包含完整的案例数据
- ✅ 可以正常导入到数据库
- ✅ `crawl_case_records` 表中状态更新为 `success`，`saved_to_json=true`

### 5.3 数据去重问题

**潜在问题**：

- 首次失败时，失败记录已保存到 JSON 文件（只有错误信息）
- 重试成功后，完整的案例数据会保存到新的批次文件
- 可能导致同一个案例在 JSON 文件中出现两次：
  - 一次是失败记录（只有错误信息）
  - 一次是成功记录（完整数据）

**解决方案**：

1. **导入时去重**（推荐）

   - 导入 JSON 文件时，按 `case_id` 去重
   - 优先使用包含完整数据的记录
   - 跳过只有错误信息的记录

2. **清理失败记录**（可选）

   - 重试成功后，从 JSON 文件中删除对应的失败记录
   - 需要维护 JSON 文件的一致性

3. **使用新表判断**（推荐）
   - 导入时查询 `crawl_case_records` 表
   - 只导入 `status='success'` 且 `saved_to_json=true` 的案例
   - 跳过失败记录的 JSON 条目

---

## 6. 实施建议

### 6.1 重试机制实现

**需要确保**：

1. ✅ 重试时调用正常的爬取流程（`CrawlStage.crawl` 或类似方法）
2. ✅ 重试成功后，数据会正常保存到 JSON 文件
3. ✅ 更新 `crawl_case_records` 表的 `saved_to_json` 和 `batch_file_name` 字段

### 6.2 数据导入优化

**建议**：

1. ✅ 导入时优先使用新表（`crawl_case_records`）判断哪些案例应该导入
2. ✅ 只导入 `status='success'` 且 `saved_to_json=true` 的案例
3. ✅ 跳过 JSON 文件中只有错误信息的记录

### 6.3 JSON 文件管理

**建议**：

1. ✅ 保留 JSON 文件作为数据备份和导入源
2. ✅ 导入成功后，可以归档或删除 JSON 文件
3. ✅ 定期清理已导入的 JSON 文件，释放存储空间

---

## 7. 总结

### 7.1 核心结论

**重试成功后，数据会保存到 JSON 文件中，包含完整的案例数据。**

### 7.2 数据流程

```
首次爬取失败
  ↓
保存失败记录到JSON（只有错误信息）
  ↓
记录到 crawl_case_records（status='failed'）
  ↓
重试失败的案例
  ↓
重新爬取成功
  ↓
保存完整数据到JSON（包含完整案例数据）✅
  ↓
更新 crawl_case_records（status='success', saved_to_json=true）
```

### 7.3 注意事项

1. ⚠️ 同一个案例可能在 JSON 文件中出现两次（失败记录 + 成功记录）
2. ✅ 导入时需要去重，优先使用包含完整数据的记录
3. ✅ 可以使用新表（`crawl_case_records`）判断哪些案例应该导入
