# 服务端 API 层设计方案

## 1. 方案概述

### 1.1 目标

设计并实现服务端 API 层，提供强大的案例检索功能，支持关键词检索、语义检索、多维度筛选等多种检索方式。

### 1.2 核心功能

- **关键词检索**：基于全文检索的关键词搜索
- **语义检索**：基于向量相似度的语义搜索
- **混合检索**：结合关键词和语义检索的混合搜索
- **多维度筛选**：品牌、行业、活动类型、时间、标签等筛选
- **排序功能**：按时间、相关性、评分等排序
- **分页功能**：支持分页查询
- **案例详情**：获取单个案例的详细信息

### 1.3 技术选型

#### 后端框架

**推荐：FastAPI**

**理由**：

- ✅ 高性能（基于 Starlette 和 Pydantic）
- ✅ 自动生成 API 文档（Swagger/OpenAPI）
- ✅ 类型提示支持，代码可读性强
- ✅ 异步支持，适合数据库 I/O 密集型操作
- ✅ 轻量级，学习曲线平缓
- ✅ 生态完善，与 PostgreSQL 集成良好

**备选：Django REST Framework**

- 如果团队更熟悉 Django，可以考虑
- 功能更全面，但相对较重

#### 数据库连接

- **psycopg2**（同步）或 **asyncpg**（异步）
- 推荐使用 **asyncpg**，配合 FastAPI 的异步特性

#### 向量模型

- **FlagEmbedding**：用于将查询文本转换为向量（BGE-large-zh，1024 维）

#### 其他依赖

- **Pydantic**：数据验证和序列化（FastAPI 内置）
- **python-dotenv**：环境变量管理
- **uvicorn**：ASGI 服务器

## 2. API 设计

### 2.1 API 端点设计

#### 2.1.1 案例检索 API

**端点**：`GET /api/v1/cases/search`

**功能**：支持多种检索方式的统一检索接口

**请求参数**：

| 参数名           | 类型     | 必填 | 说明                                                                                                      | 示例             |
| ---------------- | -------- | ---- | --------------------------------------------------------------------------------------------------------- | ---------------- |
| `query`          | string   | 否   | 检索关键词（用于关键词检索）                                                                              | "春节营销"       |
| `semantic_query` | string   | 否   | 语义检索查询文本                                                                                          | "情感营销案例"   |
| `search_type`    | string   | 否   | 检索类型：`keyword`（关键词）、`semantic`（语义）、`hybrid`（混合），默认 `hybrid`                        | "hybrid"         |
| `brand_name`     | string   | 否   | 品牌名称（精确匹配或模糊匹配）                                                                            | "耐克"           |
| `brand_industry` | string   | 否   | 品牌行业                                                                                                  | "快消"           |
| `activity_type`  | string   | 否   | 活动类型                                                                                                  | "品牌传播"       |
| `location`       | string   | 否   | 活动地点                                                                                                  | "北京"           |
| `tags`           | string[] | 否   | 标签列表（多个标签为 AND 关系）                                                                           | ["H5", "短视频"] |
| `start_date`     | string   | 否   | 开始日期（YYYY-MM-DD）                                                                                    | "2024-01-01"     |
| `end_date`       | string   | 否   | 结束日期（YYYY-MM-DD）                                                                                    | "2024-12-31"     |
| `min_score`      | integer  | 否   | 最低评分（1-5）                                                                                           | 4                |
| `sort_by`        | string   | 否   | 排序字段：`relevance`（相关性）、`time`（时间）、`score`（评分）、`favourite`（收藏数），默认 `relevance` | "time"           |
| `sort_order`     | string   | 否   | 排序顺序：`asc`（升序）、`desc`（降序），默认 `desc`                                                      | "desc"           |
| `page`           | integer  | 否   | 页码，默认 1                                                                                              | 1                |
| `page_size`      | integer  | 否   | 每页数量，默认 20，最大 100                                                                               | 20               |
| `min_similarity` | float    | 否   | 最小相似度（仅语义检索，0-1），默认 0.5                                                                   | 0.7              |

