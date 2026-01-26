# MediaCrawler API 集成方案分析

## 一、当前集成方式的问题分析

### 1.1 直接导入模块的问题

**当前方式**：通过 Python 路径直接导入 MediaCrawler 模块

**存在的问题**：

1. **依赖耦合严重**

   - MediaCrawler 有自己完整的依赖体系（requirements.txt）
   - 需要将 MediaCrawler 的所有依赖安装到 backend 虚拟环境
   - 依赖版本可能冲突（如 FastAPI、Pydantic 等）

2. **配置系统冲突**

   - MediaCrawler 有自己的配置系统（`config/base_config.py`）
   - 需要管理两套配置系统
   - 配置项可能重叠或冲突

3. **资源管理复杂**

   - MediaCrawler 使用 Playwright 浏览器自动化
   - 浏览器进程、Cookie、代理等资源需要独立管理
   - 与 backend 服务混在一起，资源隔离困难

4. **版本管理困难**

   - MediaCrawler 作为 Git 子目录，更新需要手动操作
   - 无法独立控制 MediaCrawler 的版本
   - 代码变更可能影响 backend 服务

5. **代码结构复杂**
   - 需要适配 MediaCrawler 的内部 API
   - MediaCrawler 的内部结构变化会影响集成代码
   - 维护成本高

## 二、API 服务集成方案的优势

### 2.1 架构优势

**解耦设计**：

- ✅ 通过 HTTP API 调用，完全解耦
- ✅ backend 不需要了解 MediaCrawler 的内部实现
- ✅ 只需要知道 API 接口规范

**独立部署**：

- ✅ MediaCrawler 可以作为独立服务运行
- ✅ 可以部署在不同的服务器或容器中
- ✅ 资源（CPU、内存、浏览器）完全隔离

**版本管理**：

- ✅ MediaCrawler 可以独立升级，不影响 backend
- ✅ 可以同时运行多个版本的 MediaCrawler（不同端口）
- ✅ 版本回滚简单

### 2.2 技术优势

**依赖隔离**：

- ✅ MediaCrawler 的依赖不会污染 backend 环境
- ✅ 避免依赖版本冲突
- ✅ 各自维护自己的虚拟环境

**配置隔离**：

- ✅ MediaCrawler 使用自己的配置文件
- ✅ backend 只需要配置 MediaCrawler API 的地址
- ✅ 配置变更互不影响

**资源管理**：

- ✅ 浏览器进程、Cookie、代理等资源由 MediaCrawler 独立管理
- ✅ backend 不需要关心浏览器资源
- ✅ 可以独立扩展 MediaCrawler 服务

### 2.3 运维优势

**可扩展性**：

- ✅ MediaCrawler 可以水平扩展（多个实例）
- ✅ 可以按平台分配不同的 MediaCrawler 实例
- ✅ 负载均衡更容易实现

**监控和日志**：

- ✅ MediaCrawler 的日志独立管理
- ✅ 可以独立监控 MediaCrawler 服务的健康状态
- ✅ 问题排查更容易定位

**容错性**：

- ✅ MediaCrawler 服务崩溃不影响 backend
- ✅ 可以实现重试机制
- ✅ 可以实现服务降级

## 三、MediaCrawler API 能力分析

### 3.1 现有 API 接口

根据代码分析，MediaCrawler 已经提供了完整的 API 服务：

**核心接口**：

- `POST /api/crawler/start` - 启动爬虫任务
- `POST /api/crawler/stop` - 停止爬虫任务
- `GET /api/crawler/status` - 获取爬虫状态
- `GET /api/crawler/logs` - 获取日志

**配置接口**：

- `GET /api/config/platforms` - 获取支持的平台列表
- `GET /api/config/options` - 获取配置选项

**数据接口**：

- `GET /api/data/files` - 获取数据文件列表
- `GET /api/data/download` - 下载数据文件

**WebSocket 支持**：

- 实时日志推送
- 状态更新推送

### 3.2 API 请求格式

```python
# 启动爬虫请求
POST /api/crawler/start
{
    "platform": "xhs",  # 平台：xhs, dy, ks, bili, wb, tieba, zhihu
    "login_type": "qrcode",  # 登录方式：qrcode, phone, cookie
    "crawler_type": "search",  # 爬取类型：search, detail, creator
    "keywords": "营销案例,品牌营销",  # 关键词（搜索模式）
    "specified_ids": "123,456",  # 指定ID列表（详情模式）
    "start_page": 1,
    "enable_comments": True,
    "save_option": "json",  # 保存格式：json, csv, excel, sqlite, db, mongodb
    "headless": False
}
```

