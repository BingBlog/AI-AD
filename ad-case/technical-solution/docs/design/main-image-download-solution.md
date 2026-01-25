# 案例主图下载与本地存储技术方案

## 1. 背景与问题

### 1.1 问题描述

在 `http://localhost:3000/cases` 页面直接展示 `main_image` 时，会被广告门（adquan.com）的服务拦截，导致图片无法正常加载。这是因为：

1. **防盗链机制**：广告门服务器检查 HTTP 请求的 `Referer` 头，只允许来自其自身域名的请求
2. **跨域限制**：直接在前端通过 `<img>` 标签加载外部图片时，浏览器会发送请求，但服务器可能拒绝非预期的来源

### 1.2 解决方案

将数据库中所有案例的 `main_image` 先下载到本地服务器，然后通过自己的服务提供图片访问，从而绕过广告门的防盗链限制。

## 2. 可行性测试

### 2.1 测试结果

已通过测试脚本 `scripts/test_image_download.py` 验证：

- ✅ **数据库统计**：
  - 总记录数：6141 条
  - 有 `main_image` 的记录数：6141 条（100% 覆盖率）

- ✅ **图片下载测试**：
  - 测试 URL: `https://oss.adquan.com/upload/20200628/159333611702b57de84188551c.png`
  - 下载状态：成功（HTTP 200）
  - Content-Type: `image/png`
  - 文件大小：400869 bytes（约 391 KB）

- ✅ **URL 模式分析**：
  - `oss.adquan.com`: 主要来源（约 90%）
  - `file.adquan.com`: 次要来源（约 10%）

### 2.2 下载策略

通过设置合适的 HTTP 请求头可以成功下载图片：

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://www.adquan.com/'
}
```

## 3. 技术方案设计

### 3.1 架构设计

```
┌─────────────┐
│  数据库      │
│  ad_cases    │───┐
│  main_image  │   │
└─────────────┘   │
                  │
                  ▼
         ┌────────────────┐
         │  图片下载服务    │
         │  (批量下载脚本)  │
         └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  本地存储目录    │
         │  /data/images/  │
         └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  FastAPI        │
         │  静态文件服务    │
         │  /static/images/│
         └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  前端应用       │
         │  <img src="...">│
         └────────────────┘
```

### 3.2 目录结构

```
backend/
├── data/
│   └── images/                    # 图片存储目录
│       ├── {case_id}/             # 按 case_id 分目录存储
│       │   └── main_image.{ext}   # 主图文件
│       └── .gitignore              # 忽略图片文件（不提交到 Git）
├── app/
│   ├── services/
│   │   └── image_service.py       # 图片服务（下载、存储、URL 生成）
│   └── routers/
│       └── images.py              # 图片访问路由（可选，或使用静态文件服务）
└── scripts/
    └── download_all_images.py     # 批量下载脚本
```

### 3.3 数据库设计

#### 方案 A：新增字段存储本地路径（推荐）

在 `ad_cases` 表中新增字段：

```sql
ALTER TABLE ad_cases 
ADD COLUMN main_image_local TEXT;  -- 本地图片路径，如: /static/images/297041/main_image.png
```

**优点**：
- 保留原始 URL（`main_image`），便于追溯和调试
- 新增字段不影响现有数据
- 可以逐步迁移，支持回滚

**缺点**：
- 需要修改数据库结构
- 需要更新现有代码逻辑

#### 方案 B：直接替换 main_image 字段

将 `main_image` 字段的值从外部 URL 替换为本地路径。

**优点**：
- 不需要新增字段
- 代码改动较小

**缺点**：
- 丢失原始 URL 信息
- 难以回滚
- 如果本地图片丢失，无法恢复

**推荐使用方案 A**。

### 3.4 文件命名规则

为了便于管理和避免文件名冲突，建议使用以下命名规则：

```
/data/images/{case_id}/main_image.{ext}
```

例如：
- `case_id=297041` → `/data/images/297041/main_image.png`
- `case_id=285001` → `/data/images/285001/main_image.jpg`

**优点**：
- 按 `case_id` 分目录，便于管理
- 文件名统一为 `main_image.{ext}`，便于查找
- 支持同一案例的多个图片（未来扩展）

### 3.5 图片格式处理

从 URL 或 HTTP 响应头确定图片格式：

1. **优先从 URL 提取**：`https://oss.adquan.com/upload/xxx.png` → `.png`
2. **从 Content-Type 判断**：`image/png` → `.png`
3. **默认格式**：如果无法确定，使用 `.jpg`

### 3.6 静态文件服务

使用 FastAPI 的 `StaticFiles` 提供图片访问：

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static/images", StaticFiles(directory="data/images"), name="images")
```

访问 URL 格式：
```
http://localhost:8000/static/images/297041/main_image.png
```

### 3.7 API 响应修改

修改案例查询接口，返回本地图片 URL：

```python
# 在 CaseRepository 中
if case.get('main_image_local'):
    case['main_image'] = f"/static/images/{case_id}/main_image.{ext}"
else:
    # 如果没有本地图片，返回原始 URL（向后兼容）
    case['main_image'] = case.get('main_image')
