# 广告门创意案例爬虫方案

## 1. 方案概述

### 1.1 目标

从广告门网站（https://m.adquan.com/creative）自动采集广告创意案例，提取结构化信息，为案例知识库提供数据源。

### 1.2 核心功能

- 爬取案例列表页（支持分页）
- 爬取案例详情页
- 提取结构化信息（标题、品牌、描述、图片、标签等）
- 数据去重和质量校验
- 增量采集支持

## 2. 技术选型

### 2.1 爬虫框架

**推荐方案：Python + Requests + BeautifulSoup4**

**理由：**

- 轻量级，易于维护
- 广告门移动端页面结构相对简单，无需 JS 渲染
- 开发效率高，适合快速迭代

**备选方案：Scrapy**

- 如果后续需要扩展多个数据源，可考虑迁移到 Scrapy 框架
- 提供更好的并发控制和中间件支持

### 2.2 核心依赖库

```
requests          # HTTP请求库（支持Session管理）
beautifulsoup4    # HTML解析库（用于详情页和CSRF Token提取）
lxml              # 快速XML/HTML解析器
fake-useragent    # 随机User-Agent生成
python-dotenv     # 环境变量管理
```

**说明**：

- 使用 `requests.Session()` 维护 Cookie 和会话状态
- BeautifulSoup4 用于解析 HTML 页面（获取 CSRF Token 和详情页）
- JSON 数据直接使用 Python 内置的`json`模块解析

### 2.3 数据存储

**初期方案：JSON 文件 + SQLite**

- JSON 文件：存储原始 HTML、API 返回的 JSON 数据和中间数据
- SQLite：存储结构化案例数据
- 便于后续迁移到 MySQL/PostgreSQL

**数据存储说明**：

- 保存 API 返回的原始 JSON 数据，便于调试和数据结构分析
- 保存详情页的原始 HTML，便于后续数据提取规则优化

**字段设计：**

```sql
CREATE TABLE ad_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    source_url TEXT UNIQUE NOT NULL,
    brand_name TEXT,
    brand_industry TEXT,
    activity_type TEXT,
    activity_theme TEXT,
    publish_time TEXT,
    agency_name TEXT,
    tags TEXT,  -- JSON格式存储多个标签
    images TEXT,  -- JSON格式存储图片URL列表
    video_url TEXT,
    quality_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 3. 爬取策略

### 3.1 页面结构分析

#### 列表页（API 接口）

**重要发现**：列表页通过 API 接口返回 JSON 数据，而非 HTML 页面。

**API 接口信息**：

- **接口 URL**：`https://m.adquan.com/creative`
- **请求方式**：GET
- **请求参数**：
  - `page`: 页码（从 0 开始）
  - `type`: 类型筛选（0 表示全部）
  - `searchvalue`: 搜索关键词（空字符串表示不搜索）
- **返回格式**：JSON
- **必需 Headers**：
  - `X-CSRF-TOKEN`: CSRF 令牌（需要从 HTML 页面获取）
  - `X-Requested-With: XMLHttpRequest`
  - `Referer: https://m.adquan.com/creative`
  - `Cookie`: 会话 Cookie（需要维护 session）

**API 返回数据结构（待确认）**：

- 案例列表数组
- 每个案例包含：标题、链接、图片、评分等基础信息
- 分页信息（总数、当前页等）

#### 详情页

- **访问方式**：HTML 页面
- **完整信息**：
  - 案例标题
  - 案例描述
  - 品牌信息
  - 活动信息
  - 主办方信息（广告公司、代理公司等）
  - 图片集合
  - 视频链接（如有）
  - 标签信息
  - 发布时间

### 3.2 爬取流程

```
1. 访问列表页HTML（获取CSRF Token和Cookie）
   ↓
2. 解析HTML获取CSRF Token
   ↓
3. 调用列表页API接口（page=0开始）
   ↓
4. 解析JSON数据，提取案例列表
   ↓
5. 遍历每个案例，访问详情页
   ↓
6. 提取结构化信息
   ↓
7. 数据清洗和校验
   ↓
8. 去重检查
   ↓
9. 存储到数据库
   ↓
10. 处理下一页（page+1，重复步骤3-9）
```

