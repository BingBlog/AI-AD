# 爬取任务架构优化方案

## 1. 当前问题分析

### 1.1 问题描述

当前爬取任务存在以下三个核心问题：

1. **缺少对列表页爬取结果的记录**
   - 当前只记录任务级别的统计信息（total_crawled, total_saved等）
   - 无法知道具体哪些列表页爬取成功，哪些失败
   - 无法记录每个列表页的爬取时间、案例数量、错误信息等

2. **缺少对每个案例爬取结果的记录**
   - 失败案例只保存在JSON文件中（带error字段），没有数据库记录
   - 无法快速查询哪些案例失败了，失败原因是什么
   - 无法统计失败案例的分布情况（按错误类型、按时间等）

3. **无法精确重试失败的列表页或案例**
   - 因为缺少记录，无法知道具体哪些列表页或案例失败了
   - 重试时只能重新爬取整个任务，无法精确重试失败的列表页或案例
   - 导致重试效率低，浪费资源

### 1.2 当前架构分析

#### 架构分层

```
┌─────────────────────────────────────────────────────────┐
│ API层 (Routers)                                         │
│ - crawl_tasks.py: HTTP接口处理                          │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│ 服务层 (Services)                                        │
│ - crawl_task_service.py: 任务管理逻辑                   │
│ - crawl_task_executor.py: 任务执行器                     │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│ 爬取层 (Pipeline)                                       │
│ - crawl_stage.py: 爬取流程控制                          │
│   ├─ api_client.py: 列表页API调用                       │
│   └─ detail_parser.py: 详情页解析                        │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│ 数据层 (Database)                                       │
│ - crawl_tasks: 任务基本信息                              │
│ - crawl_task_logs: 任务日志                             │
│ - crawl_task_status_history: 状态历史                    │
└─────────────────────────────────────────────────────────┘
```

#### 当前数据流

```
任务创建
  ↓
任务执行 (CrawlTaskExecutor)
  ↓
爬取阶段 (CrawlStage)
  ├─ 获取列表页 (get_creative_list_paginated)
  │   └─ 返回所有案例列表项 (无记录)
  │
  └─ 遍历每个案例
      ├─ 解析详情页 (parse)
      ├─ 验证数据 (validate_case)
      ├─ 保存到批次 (current_batch)
      └─ 失败时记录到JSON (带error字段)
  ↓
保存批次文件 (cases_batch_*.json)
  ↓
更新任务统计 (total_crawled, total_saved, total_failed)
```

#### 问题根源

1. **记录粒度不够细**：只记录任务级别的统计，没有记录列表页和案例级别的详细信息
2. **记录位置不当**：失败记录只保存在JSON文件中，没有数据库记录，无法快速查询和分析
3. **缺少关联关系**：列表页、案例、任务之间缺少明确的关联关系

## 2. 优化方案设计

### 2.1 数据库设计

#### 2.1.1 新增表：列表页爬取记录表 (crawl_list_pages)

**目的**：记录每个列表页的爬取结果

```sql
CREATE TABLE IF NOT EXISTS crawl_list_pages (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    page_number INTEGER NOT NULL,
    
    -- 爬取状态
    status VARCHAR(32) NOT NULL, -- success, failed, skipped
    error_message TEXT,
    error_type VARCHAR(64), -- network_error, parse_error, api_error, etc.
    
    -- 爬取结果
    items_count INTEGER DEFAULT 0, -- 获取到的案例数量
    crawled_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT, -- 爬取耗时（秒）
    
    -- 重试信息
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped', 'pending')),
    CONSTRAINT unique_task_page UNIQUE (task_id, page_number)
);

CREATE INDEX idx_crawl_list_pages_task_id ON crawl_list_pages(task_id);
CREATE INDEX idx_crawl_list_pages_status ON crawl_list_pages(status);
CREATE INDEX idx_crawl_list_pages_task_status ON crawl_list_pages(task_id, status);
```

#### 2.1.2 新增表：案例爬取记录表 (crawl_case_records)

**目的**：记录每个案例的爬取结果