```

## 4. 实现步骤

### 4.1 阶段一：数据库迁移

1. 创建数据库迁移脚本，新增 `main_image_local` 字段
2. 验证字段创建成功

### 4.2 阶段二：图片下载服务

1. 创建 `app/services/image_service.py`：
   - `download_image(url, case_id)`: 下载单个图片
   - `save_image(image_data, case_id, ext)`: 保存图片到本地
   - `get_local_image_url(case_id, ext)`: 生成本地访问 URL
   - `is_image_downloaded(case_id)`: 检查图片是否已下载

2. 实现错误处理：
   - 网络超时重试（最多 3 次）
   - 无效 URL 跳过
   - 下载失败记录日志

### 4.3 阶段三：批量下载脚本

1. 创建 `scripts/download_all_images.py`：
   - 从数据库查询所有有 `main_image` 的记录
   - 批量下载（支持并发，控制并发数）
   - 更新数据库 `main_image_local` 字段
   - 进度显示和错误统计

2. 特性：
   - 支持断点续传（跳过已下载的图片）
   - 支持增量更新（只下载新增或缺失的图片）
   - 日志记录（成功/失败统计）

### 4.4 阶段四：静态文件服务

1. 在 `app/main.py` 中挂载静态文件服务
2. 配置 CORS（如果需要）
3. 测试图片访问

### 4.5 阶段五：API 修改

1. 修改 `CaseRepository`，返回本地图片 URL
2. 修改前端代码（如果需要）
3. 测试完整流程

## 5. 技术细节

### 5.1 并发控制

批量下载时，使用 `asyncio.Semaphore` 控制并发数，避免过多请求导致服务器拒绝：

```python
semaphore = asyncio.Semaphore(10)  # 最多 10 个并发请求

async def download_with_limit(url, case_id):
    async with semaphore:
        return await download_image(url, case_id)
```

### 5.2 错误处理

- **网络错误**：重试 3 次，每次间隔递增（1s, 2s, 4s）
- **HTTP 错误**：记录状态码和 URL，跳过
- **文件系统错误**：记录错误，继续处理下一个

### 5.3 性能优化

- **批量查询**：一次查询 1000 条记录，避免内存占用过大
- **异步下载**：使用 `aiohttp` 实现异步下载
- **进度显示**：使用 `tqdm` 显示下载进度

### 5.4 存储空间估算

假设平均每张图片 400 KB：
- 6141 条记录 × 400 KB ≈ 2.4 GB

建议：
- 定期清理无效图片
- 考虑图片压缩（如果质量要求不高）
- 监控磁盘空间

## 6. 配置项

在 `app/config.py` 中新增配置：

```python
# 图片存储配置
IMAGE_STORAGE_DIR: str = "data/images"  # 图片存储目录
IMAGE_DOWNLOAD_CONCURRENCY: int = 10    # 下载并发数
IMAGE_DOWNLOAD_TIMEOUT: int = 30        # 下载超时时间（秒）
IMAGE_DOWNLOAD_RETRY: int = 3           # 下载重试次数
IMAGE_STATIC_URL_PREFIX: str = "/static/images"  # 静态文件 URL 前缀
```

## 7. 测试计划

### 7.1 单元测试

- 测试图片下载功能
- 测试文件保存功能
- 测试 URL 生成功能

### 7.2 集成测试

- 测试批量下载脚本
- 测试静态文件服务
- 测试 API 返回的图片 URL

### 7.3 端到端测试

- 前端页面加载图片
- 验证图片正常显示
- 验证性能（加载速度）

## 8. 风险评估

### 8.1 技术风险

- **低风险**：图片下载失败（已有重试机制）
- **低风险**：存储空间不足（可监控和清理）
- **中风险**：广告门修改防盗链策略（可能性较低）

### 8.2 业务风险

- **低风险**：图片版权问题（仅用于内部展示）
- **低风险**：数据迁移时间较长（可分批进行）

## 9. 后续优化

1. **图片压缩**：下载后自动压缩，减少存储空间
2. **CDN 加速**：如果图片量大，考虑使用 CDN
3. **懒加载**：前端实现图片懒加载，提升页面性能
4. **缓存策略**：设置合适的 HTTP 缓存头
5. **图片格式优化**：转换为 WebP 格式（如果浏览器支持）

## 10. 总结

本方案通过将外部图片下载到本地服务器，解决了广告门防盗链导致的图片无法加载问题。方案经过可行性测试，技术实现简单，风险可控。建议采用**方案 A（新增字段）**，保留原始 URL 的同时支持本地图片访问。

### 关键点

1. ✅ **可行性已验证**：测试脚本成功下载图片
2. ✅ **数据完整**：100% 的记录都有 `main_image`
3. ✅ **实现简单**：使用 FastAPI 静态文件服务即可
4. ✅ **向后兼容**：保留原始 URL，支持回滚
5. ✅ **性能可控**：支持并发下载，可控制速度

### 下一步行动

1. 创建数据库迁移脚本
2. 实现图片下载服务
3. 创建批量下载脚本
4. 配置静态文件服务
5. 修改 API 返回逻辑
6. 测试完整流程
