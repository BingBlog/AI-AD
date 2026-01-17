# 广告案例库数据库设计方案

## 1. 数据特点分析

### 1.1 数据结构

基于爬取到的数据，每个案例包含以下字段：

#### 基础信息

- `case_id` (Integer): 案例唯一标识
- `source_url` (String): 源 URL
- `title` (String): 标题
- `description` (Text): 详细描述（长文本，可能数千字）
- `author` (String): 作者
- `publish_time` (Date): 发布时间

#### 媒体资源

- `main_image` (String): 主图 URL
- `images` (Array[String]): 图片 URL 数组
- `video_url` (String): 视频 URL（可选）

#### 分类信息

- `brand_name` (String): 品牌名称
- `brand_industry` (String): 品牌行业（如"家居、家电"、"汽车"）
- `activity_type` (String): 活动类型（如"影视"、"平面"、"H5"）
- `location` (String): 所在地区（如"中国大陆"、"欧洲"）
- `tags` (Array[String]): 标签数组

#### 评分与互动

- `score` (Integer): 评分（1-5）
- `score_decimal` (String): 评分小数（如"9.5"）
- `favourite` (Integer): 收藏数

#### 公司信息

- `company_name` (String): 广告公司名称
- `company_logo` (String): 公司 Logo URL
- `agency_name` (String): 代理公司名称

### 1.2 数据特点

1. **结构化程度高**：大部分字段是结构化数据，适合关系型数据库存储
2. **长文本内容**：`description` 字段包含大量文本，需要全文检索支持
3. **数组字段**：`images` 和 `tags` 是数组类型，需要支持数组查询
4. **检索需求多样**：
   - 精确匹配：按品牌、行业、类型等筛选
   - 关键词检索：在标题、描述等字段中搜索关键词
   - 语义检索：根据语义相似度找到相关案例

## 2. 检索需求分析

### 2.1 字段关键词检索

需要支持以下检索场景：

1. **单字段检索**：

   - 标题关键词搜索
   - 描述关键词搜索
   - 品牌名称搜索
   - 标签搜索

2. **多字段组合检索**：

   - 标题 + 描述联合搜索
   - 品牌 + 行业 + 类型组合筛选

3. **高级检索**：
   - 模糊匹配
   - 分词搜索（中文分词）
   - 布尔查询（AND/OR/NOT）
   - 排序（按评分、收藏数、时间等）

### 2.2 语义检索（RAG）

需要支持以下场景：

1. **自然语言查询**：

   - "找一些关于情感营销的案例"
   - "寻找类似宜家时间就是金钱的创意案例"
   - "展示一些汽车行业的优秀广告"

2. **语义相似度匹配**：

   - 根据案例描述找到语义相似的案例
   - 根据用户输入的自然语言描述找到相关案例

3. **混合检索**：
   - 结合关键词检索和语义检索
   - 先语义检索找到候选集，再用关键词过滤

## 3. 数据库技术选型

### 3.1 选型原则

1. **性能要求**：支持快速检索，响应时间 < 500ms
2. **可扩展性**：支持数据量增长（初期数万，未来可能数十万）
3. **功能完整性**：同时支持结构化查询、全文检索和向量检索
4. **开发效率**：易于集成和使用
5. **成本考虑**：开源优先，降低运维成本

### 3.2 技术方案对比

#### 方案一：PostgreSQL + pgvector + 全文检索

**架构**：

- **主数据库**：PostgreSQL（存储结构化数据）
- **向量扩展**：pgvector（支持向量检索）
- **全文检索**：PostgreSQL 内置全文检索（GIN 索引）

**优点**：

- ✅ 一体化方案，无需多套数据库
- ✅ PostgreSQL 全文检索对中文支持良好（配合中文分词插件）
- ✅ pgvector 性能优秀，与 PostgreSQL 深度集成
- ✅ 事务支持，数据一致性有保障
- ✅ 成熟稳定，社区活跃
- ✅ 支持复杂查询（JOIN、聚合等）

**缺点**：

- ⚠️ 向量检索性能可能不如专业向量数据库（但通常足够）
- ⚠️ 需要配置中文分词插件（如 zhparser、jieba）

**适用场景**：

- 中小规模数据（< 100 万条）
- 需要强一致性
- 希望简化架构

#### 方案二：PostgreSQL + Milvus/Qdrant

**架构**：

- **主数据库**：PostgreSQL（存储结构化数据和元数据）
- **向量数据库**：Milvus 或 Qdrant（专门用于向量检索）

**优点**：

- ✅ 向量检索性能最优
- ✅ 支持大规模向量数据（百万级+）
- ✅ 向量数据库专门优化，功能丰富
- ✅ PostgreSQL 专注于结构化数据，职责清晰

**缺点**：

- ⚠️ 需要维护两套数据库
- ⚠️ 数据同步需要额外处理
- ⚠️ 架构复杂度增加
- ⚠️ 需要处理数据一致性

**适用场景**：

- 大规模数据（> 100 万条）
- 对向量检索性能要求极高
- 有专门的运维团队

#### 方案三：Elasticsearch + 向量检索

**架构**：

- **搜索引擎**：Elasticsearch（全文检索 + 向量检索）
- **元数据库**：PostgreSQL 或 MySQL（可选，存储少量元数据）

**优点**：

- ✅ 全文检索能力强大
- ✅ 支持复杂查询和聚合
- ✅ Elasticsearch 8.0+ 支持向量检索
- ✅ 分布式架构，扩展性好

**缺点**：

- ⚠️ 资源消耗较大
- ⚠️ 学习曲线较陡
- ⚠️ 向量检索功能相对较新，可能不够成熟

**适用场景**：

- 全文检索需求复杂
- 需要分布式架构
- 团队熟悉 Elasticsearch

#### 方案四：MySQL + 全文检索 + 独立向量数据库

**架构**：

- **主数据库**：MySQL（存储结构化数据）
- **全文检索**：MySQL 全文索引（或配合 Elasticsearch）
- **向量数据库**：Milvus/Qdrant/Weaviate

**优点**：

- ✅ MySQL 使用广泛，团队熟悉度高
- ✅ 向量数据库专门优化

**缺点**：

- ⚠️ MySQL 全文检索对中文支持一般
- ⚠️ 需要维护多套系统
- ⚠️ 架构复杂

