# 小红书爬虫产品与技术实施方案

## 1. 产品方案

### 1.1 业务背景

#### 1.1.1 业务目标

- **数据源扩展**：从小红书平台采集广告营销行业相关的达人分享案例
- **数据质量提升**：补充广告案例知识库，提供更丰富的案例数据
- **业务价值**：为广告创意、营销策略提供参考和灵感

#### 1.1.2 业务需求

- 采集小红书平台上与广告营销相关的笔记内容
- 提取结构化信息：标题、内容、图片、互动数据、标签等
- 支持关键词搜索，精准采集相关案例
- 少量、分散采集，降低封禁风险
- 与现有案例知识库无缝集成

### 1.2 功能需求

#### 1.2.1 核心功能

**1. 任务管理功能**

- 创建小红书爬取任务
- 配置关键词、爬取数量、延迟参数
- 任务列表查看和管理
- 任务状态监控（运行中、已完成、失败等）
- 任务详情查看（进度、统计、日志）

**2. 数据采集功能**

- 关键词搜索采集
- 每个关键词限制爬取数量（10-20 条）
- 每日总爬取量控制（50-100 条）
- 自动频率控制（搜索间隔 5-10 分钟，详情页间隔 3-5 秒）
- 断点续传支持

**3. 数据管理功能**

- 数据格式统一（与广告门数据一致）
- 数据验证和清洗
- 数据导入到数据库
- 数据去重处理
- 数据质量评分

**4. 监控和告警**

- 实时进度监控
- 错误日志记录
- 封禁风险预警
- 采集统计报表

#### 1.2.2 非功能需求

- **性能要求**：单次任务爬取时间 < 2 小时（50-100 条数据）
- **稳定性要求**：任务成功率 > 95%
- **安全性要求**：遵守平台政策，降低封禁风险
- **可维护性**：代码结构清晰，易于维护和扩展

### 1.3 用户体验设计

#### 1.3.1 任务创建流程

1. **进入任务管理页面**

   - 点击"创建任务"按钮
   - 选择数据源为"小红书"

2. **配置任务参数**

   - 输入任务名称和描述
   - 输入关键词（支持多个，逗号分隔）
   - 设置每个关键词的爬取数量（默认 15 条）
   - 设置延迟参数（默认 3-5 秒）
   - 选择是否立即执行

3. **提交任务**
   - 系统验证参数
   - 创建任务记录
   - 如果选择立即执行，任务自动开始

#### 1.3.2 任务监控界面

- **任务列表**：显示所有任务的状态、进度、统计信息
- **任务详情**：查看任务完整信息、实时进度、日志
- **实时更新**：通过 WebSocket 实时推送任务进度

#### 1.3.3 数据查看

- 采集的数据通过现有的案例查看界面展示
- 支持按数据源筛选（广告门、小红书）
- 数据格式统一，用户体验一致

### 1.4 产品价值

1. **数据源丰富**：补充小红书平台的营销案例，丰富知识库内容
2. **精准采集**：通过关键词搜索，精准采集相关案例
3. **风险可控**：少量、分散采集策略，降低封禁风险
4. **无缝集成**：与现有系统完全集成，统一管理

## 2. 技术方案

### 2.1 技术选型

#### 2.1.1 核心技术栈

- **爬虫框架**：基于 MediaCrawler（开源项目）
- **浏览器自动化**：Playwright（MediaCrawler 使用）
- **编程语言**：Python 3.8+
- **异步框架**：asyncio
- **数据存储**：JSON 文件（爬取阶段）+ PostgreSQL（最终存储）

#### 2.1.2 技术方案选择

**方案：基于 MediaCrawler 封装适配层**

- 复用 MediaCrawler 的成熟功能
- 封装适配层，与现有系统集成
- 统一数据格式和任务管理

### 2.2 系统架构

#### 2.2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│           前端界面 (React + TypeScript)          │
│  - 任务创建界面                                  │
│  - 任务列表和监控                                │
│  - 数据查看界面                                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────────┐
│        后端 API (FastAPI)                        │
│  - 任务管理 API                                  │
│  - 数据查询 API                                  │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      任务执行层 (CrawlTaskExecutor)              │
│  - 任务调度和执行                                │
│  - 进度更新和日志记录                            │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      数据源适配层                                │
│  ├── AdquanCrawlStage (广告门)                  │
│  └── MediaCrawlerCrawlStage (统一适配层) ← 新增│
│      ├── 平台选择器                             │
│      ├── MediaCrawler 平台适配器                │
│      │   ├── XHSCollector (小红书)             │
│      │   ├── DouyinCollector (抖音)            │
│      │   └── BilibiliCollector (B站)           │
│      ├── BrowserManager (共享)                  │
│      └── 统一数据转换器                         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      数据管道 (Pipeline)                         │
│  ├── 爬取阶段 → JSON 文件                        │
│  └── 导入阶段 → PostgreSQL 数据库               │
└─────────────────────────────────────────────────┘
```

#### 2.2.2 核心组件设计

**1. MediaCrawler 适配层设计**

MediaCrawler 支持多个平台（小红书、抖音、B 站等），有两种集成方案：

**方案 A：业务层实现（每个平台独立适配层）**

```
数据源适配层
├── AdquanCrawlStage (广告门)
├── XiaohongshuCrawlStage (小红书) ← 独立适配层
│   └── MediaCrawler XHSCollector
├── DouyinCrawlStage (抖音) ← 独立适配层
│   └── MediaCrawler DouyinCollector
└── BilibiliCrawlStage (B站) ← 独立适配层
    └── MediaCrawler BilibiliCollector
```

**优点**：

- ✅ 每个平台独立实现，职责清晰
- ✅ 平台特定逻辑隔离，易于维护
- ✅ 可以针对不同平台优化
- ✅ 符合现有架构（每个数据源一个适配层）

**缺点**：

- ❌ 代码重复（每个适配层都有相似逻辑）
- ❌ 新增平台需要创建新的适配层

**方案 B：统一适配层（推荐）**

```
数据源适配层
├── AdquanCrawlStage (广告门)
└── MediaCrawlerCrawlStage (统一适配层) ← 支持多平台
    ├── 平台选择器 (根据 data_source 选择平台)
    ├── MediaCrawler 平台适配器
    │   ├── XHSCollector (小红书)
    │   ├── DouyinCollector (抖音)
    │   └── BilibiliCollector (B站)
    └── 统一数据转换器