### 3.3 API 接口调用策略

#### 获取 CSRF Token

1. 首次访问 `https://m.adquan.com/creative`（HTML 页面）
2. 从 HTML 中提取 CSRF Token，常见位置：
   - `<meta name="csrf-token" content="...">`
   - `<input type="hidden" name="_token" value="...">`
   - JavaScript 变量中的 token 值
   - 需要根据实际页面结构确定提取方式
3. 保存 Cookie 用于后续请求（使用 Session 自动管理）
4. **Token 有效期**：如果 Token 失效导致 API 请求失败，需要重新获取

#### API 请求构建

```python
# API请求示例
headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Referer': 'https://m.adquan.com/creative',
    'X-CSRF-TOKEN': csrf_token,  # 从HTML页面获取
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) ...',
}

params = {
    'page': 0,  # 从0开始
    'type': 0,  # 0表示全部类型
    'searchvalue': '',  # 空字符串表示不搜索
}

response = requests.get(
    'https://m.adquan.com/creative',
    params=params,
    headers=headers,
    cookies=session_cookies
)
```

#### 分页处理

- 从 `page=0` 开始递增
- 判断是否还有下一页：
  - 检查返回的 JSON 数据中是否有分页信息
  - 或检查返回的案例列表是否为空
  - 或检查返回数量是否小于预期（如每页 20 条）

### 3.4 采集策略

#### 首次采集

- 从最新页开始，向后采集
- 设置采集页数限制（如：最近 100 页）
- 记录最后采集位置

#### 增量采集

- 基于`source_url`进行去重
- 只采集新增案例
- 检查已存在案例是否有更新

#### 采集频率

- 每日采集一次（根据需求文档）
- 支持手动触发
- 支持定时任务（使用 cron 或任务调度器）

## 4. 反爬虫处理

### 4.1 请求头设置

- 随机 User-Agent（使用 fake-useragent 库，模拟移动端浏览器）
- 设置 Referer（API 请求时设置为列表页 URL）
- 设置 Accept-Language
- **关键 Headers**：
  - `X-CSRF-TOKEN`: 从 HTML 页面动态获取
  - `X-Requested-With: XMLHttpRequest`: 标识为 AJAX 请求
  - `Accept: application/json, text/javascript, */*; q=0.01`: 标识接受 JSON 响应

### 4.2 Session 管理

- 使用 `requests.Session()` 维护会话
- 首次访问 HTML 页面获取初始 Cookie
- 后续 API 请求复用 Session，自动携带 Cookie
- 定期检查 Session 有效性，失效时重新获取

### 4.3 请求频率控制

- **延迟策略**：每个请求间隔 1-3 秒（随机）
- **并发控制**：单线程顺序爬取，避免并发过高
- **重试机制**：失败请求重试 3 次，指数退避

### 4.4 代理支持（可选）

- 预留代理 IP 配置接口
- 支持代理轮换
- 检测代理可用性

### 4.5 遵守 robots.txt

- 检查目标网站 robots.txt
- 遵守爬取规则
- 设置合理的爬取间隔

## 5. 数据提取规则

### 5.1 列表页提取（API JSON 数据）

**从 API 返回的 JSON 中提取**：

```python
# 提取字段（具体字段名需要根据实际API返回结构确认）
- 案例标题：从JSON中的title字段提取
- 案例链接：从JSON中的url或link字段提取（可能需要拼接完整URL）
- 案例ID：从JSON中的id字段提取（用于构建详情页URL）
- 缩略图：从JSON中的image或cover字段提取
- 评分/收藏数：从JSON中的score、favorite等字段提取
- 品牌名称：从JSON中的brand字段提取（如有）
- 发布时间：从JSON中的publish_time或created_at字段提取（如有）
```

**注意事项**：