**适用场景**：

- 团队对 MySQL 非常熟悉
- 已有 MySQL 基础设施

### 3.3 推荐方案

**推荐：方案一（PostgreSQL + pgvector + 全文检索）**

#### 推荐理由

1. **架构简单**：

   - 单一数据库系统，降低运维复杂度
   - 无需数据同步，保证一致性
   - 部署和维护成本低

2. **功能完整**：

   - PostgreSQL 支持结构化查询、全文检索、向量检索
   - 满足所有检索需求

3. **性能足够**：

   - 对于案例库规模（数万到数十万），PostgreSQL + pgvector 性能完全够用
   - 全文检索性能优秀（配合 GIN 索引）

4. **生态成熟**：

   - PostgreSQL 生态完善
   - pgvector 由 Supabase 团队维护，稳定可靠
   - 中文分词插件成熟（zhparser、jieba）

5. **成本优势**：
   - 完全开源
   - 无需额外向量数据库服务器
   - 降低硬件和运维成本

#### 备选方案

如果未来数据量增长到百万级，或对向量检索性能有极高要求，可以考虑：

**方案二（PostgreSQL + Milvus/Qdrant）**

- 保持 PostgreSQL 作为主数据库
- 将向量数据迁移到专门的向量数据库
- 通过应用层维护数据同步

### 3.4 技术栈详细说明

#### 3.4.1 PostgreSQL

**版本要求**：PostgreSQL 12+

**核心功能**：

- 存储所有结构化数据
- 支持 JSON/JSONB 类型（存储数组字段）
- 支持全文检索（GIN 索引）
- 支持复杂查询和聚合

**中文分词插件选择**：

1. **zhparser**（推荐）：

   - 基于 PostgreSQL 中文全文检索插件
   - 使用 scws 分词引擎
   - 性能好，准确率高
   - 安装：`CREATE EXTENSION zhparser;`

2. **pg_jieba**：
   - 基于 jieba 分词
   - 功能丰富，支持自定义词典
   - 安装：`CREATE EXTENSION pg_jieba;`

#### 3.4.2 pgvector

**版本要求**：pgvector 0.5.0+

**核心功能**：

- 支持向量类型（vector）
- 支持多种距离计算（L2、内积、余弦相似度）
- 支持 HNSW 索引（高性能近似最近邻搜索）

**安装**：

```sql
CREATE EXTENSION vector;
```

**向量维度**：

- 推荐使用 1024 维（text2vec-large-chinese、BGE-large-zh）或 768 维（BGE-base-zh、m3e-base）
- 根据使用的嵌入模型确定，需要在创建表时指定正确的维度

#### 3.4.3 嵌入模型选择

**中文文本嵌入模型推荐**：

1. **text2vec-large-chinese**（推荐）：

   - **向量维度**：1024 维
   - **特点**：专门针对中文优化，基于 BERT 架构
   - **优势**：开源免费，中文效果优秀，社区活跃
   - **GitHub**：https://github.com/shibing624/text2vec
   - **模型路径**：`shibing624/text2vec-large-chinese`

2. **BGE-large-zh**（强烈推荐）：

   - **向量维度**：1024 维
   - **特点**：智源研究院（BAAI）开发，中文效果最佳
   - **优势**：在中文检索任务上表现优异，支持长文本（512 tokens）
   - **模型路径**：`BAAI/bge-large-zh-v1.5`
   - **GitHub**：https://github.com/FlagOpen/FlagEmbedding
   - **性能对比**：在中文检索任务上通常优于 text2vec-large-chinese

3. **BGE-base-zh**（性价比选择）：

   - **向量维度**：768 维
   - **特点**：BGE 系列的基础版本，速度更快
   - **优势**：模型更小，推理速度快，适合大规模部署
   - **模型路径**：`BAAI/bge-base-zh-v1.5`
   - **适用场景**：数据量大、对速度要求高的场景

4. **m3e-base/m3e-large**：

   - **向量维度**：m3e-base 为 768 维，m3e-large 为 1024 维
   - **特点**：多语言支持，中文效果良好
   - **优势**：支持中英文混合场景
   - **GitHub**：https://github.com/wangyirui/M3E

5. **OpenAI text-embedding-ada-002**（可选）：
   - **向量维度**：1536 维
   - **特点**：需要 API 调用，有成本
   - **优势**：性能优秀，但需要网络访问
   - **适用场景**：对效果要求极高，且可接受 API 成本

**模型对比表**：

| 模型                   | 维度 | 中文效果   | 速度 | 模型大小 | 推荐场景             |
| ---------------------- | ---- | ---------- | ---- | -------- | -------------------- |
| text2vec-large-chinese | 1024 | ⭐⭐⭐⭐   | 中等 | ~1.2GB   | 中文检索，开源优先   |
| BGE-large-zh           | 1024 | ⭐⭐⭐⭐⭐ | 中等 | ~1.2GB   | **中文检索最佳选择** |
| BGE-base-zh            | 768  | ⭐⭐⭐⭐   | 快   | ~400MB   | 大规模部署，速度优先 |
| m3e-large              | 1024 | ⭐⭐⭐⭐   | 中等 | ~1.2GB   | 中英文混合场景       |
| m3e-base               | 768  | ⭐⭐⭐     | 快   | ~400MB   | 中英文混合，速度优先 |

**最终选择**：**BGE-large-zh**

- **维度**：1024 维
- **优势**：中文检索效果最佳，智源研究院官方维护
- **适用场景**：中文案例库检索，追求最佳检索质量

**注意事项**：

- 选择模型后，需要在数据库表结构中设置对应的向量维度
- 1024 维模型效果更好但占用更多存储空间
- 768 维模型速度更快，适合大规模数据场景

### 3.5 技术选型总结

| 组件     | 技术选型                | 版本要求 | 用途                               |
| -------- | ----------------------- | -------- | ---------------------------------- |
| 主数据库 | PostgreSQL              | 12+      | 存储结构化数据、全文检索、向量检索 |
| 向量扩展 | pgvector                | 0.5.0+   | 向量存储和检索                     |
| 中文分词 | zhparser 或 pg_jieba    | -        | 中文全文检索支持                   |
| 嵌入模型 | BGE-large-zh            | -        | 文本向量化（1024 维）              |
| 应用框架 | Python (FastAPI/Django) | -        | 业务逻辑和 API                     |