```sql
CREATE TABLE IF NOT EXISTS crawl_case_records (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    list_page_id BIGINT, -- 关联到 crawl_list_pages.id
    
    -- 案例标识
    case_id INTEGER, -- 原始案例ID
    case_url TEXT,
    case_title VARCHAR(500),
    
    -- 爬取状态
    status VARCHAR(32) NOT NULL, -- success, failed, skipped, validation_failed
    error_message TEXT,
    error_type VARCHAR(64), -- network_error, parse_error, validation_error, etc.
    error_stack TEXT, -- 详细错误堆栈
    
    -- 爬取结果
    crawled_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT, -- 爬取耗时（秒）
    
    -- 数据质量
    has_detail_data BOOLEAN DEFAULT FALSE, -- 是否成功获取详情页数据
    has_validation_error BOOLEAN DEFAULT FALSE, -- 是否有验证错误
    validation_errors JSONB, -- 验证错误详情
    
    -- 保存状态
    saved_to_json BOOLEAN DEFAULT FALSE, -- 是否已保存到JSON文件
    batch_file_name VARCHAR(255), -- 保存到的批次文件名
    
    -- 重试信息
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (list_page_id) REFERENCES crawl_list_pages(id) ON DELETE SET NULL,
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped', 'validation_failed', 'pending')),
    CONSTRAINT unique_task_case UNIQUE (task_id, case_id)
);

CREATE INDEX idx_crawl_case_records_task_id ON crawl_case_records(task_id);
CREATE INDEX idx_crawl_case_records_list_page_id ON crawl_case_records(list_page_id);
CREATE INDEX idx_crawl_case_records_status ON crawl_case_records(status);
CREATE INDEX idx_crawl_case_records_task_status ON crawl_case_records(task_id, status);
CREATE INDEX idx_crawl_case_records_case_id ON crawl_case_records(case_id);
```

### 2.2 架构优化

#### 2.2.1 优化后的数据流

```
任务创建
  ↓
任务执行 (CrawlTaskExecutor)
  ↓
爬取阶段 (CrawlStage)
  ├─ 获取列表页 (get_creative_list_paginated)
  │   ├─ 记录列表页开始 (crawl_list_pages: status=pending)
  │   ├─ 调用API获取数据
  │   ├─ 记录列表页结果 (crawl_list_pages: status=success/failed)
  │   └─ 返回案例列表项
  │
  └─ 遍历每个案例
      ├─ 记录案例开始 (crawl_case_records: status=pending)
      ├─ 解析详情页 (parse)
      │   ├─ 成功: 记录案例成功 (crawl_case_records: status=success)
      │   └─ 失败: 记录案例失败 (crawl_case_records: status=failed, error_message)
      ├─ 验证数据 (validate_case)
      │   ├─ 通过: 更新记录 (has_validation_error=false)
      │   └─ 失败: 更新记录 (status=validation_failed, validation_errors)
      ├─ 保存到批次 (current_batch)
      └─ 保存批次时更新记录 (saved_to_json=true, batch_file_name)
  ↓
保存批次文件 (cases_batch_*.json)
  ↓
更新任务统计 (从数据库聚合计算)
```

#### 2.2.2 新增Repository层

**目的**：封装数据库操作，提供统一的接口