- API 返回的链接可能是相对路径，需要转换为绝对路径
- 需要验证 JSON 数据结构，确认字段名称
- 保存原始 JSON 数据用于调试和后续分析

### 5.2 详情页提取

#### 基本信息

- **标题**：从页面标题或 H1 标签提取
- **描述**：从案例描述段落提取
- **链接**：当前页面 URL

#### 品牌信息

- **品牌名称**：从"品牌"或"广告主"字段提取
- **品牌行业**：从行业分类标签提取
- **识别规则**：使用正则表达式或关键词匹配

#### 活动信息

- **活动类型**：从活动类型标签提取
- **活动主题**：从主题描述提取
- **活动时间**：从发布时间提取，格式化为标准格式
- **活动地点**：从地点信息提取（如有）

#### 主办方信息

- **广告公司**：从"广告公司"或"创意公司"字段提取
- **代理公司**：从"代理公司"字段提取
- **媒体平台**：从投放平台信息提取

#### 媒体资源

- **图片**：提取所有案例相关图片 URL
  - 主图：优先提取
  - 配图：提取所有相关图片
  - 过滤：排除 logo、广告等无关图片
- **视频**：提取视频链接（如有）

#### 标签信息

- **创意标签**：从创意形式标签提取（H5、短视频等）
- **内容标签**：从内容主题标签提取
- **行业标签**：从行业相关标签提取

### 5.3 数据清洗规则

#### 文本清洗

- 去除 HTML 标签
- 去除多余空白字符
- 去除特殊字符和乱码
- 统一编码格式（UTF-8）

#### 时间格式化

- 统一时间格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
- 处理相对时间（如"3 天前"）转换为绝对时间
- 处理时间范围（如"2024 年 1 月"）

#### 链接处理

- 相对链接转换为绝对链接
- 验证链接有效性
- 去除追踪参数（如 utm_source 等）

#### 图片处理

- 验证图片 URL 有效性
- 过滤重复图片
- 提取图片尺寸信息（可选）

## 6. 数据质量校验

### 6.1 完整性校验

- **必填字段**：标题、链接必须存在
- **推荐字段**：品牌、描述、图片至少有一个
- **评分规则**：根据字段完整性计算质量评分

### 6.2 准确性校验

- **链接有效性**：验证 source_url 是否可访问
- **时间格式**：验证时间格式是否正确
- **品牌名称**：标准化品牌名称（去除空格、统一大小写）

### 6.3 去重机制

- **基于 URL 去重**：source_url 作为唯一标识
- **基于标题相似度**：计算标题相似度，超过阈值视为重复
- **基于内容相似度**：计算描述文本相似度（可选，使用简单文本相似度算法）

### 6.4 质量评分

```python
质量评分 = (
    基础分(20) +
    标题完整性(20) +
    描述完整性(20) +
    品牌信息完整性(15) +
    图片完整性(15) +
    标签完整性(10)
)
```

## 7. 错误处理

### 7.1 网络错误

- 连接超时：重试 3 次
- HTTP 错误（4xx/5xx）：记录错误，跳过该案例
- 网络异常：记录日志，等待后重试

#### 7.1.1 API 请求特殊错误处理

- **401/403 错误**：可能是 CSRF Token 失效，需要重新获取 Token
- **429 错误（请求过多）**：降低请求频率，增加延迟时间
- **JSON 解析错误**：记录原始响应内容，检查 API 返回格式是否变化
- **空数据返回**：可能是已到最后一页，或 API 参数错误

### 7.2 解析错误

- HTML 结构变化：记录错误日志，标记需要人工检查
- 字段缺失：使用默认值或标记为不完整
- 编码错误：尝试多种编码方式

### 7.3 数据错误

- 数据格式错误：记录错误，尝试修复或跳过
- 数据异常：记录异常数据，标记需要审核

### 7.4 日志记录

- 记录所有错误和异常
- 记录采集统计信息（成功数、失败数、耗时等）
- 日志文件按日期分割

## 8. 项目结构