## 4. 数据库表结构设计

### 4.1 主表设计

#### 4.1.1 案例表（ad_cases）

存储所有案例的基本信息和内容。

```sql
CREATE TABLE ad_cases (
    -- 主键和标识
    id BIGSERIAL PRIMARY KEY,
    case_id INTEGER UNIQUE NOT NULL,  -- 原始案例ID（来自爬虫）

    -- 基础信息
    source_url TEXT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,  -- 长文本描述
    author VARCHAR(100),
    publish_time DATE,

    -- 媒体资源
    main_image TEXT,
    images JSONB DEFAULT '[]'::jsonb,  -- 图片URL数组
    video_url TEXT,

    -- 分类信息
    brand_name VARCHAR(200),
    brand_industry VARCHAR(100),
    activity_type VARCHAR(100),
    location VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,  -- 标签数组

    -- 评分与互动
    score INTEGER CHECK (score >= 1 AND score <= 5),
    score_decimal VARCHAR(10),  -- 如 "9.5"
    favourite INTEGER DEFAULT 0,

    -- 公司信息
    company_name VARCHAR(200),
    company_logo TEXT,
    agency_name VARCHAR(200),

    -- 向量字段（用于语义检索）
    -- 注意：维度根据选择的模型确定（BGE-large-zh/text2vec-large-chinese 为 1024，BGE-base-zh 为 768）
    title_vector vector(1024),  -- 标题向量（1024维，使用BGE-large-zh或text2vec-large-chinese）
    description_vector vector(1024),  -- 描述向量
    combined_vector vector(1024),  -- 标题+描述组合向量

    -- 全文检索字段（用于关键词检索）
    title_tsvector tsvector,  -- 标题全文检索向量
    description_tsvector tsvector,  -- 描述全文检索向量
    combined_tsvector tsvector,  -- 标题+描述组合全文检索向量

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 索引提示
    CONSTRAINT valid_case_id CHECK (case_id > 0)
);
```

#### 4.1.2 索引设计

**B-Tree 索引**（用于精确匹配和排序）：

```sql
-- 主键索引（自动创建）
-- PRIMARY KEY (id)

-- 唯一索引
CREATE UNIQUE INDEX idx_ad_cases_case_id ON ad_cases(case_id);

-- 常用查询字段索引
CREATE INDEX idx_ad_cases_brand_industry ON ad_cases(brand_industry);
CREATE INDEX idx_ad_cases_activity_type ON ad_cases(activity_type);
CREATE INDEX idx_ad_cases_location ON ad_cases(location);
CREATE INDEX idx_ad_cases_publish_time ON ad_cases(publish_time DESC);
CREATE INDEX idx_ad_cases_score ON ad_cases(score DESC);
CREATE INDEX idx_ad_cases_favourite ON ad_cases(favourite DESC);

-- 品牌名称索引（用于模糊查询）
CREATE INDEX idx_ad_cases_brand_name ON ad_cases(brand_name);

-- 复合索引（用于组合查询）
CREATE INDEX idx_ad_cases_industry_type ON ad_cases(brand_industry, activity_type);
CREATE INDEX idx_ad_cases_industry_location ON ad_cases(brand_industry, location);
```

**GIN 索引**（用于全文检索）：

```sql
-- 全文检索索引
CREATE INDEX idx_ad_cases_title_tsvector ON ad_cases USING GIN(title_tsvector);
CREATE INDEX idx_ad_cases_description_tsvector ON ad_cases USING GIN(description_tsvector);
CREATE INDEX idx_ad_cases_combined_tsvector ON ad_cases USING GIN(combined_tsvector);

-- JSONB 索引（用于数组字段查询）
CREATE INDEX idx_ad_cases_tags_gin ON ad_cases USING GIN(tags);
CREATE INDEX idx_ad_cases_images_gin ON ad_cases USING GIN(images);
```

**HNSW 索引**（用于向量检索）：