**响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8,
    "results": [
      {
        "case_id": 291696,
        "title": "案例标题",
        "description": "案例描述...",
        "brand_name": "品牌名称",
        "brand_industry": "快消",
        "activity_type": "品牌传播",
        "location": "北京",
        "tags": ["H5", "情感营销"],
        "main_image": "https://example.com/image.jpg",
        "images": ["https://example.com/img1.jpg"],
        "score": 5,
        "score_decimal": "9.5",
        "favourite": 120,
        "publish_time": "2024-01-15",
        "source_url": "https://example.com/case/291696",
        "similarity": 0.85,
        "highlight": {
          "title": "案例<em>标题</em>",
          "description": "案例<em>描述</em>..."
        }
      }
    ],
    "facets": {
      "brands": [
        { "name": "耐克", "count": 25 },
        { "name": "阿迪达斯", "count": 18 }
      ],
      "industries": [
        { "name": "快消", "count": 45 },
        { "name": "汽车", "count": 32 }
      ],
      "activity_types": [
        { "name": "品牌传播", "count": 60 },
        { "name": "产品推广", "count": 40 }
      ],
      "tags": [
        { "name": "H5", "count": 35 },
        { "name": "短视频", "count": 28 }
      ]
    }
  }
}
```

#### 2.1.2 案例详情 API

**端点**：`GET /api/v1/cases/{case_id}`

**功能**：获取单个案例的详细信息

**路径参数**：

- `case_id`：案例 ID（integer）

**响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "case_id": 291696,
    "title": "案例标题",
    "description": "完整案例描述...",
    "author": "作者名",
    "publish_time": "2024-01-15",
    "source_url": "https://example.com/case/291696",
    "main_image": "https://example.com/image.jpg",
    "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
    "video_url": "https://example.com/video.mp4",
    "brand_name": "品牌名称",
    "brand_industry": "快消",
    "activity_type": "品牌传播",
    "location": "北京",
    "tags": ["H5", "情感营销", "春节"],
    "score": 5,
    "score_decimal": "9.5",
    "favourite": 120,
    "company_name": "公司名称",
    "company_logo": "https://example.com/logo.jpg",
    "agency_name": "广告公司名称",
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T10:00:00Z"
  }
}
```

#### 2.1.3 相似案例推荐 API

**端点**：`GET /api/v1/cases/{case_id}/similar`

**功能**：基于向量相似度推荐相似案例

**路径参数**：

- `case_id`：案例 ID（integer）

**查询参数**：

- `limit`：返回数量，默认 10，最大 50
- `min_similarity`：最小相似度，默认 0.6

**响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "case_id": 291696,
    "similar_cases": [
      {
        "case_id": 291697,
        "title": "相似案例标题",
        "brand_name": "品牌名称",
        "main_image": "https://example.com/image.jpg",
        "similarity": 0.88,
        "publish_time": "2024-01-10"
      }
    ]
  }
}
```

#### 2.1.4 筛选选项 API

**端点**：`GET /api/v1/cases/filters`

**功能**：获取所有可用的筛选选项（品牌、行业、活动类型、标签等）

**响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brands": [
      { "name": "耐克", "count": 25 },
      { "name": "阿迪达斯", "count": 18 }
    ],
    "industries": [
      { "name": "快消", "count": 45 },
      { "name": "汽车", "count": 32 }
    ],
    "activity_types": [
      { "name": "品牌传播", "count": 60 },
      { "name": "产品推广", "count": 40 }
    ],
    "tags": [
      { "name": "H5", "count": 35 },
      { "name": "短视频", "count": 28 }
    ],
    "locations": [
      { "name": "北京", "count": 50 },
      { "name": "上海", "count": 42 }
    ]
  }
}
```

#### 2.1.5 统计信息 API

**端点**：`GET /api/v1/cases/stats`

**功能**：获取案例库的统计信息

**响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_cases": 1000,
    "total_brands": 150,
    "total_industries": 20,
    "total_tags": 200,
    "cases_with_vectors": 950,
    "latest_case_date": "2024-01-20",
    "oldest_case_date": "2020-01-01"
  }
}
```

### 2.2 错误处理

**统一错误响应格式**：

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null,
  "errors": [
    {
      "field": "page",
      "message": "页码必须大于0"
    }
  ]
}
```

**HTTP 状态码**：

- `200`：成功
- `400`：请求参数错误
- `404`：资源不存在
- `500`：服务器内部错误

## 3. 技术实现方案

