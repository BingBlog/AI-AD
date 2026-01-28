# 任务进度计算逻辑说明

## 当前进度计算逻辑

### 改进前（基于内存统计）

**计算方式：**
- 基于内存中的 `CrawlStage.stats` 统计
- `completed_pages = (total_crawled + total_failed) // batch_size`
- `current_page = start_page + completed_pages`

**问题：**
1. 如果任务异常中断，内存统计可能丢失或不准确
2. 无法从持久化数据恢复准确的进度
3. 任务状态检查时无法验证实际进度
4. **任务重新执行时，内存统计会重置，导致进度数据不一致**

### 改进后（完全基于文件计算）

**核心原则：所有进度计算都基于已保存的文件，确保数据一致性**

**计算方式：**
1. **优先使用文件计算结果**：
   - 从 `crawl_resume.json` 读取 `total_count`（已爬取总数）
   - 统计批次文件数量（`batches_saved`）
   - 统计批次文件中成功保存的案例数（`total_saved`）
   - `completed_pages = total_crawled // batch_size`

2. **回退到数据库值**：
   - 如果文件不存在或为空，使用数据库中的值作为备用
   - 不再依赖内存统计（因为任务可能重新执行，内存会重置）

## 实现细节

### 1. 文件进度计算函数

**位置：** `services/pipeline/utils.py`

**函数：** `calculate_progress_from_files(task_dir, batch_size)`

**返回数据：**
```python
{
    'total_crawled': int,      # 从 crawl_resume.json 的 total_count
    'total_saved': int,        # 从批次文件统计的成功案例数
    'batches_saved': int,      # 批次文件数量
    'completed_pages': int,    # 计算的已完成页数
    'crawled_ids_count': int,  # crawl_resume.json 中的 crawled_ids 数量
}
```

**计算逻辑：**
1. 读取 `crawl_resume.json` 获取 `total_count` 和 `crawled_ids`
2. 扫描所有 `cases_batch_*.json` 文件
3. 统计每个批次文件中没有 `error` 字段的案例数（成功保存的案例）
4. 计算 `completed_pages = total_crawled // batch_size`

### 2. 进度更新逻辑

**位置：** `app/services/crawl_task_executor.py`

**方法：** `_update_progress_periodically_sync()`

**逻辑：**
1. 尝试从文件计算进度
2. 如果文件数据可用（`total_crawled > 0` 或 `batches_saved > 0`），使用文件计算结果
3. 否则回退到内存统计
4. 更新数据库进度信息

**方法：** `_update_final_stats_sync()`

**逻辑：**
1. 任务完成时，优先使用文件计算结果
2. 如果 `total_pages` 存在，使用 `total_pages` 作为 `completed_pages`
3. 否则使用文件计算的 `completed_pages`

### 3. 任务状态检查

**位置：** `app/services/crawl_task_service.py`

**方法：** `check_real_status()`

**逻辑：**
1. 检查任务进度时，优先使用文件计算结果
2. 如果文件计算的进度与数据库不一致，可以自动修复（`auto_fix=True`）
3. 如果已完成所有页数但状态未更新，可以自动修复为 `completed`

### 4. 获取任务详情

**位置：** `app/services/crawl_task_service.py`

**方法：** `get_task_detail()`

**逻辑：**
1. 获取任务详情时，自动从文件计算实际进度
2. 如果文件计算的进度与数据库不一致，自动同步到数据库
3. 使用文件计算的进度信息返回给前端

### 5. 任务列表显示

**位置：** `app/services/crawl_task_service.py`

**方法：** `_convert_to_list_item()`

**逻辑：**
1. 转换列表项时，尝试从文件计算实际进度
2. 如果文件数据可用，使用文件计算结果更新显示
3. 仅用于显示，不更新数据库（避免列表查询时频繁更新）

## 优势

1. **可靠性**：基于持久化文件，即使任务异常中断也能准确恢复进度
2. **准确性**：文件是实际保存的数据，比内存统计更可靠
3. **一致性**：任务重新执行时，进度计算仍然基于已保存的文件，不会因为内存重置而丢失
4. **可验证性**：可以通过检查文件来验证进度是否准确
5. **自动修复**：任务状态检查和详情获取时可以自动修复进度不一致的问题
6. **数据持久化**：进度信息完全基于文件系统，不依赖内存状态

## 使用场景

### 1. 定期更新进度
- 任务运行期间，定期调用 `_update_progress_periodically_sync()`
- 自动优先使用文件计算结果
- 更新数据库中的进度信息

### 2. 任务完成时
- 调用 `_update_final_stats_sync()`
- 使用文件计算结果更新最终进度
- 确保最终进度准确反映实际保存的数据

### 3. 任务状态检查
- 调用 `check_real_status(task_id, auto_fix=True)`
- 检查并修复进度不一致的问题
- 可以自动将状态从 `running` 更新为 `completed`

### 4. 获取任务详情
- 调用 `get_task_detail(task_id)`
- 自动从文件计算进度并同步到数据库
- 返回准确的进度信息给前端

### 5. 任务列表显示
- 调用 `list_tasks()`
- 列表项转换时使用文件计算的进度
- 仅用于显示，不更新数据库（避免性能问题）

## 注意事项

1. **文件必须存在**：如果任务目录或文件不存在，会回退到数据库中的值
2. **批次大小**：需要正确的 `batch_size` 才能准确计算页数
3. **性能**：扫描批次文件需要一些时间，但通常很快（文件数量有限）
4. **错误处理**：如果文件读取失败，会静默处理并回退到数据库中的值
5. **任务重新执行**：即使任务重新执行，进度计算仍然基于已保存的文件，确保数据一致性
6. **自动同步**：获取任务详情时会自动同步文件计算的进度到数据库

## 示例

### 任务目录结构
```
data/json/task_xxx/
├── crawl_resume.json      # 包含 total_count 和 crawled_ids
├── cases_batch_0000.json
├── cases_batch_0001.json
├── ...
└── cases_batch_0161.json
```

### 计算示例
```python
from services.pipeline.utils import calculate_progress_from_files
from pathlib import Path

task_dir = Path("data/json/task_xxx")
batch_size = 30

progress = calculate_progress_from_files(task_dir, batch_size)
# {
#     'total_crawled': 2419,
#     'total_saved': 2410,
#     'batches_saved': 162,
#     'completed_pages': 80,  # 2419 // 30
#     'crawled_ids_count': 2419
# }
```

## 相关文件

- `services/pipeline/utils.py` - 文件进度计算函数
- `app/services/crawl_task_executor.py` - 进度更新逻辑
- `app/services/crawl_task_service.py` - 任务状态检查
- `app/services/crawl_task_executor_sync_db.py` - 数据库更新