```sql
-- 向量索引（使用 HNSW 算法，高性能近似最近邻搜索）
-- 注意：向量维度必须与表结构中的 vector(1024) 一致
CREATE INDEX idx_ad_cases_title_vector ON ad_cases
    USING hnsw (title_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_ad_cases_description_vector ON ad_cases
    USING hnsw (description_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_ad_cases_combined_vector ON ad_cases
    USING hnsw (combined_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**索引参数说明**：

- `m = 16`：每个节点的最大连接数，影响索引构建时间和查询精度
- `ef_construction = 64`：构建时的候选集大小，影响索引质量
- `vector_cosine_ops`：使用余弦相似度进行距离计算

#### 4.1.3 触发器设计

**自动更新全文检索向量**：

```sql
-- 创建函数：更新全文检索向量
CREATE OR REPLACE FUNCTION update_tsvector()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新标题全文检索向量（使用中文分词）
    NEW.title_tsvector := to_tsvector('zhparser', COALESCE(NEW.title, ''));

    -- 更新描述全文检索向量
    NEW.description_tsvector := to_tsvector('zhparser', COALESCE(NEW.description, ''));

    -- 更新组合全文检索向量（标题权重更高）
    NEW.combined_tsvector :=
        setweight(to_tsvector('zhparser', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('zhparser', COALESCE(NEW.description, '')), 'B');

    -- 更新 updated_at
    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trigger_update_tsvector
    BEFORE INSERT OR UPDATE ON ad_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_tsvector();
```

### 4.2 辅助表设计

#### 4.2.1 品牌表（brands）

用于品牌信息的标准化和管理。

```sql
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    industry VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_brands_name ON brands(name);
CREATE INDEX idx_brands_industry ON brands(industry);
```

#### 4.2.2 行业表（industries）

用于行业分类的标准化。

```sql
CREATE TABLE industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES industries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_industries_name ON industries(name);
CREATE INDEX idx_industries_parent ON industries(parent_id);
```

#### 4.2.3 标签表（tags）

用于标签的标准化和管理。

```sql
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0,  -- 使用次数
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_usage_count ON tags(usage_count DESC);
```

#### 4.2.4 案例标签关联表（case_tags）

多对多关系表，关联案例和标签。

```sql
CREATE TABLE case_tags (
    case_id INTEGER REFERENCES ad_cases(case_id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (case_id, tag_id)
);

CREATE INDEX idx_case_tags_case_id ON case_tags(case_id);
CREATE INDEX idx_case_tags_tag_id ON case_tags(tag_id);
```

## 5. 向量化方案设计

### 5.0 模型选择指南

**重要提示**：选择嵌入模型后，需要在数据库表结构中设置对应的向量维度。

#### 5.0.1 模型选择

**已选择：BGE-large-zh** ✅

- **维度**：1024
- **优势**：中文检索效果最佳，智源研究院官方维护
- **安装**：`pip install FlagEmbedding`
- **模型路径**：`BAAI/bge-large-zh-v1.5`
- **GitHub**：https://github.com/FlagOpen/FlagEmbedding
- **文档**：https://github.com/FlagOpen/FlagEmbedding/blob/master/README_zh.md

#### 5.0.2 维度与性能对比

| 模型         | 维度 | 检索质量   | 推理速度 | 存储空间 | 状态          |
| ------------ | ---- | ---------- | -------- | -------- | ------------- |
| BGE-large-zh | 1024 | ⭐⭐⭐⭐⭐ | 中等     | 较大     | **已选择** ✅ |

**存储空间估算**（每 10 万条案例）：

- 1024 维：约 400MB（仅向量数据）
- 768 维：约 300MB（仅向量数据）

#### 5.0.3 模型切换注意事项

如果后续需要切换模型（例如从 1024 维切换到 768 维），需要：

1. 重新生成所有向量
2. 修改表结构中的向量维度
3. 重建向量索引

因此，**建议在项目初期确定模型选择**，避免后续迁移成本。

### 5.1 向量化字段选择

**需要向量化的字段**：

1. **title_vector**：标题向量

   - 用途：标题语义检索
   - 优点：快速匹配标题相似的案例

2. **description_vector**：描述向量

   - 用途：描述内容语义检索
   - 优点：匹配内容相似的案例

3. **combined_vector**：组合向量（推荐使用）
   - 用途：标题+描述组合语义检索
   - 生成方式：将标题和描述拼接后向量化，或分别向量化后加权平均
   - 优点：综合考虑标题和内容，检索效果最好

### 5.2 向量生成策略

#### 5.2.1 文本预处理

在向量化之前，需要对文本进行预处理：

```python
def preprocess_text(text: str) -> str:
    """
    文本预处理
    - 去除多余空白
    - 去除特殊字符（保留中文、英文、数字）
    - 统一编码
    """
    import re

    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)

    # 去除特殊字符（保留中文、英文、数字、常用标点）
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：、]', ' ', text)

    # 去除首尾空白
    text = text.strip()

    return text
```

#### 5.2.2 向量生成流程

**使用 BGE-large-zh 模型**：

```python
from FlagEmbedding import FlagModel
import numpy as np

# 初始化 BGE-large-zh 模型（仅需加载一次）
# query_instruction_for_retrieval 用于查询时的指令，提高检索效果
model = FlagModel(
    'BAAI/bge-large-zh-v1.5',
    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
)

def generate_vectors(case_data: dict) -> dict:
    """
    生成案例的向量

    Args:
        case_data: 案例数据字典

    Returns:
        包含 title_vector, description_vector, combined_vector 的字典
    """
    # 预处理文本
    title = preprocess_text(case_data.get('title', ''))
    description = preprocess_text(case_data.get('description', ''))

    # 生成标题向量
    # BGE 模型：对于文档（待检索的内容），不需要 query_instruction
    title_vector = model.encode(title, normalize=True) if title else None
    if title_vector is not None:
        title_vector = title_vector.tolist()  # 转换为列表格式

    # 生成描述向量
    description_vector = model.encode(description, normalize=True) if description else None
    if description_vector is not None:
        description_vector = description_vector.tolist()

    # 生成组合向量（标题+描述拼接）
    # 注意：BGE 支持长文本，最大 512 tokens
    combined_text = f"{title} {description}" if title and description else (title or description)
    combined_vector = model.encode(combined_text, normalize=True) if combined_text else None
    if combined_vector is not None:
        combined_vector = combined_vector.tolist()

    return {
        'title_vector': title_vector,
        'description_vector': description_vector,
        'combined_vector': combined_vector
    }
```

#### 5.2.3 批量向量生成

对于大量数据的向量化，建议使用批量处理：

```python
def batch_generate_vectors(cases: list, batch_size: int = 32) -> list:
    """
    批量生成向量（使用 BGE-large-zh）

    Args:
        cases: 案例列表
        batch_size: 批次大小

    Returns:
        包含向量的案例列表
    """
    from FlagEmbedding import FlagModel

    # 初始化 BGE-large-zh 模型
    model = FlagModel(
        'BAAI/bge-large-zh-v1.5',
        query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
    )

    results = []
    for i in range(0, len(cases), batch_size):
        batch = cases[i:i + batch_size]

        # 预处理文本
        texts = []
        for case in batch:
            title = preprocess_text(case.get('title', ''))
            description = preprocess_text(case.get('description', ''))
            combined = f"{title} {description}" if title and description else (title or description)
            texts.append(combined)

        # 批量编码（BGE 模型支持批量编码）
        # normalize=True 进行向量归一化，提高检索效果
        vectors = model.encode(texts, normalize=True, batch_size=batch_size)

        # 组装结果
        for j, case in enumerate(batch):
            # BGE 返回 numpy array，需要转换为列表
            case['combined_vector'] = vectors[j].tolist()
            results.append(case)

    return results
```

### 5.3 向量更新策略

#### 5.3.1 初始数据向量化

对于已有数据，需要批量生成向量：

```python
def initialize_vectors():
    """
    初始化所有案例的向量
    """
    # 1. 从数据库读取所有案例（分批读取）
    # 2. 批量生成向量
    # 3. 批量更新数据库
    pass
```

#### 5.3.2 增量数据向量化

对于新插入的数据，在插入时自动生成向量：

```python
def insert_case_with_vector(case_data: dict):
    """
    插入案例并自动生成向量
    """
    # 1. 生成向量
    vectors = generate_vectors(case_data)

    # 2. 插入数据库（包含向量字段）
    # INSERT INTO ad_cases (..., title_vector, description_vector, combined_vector) VALUES (...)
    pass
