# 爬取任务管理功能技术设计方案

## 1. 方案概述

### 1.1 目标

设计并实现爬取任务管理功能，提供可视化的任务创建、监控和控制能力，解决当前命令行脚本使用体验差、进度感知弱的问题。

### 1.2 核心功能

- **任务创建**：通过前端界面创建爬取任务，配置爬取参数
- **任务列表**：查看所有任务的状态、进度和统计信息
- **任务详情**：查看任务完整信息、实时进度和日志
- **任务控制**：支持暂停、恢复、终止、重试等操作
- **实时监控**：WebSocket 实时推送任务进度和状态
- **任务历史**：查看历史任务记录和统计趋势

### 1.3 技术架构

```
前端 (React + TypeScript)
    ↓ HTTP/WebSocket
后端 API (FastAPI)
    ↓
任务队列 (Celery/RQ)
    ↓
爬取服务 (集成现有 CrawlStage)
    ↓
数据库 (PostgreSQL)
```

## 2. 后端设计

### 2.1 API 设计

#### 2.1.1 任务管理接口

**创建任务**：

```
POST /api/v1/crawl-tasks
Request Body:
{
  "name": "任务名称",
  "data_source": "adquan",
  "description": "任务描述",
  "start_page": 0,
  "end_page": 100,
  "case_type": 3,
  "search_value": "",
  "batch_size": 100,
  "delay_range": [2, 5],
  "execute_immediately": true
}
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "task_123",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**获取任务列表**：

```
GET /api/v1/crawl-tasks?status=running&page=1&page_size=20
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "tasks": [
      {
        "task_id": "task_123",
        "name": "任务名称",
        "status": "running",
        "progress": {
          "total_pages": 100,
          "completed_pages": 50,
          "percentage": 50
        },
        "stats": {
          "total_crawled": 1000,
          "total_saved": 950,
          "total_failed": 50
        },
        "created_at": "2024-01-01T00:00:00Z",
        "started_at": "2024-01-01T00:05:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

**获取任务详情**：

```
GET /api/v1/crawl-tasks/{task_id}
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "task_123",
    "name": "任务名称",
    "data_source": "adquan",
    "description": "任务描述",
    "status": "running",
    "config": {
      "start_page": 0,
      "end_page": 100,
      "case_type": 3,
      "search_value": "",
      "batch_size": 100,
      "delay_range": [2, 5]
    },
    "progress": {
      "total_pages": 100,
      "completed_pages": 50,
      "current_page": 50,
      "percentage": 50,
      "estimated_remaining_time": 3600
    },
    "stats": {
      "total_crawled": 1000,
      "total_saved": 950,
      "total_failed": 50,
      "batches_saved": 10,
      "success_rate": 0.95,
      "avg_speed": 10.5,
      "avg_delay": 3.2,
      "error_rate": 0.05
    },
    "timeline": {
      "created_at": "2024-01-01T00:00:00Z",
      "started_at": "2024-01-01T00:05:00Z",
      "paused_at": null,
      "completed_at": null
    }
  }
}
```

**更新任务状态**：

```
POST /api/v1/crawl-tasks/{task_id}/pause
POST /api/v1/crawl-tasks/{task_id}/resume
POST /api/v1/crawl-tasks/{task_id}/cancel
POST /api/v1/crawl-tasks/{task_id}/retry
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "task_123",
    "status": "paused",
    "updated_at": "2024-01-01T01:00:00Z"
  }
}
```

**获取任务日志**：

```
GET /api/v1/crawl-tasks/{task_id}/logs?level=error&page=1&page_size=50
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "logs": [
      {
        "id": 1,
        "level": "INFO",
        "message": "开始爬取第 1 页",
        "details": {},
        "created_at": "2024-01-01T00:05:00Z"
      },
      {
        "id": 2,
        "level": "ERROR",
        "message": "爬取失败: Connection timeout",
        "details": {
          "case_id": 12345,
          "url": "https://..."
        },
        "created_at": "2024-01-01T00:05:30Z"
      }
    ],
    "total": 1000,
    "page": 1,
    "page_size": 50
  }
}
```

#### 2.1.2 WebSocket 接口

**连接地址**：

```
WS /ws/crawl-tasks/{task_id}
```

**消息格式**：

**客户端 → 服务端**：

```json
{
  "type": "subscribe",
  "task_id": "task_123"
}
```

**服务端 → 客户端**：

```json
{
  "type": "progress_update",
  "task_id": "task_123",
  "data": {
    "completed_pages": 50,
    "current_page": 50,
    "total_crawled": 1000,
    "total_saved": 950,
    "total_failed": 50,
    "percentage": 50,
    "estimated_remaining_time": 3600
  },
  "timestamp": "2024-01-01T01:00:00Z"
}
```

```json
{
  "type": "status_update",
  "task_id": "task_123",
  "data": {
    "status": "paused",
    "previous_status": "running"
  },
  "timestamp": "2024-01-01T01:00:00Z"
}
```

```json
{
  "type": "log",
  "task_id": "task_123",
  "data": {
    "level": "INFO",
    "message": "开始爬取第 51 页",
    "created_at": "2024-01-01T01:00:00Z"
  }
}
```

```json
{
  "type": "error",
  "task_id": "task_123",
  "data": {
    "level": "ERROR",
    "message": "爬取失败: Connection timeout",
    "details": {
      "case_id": 12345
    },
    "created_at": "2024-01-01T01:00:00Z"
  }
}
```

### 2.2 数据库设计

#### 2.2.1 任务表（crawl_tasks）

```sql
CREATE TABLE crawl_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    data_source VARCHAR(64) NOT NULL,
    description TEXT,

    -- 任务配置
    start_page INTEGER NOT NULL,
    end_page INTEGER,
    case_type INTEGER,
    search_value VARCHAR(255),
    batch_size INTEGER DEFAULT 100,
    delay_min FLOAT DEFAULT 2.0,
    delay_max FLOAT DEFAULT 5.0,
    enable_resume BOOLEAN DEFAULT TRUE,

    -- 任务状态
    status VARCHAR(32) NOT NULL, -- pending, running, paused, completed, failed, cancelled, terminated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    paused_at TIMESTAMP,

    -- 进度信息
    total_pages INTEGER,
    completed_pages INTEGER DEFAULT 0,
    current_page INTEGER,

    -- 统计信息
    total_crawled INTEGER DEFAULT 0,
    total_saved INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    batches_saved INTEGER DEFAULT 0,

    -- 性能指标
    avg_speed FLOAT, -- 平均爬取速度（案例/分钟）
    avg_delay FLOAT, -- 平均请求延迟（秒）
    error_rate FLOAT, -- 错误率

    -- 错误信息
    error_message TEXT,
    error_stack TEXT,

    -- 元数据
    created_by VARCHAR(64),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crawl_tasks_status ON crawl_tasks(status);
CREATE INDEX idx_crawl_tasks_created_at ON crawl_tasks(created_at);
CREATE INDEX idx_crawl_tasks_data_source ON crawl_tasks(data_source);
CREATE INDEX idx_crawl_tasks_task_id ON crawl_tasks(task_id);
```

#### 2.2.2 任务日志表（crawl_task_logs）

```sql
CREATE TABLE crawl_task_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    level VARCHAR(16) NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX idx_crawl_task_logs_task_id ON crawl_task_logs(task_id);
CREATE INDEX idx_crawl_task_logs_level ON crawl_task_logs(level);
CREATE INDEX idx_crawl_task_logs_created_at ON crawl_task_logs(created_at);
CREATE INDEX idx_crawl_task_logs_task_level ON crawl_task_logs(task_id, level);
```

#### 2.2.3 任务状态历史表（crawl_task_status_history）

```sql
CREATE TABLE crawl_task_status_history (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    previous_status VARCHAR(32),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX idx_crawl_task_status_history_task_id ON crawl_task_status_history(task_id);
CREATE INDEX idx_crawl_task_status_history_created_at ON crawl_task_status_history(created_at);
```

### 2.3 任务执行器设计

#### 2.3.1 任务队列选择

**推荐方案：Celery**

**理由**：

- ✅ 成熟的异步任务队列框架
- ✅ 支持任务暂停、恢复、终止
- ✅ 支持任务优先级和调度
- ✅ 支持任务结果存储
- ✅ 丰富的监控工具（Flower）

**备选方案：RQ (Redis Queue)**

- 更轻量级，适合中小型应用
- 基于 Redis，部署简单
- 功能相对简单，不支持复杂调度

#### 2.3.2 任务执行流程

```
1. 创建任务记录（状态：pending）
   ↓
2. 如果 execute_immediately=true，提交到任务队列
   ↓
3. 任务队列分配 Worker 执行
   ↓
4. Worker 更新任务状态（状态：running）
   ↓
5. Worker 调用 CrawlStage 执行爬取
   ↓
6. CrawlStage 执行过程中：
   - 每爬取完一页，更新进度
   - 每保存一批，更新统计
   - 记录日志到数据库
   - 通过 WebSocket 推送更新
   ↓
7. 爬取完成或失败
   ↓
8. Worker 更新任务状态（状态：completed/failed）
```

#### 2.3.3 任务控制实现

**暂停任务**：

```python
def pause_task(task_id: str):
    """暂停任务"""
    # 1. 更新任务状态为 paused
    # 2. 记录暂停时间
    # 3. 通知 Worker 暂停执行（通过共享状态或消息队列）
    # 4. Worker 检查暂停标志，保存当前进度后停止
```

**恢复任务**：

```python
def resume_task(task_id: str):
    """恢复任务"""
    # 1. 更新任务状态为 running
    # 2. 从暂停位置继续执行
    # 3. 重新提交到任务队列（从断点继续）
```

**终止任务**：

```python
def terminate_task(task_id: str):
    """终止任务"""
    # 1. 更新任务状态为 terminated
    # 2. 通知 Worker 立即停止（不保存进度）
    # 3. 记录终止原因
```

#### 2.3.4 进度跟踪实现

**进度更新策略**：

- **每页更新**：每爬取完一页，更新 `completed_pages` 和 `current_page`
- **批量更新**：每保存一批数据，更新 `total_saved` 和 `batches_saved`
- **实时推送**：通过 WebSocket 实时推送进度更新
- **定期持久化**：每 10 秒或每爬取 10 个案例，持久化到数据库

**预计剩余时间计算**：

```python
def calculate_remaining_time(task):
    """计算预计剩余时间"""
    if task.completed_pages == 0:
        return None

    elapsed_time = (datetime.now() - task.started_at).total_seconds()
    avg_time_per_page = elapsed_time / task.completed_pages
    remaining_pages = task.total_pages - task.completed_pages

    return remaining_pages * avg_time_per_page
```

### 2.4 WebSocket 实现

#### 2.4.1 技术选型

**推荐：FastAPI WebSocket + Python-SocketIO**

**理由**：

- ✅ FastAPI 原生支持 WebSocket
- ✅ 与现有 FastAPI 应用集成简单
- ✅ 支持房间（Room）概念，便于管理连接
- ✅ 支持自动重连和心跳检测

#### 2.4.2 连接管理

```python
# WebSocket 连接管理器
class TaskWebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """建立连接"""
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = set()
        self.connections[task_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, task_id: str):
        """断开连接"""
        if task_id in self.connections:
            self.connections[task_id].discard(websocket)

    async def broadcast(self, task_id: str, message: dict):
        """广播消息"""
        if task_id in self.connections:
            disconnected = set()
            for websocket in self.connections[task_id]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.add(websocket)
            # 清理断开的连接
            self.connections[task_id] -= disconnected
```

#### 2.4.3 消息推送时机

- **状态变更**：任务状态改变时立即推送
- **进度更新**：每爬取完一页推送一次
- **统计更新**：每 5 秒推送一次（或每爬取 10 个案例）
- **日志推送**：实时推送日志（INFO、WARNING、ERROR）
- **错误推送**：错误发生时立即推送

## 3. 前端设计

### 3.1 页面结构

```
/crawl-tasks                    # 任务列表页
/crawl-tasks/create             # 创建任务页
/crawl-tasks/:taskId            # 任务详情页
```

### 3.2 组件设计

#### 3.2.1 任务列表组件（CrawlTaskList）

**功能**：

- 展示任务列表
- 支持筛选和排序
- 支持批量操作

**Props**：

```typescript
interface CrawlTaskListProps {
  filters?: {
    status?: string;
    dataSource?: string;
    dateRange?: [Date, Date];
    keyword?: string;
  };
  sortBy?: "created_at" | "started_at" | "status" | "progress";
  sortOrder?: "asc" | "desc";
}
```

#### 3.2.2 任务卡片组件（CrawlTaskCard）

**功能**：

- 展示单个任务的基本信息
- 显示进度条和统计信息
- 快速操作按钮

**Props**：

```typescript
interface CrawlTaskCardProps {
  task: CrawlTask;
  onAction?: (action: string, taskId: string) => void;
}
```

#### 3.2.3 任务详情组件（CrawlTaskDetail）

**功能**：

- 展示任务完整信息
- 实时进度监控
- 任务控制按钮
- 实时日志查看

**Props**：

```typescript
interface CrawlTaskDetailProps {
  taskId: string;
}
```

#### 3.2.4 创建任务表单组件（CreateTaskForm）

**功能**：

- 分步骤表单
- 实时验证
- 参数说明

**表单步骤**：

1. 基础配置（任务名称、数据源、描述）
2. 爬取范围（起始页、结束页）
3. 筛选条件（案例类型、搜索关键词等）
4. 高级配置（批次大小、延迟等）
5. 执行策略（立即执行、定时执行）

#### 3.2.5 进度条组件（ProgressBar）

**功能**：

- 可视化进度展示
- 显示百分比和预计剩余时间

**Props**：

```typescript
interface ProgressBarProps {
  current: number;
  total: number;
  percentage: number;
  estimatedTime?: number;
}
```

#### 3.2.6 日志查看器组件（LogViewer）

**功能**：

- 实时日志展示
- 按级别筛选
- 关键词搜索
- 自动滚动
- 日志导出

**Props**：

```typescript
interface LogViewerProps {
  taskId: string;
  level?: "INFO" | "WARNING" | "ERROR" | "ALL";
  searchKeyword?: string;
  autoScroll?: boolean;
}
```

### 3.3 状态管理

#### 3.3.1 任务状态 Store（Zustand）

```typescript
interface CrawlTaskStore {
  // 状态
  tasks: CrawlTask[];
  currentTask: CrawlTask | null;
  filters: TaskFilters;
  loading: boolean;

  // 操作
  fetchTasks: () => Promise<void>;
  fetchTaskDetail: (taskId: string) => Promise<void>;
  createTask: (config: TaskConfig) => Promise<void>;
  updateTaskStatus: (taskId: string, action: string) => Promise<void>;
  setFilters: (filters: TaskFilters) => void;

  // WebSocket
  connectWebSocket: (taskId: string) => void;
  disconnectWebSocket: (taskId: string) => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
}
```

#### 3.3.2 WebSocket Hook

```typescript
function useTaskWebSocket(taskId: string) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/crawl-tasks/${taskId}`);

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: "subscribe", task_id: taskId }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
      // 更新 Store
      handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  return { connected, messages };
}
```

### 3.4 样式设计

#### 3.4.1 任务状态颜色

```less
// 状态颜色定义
@status-pending: #1890ff; // 蓝色 - 等待中
@status-running: #52c41a; // 绿色 - 运行中
@status-paused: #faad14; // 橙色 - 已暂停
@status-completed: #52c41a; // 绿色 - 已完成
@status-failed: #ff4d4f; // 红色 - 已失败
@status-cancelled: #8c8c8c; // 灰色 - 已取消
@status-terminated: #595959; // 深灰 - 已终止
```

#### 3.4.2 布局设计

**任务列表页**：

- 顶部：筛选器和搜索框
- 中间：任务卡片网格布局（响应式）
- 底部：分页器

**任务详情页**：

- 左侧：任务信息和控制按钮（固定宽度 300px）
- 中间：进度信息和统计信息（自适应）
- 右侧：实时日志（可折叠，默认展开，宽度 400px）

## 4. 实施计划

### 4.1 阶段一：基础功能（1-2 周）

**后端**：

- [ ] 数据库表设计和创建
- [ ] 任务管理 API（创建、查询、更新状态）
- [ ] 任务执行器基础框架（集成 Celery）
- [ ] 集成现有 CrawlStage 到任务执行器

**前端**：

- [ ] 任务列表页（基础展示）
- [ ] 创建任务页（表单）
- [ ] 任务详情页（基础信息展示）
- [ ] 基础的任务控制功能（开始、暂停、终止）

### 4.2 阶段二：进度监控（1 周）

**后端**：

- [ ] 进度跟踪和更新机制
- [ ] WebSocket 实现和连接管理
- [ ] 实时消息推送
- [ ] 日志记录和查询接口

**前端**：

- [ ] WebSocket 连接和消息处理
- [ ] 实时进度展示（进度条、统计信息）
- [ ] 实时日志查看器
- [ ] 预计剩余时间计算和展示

### 4.3 阶段三：优化和增强（1 周）

**后端**：

- [ ] 任务历史查询优化
- [ ] 任务统计接口
- [ ] 批量操作接口
- [ ] 性能优化（索引、查询优化）

**前端**：

- [ ] 任务筛选和排序优化
- [ ] 批量操作功能
- [ ] 日志搜索和导出
- [ ] 用户体验优化（加载状态、错误处理、动画效果）

## 5. 性能优化

### 5.1 数据库优化

- **索引优化**：在 `status`、`created_at`、`data_source` 等常用查询字段上建立索引
- **查询优化**：使用分页查询，避免一次性加载大量数据
- **连接池**：使用数据库连接池，提高并发性能

### 5.2 缓存策略

- **任务列表缓存**：缓存任务列表数据，减少数据库查询
- **任务详情缓存**：缓存已完成任务的详情，避免重复查询
- **Redis 缓存**：使用 Redis 缓存任务状态和进度信息

### 5.3 WebSocket 优化

- **连接复用**：同一任务多个客户端共享连接
- **消息压缩**：大消息进行压缩传输
- **心跳检测**：定期发送心跳，及时清理断开的连接
- **消息队列**：使用消息队列缓冲消息，避免阻塞

## 6. 错误处理和监控

### 6.1 错误处理

- **任务执行错误**：记录错误日志，更新任务状态为 failed
- **WebSocket 错误**：自动重连机制，连接失败时降级为轮询
- **API 错误**：统一的错误响应格式，包含错误码和错误信息

### 6.2 监控指标

- **任务执行时间**：监控任务平均执行时间
- **任务成功率**：监控任务成功/失败比例
- **WebSocket 连接数**：监控活跃连接数
- **API 响应时间**：监控 API 接口响应时间

### 6.3 日志记录

- **任务日志**：记录任务执行过程中的所有关键操作
- **API 日志**：记录所有 API 请求和响应
- **WebSocket 日志**：记录连接建立、断开和消息推送

---

**文档版本**：v1.0  
**创建时间**：2024-01-XX  
**最后更新**：2024-01-XX
