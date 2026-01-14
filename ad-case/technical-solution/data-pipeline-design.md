# 爬取数据到入库方案设计

## 1. 需求分析

### 1.1 业务场景

- **数据源**：广告门网站（通过 API 和 HTML 解析）
- **数据量**：初期数万条，未来可能数十万条
- **更新频率**：定期爬取（每日/每周）
- **数据特点**：
  - 需要爬取列表页和详情页
  - 详情页需要 HTML 解析
  - 需要生成向量（BGE-large-zh）
  - 需要处理 CSRF Token 等反爬机制

### 1.2 核心需求

1. **可靠性**：爬取失败不影响已爬取数据
2. **可恢复性**：支持断点续传，失败后可重试
3. **可观测性**：能够监控爬取进度和状态
4. **性能**：支持批量处理和并发控制
5. **数据一致性**：避免重复数据，支持增量更新

## 2. 方案对比

### 方案一：直接爬取并入库（Streaming Pipeline）

**架构流程**：

```
爬取任务 → 获取列表页 → 解析详情页 → 生成向量 → 直接入库 → 完成
```

**实现方式**：

```python
def crawl_and_insert():
    """直接爬取并入库"""
    # 1. 获取列表页
    items = api_client.get_creative_list_paginated()

    # 2. 遍历每个案例
    for item in items:
        # 3. 解析详情页
        detail = detail_parser.parse(item['url'])

        # 4. 生成向量
        vectors = generate_vectors(detail)

        # 5. 直接入库
        insert_to_database(detail, vectors)
```

**优点**：

- ✅ **实时性好**：数据立即入库，无需等待
- ✅ **存储空间小**：不需要中间文件存储
- ✅ **流程简单**：一步到位，代码逻辑清晰
- ✅ **内存占用低**：逐条处理，不需要一次性加载所有数据

**缺点**：

- ❌ **容错性差**：爬取失败可能导致数据丢失
- ❌ **难以重试**：失败后需要重新爬取整个流程
- ❌ **调试困难**：无法查看中间数据，难以定位问题
- ❌ **难以并行**：爬取和入库耦合，难以分离优化
- ❌ **数据验证困难**：入库前无法批量验证数据质量

### 方案二：先爬取保存 JSON，再入库（Batch Pipeline）

**架构流程**：

```
爬取任务 → 获取列表页 → 解析详情页 → 保存JSON → [验证] → 读取JSON → 生成向量 → 批量入库 → 完成
```

**实现方式**：

```python
# 阶段1：爬取并保存JSON
def crawl_to_json():
    """爬取数据并保存到JSON"""
    all_cases = []
    for item in api_client.get_creative_list_paginated():
        detail = detail_parser.parse(item['url'])
        all_cases.append(detail)

    # 保存到JSON文件
    with open('data/cases_batch_001.json', 'w') as f:
        json.dump(all_cases, f)

# 阶段2：从JSON读取并入库
def json_to_database():
    """从JSON文件读取并入库"""
    with open('data/cases_batch_001.json', 'r') as f:
        cases = json.load(f)

    # 批量生成向量
    cases_with_vectors = batch_generate_vectors(cases)

    # 批量入库
    batch_insert_to_database(cases_with_vectors)
```

**优点**：

- ✅ **容错性强**：爬取失败不影响已保存的数据
- ✅ **易于重试**：可以单独重跑入库流程
- ✅ **调试方便**：可以查看 JSON 文件，验证数据质量
- ✅ **可并行处理**：爬取和入库可以分离，独立优化
- ✅ **支持增量**：可以对比 JSON 文件，只处理新数据
- ✅ **数据备份**：JSON 文件可作为数据备份

**缺点**：

- ❌ **存储空间大**：需要存储中间 JSON 文件
- ❌ **实时性差**：需要等待爬取完成才能入库
- ❌ **流程复杂**：需要两个阶段，管理成本高
- ❌ **内存占用**：批量处理时需要加载所有数据到内存

### 方案三：消息队列 + 异步处理（Queue-based Pipeline）

**架构流程**：

```
爬取任务 → 获取列表页 → 解析详情页 → 发送消息队列 → [队列] → 消费者 → 生成向量 → 入库 → 完成
```

**实现方式**：