```python
# app/repositories/crawl_list_page_repository.py
class CrawlListPageRepository:
    """列表页爬取记录Repository"""
    
    async def create_list_page_record(
        self, task_id: str, page_number: int
    ) -> int:
        """创建列表页记录"""
        
    async def update_list_page_success(
        self, record_id: int, items_count: int, duration: float
    ):
        """更新列表页成功记录"""
        
    async def update_list_page_failed(
        self, record_id: int, error_message: str, error_type: str, duration: float
    ):
        """更新列表页失败记录"""
        
    async def get_failed_list_pages(self, task_id: str) -> List[Dict]:
        """获取失败的列表页"""
        
    async def increment_retry_count(self, record_id: int):
        """增加重试次数"""

# app/repositories/crawl_case_record_repository.py
class CrawlCaseRecordRepository:
    """案例爬取记录Repository"""
    
    async def create_case_record(
        self, task_id: str, list_page_id: int, case_id: int,
        case_url: str, case_title: str
    ) -> int:
        """创建案例记录"""
        
    async def update_case_success(
        self, record_id: int, duration: float
    ):
        """更新案例成功记录"""
        
    async def update_case_failed(
        self, record_id: int, error_message: str, error_type: str,
        error_stack: str, duration: float
    ):
        """更新案例失败记录"""
        
    async def update_case_validation_failed(
        self, record_id: int, validation_errors: Dict
    ):
        """更新案例验证失败记录"""
        
    async def update_case_saved(
        self, record_id: int, batch_file_name: str
    ):
        """更新案例保存状态"""
        
    async def get_failed_cases(self, task_id: str) -> List[Dict]:
        """获取失败的案例"""
        
    async def increment_retry_count(self, record_id: int):
        """增加重试次数"""
```

### 2.3 代码改造

#### 2.3.1 CrawlStage 改造

**改造点**：
1. 在获取列表页时记录列表页爬取结果
2. 在处理每个案例时记录案例爬取结果
3. 在保存批次时更新案例保存状态

**关键代码位置**：

```python
# services/pipeline/crawl_stage.py

def crawl(self, ...):
    # 1. 获取列表页数据
    list_items = self.api_client.get_creative_list_paginated(...)
    
    # 2. 遍历每个案例
    for item in list_items:
        # 创建案例记录
        case_record_id = await self.case_repo.create_case_record(...)
        
        try:
            # 解析详情页
            detail_data = self.detail_parser.parse(case_url)
            
            # 更新案例记录为成功
            await self.case_repo.update_case_success(case_record_id, ...)
            
        except Exception as e:
            # 更新案例记录为失败
            await self.case_repo.update_case_failed(case_record_id, ...)
        
        # 保存批次时更新保存状态
        if len(current_batch) >= self.batch_size:
            self._save_batch(current_batch, batch_num)
            # 更新所有案例的保存状态
            await self._update_cases_saved_status(...)
```

#### 2.3.2 API Client 改造

**改造点**：
1. 在调用API时记录列表页爬取开始和结果

**关键代码位置**：

```python
# services/spider/api_client.py

def get_creative_list_paginated(self, start_page: int, max_pages: Optional[int]):
    all_items = []
    
    for page in range(start_page, start_page + max_pages):
        # 创建列表页记录
        list_page_record_id = await self.list_page_repo.create_list_page_record(...)
        
        try:
            start_time = time.time()
            data = self.get_creative_list(page)
            duration = time.time() - start_time
            
            items = data.get('data', {}).get('items', [])
            
            # 更新列表页记录为成功
            await self.list_page_repo.update_list_page_success(
                list_page_record_id, len(items), duration
            )
            
            all_items.extend(items)
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 更新列表页记录为失败
            await self.list_page_repo.update_list_page_failed(
                list_page_record_id, str(e), error_type, duration
            )
            
            # 决定是否继续：如果连续失败多次，可能已到最后一页
            # ...
    
    return all_items
```

### 2.4 重试机制优化

#### 2.4.1 精确重试列表页

```python
# app/services/crawl_task_service.py

async def retry_failed_list_pages(self, task_id: str) -> bool:
    """重试失败的列表页"""
    # 1. 查询失败的列表页
    failed_pages = await self.list_page_repo.get_failed_list_pages(task_id)
    
    # 2. 创建新的重试任务或更新现有任务
    for page_info in failed_pages:
        page_number = page_info['page_number']
        # 重试该列表页
        await self._retry_single_list_page(task_id, page_number)
```

#### 2.4.2 精确重试案例

```python
async def retry_failed_cases(self, task_id: str, case_ids: Optional[List[int]] = None) -> bool:
    """重试失败的案例"""
    # 1. 查询失败的案例
    if case_ids:
        failed_cases = await self.case_repo.get_cases_by_ids(task_id, case_ids)
    else:
        failed_cases = await self.case_repo.get_failed_cases(task_id)
    
    # 2. 重试每个案例
    for case_info in failed_cases:
        await self._retry_single_case(task_id, case_info)
```