### 3.1 项目结构

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── case.py             # 案例模型
│   │   └── response.py         # 响应模型
│   ├── schemas/                # Pydantic 模式
│   │   ├── __init__.py
│   │   ├── case.py             # 案例 Schema
│   │   └── search.py           # 检索请求/响应 Schema
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── search_service.py  # 检索服务
│   │   ├── vector_service.py  # 向量服务
│   │   └── case_service.py    # 案例服务
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   └── case_repository.py # 案例数据访问
│   └── routers/                # 路由
│       ├── __init__.py
│       └── cases.py            # 案例相关路由
├── requirements.txt
└── .env.example
```

### 3.2 核心实现逻辑

#### 3.2.1 检索服务实现

**关键词检索**：

- 使用 PostgreSQL 的 `tsvector` 和 `tsquery` 进行全文检索
- 支持中文分词（如果安装了 zhparser 或 pg_jieba）
- 使用 GIN 索引加速检索

**语义检索**：

- 使用 FlagEmbedding 将查询文本转换为向量
- 使用 `pgvector` 的 `<=>` 操作符计算余弦相似度
- 使用 HNSW 索引加速向量检索

**混合检索**：

- 分别执行关键词检索和语义检索
- 使用加权融合算法合并结果
- 支持可配置的权重比例

**筛选和排序**：

- 在 SQL 查询中添加 WHERE 条件
- 使用 ORDER BY 进行排序
- 支持多字段组合排序

#### 3.2.2 数据库查询优化

**索引使用**：

- 充分利用已创建的 B-Tree、GIN、HNSW 索引
- 根据查询条件选择合适的索引

**查询优化**：

- 使用 EXPLAIN ANALYZE 分析查询计划
- 避免全表扫描
- 合理使用 LIMIT 和 OFFSET

**连接池**：

- 使用连接池管理数据库连接
- 异步操作使用 asyncpg 连接池

### 3.3 向量服务实现

**向量生成**：

- 使用 FlagEmbedding 的 BGE-large-zh 模型
- 支持批量生成向量（用于相似案例推荐）
- 缓存常用查询的向量结果

**向量检索**：

- 使用 PostgreSQL 的向量操作符
- 支持不同的相似度计算方法（余弦、L2、内积）

## 4. 性能优化

### 4.1 查询性能优化

1. **索引优化**：

   - 确保所有常用查询字段都有索引
   - 定期分析索引使用情况，删除无用索引

2. **查询优化**：

   - 避免 SELECT \*
   - 使用分页限制返回数据量
   - 使用 EXPLAIN 分析慢查询

3. **缓存策略**：
   - 缓存热门查询结果（Redis）
   - 缓存筛选选项数据
   - 设置合理的缓存过期时间

### 4.2 向量检索优化

1. **索引参数调优**：

   - 根据数据量调整 HNSW 索引参数（m, ef_construction）
   - 平衡检索精度和速度

2. **批量处理**：
   - 批量生成向量，减少模型加载次数
   - 批量查询相似案例

### 4.3 API 性能优化

1. **异步处理**：

   - 使用 FastAPI 的异步特性
   - 数据库操作使用异步驱动（asyncpg）

2. **响应压缩**：

   - 启用 Gzip 压缩
   - 减少响应体积

3. **限流和熔断**：
   - 实现 API 限流（防止滥用）
   - 实现熔断机制（保护数据库）

## 5. 安全性设计

### 5.1 输入验证

- 使用 Pydantic 进行请求参数验证
- 防止 SQL 注入（使用参数化查询）
- 防止 XSS 攻击（转义输出）

### 5.2 访问控制

- 实现 API 密钥认证（可选）
- 实现请求频率限制
- 记录 API 访问日志

### 5.3 数据安全

- 敏感信息不返回给客户端
- 数据库连接使用环境变量管理
- 定期备份数据库

## 6. 部署方案

### 6.1 开发环境

- 使用 uvicorn 开发服务器
- 支持热重载
- 使用本地 PostgreSQL 数据库

### 6.2 生产环境

- 使用 Gunicorn + uvicorn workers
- 使用 Nginx 作为反向代理
- 使用 Docker 容器化部署
- 配置日志收集和监控

### 6.3 环境变量配置

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ad_case_db
DB_USER=postgres
DB_PASSWORD=

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_WORKERS=4

# 向量模型配置
VECTOR_MODEL_PATH=/path/to/bge-large-zh
VECTOR_DIMENSION=1024

# 缓存配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 7. 测试方案

### 7.1 单元测试

- 测试各个服务层的业务逻辑
- 测试数据访问层的查询逻辑
- 使用 pytest 框架

### 7.2 集成测试

- 测试 API 端点的完整流程
- 测试数据库查询性能
- 测试向量检索准确性

### 7.3 性能测试

- 使用 locust 或 Apache Bench 进行压力测试
- 测试并发查询性能
- 测试大数据量下的查询性能

## 8. 开发计划

### 阶段一：基础框架搭建（1-2 天）✅ **已完成**

- [x] 创建 FastAPI 项目结构
- [x] 配置数据库连接
- [x] 实现基础路由和响应格式

**完成时间**: 2024-01-XX  
**验证报告**: 见 `api/STAGE1_VERIFICATION.md`

### 阶段二：核心检索功能（3-5 天）

- [ ] 实现关键词检索
- [ ] 实现语义检索
- [ ] 实现混合检索
- [ ] 实现筛选和排序

### 阶段三：辅助功能（2-3 天）

- [ ] 实现案例详情接口
- [ ] 实现相似案例推荐
- [ ] 实现筛选选项接口
- [ ] 实现统计信息接口

### 阶段四：优化和测试（2-3 天）

- [ ] 性能优化
- [ ] 添加缓存
- [ ] 编写测试用例
- [ ] API 文档完善

### 阶段五：部署和上线（1-2 天）

- [ ] Docker 容器化
- [ ] 生产环境配置
- [ ] 监控和日志配置

## 9. 后续扩展

### 9.1 功能扩展

- 用户认证和授权
- 案例收藏功能
- 检索历史记录
- 个性化推荐

### 9.2 性能扩展

- 引入 Redis 缓存
- 引入 Elasticsearch 增强全文检索
- 引入 CDN 加速静态资源

### 9.3 监控和运维

- 集成 Prometheus 监控
- 集成日志收集系统（ELK）
- 实现健康检查接口