```python
# 生产者：爬取并发送到队列
def crawl_to_queue():
    """爬取数据并发送到消息队列"""
    for item in api_client.get_creative_list_paginated():
        detail = detail_parser.parse(item['url'])
        # 发送到消息队列
        queue.send_message(detail)

# 消费者：从队列读取并入库
def queue_to_database():
    """从消息队列读取并入库"""
    while True:
        message = queue.receive_message()
        if message:
            detail = message.data
            vectors = generate_vectors(detail)
            insert_to_database(detail, vectors)
            queue.ack_message(message)
```

**优点**：

- ✅ **解耦性好**：爬取和入库完全解耦
- ✅ **可扩展性强**：可以启动多个消费者并行处理
- ✅ **容错性强**：消息队列保证数据不丢失
- ✅ **支持重试**：失败的消息可以重新消费
- ✅ **实时性好**：数据可以实时处理

**缺点**：

- ❌ **架构复杂**：需要引入消息队列中间件（Redis/RabbitMQ/Kafka）
- ❌ **运维成本高**：需要维护消息队列服务
- ❌ **学习成本**：团队需要熟悉消息队列的使用
- ❌ **可能过度设计**：对于中小规模数据可能不需要

### 方案四：混合方案（Hybrid Pipeline）

**架构流程**：

```
爬取任务 → 获取列表页 → 解析详情页 → [保存JSON + 发送队列] →
    → JSON备份（用于数据恢复和验证）
    → 消息队列（用于实时入库）
```

**实现方式**：

```python
def crawl_with_backup():
    """爬取数据，同时保存JSON和发送队列"""
    all_cases = []

    for item in api_client.get_creative_list_paginated():
        detail = detail_parser.parse(item['url'])

        # 1. 保存到JSON（备份）
        all_cases.append(detail)

        # 2. 发送到队列（实时处理）
        queue.send_message(detail)

    # 3. 批量保存JSON（最终备份）
    save_to_json(all_cases)
```

**优点**：

- ✅ **兼顾实时和备份**：既有实时处理，又有数据备份
- ✅ **容错性强**：队列失败可以从 JSON 恢复
- ✅ **灵活性高**：可以根据需要选择处理方式

**缺点**：

- ❌ **复杂度最高**：需要维护两套流程
- ❌ **资源消耗大**：需要存储和队列双重资源

## 3. 方案对比表

| 维度           | 方案一：直接入库 | 方案二：JSON 中间文件 | 方案三：消息队列 | 方案四：混合方案 |
| -------------- | ---------------- | --------------------- | ---------------- | ---------------- |
| **实时性**     | ⭐⭐⭐⭐⭐       | ⭐⭐                  | ⭐⭐⭐⭐⭐       | ⭐⭐⭐⭐         |
| **容错性**     | ⭐⭐             | ⭐⭐⭐⭐⭐            | ⭐⭐⭐⭐         | ⭐⭐⭐⭐⭐       |
| **可恢复性**   | ⭐               | ⭐⭐⭐⭐⭐            | ⭐⭐⭐⭐         | ⭐⭐⭐⭐⭐       |
| **调试便利性** | ⭐⭐             | ⭐⭐⭐⭐⭐            | ⭐⭐⭐           | ⭐⭐⭐⭐         |
| **架构复杂度** | ⭐⭐⭐⭐⭐       | ⭐⭐⭐⭐              | ⭐⭐             | ⭐               |
| **运维成本**   | ⭐⭐⭐⭐⭐       | ⭐⭐⭐⭐              | ⭐⭐             | ⭐               |
| **存储成本**   | ⭐⭐⭐⭐⭐       | ⭐⭐⭐                | ⭐⭐⭐⭐         | ⭐⭐             |
| **性能**       | ⭐⭐⭐⭐         | ⭐⭐⭐                | ⭐⭐⭐⭐⭐       | ⭐⭐⭐⭐         |
| **适用规模**   | 小规模           | 中小规模              | 大规模           | 大规模           |

## 4. 业界常见做法

### 4.1 小规模数据（< 10 万条）

**常见做法**：**方案二（JSON 中间文件）**

**原因**：

1. **数据量小**：JSON 文件不会太大，存储成本可接受
2. **容错需求高**：小团队更需要简单可靠的方案
3. **调试便利**：可以方便地查看和验证数据
4. **无需复杂架构**：不需要引入额外的中间件