## 3. 实施计划

### 3.1 阶段一：数据库设计（1-2天）

1. ✅ 创建数据库迁移脚本
   - 创建 `crawl_list_pages` 表
   - 创建 `crawl_case_records` 表
   - 创建索引和约束

2. ✅ 创建数据模型
   - `app/models/crawl_list_page.py`
   - `app/models/crawl_case_record.py`

### 3.2 阶段二：Repository层（1-2天）

1. ✅ 创建Repository类
   - `app/repositories/crawl_list_page_repository.py`
   - `app/repositories/crawl_case_record_repository.py`

2. ✅ 实现CRUD操作
   - 创建记录
   - 更新状态
   - 查询失败记录
   - 更新重试次数

### 3.3 阶段三：爬取层改造（2-3天）

1. ✅ 改造 `CrawlStage`
   - 集成Repository
   - 记录列表页爬取结果
   - 记录案例爬取结果
   - 更新保存状态

2. ✅ 改造 `AdquanAPIClient`
   - 记录列表页爬取开始和结果

### 3.4 阶段四：服务层优化（1-2天）

1. ✅ 优化 `CrawlTaskService`
   - 实现精确重试列表页
   - 实现精确重试案例
   - 从数据库聚合统计信息

2. ✅ 优化 `CrawlTaskExecutor`
   - 集成新的记录机制

### 3.5 阶段五：API层扩展（1天）

1. ✅ 新增API接口
   - `GET /api/v1/crawl-tasks/{task_id}/list-pages` - 查询列表页记录
   - `GET /api/v1/crawl-tasks/{task_id}/cases` - 查询案例记录
   - `POST /api/v1/crawl-tasks/{task_id}/retry-list-pages` - 重试失败的列表页
   - `POST /api/v1/crawl-tasks/{task_id}/retry-cases` - 重试失败的案例

### 3.6 阶段六：测试与验证（2-3天）

1. ✅ 单元测试
2. ✅ 集成测试
3. ✅ 端到端测试

## 4. 预期效果

### 4.1 可观测性提升

- ✅ 可以查看每个列表页的爬取状态和结果
- ✅ 可以查看每个案例的爬取状态和结果
- ✅ 可以统计失败案例的分布情况（按错误类型、按时间等）

### 4.2 重试效率提升

- ✅ 可以精确重试失败的列表页，无需重新爬取整个任务
- ✅ 可以精确重试失败的案例，无需重新爬取整个列表页
- ✅ 重试效率提升 80%+（仅重试失败的部分）

### 4.3 问题定位能力提升

- ✅ 可以快速定位哪些列表页失败了，失败原因是什么
- ✅ 可以快速定位哪些案例失败了，失败原因是什么
- ✅ 可以分析失败模式，优化爬取策略

## 5. 风险评估与应对

### 5.1 性能影响

**风险**：频繁的数据库写入可能影响爬取性能

**应对**：
- 使用批量插入优化（每10个案例批量插入一次）
- 使用异步数据库操作，不阻塞爬取流程
- 考虑使用消息队列异步处理记录（未来优化）

### 5.2 数据一致性

**风险**：数据库记录与JSON文件可能不一致

**应对**：
- 在保存批次文件时同步更新数据库记录
- 提供数据一致性检查工具
- 定期校验数据库记录与JSON文件的一致性

### 5.3 存储空间

**风险**：大量记录可能占用较多存储空间

**应对**：
- 定期归档历史记录（保留最近3个月）
- 压缩存储错误堆栈等大字段
- 考虑使用分区表（按时间分区）

## 6. 后续优化方向

1. **实时监控**：基于记录数据构建实时监控面板
2. **智能重试**：根据错误类型自动选择重试策略
3. **失败分析**：分析失败模式，自动优化爬取策略
4. **数据归档**：自动归档历史记录，释放存储空间