### 3.3 数据获取方式

MediaCrawler 支持多种数据保存格式：

- JSON 文件（推荐，易于解析）
- CSV 文件
- Excel 文件
- SQLite 数据库
- MySQL 数据库
- MongoDB 数据库

**推荐方案**：使用 JSON 格式，backend 通过 API 下载 JSON 文件，然后导入到自己的数据库。

## 四、集成方案设计

### 4.1 架构设计

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │
│   (FastAPI)     │
│                 │
│  ┌───────────┐  │
│  │ Crawl    │  │
│  │ Task     │  │
│  │ Service  │  │
│  └────┬──────┘  │
│       │         │
│       │ HTTP    │
│       │ API     │
└───────┼─────────┘
        │
        ▼
┌─────────────────┐
│  MediaCrawler   │
│  API Service    │
│  (Port 8080)    │
│                 │
│  ┌───────────┐  │
│  │ Crawler   │  │
│  │ Manager   │  │
│  └────┬──────┘  │
│       │         │
│       ▼         │
│  ┌───────────┐  │
│  │ Playwright│  │
│  │ Browser   │  │
│  └───────────┘  │
└─────────────────┘
```

### 4.2 数据流程

1. **任务创建**：

   - Frontend → Backend：创建爬取任务
   - Backend → MediaCrawler API：启动爬虫任务
   - MediaCrawler：执行爬取，保存数据到 JSON 文件

2. **任务监控**：

   - Backend 定期轮询 MediaCrawler API 获取任务状态
   - 或使用 WebSocket 实时接收状态更新

3. **数据导入**：
   - Backend 通过 MediaCrawler API 获取数据文件列表
   - Backend 下载 JSON 文件
   - Backend 解析 JSON 并导入到自己的数据库

### 4.3 实现要点

**1. MediaCrawler 客户端封装**

创建 `MediaCrawlerClient` 类，封装所有 API 调用：

```python
class MediaCrawlerClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    async def start_crawler(self, config: CrawlerConfig) -> str:
        """启动爬虫任务，返回任务ID"""
        pass

    async def get_status(self, task_id: str) -> CrawlerStatus:
        """获取任务状态"""
        pass

    async def stop_crawler(self, task_id: str) -> bool:
        """停止爬虫任务"""
        pass

    async def get_data_files(self) -> List[DataFile]:
        """获取数据文件列表"""
        pass

    async def download_file(self, file_path: str) -> bytes:
        """下载数据文件"""
        pass
```

**2. 任务状态同步**

- Backend 维护任务状态映射（backend task_id → MediaCrawler task_id）
- 定期轮询或使用 WebSocket 同步状态

**3. 数据文件管理**

- MediaCrawler 保存数据到指定目录
- Backend 通过 API 获取文件列表
- Backend 下载并解析 JSON 文件
- 导入到自己的数据库

## 五、实施建议

### 5.1 推荐方案：API 服务集成 ✅

**理由**：

1. ✅ 完全解耦，架构清晰
2. ✅ 独立部署，资源隔离
3. ✅ 易于维护和扩展
4. ✅ MediaCrawler 已经提供了完整的 API
5. ✅ 符合微服务架构理念

### 5.2 实施步骤

1. **启动 MediaCrawler API 服务**

   ```bash
   cd MediaCrawler
   uv run uvicorn api.main:app --port 8080 --host 0.0.0.0
   ```

2. **创建 MediaCrawler 客户端**

   - 在 backend 中创建 `MediaCrawlerClient` 类
   - 封装所有 API 调用

3. **修改 CrawlTaskService**

   - 将直接调用改为通过 API 调用
   - 实现任务状态同步
   - 实现数据文件下载和导入

4. **配置管理**
   - 在 backend 配置文件中添加 MediaCrawler API 地址
   - 支持环境变量配置

### 5.3 注意事项

1. **API 版本管理**

   - MediaCrawler API 可能会更新
   - 需要版本兼容性处理

2. **错误处理**

   - MediaCrawler 服务不可用时的降级策略
   - 网络错误的重试机制

3. **性能优化**
   - 使用异步 HTTP 客户端（httpx）
   - 实现连接池
   - 考虑使用 WebSocket 减少轮询

## 六、总结

**结论**：通过 API 服务集成 MediaCrawler 是**更合理、更优雅**的方案。

**优势总结**：

- ✅ 架构解耦，易于维护
- ✅ 资源隔离，独立扩展
- ✅ 版本管理灵活
- ✅ 符合微服务架构
- ✅ MediaCrawler 已提供完整 API

**建议**：立即切换到 API 服务集成方案。