**典型案例**：

- 数据采集脚本
- 数据迁移工具
- 小规模爬虫项目

### 4.2 中等规模数据（10 万 - 100 万条）

**常见做法**：**方案二（JSON 中间文件）或方案三（消息队列）**

**选择依据**：

- **团队规模小**：选择方案二
- **团队规模大**：选择方案三
- **实时性要求高**：选择方案三
- **实时性要求低**：选择方案二

### 4.3 大规模数据（> 100 万条）

**常见做法**：**方案三（消息队列）或方案四（混合方案）**

**原因**：

1. **性能要求高**：需要并行处理
2. **可靠性要求高**：需要消息队列保证数据不丢失
3. **可扩展性强**：可以动态扩展消费者

**典型案例**：

- 大型数据采集平台
- 实时数据处理系统
- 企业级数据管道

## 5. 推荐方案

### 5.1 当前项目推荐：方案二（JSON 中间文件）

**推荐理由**：

1. **数据规模适中**：初期数万条，JSON 文件大小可控（每 10 万条约 100-200MB）
2. **团队规模**：中小团队，需要简单可靠的方案
3. **容错需求**：爬取可能失败，需要能够重试
4. **调试需求**：需要能够查看和验证数据质量
5. **成本考虑**：不需要引入额外的中间件，降低运维成本

### 5.2 方案二优化设计

#### 5.2.1 分阶段处理

**阶段 1：爬取阶段（Crawl Stage）**

```python
def crawl_stage(output_dir: Path, batch_size: int = 100):
    """
    爬取阶段：爬取数据并保存到JSON文件

    Args:
        output_dir: 输出目录
        batch_size: 每批保存的案例数量
    """
    api_client = AdquanAPIClient()
    detail_parser = DetailPageParser(session=api_client.session)

    all_cases = []
    batch_num = 0

    for item in api_client.get_creative_list_paginated():
        try:
            # 解析详情页
            detail = detail_parser.parse(item['url'])

            # 合并数据
            case_data = {
                **item,
                **detail
            }

            all_cases.append(case_data)

            # 达到批次大小，保存JSON
            if len(all_cases) >= batch_size:
                save_batch_json(all_cases, output_dir, batch_num)
                all_cases = []
                batch_num += 1

        except Exception as e:
            logger.error(f"爬取失败: {e}")
            # 记录失败，继续处理
            continue

    # 保存剩余数据
    if all_cases:
        save_batch_json(all_cases, output_dir, batch_num)
```

**阶段 2：入库阶段（Import Stage）**

```python
def import_stage(json_files: List[Path], skip_existing: bool = True):
    """
    入库阶段：从JSON文件读取并入库

    Args:
        json_files: JSON文件列表
        skip_existing: 是否跳过已存在的案例
    """
    model = FlagModel('BAAI/bge-large-zh-v1.5', ...)

    for json_file in json_files:
        # 读取JSON
        with open(json_file, 'r') as f:
            cases = json.load(f)['cases']

        # 批量生成向量
        cases_with_vectors = []
        for case in cases:
            vectors = generate_vectors(case, model)
            case['combined_vector'] = vectors['combined_vector']
            cases_with_vectors.append(case)

        # 批量入库
        batch_insert_to_database(cases_with_vectors, skip_existing)
```

#### 5.2.2 断点续传支持

```python
def crawl_with_resume(output_dir: Path, resume_file: Path = None):
    """
    支持断点续传的爬取

    Args:
        output_dir: 输出目录
        resume_file: 断点续传文件（记录已爬取的case_id）
    """
    # 加载已爬取的case_id
    crawled_ids = set()
    if resume_file and resume_file.exists():
        with open(resume_file, 'r') as f:
            crawled_ids = set(json.load(f))

    # 爬取时跳过已爬取的案例
    for item in api_client.get_creative_list_paginated():
        if item['id'] in crawled_ids:
            continue

        # 爬取并保存
        # ...

        # 更新已爬取列表
        crawled_ids.add(item['id'])
        save_resume_file(resume_file, crawled_ids)
```

#### 5.2.3 数据验证