```

**优点**：

- ✅ 代码复用，减少重复
- ✅ 统一的数据转换逻辑
- ✅ 新增平台只需扩展，无需新建适配层
- ✅ 统一的错误处理和日志记录

**缺点**：

- ❌ 适配层逻辑可能更复杂
- ❌ 需要处理不同平台的差异

**推荐方案：方案 B（统一适配层）**

基于以下考虑：

1. MediaCrawler 本身已经提供了统一的平台适配器接口
2. 不同平台的数据格式转换逻辑相似
3. 减少代码重复，提高可维护性
4. 符合 DRY（Don't Repeat Yourself）原则

**2. MediaCrawlerCrawlStage（统一适配层）**

- 实现与 `CrawlStage` 相同的接口
- 根据 `data_source` 选择对应的 MediaCrawler 平台适配器
- 统一处理数据格式转换
- 统一实现少量爬取控制

**3. MediaCrawler 平台适配器**

- 使用 MediaCrawler 的 `BrowserManager` 管理浏览器（共享）
- 根据平台选择对应的 Collector（XHSCollector、DouyinCollector 等）
- 复用 MediaCrawler 的反爬虫机制

**4. 统一数据转换层**

- 将不同平台的 MediaCrawler 数据格式转换为统一格式
- 平台特定的字段映射
- 统一的数据验证和清洗

### 2.3 详细设计

#### 2.3.1 适配层实现

**统一适配层设计**：

```python
class MediaCrawlerCrawlStage:
    """MediaCrawler 统一适配层，支持多平台"""

    # 平台映射表
    PLATFORM_MAPPING = {
        "xiaohongshu": {
            "collector": XHSCollector,
            "transformer": XHSDataTransformer,
            "config": XHSConfig
        },
        "douyin": {
            "collector": DouyinCollector,
            "transformer": DouyinDataTransformer,
            "config": DouyinConfig
        },
        "bilibili": {
            "collector": BilibiliCollector,
            "transformer": BilibiliDataTransformer,
            "config": BilibiliConfig
        }
    }

    def __init__(self, output_dir, batch_size, delay_range,
                 platform="xiaohongshu", ...):
        """
        初始化 MediaCrawler 适配层

        Args:
            platform: 平台名称（xiaohongshu, douyin, bilibili等）
        """
        self.platform = platform
        self.platform_config = self.PLATFORM_MAPPING[platform]

        # 初始化共享的浏览器管理器
        self.browser_manager = BrowserManager()

        # 初始化平台特定的采集器
        self.collector = self.platform_config["collector"](
            browser_manager=self.browser_manager
        )

        # 初始化平台特定的数据转换器
        self.data_transformer = self.platform_config["transformer"]()

    def crawl(self, keywords=None, max_items_per_keyword=15, ...):
        """
        执行爬取（统一接口）

        根据平台不同，参数含义可能不同：
        - 小红书：keywords 是关键词列表
        - 抖音：keywords 是关键词列表
        - B站：可能是视频ID列表或其他
        """
        # 1. 根据平台选择采集策略
        # 2. 调用对应平台的 MediaCrawler Collector
        # 3. 使用平台特定的数据转换器
        # 4. 保存到 JSON 文件
```

**平台特定实现**：

```python
class XHSDataTransformer:
    """小红书数据转换器"""

    def transform(self, raw_data):
        """将小红书数据转换为统一格式"""
        return {
            "title": raw_data["note_title"],
            "description": raw_data["note_desc"],
            "source_url": raw_data["note_url"],
            "source_platform": "xiaohongshu",
            # ... 其他字段映射
        }

class DouyinDataTransformer:
    """抖音数据转换器"""

    def transform(self, raw_data):
        """将抖音数据转换为统一格式"""
        return {
            "title": raw_data["aweme_title"],
            "description": raw_data["aweme_desc"],
            "source_url": raw_data["aweme_url"],
            "source_platform": "douyin",
            # ... 其他字段映射
        }
```

**关键方法**：

- `crawl()`: 主爬取方法，实现与 `CrawlStage` 相同的接口
- `_get_collector()`: 根据平台获取对应的 Collector
- `_get_transformer()`: 根据平台获取对应的数据转换器
- `_search_by_keyword()`: 按关键词搜索（平台通用）
- `_collect_items()`: 采集内容详情（平台通用）
- `_transform_data()`: 数据格式转换（调用平台特定的转换器）
- `_save_batch()`: 批量保存数据（通用）

#### 2.3.2 数据格式转换

**字段映射表**：

| 小红书字段   | 统一数据模型字段 | 转换说明             |
| ------------ | ---------------- | -------------------- |
| note_title   | title            | 直接映射             |
| note_desc    | description      | 直接映射             |
| note_url     | source_url       | 直接映射             |
| user_name    | brand_name       | 达人昵称映射为品牌名 |
| user_id      | -                | 存储在扩展字段       |
| images       | images           | JSON 数组格式        |
| likes        | -                | 存储在扩展字段       |
| comments     | -                | 存储在扩展字段       |
| collects     | favourite        | 直接映射             |
| publish_time | publish_time     | 时间格式转换         |
| tags         | tags             | JSON 数组格式        |
| -            | source_platform  | 设置为 "xiaohongshu" |

**数据转换流程**：

1. 从 MediaCrawler 获取原始数据
2. 字段映射和类型转换
3. 数据清洗（去除无效数据、格式化）
4. 数据验证（使用现有的 `CaseValidator`）
5. 输出统一格式

#### 2.3.3 少量爬取控制

**实现策略**：

- **关键词级别控制**：每个关键词最多爬取 `max_notes_per_keyword` 条（默认 15 条）
- **任务级别控制**：每日总爬取量不超过 `max_notes_per_day`（默认 100 条）
- **搜索间隔控制**：每个关键词搜索间隔 5-10 分钟（随机）
- **详情页间隔控制**：每个详情页访问间隔 3-5 秒（随机）

**实现代码逻辑**：

```python
def crawl(self, keywords, max_notes_per_keyword, max_notes_per_day):
    total_crawled = 0

    for keyword in keywords:
        if total_crawled >= max_notes_per_day:
            break

        # 搜索关键词
        search_results = self._search_by_keyword(keyword)

        # 限制每个关键词的数量
        notes_to_crawl = search_results[:max_notes_per_keyword]

        # 采集笔记
        for note in notes_to_crawl:
            if total_crawled >= max_notes_per_day:
                break

            data = self._collect_note(note)
            self._save_data(data)
            total_crawled += 1

            # 详情页间隔
            await asyncio.sleep(random.uniform(3, 5))

        # 搜索间隔
        await asyncio.sleep(random.uniform(300, 600))
```

#### 2.3.4 与现有系统集成

**任务执行器集成**：

```python
class CrawlTaskExecutor:
    def _execute_sync(self, data_source, ...):
        # 根据 data_source 选择爬虫
        if data_source in ["xiaohongshu", "douyin", "bilibili"]:
            # MediaCrawler 支持的平台，使用统一适配层
            crawl_stage = MediaCrawlerCrawlStage(
                platform=data_source,  # 传入平台名称
                ...
            )
        elif data_source == "adquan":
            # 广告门使用独立的爬虫
            crawl_stage = CrawlStage(...)
        else:
            raise ValueError(f"不支持的数据源: {data_source}")

        # 执行爬取（统一接口）
        stats = crawl_stage.crawl(...)
```

**平台扩展**：

当需要支持新平台时，只需：

1. 在 `PLATFORM_MAPPING` 中添加平台配置
2. 实现平台特定的数据转换器
3. 配置平台特定的参数

无需修改任务执行器和其他核心逻辑。

**数据管道复用**：

- 爬取阶段输出 JSON 文件，格式与广告门一致
- 导入阶段完全复用现有的 `ImportStage`
- 支持向量生成、图片下载等所有现有功能

### 2.4 技术实现要点

#### 2.4.1 MediaCrawler 集成

**依赖安装**：

```bash
# 安装 MediaCrawler（可能需要 fork 或锁定版本）
pip install git+https://github.com/NanmiCoder/MediaCrawler.git

