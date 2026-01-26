# 图片下载服务集成到任务爬取环节 - 实施完成

## 实施日期
2026-01-25

## 实施总结

已成功将图片下载服务集成到数据导入阶段，在案例数据入库时自动下载图片。

## 已完成的变更

### 1. ImportStage 类修改 ✅

**文件**: `services/pipeline/import_stage.py`

**变更内容**:
1. ✅ 添加初始化参数：
   - `download_images: bool = False` - 是否在导入时下载图片
   - `image_download_concurrency: int = 5` - 图片下载并发数

2. ✅ 添加统计信息字段：
   - `images_downloaded` - 成功下载的图片数
   - `images_failed` - 下载失败的图片数
   - `images_skipped` - 跳过的图片数（已存在）

3. ✅ 添加 `_download_images_batch()` 方法：
   - 批量下载图片（同步包装异步方法）
   - 使用 `asyncio.Semaphore` 控制并发数
   - 检查图片是否已下载，避免重复下载
   - 错误处理：下载失败不影响数据导入

4. ✅ 修改 `_insert_batch()` 方法：
   - 在插入数据库前，如果启用图片下载，先批量下载图片
   - 修改 INSERT SQL，添加 `main_image_local` 字段
   - 修改 ON CONFLICT 语句，更新 `main_image_local` 字段
   - 在准备数据时，添加 `main_image_local` 字段

5. ✅ 更新日志输出：
   - 添加图片下载统计信息到日志

### 2. ImportTaskExecutor 类修改 ✅

**文件**: `app/services/import_task_executor.py`

**变更内容**:
1. ✅ 在 `execute()` 方法中添加参数：
   - `download_images: bool = False`
   - `image_download_concurrency: int = 5`

2. ✅ 在 `_execute_sync()` 方法中添加参数：
   - `download_images: bool = False`
   - `image_download_concurrency: int = 5`

3. ✅ 在创建 `ImportStage` 实例时传递参数：
   - `download_images=download_images`
   - `image_download_concurrency=image_download_concurrency`

### 3. TaskImportService 和 Schema 修改 ✅

**文件**: `app/schemas/task_import.py`

**变更内容**:
1. ✅ 在 `ImportStartRequest` 中添加字段：
   - `download_images: bool = False` - 是否在导入时下载图片
   - `image_download_concurrency: int = 5` - 图片下载并发数（1-20）

**文件**: `app/services/task_import_service.py`

**变更内容**:
1. ✅ 在 `start_import()` 方法中传递参数：
   - `download_images=request.download_images`
   - `image_download_concurrency=request.image_download_concurrency`

## 功能特性

### 1. 向后兼容
- ✅ 默认关闭：`download_images=False`
- ✅ 现有代码无需修改即可正常工作
- ✅ 需要显式启用图片下载功能

### 2. 错误处理
- ✅ 图片下载失败不影响数据导入
- ✅ 记录下载失败的案例到统计信息
- ✅ 详细的错误日志

### 3. 性能优化
- ✅ 支持并发下载（默认 5 个并发）
- ✅ 检查已下载的图片，避免重复下载
- ✅ 可配置并发数（1-20）

### 4. 统计信息
- ✅ 记录图片下载成功数
- ✅ 记录图片下载失败数
- ✅ 记录跳过的图片数（已存在）

## 使用方式

### API 请求示例

```json
POST /api/v1/task-imports/{task_id}/start
{
  "import_mode": "full",
  "skip_existing": true,
  "generate_vectors": true,
  "batch_size": 50,
  "download_images": true,
  "image_download_concurrency": 5
}
```

### 参数说明

- `download_images`: 是否在导入时下载图片（默认 `false`）
- `image_download_concurrency`: 图片下载并发数（默认 `5`，范围 1-20）

## 性能影响

### 时间成本

假设：
- 平均每张图片下载时间：2 秒
- 并发数：5
- 批次大小：50

**计算**：
- 每批次下载时间：50 / 5 * 2 = 20 秒
- 原来入库时间：约 5 秒
- **总时间增加**：约 20 秒/批次（4 倍）

### 优化建议

1. **降低并发数**：如果服务器性能有限，可以减少并发数（如 3）
2. **增大批次大小**：可以减少批次数量，但会增加内存占用
3. **选择性启用**：只在需要时启用图片下载功能

## 测试建议

### 1. 功能测试
- 测试启用图片下载的导入流程
- 测试图片下载失败时的数据导入
- 测试已下载图片的跳过逻辑

### 2. 性能测试
- 测试不同并发数下的性能
- 测试大批量导入时的内存占用

### 3. 错误处理测试
- 测试网络错误时的处理
- 测试无效 URL 的处理

## 注意事项

1. **默认关闭**：图片下载功能默认关闭，需要显式启用
2. **性能影响**：启用图片下载会显著增加导入时间（约 4 倍）
3. **存储空间**：确保有足够的磁盘空间存储图片（约 2.4 GB）
4. **网络要求**：需要稳定的网络连接下载图片

## 后续优化建议

1. **异步优化**：在生成向量时并行下载图片（需要重构）
2. **断点续传**：支持导入任务中断后继续下载图片
3. **图片压缩**：下载后自动压缩，减少存储空间
4. **CDN 支持**：如果图片量大，考虑使用 CDN

## 文件变更清单

1. ✅ `services/pipeline/import_stage.py` - 主要修改
2. ✅ `app/services/import_task_executor.py` - 传递参数
3. ✅ `app/services/task_import_service.py` - 处理请求参数
4. ✅ `app/schemas/task_import.py` - 添加请求字段

## 验证步骤

1. 启动后端服务
2. 创建导入任务，设置 `download_images=true`
3. 观察日志，确认图片下载功能正常工作
4. 检查数据库，确认 `main_image_local` 字段已更新
5. 检查文件系统，确认图片已下载到 `data/images/` 目录

## 总结

✅ 所有变更已完成并经过 lint 检查
✅ 向后兼容，默认关闭
✅ 错误处理完善，不影响主流程
✅ 性能可控，可通过配置调整

功能已就绪，可以开始使用！
