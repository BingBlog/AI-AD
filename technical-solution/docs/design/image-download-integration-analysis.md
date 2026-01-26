# 图片下载服务集成到任务爬取环节 - 变更分析

## 1. 概述

将图片下载服务集成到数据导入阶段，在案例数据入库时自动下载图片，避免后续单独运行批量下载脚本。

## 2. 当前流程分析

### 2.1 数据流程

```
爬取阶段 (CrawlStage)
  ↓ 保存到 JSON 文件
导入阶段 (ImportStage)
  ├─ 读取 JSON 文件
  ├─ 验证数据
  ├─ 生成向量
  └─ 批量入库 (_insert_batch)
      └─ 插入数据库（不包含 main_image_local）
```

### 2.2 关键代码位置

1. **ImportStage 类** (`services/pipeline/import_stage.py`)

   - `_insert_batch()`: 批量插入数据库的方法
   - 当前只插入 `main_image` 字段，不包含 `main_image_local`

2. **ImageService 类** (`app/services/image_service.py`)
   - `download_image()`: 异步下载图片方法
   - `is_image_downloaded()`: 检查图片是否已下载

## 3. 集成方案

### 3.1 集成点选择

**推荐方案：在导入阶段的 `_insert_batch` 方法中集成**

**优点**：

- ✅ 不影响爬取速度（爬取阶段只保存 JSON）
- ✅ 与数据入库同步，保证数据一致性
- ✅ 可以统一处理错误和统计
- ✅ 支持配置开关，灵活控制

**缺点**：

- ⚠️ 入库速度会变慢（需要下载图片）
- ⚠️ 需要处理同步/异步转换（ImportStage 是同步的，ImageService 是异步的）

### 3.2 技术挑战

1. **同步/异步转换**：

   - `ImportStage._insert_batch()` 是同步方法
   - `ImageService.download_image()` 是异步方法
   - 需要在同步方法中调用异步方法

2. **批量下载优化**：

   - 可以批量下载图片，提高效率
   - 需要控制并发数，避免过多请求

3. **错误处理**：
   - 图片下载失败不应阻止数据导入
   - 需要记录下载失败的案例

## 4. 详细变更清单

### 4.1 ImportStage 类修改

#### 4.1.1 初始化参数

**文件**: `services/pipeline/import_stage.py`

**变更**:

- 添加 `download_images: bool = False` 参数
- 添加 `image_download_concurrency: int = 5` 参数（控制并发数）

**代码位置**: `__init__` 方法

```python
def __init__(
    self,
    db_config: Dict[str, Any],
    model_name: str = 'BAAI/bge-large-zh-v1.5',
    batch_size: int = 50,
    skip_existing: bool = False,
    skip_invalid: bool = False,
    normalize_data: bool = True,
    import_failed_only: bool = False,
    task_id: Optional[str] = None,
    download_images: bool = False,  # 新增：是否下载图片
    image_download_concurrency: int = 5,  # 新增：图片下载并发数
):
```

#### 4.1.2 添加图片下载方法

**文件**: `services/pipeline/import_stage.py`

**变更**:

- 添加 `_download_images_batch()` 方法
- 处理同步/异步转换（使用 `asyncio.run()`）

**代码位置**: `_insert_batch` 方法之前

```python
def _download_images_batch(self, cases: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    批量下载图片（同步包装异步方法）

    Args:
        cases: 案例列表

    Returns:
        下载失败的案例字典 {case_id: error_message}
    """
    import asyncio
    from app.services.image_service import ImageService

    async def download_async():
        image_service = ImageService()
        semaphore = asyncio.Semaphore(self.image_download_concurrency)
        failed_cases = {}

        async def download_with_limit(case: Dict[str, Any]):
            async with semaphore:
                case_id = case.get('case_id')
                main_image = case.get('main_image')

                if not main_image:
                    return

                # 检查是否已下载
                is_downloaded, local_url = image_service.is_image_downloaded(case_id)
                if is_downloaded:
                    case['main_image_local'] = local_url
                    return

                # 下载图片
                success, local_url, error = await image_service.download_image(
                    main_image, case_id
                )

                if success and local_url:
                    case['main_image_local'] = local_url
                else:
                    failed_cases[case_id] = error or "下载失败"

        # 创建任务列表
        tasks = [download_with_limit(case) for case in cases if case.get('main_image')]

        # 执行下载
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return failed_cases

    # 在同步方法中运行异步代码
    try:
        return asyncio.run(download_async())
    except Exception as e:
        logger.error(f"批量下载图片失败: {e}")
        return {}
```