# 或使用本地 fork 版本
pip install -e ./MediaCrawler
```

**核心组件使用**：

```python
from MediaCrawler import BrowserManager, XHSCollector

# 初始化浏览器管理器
browser_manager = BrowserManager(
    headless=True,
    proxy=proxy_config,
    cookie_file="cookies.json"
)

# 初始化采集器
collector = XHSCollector(browser_manager)

# 搜索关键词
results = await collector.search(keyword="营销案例", limit=15)
```

#### 2.4.2 反爬虫处理

**复用 MediaCrawler 的机制**：

- 浏览器指纹隐藏（stealth.js）
- Cookie 和会话管理
- 随机化请求间隔
- 模拟真实用户行为

**额外优化**：

- 搜索间隔控制（5-10 分钟）
- 详情页间隔控制（3-5 秒）
- 少量爬取策略（降低频率）

#### 2.4.3 错误处理

**错误类型和处理**：

- **网络错误**：重试机制，指数退避
- **验证码**：记录日志，暂停任务，人工处理
- **封禁检测**：检测封禁特征，自动停止任务
- **数据解析错误**：记录错误，跳过该条数据

**错误恢复**：

- 支持断点续传
- 失败任务可以重试
- 记录详细的错误日志

### 2.5 配置管理

#### 2.5.1 任务配置

**与现有任务配置的映射**：

```python
# 现有任务配置
{
    "data_source": "xiaohongshu",
    "search_value": "营销案例,品牌营销",  # 关键词
    "batch_size": 15,  # 每个关键词爬取数
    "delay_min": 3.0,  # 详情页最小延迟
    "delay_max": 5.0,  # 详情页最大延迟
}

# 转换为 MediaCrawler 配置
{
    "keywords": ["营销案例", "品牌营销"],
    "max_notes_per_keyword": 15,
    "detail_interval": (3.0, 5.0),
    "search_interval": (300, 600),  # 5-10分钟
    "max_notes_per_day": 100,
}
```

#### 2.5.2 MediaCrawler 配置

**配置文件示例**：

```yaml
# MediaCrawler 配置
browser:
  headless: true
  proxy_enabled: false
  cookie_file: "cookies/xiaohongshu.json"

xiaohongshu:
  mode: search
  search_interval: 300-600 # 秒
  detail_interval: 3-5 # 秒
  max_retries: 3

output:
  format: json
  dir: "data/json"
```

### 2.6 数据流程

#### 2.6.1 爬取流程

```
1. 创建任务
   ↓
2. 解析关键词列表
   ↓
3. 遍历关键词
   ├── 搜索关键词（MediaCrawler）
   ├── 获取搜索结果（限制数量）
   ├── 遍历笔记
   │   ├── 访问详情页（MediaCrawler）
   │   ├── 提取数据
   │   ├── 数据格式转换
   │   └── 保存到批次
   └── 等待搜索间隔
   ↓
4. 批量保存 JSON 文件
   ↓
5. 更新任务进度和统计
```

#### 2.6.2 数据导入流程

```
1. 读取 JSON 文件
   ↓
2. 数据验证（CaseValidator）
   ↓
3. 生成向量（BGE-large-zh）
   ↓
4. 下载图片（可选）
   ↓
5. 批量入库（PostgreSQL）
   ↓