```
technical-solution/
├── spider/
│   ├── __init__.py
│   ├── adquan_spider.py      # 主爬虫类
│   ├── parser.py              # 页面解析器
│   ├── data_cleaner.py        # 数据清洗器
│   ├── database.py            # 数据库操作
│   └── utils.py               # 工具函数
├── config/
│   ├── config.py              # 配置文件
│   └── .env.example           # 环境变量示例
├── data/
│   ├── raw/                   # 原始HTML存储
│   ├── json/                  # JSON中间数据
│   └── database/              # SQLite数据库
├── logs/                      # 日志文件
├── requirements.txt           # 依赖包
├── main.py                    # 主程序入口
└── README.md                  # 使用说明
```

## 9. 配置管理

### 9.1 配置文件

```python
# config/config.py
SPIDER_CONFIG = {
    'base_url': 'https://m.adquan.com/creative',
    'delay_range': (1, 3),  # 请求延迟范围（秒）
    'max_retries': 3,       # 最大重试次数
    'timeout': 30,          # 请求超时时间
    'max_pages': 100,       # 最大采集页数
    'user_agent_rotate': True,  # 是否轮换User-Agent
}
```

### 9.2 环境变量

```bash
# .env
DATABASE_PATH=./data/database/ad_cases.db
LOG_LEVEL=INFO
PROXY_ENABLED=False
PROXY_LIST=
```

## 10. 监控和统计

### 10.1 采集统计

- 总采集数量
- 成功/失败数量
- 新增/更新数量
- 采集耗时
- 数据质量分布

### 10.2 错误监控

- 错误类型统计
- 错误频率分析
- 需要人工处理的案例列表

### 10.3 性能监控

- 平均响应时间
- 请求成功率
- 数据库写入性能

## 11. 扩展性考虑

### 11.1 多数据源支持

- 抽象爬虫基类
- 每个数据源实现独立爬虫类
- 统一数据接口

### 11.2 分布式爬取（未来）

- 支持多进程/多线程
- 支持分布式任务队列（如 Celery）
- 支持分布式存储

### 11.3 数据导出

- 支持导出为 JSON/CSV 格式
- 支持 API 接口提供数据
- 支持数据同步到其他系统

## 12. 实施计划

### 阶段一：基础功能（1 周）

- [ ] 实现 CSRF Token 获取机制
- [ ] 实现 Session 管理
- [ ] 实现列表页 API 调用和 JSON 解析
- [ ] 实现详情页 HTML 爬取
- [ ] 基础数据提取
- [ ] 数据存储到 SQLite

### 阶段二：数据清洗（1 周）

- [ ] 实现数据清洗规则
- [ ] 实现去重机制
- [ ] 实现质量评分
- [ ] 完善错误处理

### 阶段三：优化和测试（1 周）

- [ ] 反爬虫优化
- [ ] 性能优化
- [ ] 单元测试
- [ ] 集成测试

### 阶段四：监控和文档（0.5 周）

- [ ] 添加日志和监控
- [ ] 编写使用文档
- [ ] 部署和上线

## 13. 风险评估

### 13.1 技术风险

- **网站结构变化**：风险等级：中
  - 应对：定期检查，及时更新解析规则
- **反爬虫升级**：风险等级：中
  - 应对：预留代理、验证码处理接口

### 13.2 合规风险

- **robots.txt 遵守**：风险等级：低
  - 应对：严格遵守 robots.txt 规则
- **数据使用合规**：风险等级：中
  - 应对：仅用于内部参考，不对外传播

### 13.3 数据质量风险

- **数据不完整**：风险等级：中
  - 应对：设置质量阈值，低质量数据标记审核

## 14. 后续优化方向

1. **智能提取**：使用 NLP 技术提升信息提取准确性
2. **图片下载**：支持图片本地存储
3. **内容分析**：自动生成案例摘要和关键词
4. **相似度计算**：使用向量化技术计算案例相似度
5. **实时监控**：添加 Web 界面监控爬虫状态