#### 4.1.3 修改 \_insert_batch 方法

**文件**: `services/pipeline/import_stage.py`

**变更**:

1. 在准备数据之前，如果启用图片下载，先批量下载图片
2. 在插入 SQL 中添加 `main_image_local` 字段
3. 在 ON CONFLICT 时也更新 `main_image_local`

**代码位置**: `_insert_batch` 方法

```python
def _insert_batch(self, conn, batch: List[Dict[str, Any]]) -> tuple[List[int], Dict[int, str]]:
    # 如果启用图片下载，先批量下载图片
    if self.download_images:
        logger.info(f"开始批量下载图片，共 {len(batch)} 个案例")
        image_failed_cases = self._download_images_batch(batch)
        if image_failed_cases:
            logger.warning(f"图片下载失败: {len(image_failed_cases)} 个案例")
        logger.info("图片下载完成")

    # 修改 INSERT SQL，添加 main_image_local 字段
    insert_sql = """
        INSERT INTO ad_cases (
            case_id, source_url, title, description, author, publish_time,
            main_image, main_image_local, images, video_url,
            brand_name, brand_industry, activity_type, location, tags,
            score, score_decimal, favourite,
            company_name, company_logo, agency_name,
            combined_vector
        ) VALUES (
            %(case_id)s, %(source_url)s, %(title)s, %(description)s,
            %(author)s, %(publish_time)s,
            %(main_image)s, %(main_image_local)s, %(images)s::jsonb, %(video_url)s,
            %(brand_name)s, %(brand_industry)s, %(activity_type)s,
            %(location)s, %(tags)s::jsonb,
            %(score)s, %(score_decimal)s, %(favourite)s,
            %(company_name)s, %(company_logo)s, %(agency_name)s,
            %(combined_vector)s::vector(1024)
        )
        ON CONFLICT (case_id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            combined_vector = EXCLUDED.combined_vector,
            main_image_local = EXCLUDED.main_image_local,
            updated_at = CURRENT_TIMESTAMP
    """

    # 在准备数据时，添加 main_image_local 字段
    data = {
        ...
        'main_image': case.get('main_image'),
        'main_image_local': case.get('main_image_local'),  # 新增
        'images': json.dumps(case.get('images', []), ensure_ascii=False),
        ...
    }
```

### 4.2 ImportTaskExecutor 类修改

**文件**: `app/services/import_task_executor.py`

**变更**:

- 在创建 `ImportStage` 实例时，传递图片下载相关参数
- 从导入请求中读取 `download_images` 参数

**代码位置**: `_execute_sync` 方法

```python
self.import_stage = ImportStage(
    db_config=db_config,
    model_name=model_name,
    batch_size=batch_size,
    skip_existing=skip_existing and not update_existing,
    skip_invalid=skip_invalid,
    normalize_data=normalize_data,
    import_failed_only=import_failed_only,
    task_id=self.task_id,
    download_images=download_images,  # 新增
    image_download_concurrency=image_download_concurrency,  # 新增
)
```

### 4.3 TaskImportService 类修改

**文件**: `app/services/task_import_service.py`

**变更**:

- 在 `ImportStartRequest` schema 中添加 `download_images` 参数
- 在启动导入任务时传递该参数

**需要查看的文件**:

- `app/schemas/task_import.py`: 添加 `download_images` 字段
- `app/services/task_import_service.py`: 传递参数到 `ImportTaskExecutor`

### 4.4 统计信息增强

**文件**: `services/pipeline/import_stage.py`

**变更**:

- 在 `self.stats` 中添加图片下载相关统计
  - `images_downloaded`: 成功下载的图片数
  - `images_failed`: 下载失败的图片数
  - `images_skipped`: 跳过的图片数（已存在）

## 5. 配置项

### 5.1 环境变量（可选）

在 `app/config.py` 中添加默认配置：

