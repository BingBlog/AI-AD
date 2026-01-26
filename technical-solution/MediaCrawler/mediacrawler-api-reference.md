# MediaCrawler API 接口文档

## 概述

MediaCrawler 提供了完整的 REST API 和 WebSocket API，用于控制爬虫任务和管理数据。

**API 基础地址**：`http://localhost:8080`

**API 文档**：`http://localhost:8080/docs` (Swagger UI)

## 一、健康检查接口

### GET /api/health

检查 API 服务是否正常运行。

**响应示例**：
```json
{
  "status": "ok"
}
```

## 二、环境检查接口

### GET /api/env/check

检查 MediaCrawler 环境配置是否正确。

**响应示例**：
```json
{
  "success": true,
  "message": "MediaCrawler environment configured correctly",
  "output": "..."
}
```

## 三、配置接口

### GET /api/config/platforms

获取支持的平台列表。

**响应示例**：
```json
{
  "platforms": [
    {"value": "xhs", "label": "Xiaohongshu", "icon": "book-open"},
    {"value": "dy", "label": "Douyin", "icon": "music"},
    {"value": "ks", "label": "Kuaishou", "icon": "video"},
    {"value": "bili", "label": "Bilibili", "icon": "tv"},
    {"value": "wb", "label": "Weibo", "icon": "message-circle"},
    {"value": "tieba", "label": "Baidu Tieba", "icon": "messages-square"},
    {"value": "zhihu", "label": "Zhihu", "icon": "help-circle"}
  ]
}
```

### GET /api/config/options

获取所有配置选项。

**响应示例**：
```json
{
  "login_types": [
    {"value": "qrcode", "label": "QR Code Login"},
    {"value": "cookie", "label": "Cookie Login"}
  ],
  "crawler_types": [
    {"value": "search", "label": "Search Mode"},
    {"value": "detail", "label": "Detail Mode"},
    {"value": "creator", "label": "Creator Mode"}
  ],
  "save_options": [
    {"value": "json", "label": "JSON File"},
    {"value": "csv", "label": "CSV File"},
    {"value": "excel", "label": "Excel File"},
    {"value": "sqlite", "label": "SQLite Database"},
    {"value": "db", "label": "MySQL Database"},
    {"value": "mongodb", "label": "MongoDB Database"}
  ]
}
```

## 四、爬虫控制接口

### POST /api/crawler/start

启动爬虫任务。

**请求体**：
```json
{
  "platform": "xhs",              // 平台：xhs, dy, ks, bili, wb, tieba, zhihu
  "login_type": "qrcode",         // 登录方式：qrcode, phone, cookie
  "crawler_type": "search",       // 爬取类型：search, detail, creator
  "keywords": "营销案例,品牌营销",  // 关键词（搜索模式，逗号分隔）
  "specified_ids": "123,456",     // 指定ID列表（详情模式，逗号分隔）
  "creator_ids": "user1,user2",   // 创作者ID列表（创作者模式，逗号分隔）
  "start_page": 1,                // 起始页码
  "enable_comments": true,        // 是否爬取评论
  "enable_sub_comments": false,   // 是否爬取二级评论
  "save_option": "json",          // 保存格式：json, csv, excel, sqlite, db, mongodb
  "cookies": "",                  // Cookie 字符串（可选）
  "headless": false               // 是否无头模式
}
```

**响应示例**：
```json
{
  "status": "ok",
  "message": "Crawler started successfully"
}
```

**错误响应**：
- `400`：爬虫已在运行
- `500`：启动失败

### POST /api/crawler/stop

停止爬虫任务。

**响应示例**：
```json
{
  "status": "ok",
  "message": "Crawler stopped successfully"
}
```

**错误响应**：
- `400`：没有运行中的爬虫
- `500`：停止失败

### GET /api/crawler/status

获取爬虫状态。

**响应示例**：
```json
{
  "status": "running",           // idle, running, stopping, error
  "platform": "xhs",
  "crawler_type": "search",
  "started_at": "2025-01-26T20:00:00",
  "error_message": null
}
```

### GET /api/crawler/logs

获取爬虫日志。

**查询参数**：
- `limit` (int, 可选)：返回的日志数量，默认 100

**响应示例**：
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "20:00:00",
      "level": "info",
      "message": "Starting crawler..."
    },
    {
      "id": 2,
      "timestamp": "20:00:01",
      "level": "success",
      "message": "Crawler started successfully"
    }
  ]
}
```

## 五、数据管理接口

### GET /api/data/files

获取数据文件列表。

**查询参数**：
- `platform` (string, 可选)：平台筛选（xhs, dy, ks, bili, wb, tieba, zhihu）
- `file_type` (string, 可选)：文件类型筛选（json, csv, xlsx, xls）

**响应示例**：
```json
{
  "files": [
    {
      "name": "xhs_search_20250126.json",
      "path": "xhs/xhs_search_20250126.json",
      "size": 102400,
      "modified_at": 1706284800.0,
      "record_count": 15,
      "type": "json"
    }
  ]
}
```

### GET /api/data/files/{file_path}

获取文件内容或预览。

**路径参数**：
- `file_path`：文件相对路径（相对于 data 目录）

**查询参数**：
- `preview` (bool, 默认 true)：是否预览模式
- `limit` (int, 默认 100)：预览时返回的记录数

**响应示例（预览模式）**：
```json
{
  "data": [
    {
      "id": "123",
      "title": "营销案例",
      "content": "..."
    }
  ],
  "total": 15
}
```

**响应示例（下载模式）**：
返回文件流，Content-Type: `application/octet-stream`

### GET /api/data/download/{file_path}

下载数据文件。

**路径参数**：
- `file_path`：文件相对路径（相对于 data 目录）

**响应**：
返回文件流，Content-Type: `application/octet-stream`

### GET /api/data/stats

获取数据统计信息。

**响应示例**：
```json
{
  "total_files": 10,
  "total_size": 10485760,
  "by_platform": {
    "xhs": 5,
    "dy": 3,
    "bili": 2
  },
  "by_type": {
    "json": 8,
    "csv": 2
  }
}
```

## 六、WebSocket 接口

### WebSocket /api/ws/logs

实时日志流。

**连接**：
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws/logs');
ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log);
};
```

**消息格式**：
```json
{
  "id": 1,
  "timestamp": "20:00:00",
  "level": "info",
  "message": "Starting crawler..."
}
```

**心跳**：
- 客户端发送 `"ping"`，服务器回复 `"pong"`
- 服务器每 30 秒发送 `"ping"` 保持连接

### WebSocket /api/ws/status

实时状态流。

**连接**：
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws/status');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log(status);
};
```

**消息格式**（每秒推送一次）：
```json
{
  "status": "running",
  "platform": "xhs",
  "crawler_type": "search",
  "started_at": "2025-01-26T20:00:00",
  "error_message": null
}
```

## 七、数据格式说明

### 平台代码映射

| 平台 | 代码 | 说明 |
|------|------|------|
| 小红书 | xhs | Xiaohongshu |
| 抖音 | dy | Douyin |
| 快手 | ks | Kuaishou |
| B站 | bili | Bilibili |
| 微博 | wb | Weibo |
| 贴吧 | tieba | Baidu Tieba |
| 知乎 | zhihu | Zhihu |

### 爬取类型说明

- **search**：关键词搜索模式，需要提供 `keywords` 参数
- **detail**：指定内容详情模式，需要提供 `specified_ids` 参数
- *