```python
def validate_cases(cases: List[dict]) -> Tuple[List[dict], List[dict]]:
    """
    验证案例数据

    Returns:
        (valid_cases, invalid_cases)
    """
    valid_cases = []
    invalid_cases = []

    for case in cases:
        # 验证必需字段
        if not case.get('case_id'):
            invalid_cases.append({**case, 'error': '缺少case_id'})
            continue

        if not case.get('title'):
            invalid_cases.append({**case, 'error': '缺少title'})
            continue

        # 验证数据格式
        if case.get('publish_time') and not is_valid_date(case['publish_time']):
            invalid_cases.append({**case, 'error': '日期格式错误'})
            continue

        valid_cases.append(case)

    return valid_cases, invalid_cases
```

#### 5.2.4 增量更新支持

```python
def incremental_import(json_file: Path):
    """
    增量导入：只导入新案例

    Args:
        json_file: JSON文件路径
    """
    # 1. 读取JSON文件
    with open(json_file, 'r') as f:
        cases = json.load(f)['cases']

    # 2. 查询数据库中已存在的case_id
    existing_ids = get_existing_case_ids()

    # 3. 过滤出新案例
    new_cases = [c for c in cases if c['case_id'] not in existing_ids]

    # 4. 只处理新案例
    if new_cases:
        import_cases(new_cases)
```

## 6. 实施建议

### 6.1 第一阶段：基础实现（方案二）

**目标**：实现基本的爬取和入库功能

**步骤**：

1. **实现爬取阶段**

   - 爬取列表页和详情页
   - 保存到 JSON 文件（按批次）
   - 支持断点续传

2. **实现入库阶段**

   - 读取 JSON 文件
   - 生成向量
   - 批量入库

3. **实现数据验证**
   - 验证数据完整性
   - 记录错误数据

### 6.2 第二阶段：优化和增强

**目标**：提高可靠性和性能

**优化点**：

1. **并发优化**

   - 爬取阶段：多线程爬取详情页
   - 入库阶段：批量插入优化

2. **监控和日志**

   - 添加进度监控
   - 添加错误统计
   - 添加性能指标

3. **增量更新**
   - 支持增量爬取
   - 支持增量入库

### 6.3 第三阶段：架构升级（可选）

**如果数据量增长到百万级**：

考虑升级到**方案三（消息队列）**

**迁移路径**：

1. 保持 JSON 文件作为备份
2. 引入消息队列（Redis Queue 或 RabbitMQ）
3. 爬取阶段同时发送到队列和保存 JSON
4. 逐步迁移到纯队列方案

## 7. 代码结构建议

```
ad-case/
├── spider/                    # 爬虫模块
│   ├── api_client.py         # API客户端
│   ├── detail_parser.py      # 详情页解析器
│   └── crawler.py            # 爬取主程序
├── pipeline/                  # 数据管道模块
│   ├── crawl_stage.py        # 爬取阶段
│   ├── import_stage.py       # 入库阶段
│   ├── validator.py          # 数据验证
│   └── utils.py              # 工具函数
├── data/                      # 数据目录
│   ├── json/                 # JSON文件
│   │   ├── cases_batch_001.json
│   │   └── cases_batch_002.json
│   └── logs/                 # 日志文件
└── scripts/                  # 脚本目录
    ├── crawl.py              # 爬取脚本
    ├── import.py             # 入库脚本
    └── validate.py           # 验证脚本
```

## 8. 总结

### 8.1 最终选择

**已选择方案：方案二（JSON 中间文件）** ✅

**核心优势**：

1. ✅ **简单可靠**：适合中小规模数据
2. ✅ **容错性强**：支持断点续传和重试
3. ✅ **易于调试**：可以查看中间数据
4. ✅ **成本低**：不需要额外中间件

### 8.2 实施路径

1. **立即实施**：方案二（JSON 中间文件）
2. **未来扩展**：如果数据量增长，考虑方案三（消息队列）

### 8.3 关键设计点

1. **分批次保存**：避免单个 JSON 文件过大
2. **断点续传**：支持失败后继续爬取
3. **数据验证**：入库前验证数据质量
4. **增量更新**：支持只处理新数据
5. **监控日志**：记录爬取进度和错误

---

**文档版本**：v1.0  
**创建时间**：2026-01-13  
**最后更新**：2026-01-13