```

#### 5.3.3 向量更新时机

- **插入时**：新案例插入时自动生成向量
- **更新时**：标题或描述更新时重新生成向量
- **批量更新**：定期批量更新所有向量（如果模型升级）

## 6. 检索策略设计

### 6.1 关键词检索实现

#### 6.1.1 单字段检索

**标题检索**：

```sql
-- 使用全文检索
SELECT id, title, description
FROM ad_cases
WHERE title_tsvector @@ to_tsquery('zhparser', '关键词')
ORDER BY ts_rank(title_tsvector, to_tsquery('zhparser', '关键词')) DESC
LIMIT 20;
```

**描述检索**：

```sql
SELECT id, title, description
FROM ad_cases
WHERE description_tsvector @@ to_tsquery('zhparser', '关键词')
ORDER BY ts_rank(description_tsvector, to_tsquery('zhparser', '关键词')) DESC
LIMIT 20;
```

#### 6.1.2 多字段组合检索

**标题+描述联合检索**：

```sql
SELECT id, title, description,
       ts_rank(combined_tsvector, query) AS rank
FROM ad_cases,
     to_tsquery('zhparser', '关键词1 & 关键词2') AS query
WHERE combined_tsvector @@ query
ORDER BY rank DESC
LIMIT 20;
```

#### 6.1.3 高级检索

**布尔查询（AND/OR/NOT）**：

```sql
-- AND 查询：必须同时包含"营销"和"创意"
SELECT * FROM ad_cases
WHERE combined_tsvector @@ to_tsquery('zhparser', '营销 & 创意');

-- OR 查询：包含"营销"或"创意"
SELECT * FROM ad_cases
WHERE combined_tsvector @@ to_tsquery('zhparser', '营销 | 创意');

-- NOT 查询：包含"营销"但不包含"广告"
SELECT * FROM ad_cases
WHERE combined_tsvector @@ to_tsquery('zhparser', '营销 & !广告');
```

**短语查询**：

```sql
-- 查找包含完整短语的案例
SELECT * FROM ad_cases
WHERE combined_tsvector @@ phraseto_tsquery('zhparser', '情感营销');
```

**模糊匹配**：

```sql
-- 使用 LIKE 进行模糊匹配（用于品牌名称等）
SELECT * FROM ad_cases
WHERE brand_name LIKE '%关键词%';
```

### 6.2 语义检索实现

#### 6.2.1 基础语义检索

**使用组合向量进行语义检索**：

```sql
-- 1. 将用户查询转换为向量（在应用层完成）
-- query_vector = model.encode("找一些关于情感营销的案例")

-- 2. 使用向量相似度检索
SELECT id, title, description,
       1 - (combined_vector <=> query_vector) AS similarity
FROM ad_cases
WHERE combined_vector IS NOT NULL
ORDER BY combined_vector <=> query_vector
LIMIT 20;
```

**说明**：

- `<=>` 是 pgvector 的余弦距离操作符
- `1 - distance` 转换为相似度（0-1 之间，越大越相似）
- 结果按相似度降序排列

#### 6.2.2 带过滤条件的语义检索

**语义检索 + 行业筛选**：

```sql
SELECT id, title, description,
       1 - (combined_vector <=> query_vector) AS similarity
FROM ad_cases
WHERE combined_vector IS NOT NULL
  AND brand_industry = '汽车'
ORDER BY combined_vector <=> query_vector
LIMIT 20;
```

**语义检索 + 多条件筛选**：

```sql
SELECT id, title, description,
       1 - (combined_vector <=> query_vector) AS similarity
FROM ad_cases
WHERE combined_vector IS NOT NULL
  AND brand_industry = '汽车'
  AND activity_type = '影视'
  AND publish_time >= '2020-01-01'
ORDER BY combined_vector <=> query_vector
LIMIT 20;
```

#### 6.2.3 相似案例推荐

**根据案例 ID 找到相似案例**：

```sql
-- 1. 获取目标案例的向量
SELECT combined_vector INTO target_vector
FROM ad_cases
WHERE case_id = 291696;

-- 2. 找到相似案例（排除自己）
SELECT id, case_id, title,
       1 - (combined_vector <=> target_vector) AS similarity
FROM ad_cases
WHERE combined_vector IS NOT NULL
  AND case_id != 291696
ORDER BY combined_vector <=> target_vector
LIMIT 10;
```

### 6.3 混合检索实现

#### 6.3.1 策略一：先语义后关键词

```sql
-- 1. 语义检索找到候选集（Top 100）
WITH semantic_candidates AS (
    SELECT id, title, description,
           1 - (combined_vector <=> query_vector) AS semantic_score
    FROM ad_cases
    WHERE combined_vector IS NOT NULL
    ORDER BY combined_vector <=> query_vector
    LIMIT 100
)
-- 2. 在候选集中进行关键词过滤和排序
SELECT id, title, description,
       semantic_score,
       ts_rank(combined_tsvector, keyword_query) AS keyword_score,
       (semantic_score * 0.7 + ts_rank(combined_tsvector, keyword_query) * 0.3) AS final_score
FROM semantic_candidates,
     to_tsquery('zhparser', '关键词') AS keyword_query
WHERE combined_tsvector @@ keyword_query
ORDER BY final_score DESC
LIMIT 20;
```

#### 6.3.2 策略二：先关键词后语义

```sql
-- 1. 关键词检索找到候选集
WITH keyword_candidates AS (
    SELECT id, title, description,
           ts_rank(combined_tsvector, keyword_query) AS keyword_score
    FROM ad_cases,
         to_tsquery('zhparser', '关键词') AS keyword_query
    WHERE combined_tsvector @@ keyword_query
    ORDER BY keyword_score DESC
    LIMIT 100
)
-- 2. 在候选集中进行语义排序
SELECT id, title, description,
       keyword_score,
       1 - (combined_vector <=> query_vector) AS semantic_score,
       (keyword_score * 0.5 + (1 - (combined_vector <=> query_vector)) * 0.5) AS final_score
