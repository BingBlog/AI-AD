# 图片下载功能使用说明

## 概述

本功能用于将数据库中所有案例的 `main_image` 下载到本地服务器，解决广告门防盗链导致的图片无法加载问题。

## 使用步骤

### 1. 执行数据库迁移

首先需要执行数据库迁移脚本，添加 `main_image_local` 字段：

```bash
cd backend
psql -U postgres -d ad_case_db -f database/migrations/006_add_main_image_local_field.sql
```

或者使用 Python 脚本执行：

```python
import asyncpg
import asyncio

async def run_migration():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='',
        database='ad_case_db'
    )
    with open('database/migrations/006_add_main_image_local_field.sql', 'r') as f:
        sql = f.read()
        await conn.execute(sql)
    await conn.close()

asyncio.run(run_migration())
```

### 2. 安装依赖

确保已安装所需的 Python 包：

```bash
pip install aiohttp tqdm
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 3. 运行批量下载脚本

执行批量下载脚本，下载所有图片：

```bash
cd backend
python scripts/download_all_images.py
```

脚本功能：
- 从数据库读取所有有 `main_image` 的案例
- 批量下载图片到 `data/images/{case_id}/main_image.{ext}`
- 更新数据库中的 `main_image_local` 字段
- 显示下载进度和统计信息
- 支持断点续传（跳过已下载的图片）

### 4. 验证图片访问

启动后端服务后，可以通过以下 URL 访问图片：

```
http://localhost:8000/static/images/{case_id}/main_image.{ext}
```

例如：
```
http://localhost:8000/static/images/297041/main_image.png
```

### 5. 前端使用

前端代码无需修改，API 会自动返回本地图片 URL（如果已下载）或原始 URL（如果未下载）。

## 配置说明

在 `.env` 文件中可以配置以下参数：

```env
# 图片存储配置
IMAGE_STORAGE_DIR=data/images          # 图片存储目录
IMAGE_DOWNLOAD_CONCURRENCY=10         # 下载并发数
IMAGE_DOWNLOAD_TIMEOUT=30             # 下载超时时间（秒）
IMAGE_DOWNLOAD_RETRY=3                # 下载重试次数
IMAGE_STATIC_URL_PREFIX=/static/images # 静态文件 URL 前缀
```

## 存储空间

假设平均每张图片 400 KB：
- 6141 条记录 × 400 KB ≈ 2.4 GB

建议定期监控磁盘空间使用情况。

## 故障排查

### 图片下载失败

1. 检查网络连接
2. 检查广告门网站是否可访问
3. 查看日志文件 `download_images.log`

### 图片无法访问

1. 确认后端服务已启动
2. 检查 `data/images` 目录是否存在
3. 检查文件权限
4. 确认静态文件服务已正确配置

### 数据库字段未更新

1. 确认已执行数据库迁移脚本
2. 检查数据库连接配置
3. 查看脚本日志输出

## 增量更新

脚本支持增量更新，默认会跳过已下载的图片。如果需要重新下载所有图片，可以：

1. 删除 `data/images` 目录
2. 清空数据库中的 `main_image_local` 字段
3. 重新运行下载脚本

## 性能优化

- 调整 `IMAGE_DOWNLOAD_CONCURRENCY` 控制并发数（默认 10）
- 如果下载速度慢，可以适当增加并发数
- 如果遇到服务器拒绝，可以减少并发数

## 注意事项

1. 图片文件较大，建议使用 `.gitignore` 忽略 `data/images` 目录
2. 定期备份图片文件
3. 监控磁盘空间使用情况
4. 如果广告门修改防盗链策略，可能需要更新下载逻辑