6. 更新任务状态
```

## 3. 实施计划

### 3.1 开发阶段

#### 阶段一：环境准备和调研（3-5 天）

**任务清单**：

- [ ] 安装 MediaCrawler 依赖
- [ ] 研究 MediaCrawler 源码结构
- [ ] 理解关键组件的使用方式
- [ ] 测试 MediaCrawler 的基本功能
- [ ] 分析数据格式和接口

**交付物**：

- MediaCrawler 使用文档
- 数据格式分析报告
- 技术可行性验证报告

#### 阶段二：适配层开发（1-2 周）

**任务清单**：

- [ ] 创建 `MediaCrawlerCrawlStage` 统一适配层框架
- [ ] 实现平台选择机制（PLATFORM_MAPPING）
- [ ] 集成 MediaCrawler 的浏览器管理器（共享）
- [ ] 实现小红书平台支持（XHSCollector + XHSDataTransformer）
- [ ] 实现关键词搜索功能（平台通用）
- [ ] 实现少量爬取控制（平台通用）
- [ ] 实现数据格式转换（平台特定转换器）
- [ ] 实现 JSON 输出（通用）
- [ ] 实现断点续传（通用）
- [ ] 实现错误处理（通用）
- [ ] 预留其他平台扩展接口（抖音、B 站等）

**交付物**：

- `XiaohongshuCrawlStage` 类实现
- 单元测试
- 代码文档

#### 阶段三：系统集成（1 周）

**任务清单**：

- [ ] 在 `CrawlTaskExecutor` 中添加数据源判断
- [ ] 集成任务管理功能
- [ ] 集成进度更新和日志记录
- [ ] 测试任务创建和执行流程
- [ ] 测试数据格式和导入流程

**交付物**：

- 集成后的完整系统
- 集成测试报告

#### 阶段四：测试和优化（1 周）

**任务清单**：

- [ ] 功能测试
- [ ] 性能测试
- [ ] 稳定性测试
- [ ] 优化爬取策略
- [ ] 完善错误处理
- [ ] 文档编写

**交付物**：

- 测试报告
- 优化后的系统
- 使用文档

### 3.2 时间计划

| 阶段           | 时间       | 人员       |
| -------------- | ---------- | ---------- |
| 环境准备和调研 | 3-5 天     | 1 人       |
| 适配层开发     | 1-2 周     | 1-2 人     |
| 系统集成       | 1 周       | 1-2 人     |
| 测试和优化     | 1 周       | 1-2 人     |
| **总计**       | **3-4 周** | **1-2 人** |

### 3.3 资源需求

#### 3.3.1 人力资源

- **开发人员**：1-2 人，熟悉 Python、Playwright、异步编程
- **测试人员**：1 人，负责功能测试和集成测试

#### 3.3.2 技术资源

- **开发环境**：Python 3.8+、Playwright、MediaCrawler
- **测试环境**：独立的测试服务器
- **生产环境**：与现有系统共享

#### 3.3.3 其他资源

- **代理 IP**（可选）：如果需要代理轮换
- **Cookie 文件**：用于登录和会话保持

## 4. 风险评估与应对

### 4.1 技术风险

#### 4.1.1 MediaCrawler 版本更新风险

**风险**：MediaCrawler 更新可能导致 API 变化

**应对**：

- 锁定 MediaCrawler 版本
- 或 fork 项目自行维护
- 建立版本兼容性测试

#### 4.1.2 反爬虫机制升级风险

**风险**：小红书反爬虫机制升级，导致爬虫失效

**应对**：

- 复用 MediaCrawler 的成熟机制
- 采用少量、分散爬取策略
- 建立监控和告警机制
- 准备备用方案（浏览器插件等）

#### 4.1.3 数据格式变化风险

**风险**：小红书页面结构变化，导致数据提取失败

**应对**：

- 使用稳定的选择器
- 建立数据验证机制
- 记录错误日志，及时修复

### 4.2 业务风险

#### 4.2.1 封禁风险

**风险**：账号或 IP 被封禁

**应对**：

- 严格遵循少量爬取策略
- 控制请求频率
- 使用代理轮换（如需要）
- 多账号备份

#### 4.2.2 数据质量风险

**风险**：采集的数据质量不高

**应对**：

- 建立数据验证机制
- 设置质量阈值
- 人工审核低质量数据

### 4.3 合规风险

#### 4.3.1 法律风险

**风险**：可能违反平台政策或法律法规

**应对**：

- 遵守 robots.txt 和使用条款
- 仅采集公开数据
- 不进行数据二次传播
- 建立合规审查制度

## 5. 成功指标

### 5.1 功能指标

- ✅ 支持关键词搜索采集
- ✅ 支持少量爬取控制（单次 10-20 条，每日 50-100 条）
- ✅ 支持断点续传
- ✅ 数据格式统一，可正常导入数据库

### 5.2 性能指标

- 任务成功率 > 95%
- 单次任务爬取时间 < 2 小时（50-100 条数据）
- 数据完整率 > 90%

### 5.3 风险指标

- 封禁率 < 5%（目标：0%）
- 错误率 < 5%
- 数据质量评分 > 80 分

## 6. 后续优化方向

### 6.1 功能扩展

- 支持更多采集模式（指定笔记、创作者笔记）
- 支持图片和视频下载
- 支持评论数据采集

### 6.2 性能优化

- 优化爬取速度（在保证安全的前提下）
- 优化数据转换性能
- 支持并发爬取（多关键词并行）

### 6.3 智能化

- 智能关键词推荐
- 自动数据质量评分
- 智能去重和相似度检测

## 7. 附录

### 7.1 参考资料

- MediaCrawler 项目：https://github.com/NanmiCoder/MediaCrawler
- Playwright 文档：https://playwright.dev/python/
- 小红书爬虫调研文档：`xiaohongshu-crawler-research.md`

### 7.2 术语表

- **MediaCrawler**：开源的多平台媒体爬虫框架
- **适配层**：封装 MediaCrawler，与现有系统集成的中间层
- **少量爬取**：单次爬取少量数据，降低封禁风险的策略
- **关键词搜索**：通过关键词搜索获取相关笔记的采集方式

### 7.3 接口定义

#### 7.3.1 MediaCrawlerCrawlStage 接口

**类定义**：

```python
class MediaCrawlerCrawlStage:
    """MediaCrawler 统一适配层，支持多平台"""

    # 支持的平台列表
    SUPPORTED_PLATFORMS = ["xiaohongshu", "douyin", "bilibili"]

    def __init__(
        self,
        output_dir: Path,
        platform: str = "xiaohongshu",  # 平台名称
        batch_size: int = 15,
        resume_file: Optional[Path] = None,
        delay_range: tuple = (3, 5),
        enable_resume: bool = True,
        progress_callback: Optional[Callable[[], bool]] = None,
        task_id: Optional[str] = None
    ):
        """
        初始化 MediaCrawler 爬取阶段

        Args:
            output_dir: JSON文件输出目录
            platform: 平台名称（xiaohongshu, douyin, bilibili等）
            batch_size: 每批保存的案例数量
            resume_file: 断点续传文件路径
            delay_range: 详情页访问延迟范围（秒）
            enable_resume: 是否启用断点续传
            progress_callback: 进度回调函数
            task_id: 任务ID
        """
        if platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}")

        self.platform = platform
        # 根据平台初始化对应的组件
        ...

    def crawl(
        self,
        keywords: Optional[List[str]] = None,
        max_items_per_keyword: int = 15,
        max_items_per_day: int = 100,
        search_interval: tuple = (300, 600),
        skip_existing: bool = True,
        **platform_specific_params  # 平台特定参数
    ) -> Dict[str, Any]:
        """
        执行爬取任务（统一接口）

        Args:
            keywords: 关键词列表（适用于小红书、抖音等）
            max_items_per_keyword: 每个关键词最多爬取数量
            max_items_per_day: 每日最多爬取数量
            search_interval: 搜索间隔范围（秒）
            skip_existing: 是否跳过已爬取的案例
            **platform_specific_params: 平台特定参数
                - 小红书：无额外参数
                - 抖音：可能需要额外参数
                - B站：可能需要视频ID列表等

        Returns:
            爬取统计信息字典，包含：
            - total_crawled: 总爬取数
            - total_saved: 总保存数
            - total_failed: 总失败数
            - batches_saved: 已保存批次数
            - duration_seconds: 耗时（秒）
        """
        # 根据平台调用对应的采集逻辑
        ...

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
```

**平台特定转换器接口**：

```python
class BasePlatformTransformer:
    """平台数据转换器基类"""

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将平台原始数据转换为统一格式

        Args:
            raw_data: 平台原始数据

        Returns:
            统一格式的数据字典
        """
        raise NotImplementedError

class XHSDataTransformer(BasePlatformTransformer):
    """小红书数据转换器"""
    ...

class DouyinDataTransformer(BasePlatformTransformer):
    """抖音数据转换器"""
    ...
```

**接口兼容性**：

- 与现有 `CrawlStage` 保持相同的初始化参数（增加 `platform` 参数）
- `crawl()` 方法的参数设计为通用接口，支持平台特定参数扩展
- 返回格式与 `CrawlStage` 一致，确保兼容性
- 支持通过 `platform` 参数动态选择平台

#### 7.3.2 数据格式定义

**输入格式（任务配置）**：

```python
{
    "data_source": "xiaohongshu",
    "search_value": "营销案例,品牌营销,创意营销",  # 关键词，逗号分隔
    "batch_size": 15,  # 每个关键词爬取数
    "delay_min": 3.0,  # 详情页最小延迟
    "delay_max": 5.0,  # 详情页最大延迟
}
```

**输出格式（JSON 文件）**：

```json
{
  "task_id": "task_xxx",
  "batch_number": 0,
  "created_at": "2024-01-01T00:00:00",
  "cases": [
    {
      "title": "笔记标题",
      "description": "笔记内容",
      "source_url": "https://www.xiaohongshu.com/...",
      "source_platform": "xiaohongshu",
      "brand_name": "达人昵称",
      "images": ["url1", "url2"],
      "favourite": 100,
      "publish_time": "2024-01-01",
      "tags": ["标签1", "标签2"],
      "extended_data": {
        "user_id": "xxx",
        "likes": 200,
        "comments": 50
      }
    }
  ]
}
```

### 7.4 测试方案

#### 7.4.1 单元测试

**测试范围**：

- 数据格式转换功能
- 少量爬取控制逻辑
- 关键词解析功能
- 错误处理机制

**测试用例示例**：

```python
def test_data_transformation():
    """测试数据格式转换"""
    transformer = DataTransformer()
    xhs_data = {
        "note_title": "测试标题",
        "note_desc": "测试内容",
        "user_name": "测试用户"
    }
    result = transformer.transform(xhs_data)
    assert result["title"] == "测试标题"
    assert result["source_platform"] == "xiaohongshu"

def test_crawl_limit():
    """测试爬取数量限制"""
    stage = XiaohongshuCrawlStage(...)
    keywords = ["关键词1", "关键词2"]
    stats = stage.crawl(
        keywords=keywords,
        max_notes_per_keyword=5,
        max_notes_per_day=10
    )
    assert stats["total_crawled"] <= 10
```

#### 7.4.2 集成测试

**测试场景**：

1. **任务创建和执行**：

   - 创建小红书爬取任务
   - 验证任务参数解析
   - 验证任务执行流程

2. **数据采集**：

   - 验证关键词搜索功能
   - 验证数据采集功能
   - 验证数据格式转换

3. **数据导入**：
   - 验证 JSON 文件格式
   - 验证数据导入流程
   - 验证数据完整性

#### 7.4.3 性能测试

**测试指标**：

- 单次任务执行时间
- 内存使用情况
- CPU 使用情况
- 网络请求频率

**测试方法**：

- 使用少量关键词进行测试
- 监控资源使用情况
- 验证频率控制是否生效

#### 7.4.4 稳定性测试

**测试场景**：

- 长时间运行测试（24 小时）
- 网络异常测试
- 验证码处理测试
- 封禁检测测试

### 7.5 部署方案

#### 7.5.1 环境准备

**依赖安装**：

```bash
# 1. 安装 MediaCrawler
pip install git+https://github.com/NanmiCoder/MediaCrawler.git

# 或使用本地版本
cd MediaCrawler
pip install -e .

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 安装项目依赖
pip install -r requirements.txt
```

**环境变量配置**：

```bash
# .env 文件
# MediaCrawler 配置
MEDIACRAWLER_COOKIE_FILE=./cookies/xiaohongshu.json
MEDIACRAWLER_PROXY_ENABLED=false

# 小红书爬虫配置
XHS_MAX_NOTES_PER_KEYWORD=15
XHS_MAX_NOTES_PER_DAY=100
XHS_SEARCH_INTERVAL_MIN=300
XHS_SEARCH_INTERVAL_MAX=600
```

#### 7.5.2 代码部署

**目录结构**：

```
backend/
├── services/
│   ├── pipeline/
│   │   ├── crawl_stage.py  # 现有广告门爬虫
│   │   └── xiaohongshu_crawl_stage.py  # 新增小红书爬虫
│   └── spider/
│       └── xiaohongshu/
│           ├── __init__.py
│           ├── data_transformer.py  # 数据转换
│           └── config.py  # 配置管理
```

**部署步骤**：

1. 将代码部署到服务器
2. 安装依赖
3. 配置环境变量
4. 准备 Cookie 文件（如需要）
5. 测试功能

#### 7.5.3 监控配置

**日志监控**：

- 任务执行日志
- 错误日志
- 性能日志

**告警配置**：

- 任务失败告警
- 封禁风险告警
- 性能异常告警

### 7.6 维护方案

#### 7.6.1 日常维护

**定期检查**：

- 检查任务执行情况
- 检查数据质量
- 检查错误日志
- 检查封禁情况

**维护频率**：

- 每日检查任务执行情况
- 每周检查数据质量
- 每月检查系统性能

#### 7.6.2 版本更新

**MediaCrawler 更新**：

- 关注 MediaCrawler 版本更新
- 评估更新影响
- 测试新版本兼容性
- 逐步升级

**适配层更新**：

- 根据业务需求更新
- 优化性能和稳定性
- 修复 bug

#### 7.6.3 问题处理

**常见问题**：

1. **爬取失败**：

   - 检查网络连接
   - 检查 Cookie 是否有效
   - 检查反爬虫机制是否升级

2. **数据格式错误**：

   - 检查数据转换逻辑
   - 检查字段映射
   - 检查数据验证规则

3. **封禁问题**：
   - 降低爬取频率
   - 更换 IP 或账号
   - 调整爬取策略

## 8. 多平台支持架构设计

### 8.1 问题分析

MediaCrawler 支持多个平台（小红书、抖音、B 站等），需要确定多平台支持的实现方式：

**问题**：多平台支持是在业务层实现（每个平台一个适配层），还是构建统一功能让 MediaCrawler 同时完成跨平台爬取？

### 8.2 方案对比

#### 8.2.1 方案 A：业务层实现（每个平台独立适配层）

**架构**：

```
数据源适配层
├── AdquanCrawlStage (广告门)
├── XiaohongshuCrawlStage (小红书)
│   └── MediaCrawler XHSCollector
├── DouyinCrawlStage (抖音)
│   └── MediaCrawler DouyinCollector
└── BilibiliCrawlStage (B站)
    └── MediaCrawler BilibiliCollector
```

**优点**：

- ✅ 每个平台独立实现，职责清晰
- ✅ 平台特定逻辑隔离，易于维护
- ✅ 可以针对不同平台优化

**缺点**：

- ❌ 代码重复（每个适配层都有相似逻辑）
- ❌ 新增平台需要创建新的适配层
- ❌ 维护成本高

#### 8.2.2 方案 B：统一适配层（推荐）

**架构**：

```
数据源适配层
├── AdquanCrawlStage (广告门)
└── MediaCrawlerCrawlStage (统一适配层)
    ├── 平台选择器 (根据 data_source 选择平台)
    ├── MediaCrawler 平台适配器
    │   ├── XHSCollector (小红书)
    │   ├── DouyinCollector (抖音)
    │   └── BilibiliCollector (B站)
    ├── BrowserManager (共享)
    └── 统一数据转换器
        ├── XHSDataTransformer
        ├── DouyinDataTransformer
        └── BilibiliDataTransformer
```

**优点**：

- ✅ 代码复用，减少重复
- ✅ 统一的数据转换逻辑
- ✅ 新增平台只需扩展，无需新建适配层
- ✅ 统一的错误处理和日志记录
- ✅ 共享浏览器管理器，资源利用更高效

**缺点**：

- ❌ 适配层逻辑可能更复杂
- ❌ 需要处理不同平台的差异

### 8.3 推荐方案：统一适配层

#### 8.3.1 设计原则

1. **统一接口**：所有 MediaCrawler 平台使用同一个适配层类
2. **平台隔离**：平台特定的逻辑通过转换器和配置隔离
3. **共享资源**：浏览器管理器等资源在平台间共享
4. **易于扩展**：新增平台只需添加配置和转换器

#### 8.3.2 实现方式

**核心类设计**：

```python
class MediaCrawlerCrawlStage:
    """MediaCrawler 统一适配层，支持多平台"""

    # 平台映射配置
    PLATFORM_MAPPING = {
        "xiaohongshu": {
            "collector": XHSCollector,
            "transformer": XHSDataTransformer,
            "config": XHSConfig
        },
        "douyin": {
            "collector": DouyinCollector,
            "transformer": DouyinDataTransformer,
            "config": DouyinConfig
        },
        "bilibili": {
            "collector": BilibiliCollector,
            "transformer": BilibiliDataTransformer,
            "config": BilibiliConfig
        }
    }

    def __init__(self, platform="xiaohongshu", ...):
        """根据 platform 参数初始化对应平台"""
        self.platform = platform
        config = self.PLATFORM_MAPPING[platform]

        # 共享的浏览器管理器
        self.browser_manager = BrowserManager()

        # 平台特定的采集器
        self.collector = config["collector"](self.browser_manager)

        # 平台特定的数据转换器
        self.transformer = config["transformer"]()
```

**任务执行器集成**：

```python
class CrawlTaskExecutor:
    def _execute_sync(self, data_source, ...):
        # MediaCrawler 支持的平台统一处理
        if data_source in ["xiaohongshu", "douyin", "bilibili"]:
            crawl_stage = MediaCrawlerCrawlStage(
                platform=data_source,  # 传入平台名称
                ...
            )
        elif data_source == "adquan":
            crawl_stage = CrawlStage(...)  # 广告门独立实现
```

#### 8.3.3 平台扩展流程

**添加新平台（以抖音为例）**：

1. **在 PLATFORM_MAPPING 中添加配置**：

```python
PLATFORM_MAPPING["douyin"] = {
    "collector": DouyinCollector,
    "transformer": DouyinDataTransformer,
    "config": DouyinConfig
}
```

2. **实现数据转换器**：

```python
class DouyinDataTransformer(BasePlatformTransformer):
    def transform(self, raw_data):
        return {
            "title": raw_data["aweme_title"],
            "source_platform": "douyin",
            # ... 字段映射
        }
```

3. **测试验证**：创建测试任务验证功能

**无需修改**：

- `MediaCrawlerCrawlStage` 核心逻辑
- `CrawlTaskExecutor` 任务执行器
- 数据管道和导入流程

### 8.4 跨平台爬取场景

#### 8.4.1 场景一：单任务单平台（当前方案）

- 一个任务只爬取一个平台
- 通过 `data_source` 指定平台（如 "xiaohongshu"、"douyin"）
- 适合当前业务需求

#### 8.4.2 场景二：单任务多平台（未来扩展）

如果需要在一个任务中同时爬取多个平台：

**实现方式**：

```python
# 任务配置
{
    "data_source": "mediacrawler_multi",  # 多平台标识
    "platforms": ["xiaohongshu", "douyin"],  # 平台列表
    "keywords": ["营销案例"],
    ...
}

# 在 MediaCrawlerCrawlStage 中扩展
def crawl_multiple_platforms(self, platforms, keywords, ...):
    """跨平台爬取"""
    all_results = []
    for platform in platforms:
        # 为每个平台创建子任务或顺序执行
        results = self._crawl_single_platform(platform, keywords, ...)
        all_results.extend(results)
    return all_results
```

**推荐**：当前阶段采用场景一（单任务单平台），未来如需跨平台爬取，可以在统一适配层中扩展支持。

### 8.7 跨平台爬取实现方案

#### 8.7.1 需求场景

**业务场景**：

- 用户希望一次任务同时从多个平台（小红书、抖音、B 站）采集相同关键词的内容
- 对比不同平台的营销案例
- 提高数据采集效率

**实现目标**：

- 支持在一个任务中指定多个平台
- 每个平台使用相同的关键词进行搜索
- 统一的数据格式和导入流程
- 统一的进度监控和日志记录

#### 8.7.2 架构设计

**扩展后的架构**：

```
任务配置
├── data_source: "mediacrawler_multi"  # 多平台标识
├── platforms: ["xiaohongshu", "douyin", "bilibili"]  # 平台列表
└── keywords: ["营销案例"]  # 关键词（所有平台共享）

MediaCrawlerCrawlStage
├── 平台列表解析
├── 并行/串行执行策略
└── 结果合并
    ├── 平台1结果
    ├── 平台2结果
    └── 平台3结果
    ↓
统一数据格式
    ↓
JSON文件输出
```

#### 8.7.3 实现方案

**方案 A：串行执行（推荐，降低风险）**

```python
class MediaCrawlerCrawlStage:
    """支持单平台和多平台爬取"""

    def crawl(
        self,
        platforms: Union[str, List[str]],  # 支持单个平台或平台列表
        keywords: List[str],
        max_items_per_keyword: int = 15,
        max_items_per_day: int = 100,
        execution_mode: str = "sequential",  # sequential 或 parallel
        ...
    ) -> Dict[str, Any]:
        """
        执行爬取任务

        Args:
            platforms: 平台名称（字符串）或平台列表（多平台）
            keywords: 关键词列表
            execution_mode: 执行模式
                - "sequential": 串行执行（推荐，降低封禁风险）
                - "parallel": 并行执行（提高效率，但风险较高）
        """
        # 统一为列表格式
        if isinstance(platforms, str):
            platforms = [platforms]

        all_results = []
        total_stats = {
            "total_crawled": 0,
            "total_saved": 0,
            "total_failed": 0,
            "batches_saved": 0,
            "platform_stats": {}  # 每个平台的统计
        }

        # 串行执行每个平台
        for platform in platforms:
            logger.info(f"开始爬取平台: {platform}")

            # 为每个平台创建子适配器
            platform_stage = self._create_platform_stage(platform)

            # 执行平台爬取
            platform_stats = platform_stage.crawl(
                keywords=keywords,
                max_items_per_keyword=max_items_per_keyword,
                max_items_per_day=max_items_per_day // len(platforms),  # 平均分配
                ...
            )

            # 合并结果
            all_results.extend(platform_stats.get("results", []))
            total_stats["total_crawled"] += platform_stats["total_crawled"]
            total_stats["total_saved"] += platform_stats["total_saved"]
            total_stats["total_failed"] += platform_stats["total_failed"]
            total_stats["platform_stats"][platform] = platform_stats

            # 平台间间隔（降低风险）
            if platform != platforms[-1]:  # 不是最后一个平台
                await asyncio.sleep(random.uniform(60, 120))  # 1-2分钟间隔

        # 保存合并后的结果
        self._save_batch(all_results, batch_num)

        return total_stats
```

**方案 B：并行执行（可选，提高效率）**

```python
async def crawl_parallel(
    self,
    platforms: List[str],
    keywords: List[str],
    ...
) -> Dict[str, Any]:
    """并行执行多平台爬取"""
    import asyncio

    # 创建平台任务
    tasks = []
    for platform in platforms:
        platform_stage = self._create_platform_stage(platform)
        task = asyncio.create_task(
            platform_stage.crawl_async(keywords=keywords, ...)
        )
        tasks.append((platform, task))

    # 等待所有任务完成
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    # 合并结果
    all_results = []
    for (platform, _), result in zip(tasks, results):
        if isinstance(result, Exception):
            logger.error(f"平台 {platform} 爬取失败: {result}")
            continue
        all_results.extend(result.get("results", []))

    return self._merge_results(results)
```

**推荐方案 A（串行执行）**：

- 降低封禁风险（不同平台串行执行，避免同时大量请求）
- 资源消耗可控（不会同时启动多个浏览器实例）
- 错误处理简单（一个平台失败不影响其他平台）
- 进度监控清晰（可以分别监控每个平台的进度）

#### 8.7.4 任务配置扩展

**单平台任务配置（现有）**：

```python
{
    "data_source": "xiaohongshu",  # 单个平台
    "search_value": "营销案例",
    "batch_size": 15,
    ...
}
```

**多平台任务配置（扩展）**：

```python
{
    "data_source": "mediacrawler_multi",  # 多平台标识
    "platforms": ["xiaohongshu", "douyin", "bilibili"],  # 平台列表
    "search_value": "营销案例",  # 所有平台共享关键词
    "batch_size": 15,  # 每个平台每个关键词的爬取数
    "max_items_per_day": 150,  # 总爬取量（平均分配到各平台）
    "execution_mode": "sequential",  # 执行模式
    ...
}
```

**任务模型扩展**：

```python
# 在 CrawlTask 模型中添加字段
class CrawlTask:
    data_source: str  # "xiaohongshu" 或 "mediacrawler_multi"
    platforms: Optional[List[str]] = None  # 多平台列表（当 data_source="mediacrawler_multi" 时使用）
    execution_mode: str = "sequential"  # sequential 或 parallel
```

#### 8.7.5 数据合并策略

**数据去重**：

- 不同平台可能返回相同内容（如跨平台发布的案例）
- 基于 `source_url` 或内容相似度去重
- 保留所有平台的数据，但标记为重复

**数据标识**：

```json
{
    "title": "营销案例",
    "source_url": "https://...",
    "source_platform": "xiaohongshu",  # 原始平台
    "collected_from": ["xiaohongshu", "douyin"],  # 从哪些平台采集到
    "duplicate_sources": ["douyin"]  # 如果其他平台也有相同内容
}
```

**批次保存**：

- 可以按平台分别保存批次文件
- 也可以合并保存到一个批次文件
- 推荐：合并保存，但记录平台来源

#### 8.7.6 进度监控

**多平台进度跟踪**：

```python
{
    "total_progress": {
        "total_crawled": 45,
        "total_saved": 40,
        "total_failed": 5
    },
    "platform_progress": {
        "xiaohongshu": {
            "status": "completed",
            "crawled": 15,
            "saved": 15,
            "failed": 0
        },
        "douyin": {
            "status": "running",
            "crawled": 15,
            "saved": 12,
            "failed": 3
        },
        "bilibili": {
            "status": "pending",
            "crawled": 0,
            "saved": 0,
            "failed": 0
        }
    }
}
```

**日志记录**：

- 每个平台的日志独立记录
- 统一的任务日志包含所有平台
- 支持按平台筛选日志

#### 8.7.7 实施步骤

**阶段一：基础扩展（1 周）**

1. 扩展 `MediaCrawlerCrawlStage` 支持平台列表参数
2. 实现串行执行逻辑
3. 实现结果合并
4. 扩展任务配置模型

**阶段二：功能完善（1 周）**

1. 实现多平台进度监控
2. 实现数据去重逻辑
3. 完善错误处理（一个平台失败不影响其他）
4. 优化平台间间隔控制

**阶段三：测试验证（3-5 天）**

1. 测试多平台任务创建和执行
2. 测试数据合并和去重
3. 测试进度监控和日志记录
4. 性能测试

#### 8.7.8 注意事项

1. **封禁风险控制**：

   - 平台间执行间隔（1-2 分钟）
   - 每个平台的爬取量平均分配
   - 严格遵循少量爬取策略

2. **资源管理**：

   - 串行执行避免同时启动多个浏览器
   - 及时释放浏览器资源
   - 控制内存和 CPU 使用

3. **错误处理**：

   - 一个平台失败不应影响其他平台
   - 记录详细的错误信息
   - 支持部分成功（部分平台成功）

4. **数据一致性**：
   - 确保不同平台的数据格式统一
   - 正确处理平台特定的字段差异
   - 数据去重策略要合理

### 8.5 平台差异处理

#### 8.5.1 采集方式差异

- **小红书**：关键词搜索、指定笔记、创作者笔记
- **抖音**：关键词搜索、视频 ID、用户 ID
- **B 站**：视频 ID、UP 主 ID、关键词搜索

**处理方式**：通过平台特定的 Collector 处理，MediaCrawler 已提供平台特定的采集器。

#### 8.5.2 数据格式差异

- 字段名称不同
- 数据结构不同
- 数据类型不同

**处理方式**：通过平台特定的 Transformer 处理，每个平台实现自己的数据转换逻辑。

#### 8.5.3 反爬虫机制差异

- 不同平台的反爬虫策略不同
- MediaCrawler 已处理平台特定的反爬虫机制

**处理方式**：MediaCrawler 已处理，无需额外处理。

### 8.6 总结

**推荐方案**：使用统一适配层（`MediaCrawlerCrawlStage`）支持所有 MediaCrawler 平台。

**核心优势**：

1. 代码复用，减少重复
2. 易于扩展，新增平台成本低
3. 统一管理，维护成本低
4. 资源共享，效率更高

**实施建议**：

1. 第一阶段：实现小红书平台支持
2. 第二阶段：扩展支持抖音、B 站等其他平台
3. 第三阶段：如需跨平台爬取，扩展多平台支持

### 8.7 跨平台爬取实现方案

#### 8.7.1 需求场景

**业务场景**：

- 用户希望一次任务同时从多个平台（小红书、抖音、B 站）采集相同关键词的内容
- 对比不同平台的营销案例
- 提高数据采集效率

**实现目标**：

- 支持在一个任务中指定多个平台
- 每个平台使用相同的关键词进行搜索
- 统一的数据格式和导入流程
- 统一的进度监控和日志记录

#### 8.7.2 架构设计

**扩展后的架构**：

```
任务配置
├── data_source: "mediacrawler_multi"  # 多平台标识
├── platforms: ["xiaohongshu", "douyin", "bilibili"]  # 平台列表
└── keywords: ["营销案例"]  # 关键词（所有平台共享）

MediaCrawlerCrawlStage
├── 平台列表解析
├── 串行执行策略（推荐）
└── 结果合并
    ├── 平台1结果
    ├── 平台2结果
    └── 平台3结果
    ↓
统一数据格式
    ↓
JSON文件输出
```

#### 8.7.3 实现方案

**核心实现**：

```python
class MediaCrawlerCrawlStage:
    """支持单平台和多平台爬取"""

    def crawl(
        self,
        platform: Union[str, List[str]],  # 支持单个平台或平台列表
        keywords: List[str],
        max_items_per_keyword: int = 15,
        max_items_per_day: int = 100,
        execution_mode: str = "sequential",  # sequential 或 parallel
        ...
    ) -> Dict[str, Any]:
        """
        执行爬取任务

        Args:
            platform: 平台名称（字符串）或平台列表（多平台）
            keywords: 关键词列表
            execution_mode: 执行模式
                - "sequential": 串行执行（推荐，降低封禁风险）
                - "parallel": 并行执行（提高效率，但风险较高）
        """
        # 统一为列表格式
        if isinstance(platform, str):
            platforms = [platform]
        else:
            platforms = platform

        # 单平台执行
        if len(platforms) == 1:
            return self._crawl_single_platform(platforms[0], keywords, ...)

        # 多平台执行
        if execution_mode == "sequential":
            return self._crawl_multiple_platforms_sequential(platforms, keywords, ...)
        else:
            return self._crawl_multiple_platforms_parallel(platforms, keywords, ...)

    def _crawl_multiple_platforms_sequential(
        self,
        platforms: List[str],
        keywords: List[str],
        max_items_per_keyword: int,
        max_items_per_day: int,
        ...
    ) -> Dict[str, Any]:
        """串行执行多平台爬取（推荐）"""
        all_results = []
        total_stats = {
            "total_crawled": 0,
            "total_saved": 0,
            "total_failed": 0,
            "batches_saved": 0,
            "platform_stats": {}  # 每个平台的统计
        }

        # 平均分配每日爬取量
        items_per_platform = max_items_per_day // len(platforms)

        # 串行执行每个平台
        for idx, platform in enumerate(platforms):
            logger.info(f"[{idx+1}/{len(platforms)}] 开始爬取平台: {platform}")

            try:
                # 为每个平台创建子适配器
                platform_stage = self._create_platform_stage(platform)

                # 执行平台爬取
                platform_stats = platform_stage.crawl(
                    keywords=keywords,
                    max_items_per_keyword=max_items_per_keyword,
                    max_items_per_day=items_per_platform,
                    ...
                )

                # 合并结果
                platform_results = platform_stats.get("results", [])
                all_results.extend(platform_results)

                # 更新统计
                total_stats["total_crawled"] += platform_stats["total_crawled"]
                total_stats["total_saved"] += platform_stats["total_saved"]
                total_stats["total_failed"] += platform_stats["total_failed"]
                total_stats["platform_stats"][platform] = platform_stats

                logger.info(f"平台 {platform} 爬取完成: "
                          f"爬取 {platform_stats['total_crawled']} 条, "
                          f"成功 {platform_stats['total_saved']} 条")

            except Exception as e:
                logger.error(f"平台 {platform} 爬取失败: {e}")
                total_stats["platform_stats"][platform] = {
                    "status": "failed",
                    "error": str(e),
                    "total_crawled": 0,
                    "total_saved": 0,
                    "total_failed": 0
                }

            # 平台间间隔（降低风险）
            if idx < len(platforms) - 1:  # 不是最后一个平台
                wait_time = random.uniform(60, 120)  # 1-2分钟间隔
                logger.info(f"等待 {wait_time:.1f} 秒后继续下一个平台...")
                time.sleep(wait_time)

        # 保存合并后的结果
        if all_results:
            batch_num = get_next_batch_number(self.output_dir)
            self._save_batch(all_results, batch_num)
            total_stats["batches_saved"] = 1

        return total_stats
```

#### 8.7.4 任务配置扩展

**任务模型扩展**：

```python
# 在 CrawlTask 模型中添加字段
class CrawlTask:
    data_source: str  # "xiaohongshu" 或 "mediacrawler_multi"
    platforms: Optional[List[str]] = None  # 多平台列表
    execution_mode: str = "sequential"  # sequential 或 parallel
```

**任务配置示例**：

```python
# 单平台任务（现有）
{
    "data_source": "xiaohongshu",
    "search_value": "营销案例",
    "batch_size": 15,
    ...
}

# 多平台任务（扩展）
{
    "data_source": "mediacrawler_multi",
    "platforms": ["xiaohongshu", "douyin", "bilibili"],
    "search_value": "营销案例",
    "batch_size": 15,  # 每个平台每个关键词的爬取数
    "max_items_per_day": 150,  # 总爬取量（平均分配到各平台）
    "execution_mode": "sequential",
    ...
}
```

**任务执行器集成**：

```python
class CrawlTaskExecutor:
    def _execute_sync(self, data_source, platforms=None, ...):
        # 判断是否为多平台任务
        if data_source == "mediacrawler_multi":
            if not platforms:
                raise ValueError("多平台任务必须指定 platforms 参数")

            crawl_stage = MediaCrawlerCrawlStage(
                platform=platforms,  # 传入平台列表
                execution_mode=execution_mode or "sequential",
                ...
            )
        elif data_source in ["xiaohongshu", "douyin", "bilibili"]:
            # 单平台任务
            crawl_stage = MediaCrawlerCrawlStage(
                platform=data_source,  # 单个平台
                ...
            )
        elif data_source == "adquan":
            crawl_stage = CrawlStage(...)  # 广告门独立实现

        # 执行爬取（统一接口）
        stats = crawl_stage.crawl(...)
```

#### 8.7.5 数据合并和去重

**数据去重策略**：

```python
def _merge_and_deduplicate(self, all_results: List[Dict]) -> List[Dict]:
    """合并结果并去重"""
    seen_urls = set()
    seen_titles = set()
    merged_results = []

    for result in all_results:
        url = result.get("source_url")
        title = result.get("title")

        # 基于 URL 去重（最准确）
        if url and url in seen_urls:
            # 标记为重复，但记录来源平台
            existing = next(r for r in merged_results if r.get("source_url") == url)
            if "collected_from" not in existing:
                existing["collected_from"] = [existing.get("source_platform")]
            if result.get("source_platform") not in existing["collected_from"]:
                existing["collected_from"].append(result.get("source_platform"))
            continue

        # 基于标题相似度去重（可选，用于跨平台相同内容）
        if title and self._is_similar_title(title, seen_titles):
            # 相似标题，标记但保留
            result["possible_duplicate"] = True

        seen_urls.add(url)
        seen_titles.add(title)
        merged_results.append(result)

    return merged_results
```

**数据标识**：

```json
{
    "title": "营销案例",
    "source_url": "https://...",
    "source_platform": "xiaohongshu",  # 原始平台
    "collected_from": ["xiaohongshu", "douyin"],  # 从哪些平台采集到
    "possible_duplicate": false  # 是否可能是重复内容
}
```

#### 8.7.6 进度监控

**多平台进度跟踪**：

```python
{
    "total_progress": {
        "total_crawled": 45,
        "total_saved": 40,
        "total_failed": 5,
        "current_platform": "douyin",
        "platform_index": 2,
        "total_platforms": 3
    },
    "platform_progress": {
        "xiaohongshu": {
            "status": "completed",
            "crawled": 15,
            "saved": 15,
            "failed": 0,
            "duration_seconds": 1200
        },
        "douyin": {
            "status": "running",
            "crawled": 15,
            "saved": 12,
            "failed": 3,
            "duration_seconds": 800
        },
        "bilibili": {
            "status": "pending",
            "crawled": 0,
            "saved": 0,
            "failed": 0
        }
    }
}
```

**实时更新**：

- 每个平台完成后更新该平台的进度
- 总体进度实时计算
- 通过 WebSocket 实时推送进度更新

#### 8.7.7 实施步骤

**阶段一：基础扩展（1 周）**

1. 扩展 `MediaCrawlerCrawlStage` 支持平台列表参数
2. 实现串行执行逻辑
3. 实现结果合并和去重
4. 扩展任务配置模型（添加 `platforms` 字段）

**阶段二：功能完善（1 周）**

1. 实现多平台进度监控
2. 完善数据去重逻辑
3. 完善错误处理（一个平台失败不影响其他）
4. 优化平台间间隔控制
5. 前端界面支持多平台任务创建

**阶段三：测试验证（3-5 天）**

1. 测试多平台任务创建和执行
2. 测试数据合并和去重
3. 测试进度监控和日志记录
4. 性能测试和稳定性测试

#### 8.7.8 注意事项

1. **封禁风险控制**：

   - 平台间执行间隔（1-2 分钟）
   - 每个平台的爬取量平均分配
   - 严格遵循少量爬取策略
   - 串行执行降低并发风险

2. **资源管理**：

   - 串行执行避免同时启动多个浏览器
   - 及时释放浏览器资源
   - 控制内存和 CPU 使用

3. **错误处理**：

   - 一个平台失败不应影响其他平台
   - 记录详细的错误信息
   - 支持部分成功（部分平台成功）
   - 失败平台可以单独重试

4. **数据一致性**：

   - 确保不同平台的数据格式统一
   - 正确处理平台特定的字段差异
   - 数据去重策略要合理
   - 保留平台来源信息

5. **用户体验**：
   - 前端界面支持多平台选择
   - 清晰的进度展示（总体+分平台）
   - 详细的日志记录
   - 友好的错误提示