FROM keyword_candidates
WHERE combined_vector IS NOT NULL
ORDER BY final_score DESC
LIMIT 20;
```

#### 6.3.3 策略三：加权融合

```sql
-- 同时计算关键词得分和语义得分，加权融合
SELECT id, title, description,
       ts_rank(combined_tsvector, keyword_query) AS keyword_score,
       1 - (combined_vector <=> query_vector) AS semantic_score,
       (ts_rank(combined_tsvector, keyword_query) * 0.4 +
        (1 - (combined_vector <=> query_vector)) * 0.6) AS final_score
FROM ad_cases,
     to_tsquery('zhparser', '关键词') AS keyword_query
WHERE combined_tsvector @@ keyword_query
  AND combined_vector IS NOT NULL
ORDER BY final_score DESC
LIMIT 20;
```

### 6.4 检索 API 设计

#### 6.4.1 关键词检索 API

```python
from fastapi import FastAPI, Query
from typing import Optional, List

app = FastAPI()

@app.get("/api/cases/search")
async def search_cases(
    keyword: str = Query(..., description="搜索关键词"),
    fields: Optional[str] = Query("all", description="搜索字段: title, description, all"),
    brand_industry: Optional[str] = None,
    activity_type: Optional[str] = None,
    location: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("relevance", description="排序方式: relevance, score, favourite, time")
):
    """
    关键词检索API
    """
    # 构建查询
    # 执行检索
    # 返回结果
    pass
```

#### 6.4.2 语义检索 API

```python
from FlagEmbedding import FlagModel
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# 全局模型实例（应用启动时加载）
model = FlagModel(
    'BAAI/bge-large-zh-v1.5',
    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
)