```python
# 图片下载配置（导入时）
IMAGE_DOWNLOAD_ON_IMPORT: bool = False  # 导入时是否自动下载图片
IMAGE_DOWNLOAD_CONCURRENCY_ON_IMPORT: int = 5  # 导入时图片下载并发数
```

### 5.2 导入请求参数

在导入任务的请求中添加参数：

```python
class ImportStartRequest(BaseModel):
    ...
    download_images: bool = False  # 是否在导入时下载图片
    image_download_concurrency: int = 5  # 图片下载并发数
```

## 6. 错误处理策略

### 6.1 图片下载失败

- **不影响数据导入**：即使图片下载失败，案例数据仍然可以正常入库
- **记录错误信息**：在统计信息中记录下载失败的案例
- **日志记录**：记录详细的错误信息，便于排查

### 6.2 网络超时

- **重试机制**：使用 `ImageService` 已有的重试机制（默认 3 次）
- **超时设置**：使用配置的 `IMAGE_DOWNLOAD_TIMEOUT`（默认 30 秒）

### 6.3 并发控制

- **信号量控制**：使用 `asyncio.Semaphore` 控制并发数
- **默认并发数**：5 个（可配置）

## 7. 性能影响评估

### 7.1 时间成本

假设：

- 平均每张图片下载时间：2 秒
- 并发数：5
- 批次大小：50

**计算**：

- 每批次下载时间：50 / 5 \* 2 = 20 秒
- 原来入库时间：约 5 秒
- **总时间增加**：约 20 秒/批次（4 倍）

### 7.2 优化建议

1. **降低并发数**：如果服务器性能有限，可以减少并发数
2. **增大批次大小**：可以减少批次数量，但会增加内存占用
3. **异步下载**：在生成向量时并行下载图片（需要重构）

## 8. 向后兼容性

### 8.1 默认行为

- **默认不下载图片**：`download_images=False`
- 现有代码无需修改即可正常工作
- 需要显式启用图片下载功能

### 8.2 数据库兼容

- `main_image_local` 字段可以为 NULL
- 如果未下载图片，该字段为 NULL，不影响现有功能

## 9. 测试建议

### 9.1 单元测试

- 测试 `_download_images_batch` 方法
- 测试同步/异步转换
- 测试错误处理

### 9.2 集成测试

- 测试完整的导入流程（启用图片下载）
- 测试图片下载失败时的数据导入
- 测试并发下载的性能

### 9.3 性能测试

- 测试不同并发数下的性能
- 测试大批量导入时的内存占用

## 10. 实施步骤

1. ✅ **修改 ImportStage 类**

   - 添加初始化参数
   - 添加图片下载方法
   - 修改插入 SQL

2. ✅ **修改 ImportTaskExecutor 类**

   - 传递图片下载参数

3. ✅ **修改 TaskImportService 和 Schema**

   - 添加请求参数

4. ✅ **测试验证**

   - 单元测试
   - 集成测试

5. ✅ **文档更新**
   - 更新使用说明
   - 更新 API 文档

## 11. 风险评估

### 11.1 技术风险

- **低风险**：同步/异步转换（已有成熟方案）
- **低风险**：错误处理（不影响主流程）

### 11.2 性能风险

- **中风险**：导入速度变慢（可通过配置控制）
- **低风险**：内存占用增加（可控）

### 11.3 业务风险

- **低风险**：向后兼容（默认关闭）
- **低风险**：数据一致性（图片下载失败不影响数据）

## 12. 总结

### 12.1 变更文件清单

1. `services/pipeline/import_stage.py` - 主要修改
2. `app/services/import_task_executor.py` - 传递参数
3. `app/services/task_import_service.py` - 处理请求参数
4. `app/schemas/task_import.py` - 添加请求字段
5. `app/config.py` - 添加默认配置（可选）

### 12.2 关键决策点

1. **是否默认启用**：建议默认关闭，需要时显式启用
2. **并发数设置**：建议默认 5，可根据服务器性能调整
3. **错误处理**：图片下载失败不影响数据导入

### 12.3 建议

- ✅ **推荐实施**：功能完整，风险可控
- ✅ **分阶段实施**：先实现基础功能，后续优化性能
- ✅ **充分测试**：确保向后兼容性和错误处理