@app.post("/api/cases/semantic-search")
async def semantic_search(
    query: str = Query(..., description="自然语言查询"),
    brand_industry: Optional[str] = None,
    activity_type: Optional[str] = None,
    similarity_threshold: float = Query(0.5, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    语义检索API（使用 BGE-large-zh）
    """
    # 1. 将查询转换为向量（BGE 会自动应用 query_instruction）
    query_vector = model.encode(query, normalize=True)
    query_vector_list = query_vector.tolist()

    # 2. 构建 SQL 查询
    conn = psycopg2.connect(...)  # 数据库连接
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 构建 WHERE 条件
    where_conditions = ["combined_vector IS NOT NULL"]
    params = [query_vector_list]
    param_index = 2

    if brand_industry:
        where_conditions.append(f"brand_industry = ${param_index}")
        params.append(brand_industry)
        param_index += 1

    if activity_type:
        where_conditions.append(f"activity_type = ${param_index}")
        params.append(activity_type)
        param_index += 1

    where_clause = " AND ".join(where_conditions)

    # 3. 执行向量检索
    sql = f"""
        SELECT id, case_id, title, description, brand_industry, activity_type,
               1 - (combined_vector <=> $1::vector(1024)) AS similarity
        FROM ad_cases
        WHERE {where_clause}
          AND (1 - (combined_vector <=> $1::vector(1024))) >= ${param_index}
        ORDER BY combined_vector <=> $1::vector(1024)
        LIMIT ${param_index + 1}
    """
    params.append(similarity_threshold)
    params.append(limit)

    cur.execute(sql, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    # 4. 返回结果
    return {
        "total": len(results),
        "results": [dict(row) for row in results]
    }
```

#### 6.4.3 混合检索 API

```python
from FlagEmbedding import FlagModel
import psycopg2
from psycopg2.extras import RealDictCursor

# 全局模型实例
model = FlagModel(
    'BAAI/bge-large-zh-v1.5',
    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
)

@app.post("/api/cases/hybrid-search")
async def hybrid_search(
    query: str = Query(..., description="查询文本"),
    keyword: Optional[str] = None,
    semantic_weight: float = Query(0.6, ge=0, le=1),
    keyword_weight: float = Query(0.4, ge=0, le=1),
    filters: Optional[dict] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    混合检索API（关键词 + 语义，使用 BGE-large-zh）
    """
    # 1. 将查询转换为向量
    query_vector = model.encode(query, normalize=True)
    query_vector_list = query_vector.tolist()

    # 2. 构建 SQL 查询（同时计算关键词得分和语义得分）
    conn = psycopg2.connect(...)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 构建 WHERE 条件
    where_conditions = ["combined_vector IS NOT NULL"]
    params = [query_vector_list]
    param_index = 2

    # 关键词过滤（如果提供）
    keyword_query = None
    if keyword:
        where_conditions.append(f"combined_tsvector @@ to_tsquery('zhparser', ${param_index})")
        params.append(keyword)
        keyword_query = f"to_tsquery('zhparser', ${param_index})"
        param_index += 1

    # 其他过滤条件
    if filters:
        if filters.get('brand_industry'):
            where_conditions.append(f"brand_industry = ${param_index}")
            params.append(filters['brand_industry'])
            param_index += 1
        if filters.get('activity_type'):
            where_conditions.append(f"activity_type = ${param_index}")
            params.append(filters['activity_type'])
            param_index += 1

    where_clause = " AND ".join(where_conditions)

    # 3. 构建 SELECT 语句（计算加权得分）
    if keyword:
        sql = f"""
            SELECT id, case_id, title, description,
                   ts_rank(combined_tsvector, {keyword_query}) AS keyword_score,
                   1 - (combined_vector <=> $1::vector(1024)) AS semantic_score,
                   (ts_rank(combined_tsvector, {keyword_query}) * ${param_index} +
                    (1 - (combined_vector <=> $1::vector(1024))) * ${param_index + 1}) AS final_score
            FROM ad_cases
            WHERE {where_clause}
            ORDER BY final_score DESC
            LIMIT ${param_index + 2}
        """
        params.extend([keyword_weight, semantic_weight, limit])
    else:
        # 只有语义检索
        sql = f"""
            SELECT id, case_id, title, description,
                   1 - (combined_vector <=> $1::vector(1024)) AS semantic_score,
                   1 - (combined_vector <=> $1::vector(1024)) AS final_score
            FROM ad_cases
            WHERE {where_clause}
            ORDER BY combined_vector <=> $1::vector(1024)
            LIMIT ${param_index}
        """
        params.append(limit)

    cur.execute(sql, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    # 4. 返回结果
    return {
        "total": len(results),
        "results": [dict(row) for row in results]
    }
```

## 7. 性能优化方案

### 7.1 索引优化

#### 7.1.1 索引维护

- **定期重建索引**：对于频繁更新的表，定期重建索引以保持性能
- **监控索引使用情况**：使用 `pg_stat_user_indexes` 监控索引使用率
- **删除未使用的索引**：删除长期未使用的索引以节省空间

#### 7.1.2 索引参数调优

**HNSW 索引参数调优**：

```sql
-- 对于查询性能要求高的场景，可以增加 m 和 ef_construction
CREATE INDEX idx_ad_cases_combined_vector ON ad_cases
    USING hnsw (combined_vector vector_cosine_ops)
    WITH (m = 32, ef_construction = 128);

-- 查询时调整 ef_search 参数（默认40）
SET hnsw.ef_search = 100;  -- 增加搜索精度，但会降低速度
```

### 7.2 查询优化

#### 7.2.1 查询计划分析

使用 `EXPLAIN ANALYZE` 分析查询计划：

```sql
EXPLAIN ANALYZE
SELECT id, title, description
FROM ad_cases
WHERE combined_tsvector @@ to_tsquery('zhparser', '关键词')
ORDER BY ts_rank(combined_tsvector, to_tsquery('zhparser', '关键词')) DESC
LIMIT 20;
```

#### 7.2.2 查询优化技巧

1. **限制结果集大小**：始终使用 `LIMIT` 限制返回结果数量
2. **避免全表扫描**：确保查询条件能够使用索引
3. **使用覆盖索引**：如果可能，使用包含所有查询字段的索引
4. **分页优化**：使用游标分页而非 OFFSET（对于大数据集）

### 7.3 缓存策略

#### 7.3.1 查询结果缓存

对于热门查询，使用 Redis 缓存结果：

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cached_search(keyword: str, cache_ttl: int = 3600):
    """
    带缓存的搜索
    """
    cache_key = f"search:{keyword}"

    # 尝试从缓存获取
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # 执行查询
    result = execute_search(keyword)

    # 写入缓存
    redis_client.setex(cache_key, cache_ttl, json.dumps(result))

    return result
```

#### 7.3.2 向量缓存

对于频繁查询的向量，可以缓存：

```python
def cached_encode(text: str):
    """
    带缓存的向量编码
    """
    cache_key = f"vector:{hash(text)}"

    cached_vector = redis_client.get(cache_key)
    if cached_vector:
        return json.loads(cached_vector)

    vector = model.encode(text)
    redis_client.setex(cache_key, 86400, json.dumps(vector.tolist()))

    return vector
```

### 7.4 数据库配置优化

#### 7.4.1 PostgreSQL 配置

```conf
# postgresql.conf

# 内存配置
shared_buffers = 4GB  # 根据服务器内存调整
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

# 查询优化
random_page_cost = 1.1  # SSD 优化
effective_io_concurrency = 200

# 连接配置
max_connections = 200
```

#### 7.4.2 pgvector 配置

```sql
-- 调整 HNSW 搜索参数（会话级别）
SET hnsw.ef_search = 100;  -- 默认40，增加可提高精度但降低速度
```

## 8. 数据迁移方案

### 8.1 迁移流程

#### 8.1.1 数据准备

1. **数据清洗**：

   - 去除重复数据
   - 验证数据格式
   - 处理缺失值

2. **数据转换**：
   - JSON 数组转换为 PostgreSQL JSONB
   - 日期字符串转换为 DATE 类型
   - URL 规范化

#### 8.1.2 批量导入

```python
import json
import psycopg2
from psycopg2.extras import execute_batch

def migrate_json_to_db(json_file: str, batch_size: int = 100):
    """
    从JSON文件批量导入数据到PostgreSQL
    """
    # 1. 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cases = data.get('cases', [])

    # 2. 连接数据库
    conn = psycopg2.connect(
        host='localhost',
        database='ad_case_db',
        user='postgres',
        password='password'
    )
    cur = conn.cursor()

    # 3. 批量插入（不包含向量）
    insert_sql = """
        INSERT INTO ad_cases (
            case_id, source_url, title, description, author, publish_time,
            main_image, images, video_url,
            brand_name, brand_industry, activity_type, location, tags,
            score, score_decimal, favourite,
            company_name, company_logo, agency_name
        ) VALUES (
            %(case_id)s, %(source_url)s, %(title)s, %(description)s,
            %(author)s, %(publish_time)s,
            %(main_image)s, %(images)s::jsonb, %(video_url)s,
            %(brand_name)s, %(brand_industry)s, %(activity_type)s,
            %(location)s, %(tags)s::jsonb,
            %(score)s, %(score_decimal)s, %(favourite)s,
            %(company_name)s, %(company_logo)s, %(agency_name)s
        )
        ON CONFLICT (case_id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP
    """

    # 准备数据
    case_data = []
    for case in cases:
        case_data.append({
            'case_id': case.get('case_id'),
            'source_url': case.get('source_url'),
            'title': case.get('title'),
            'description': case.get('description'),
            'author': case.get('author'),
            'publish_time': case.get('publish_time'),
            'main_image': case.get('main_image'),
            'images': json.dumps(case.get('images', [])),
            'video_url': case.get('video_url'),
            'brand_name': case.get('brand_name'),
            'brand_industry': case.get('brand_industry'),
            'activity_type': case.get('activity_type'),
            'location': case.get('location'),
            'tags': json.dumps(case.get('tags', [])),
            'score': case.get('score'),
            'score_decimal': case.get('score_decimal'),
            'favourite': case.get('favourite'),
            'company_name': case.get('company_name'),
            'company_logo': case.get('company_logo'),
            'agency_name': case.get('agency_name')
        })

    # 批量执行
    execute_batch(cur, insert_sql, case_data, page_size=batch_size)

    conn.commit()
    cur.close()
    conn.close()

    print(f"成功导入 {len(cases)} 条案例")
```

#### 8.1.3 向量生成和更新

```python
def generate_and_update_vectors(batch_size: int = 32):
    """
    批量生成并更新向量（使用 BGE-large-zh，1024维）

    Args:
        batch_size: 批次大小
    """
    from FlagEmbedding import FlagModel
    import psycopg2
    from psycopg2.extras import execute_batch

    # 初始化 BGE-large-zh 模型
    model = FlagModel(
        'BAAI/bge-large-zh-v1.5',
        query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
    )

    # 向量维度：1024（BGE-large-zh）
    vector_dim = 1024

    conn = psycopg2.connect(...)
    cur = conn.cursor()

    # 1. 查询所有需要生成向量的案例
    cur.execute("""
        SELECT id, case_id, title, description
        FROM ad_cases
        WHERE combined_vector IS NULL
        ORDER BY id
    """)

    cases = cur.fetchall()

    # 2. 批量生成向量
    for i in range(0, len(cases), batch_size):
        batch = cases[i:i + batch_size]

        # 准备文本
        texts = []
        case_ids = []
        for case in batch:
            title = case[2] or ''
            description = case[3] or ''
            combined = f"{title} {description}".strip()
            texts.append(combined)
            case_ids.append(case[0])

        # 批量编码（BGE 模型支持批量编码）
        vectors = model.encode(texts, normalize=True, batch_size=batch_size)

        # 批量更新
        update_sql = """
            UPDATE ad_cases
            SET combined_vector = %s::vector(1024)
            WHERE id = %s
        """

        update_data = [
            (vectors[j].tolist(), case_ids[j])
            for j in range(len(batch))
        ]

        execute_batch(cur, update_sql, update_data)

        conn.commit()
        print(f"已处理 {i + len(batch)} / {len(cases)} 条案例")

    cur.close()
    conn.close()
```

### 8.2 迁移脚本

完整的迁移脚本示例：

```python
#!/usr/bin/env python3
"""
数据迁移脚本
从JSON文件迁移到PostgreSQL数据库
"""

import json
import psycopg2
from psycopg2.extras import execute_batch
from text2vec import SentenceModel
import argparse

def main():
    parser = argparse.ArgumentParser(description='数据迁移脚本')
    parser.add_argument('--json-file', required=True, help='JSON数据文件路径')
    parser.add_argument('--db-host', default='localhost', help='数据库主机')
    parser.add_argument('--db-name', required=True, help='数据库名称')
    parser.add_argument('--db-user', required=True, help='数据库用户')
    parser.add_argument('--db-password', required=True, help='数据库密码')
    parser.add_argument('--batch-size', type=int, default=100, help='批次大小')
    parser.add_argument('--skip-vectors', action='store_true', help='跳过向量生成')

    args = parser.parse_args()

    # 1. 导入基础数据
    print("开始导入基础数据...")
    migrate_json_to_db(
        args.json_file,
        args.db_host,
        args.db_name,
        args.db_user,
        args.db_password,
        args.batch_size
    )

    # 2. 生成向量（如果未跳过）
    if not args.skip_vectors:
        print("开始生成向量...")
        generate_and_update_vectors(
            args.db_host,
            args.db_name,
            args.db_user,
            args.db_password,
            batch_size=32
        )

    print("迁移完成！")

if __name__ == '__main__':
    main()
```

## 9. BGE-large-zh 快速开始

### 9.1 安装依赖

```bash
# 安装 FlagEmbedding 库
pip install FlagEmbedding

# 或者使用 conda
conda install -c conda-forge flagembedding
```

### 9.2 基本使用示例

```python
from FlagEmbedding import FlagModel

# 初始化模型（首次运行会自动下载模型，约 1.2GB）
model = FlagModel(
    'BAAI/bge-large-zh-v1.5',
    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
)

# 单个文本编码
text = "宜家把时间就是金钱变成了现实"
vector = model.encode(text, normalize=True)
print(f"向量维度: {vector.shape}")  # (1024,)

# 批量编码
texts = ["文本1", "文本2", "文本3"]
vectors = model.encode(texts, normalize=True, batch_size=32)
print(f"批量向量维度: {vectors.shape}")  # (3, 1024)

# 查询编码（会自动应用 query_instruction）
query = "找一些关于情感营销的案例"
query_vector = model.encode(query, normalize=True)
```

### 9.3 注意事项

1. **首次使用**：首次运行会自动从 HuggingFace 下载模型（约 1.2GB），需要网络连接
2. **内存要求**：模型加载需要约 2-3GB 内存
3. **GPU 加速**：如果有 GPU，会自动使用 GPU 加速
4. **文本长度**：BGE-large-zh 最大支持 512 tokens，超长文本会被截断
5. **向量归一化**：建议始终使用 `normalize=True`，提高检索效果

### 9.4 性能优化建议

1. **模型复用**：在应用启动时加载一次模型，避免重复加载
2. **批量处理**：使用批量编码（`batch_size`）提高效率
3. **GPU 加速**：如果有 GPU，确保 CUDA 环境正确配置
4. **缓存机制**：对频繁查询的文本进行向量缓存

## 10. 总结

### 10.1 技术方案总结

本方案采用 **PostgreSQL + pgvector + 全文检索 + BGE-large-zh** 的一体化架构，实现了：

1. ✅ **结构化数据存储**：使用 PostgreSQL 存储所有结构化数据
2. ✅ **关键词检索**：使用 PostgreSQL 全文检索（GIN 索引）+ 中文分词（zhparser）
3. ✅ **语义检索**：使用 pgvector + BGE-large-zh（1024 维）实现向量检索
4. ✅ **混合检索**：支持关键词和语义检索的组合使用

**核心技术栈**：

- **数据库**：PostgreSQL 12+
- **向量扩展**：pgvector 0.5.0+
- **中文分词**：zhparser
- **嵌入模型**：BGE-large-zh（BAAI/bge-large-zh-v1.5，1024 维）

### 10.2 核心优势

- **架构简单**：单一数据库系统，降低运维复杂度
- **性能优秀**：针对中小规模数据（< 100 万条）性能完全够用
- **功能完整**：满足所有检索需求
- **成本低廉**：完全开源，无需额外基础设施

### 10.3 后续优化方向

1. **性能优化**：根据实际使用情况调整索引参数和查询策略
2. **功能扩展**：支持更多检索维度（如时间范围、评分范围等）
3. **用户体验**：优化检索结果排序算法，提高相关性
4. **监控告警**：建立性能监控和告警机制

---

**文档版本**：v1.0  
**创建时间**：2026-01-13  
**最后更新**：2026-01-13
