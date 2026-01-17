# 项目结构重构说明

## 重构日期

2024-01-XX

## 重构目标

按照最佳实践重新组织项目结构，使其更加清晰、易于维护和扩展。

## 主要变更

### 1. 目录重命名

- `api/` → `backend/`：更清晰的后端服务命名

### 2. 目录整理

#### 文档组织

**之前**：文档散落在各个目录
- 设计文档在根目录：`api-design.md`, `database-design.md`, `frontend-design.md` 等
- 验证文档在 `api/` 目录：`STAGE1_COMPLETE.md`, `ENV_VERIFICATION_FINAL.md` 等

**之后**：统一的文档目录结构
```
docs/
├── design/           # 设计文档
│   ├── api-design.md
│   ├── database-design.md
│   ├── frontend-design.md
│   └── ...
├── api/              # API文档（预留）
└── verification/     # 验证文档
    ├── STAGE1_COMPLETE.md
    ├── ENV_VERIFICATION_FINAL.md
    └── ...
```

#### 服务模块组织

**之前**：服务模块在根目录
- `pipeline/` 在根目录
- `spider/` 在根目录

**之后**：统一的服务目录
```
services/
├── pipeline/         # 数据处理管道
│   ├── crawl_stage.py
│   ├── import_stage.py
│   └── ...
└── spider/           # 爬虫服务
    ├── api_client.py
    ├── detail_parser.py
    └── ...
```

#### 测试文件组织

**之前**：测试文件分散在各处
- `test_detail_crawler.py` 在根目录
- `api/test_basic.py` 在 api 目录
- `check_csrf_token.py` 在根目录

**之后**：统一的测试目录
```
backend/
└── tests/            # 后端测试文件
    ├── test_basic.py
    ├── test_detail_crawler.py
    ├── check_csrf_token.py
    └── verify_setup.py
```

#### 数据文件组织

**之前**：示例文件散落在根目录
- `adquan_page_source.html` 在根目录
- `detail_page_sample.html` 在根目录

**之后**：统一的数据目录
```
data/
├── json/             # JSON数据文件
└── samples/          # 示例文件
    ├── adquan_page_source.html
    └── detail_page_sample.html
```

### 3. 导入路径更新

所有受影响的导入路径都已更新：

#### Scripts 脚本
- `from pipeline.crawl_stage` → `from services.pipeline.crawl_stage`
- `from pipeline.import_stage` → `from services.pipeline.import_stage`
- `from pipeline.utils` → `from services.pipeline.utils`
- `from pipeline.validator` → `from services.pipeline.validator`

#### Services 服务
- `from spider.api_client` → `from services.spider.api_client`
- `from spider.detail_parser` → `from services.spider.detail_parser`

#### Tests 测试
- `from spider.api_client` → `from services.spider.api_client`
- `from spider.detail_parser` → `from services.spider.detail_parser`

### 4. 文件清理

- 删除了根目录下的重复 `requirements.txt`（保留 `backend/requirements.txt`）
- 清理了空的 `tests/` 目录

### 5. 配置文件更新

#### README 文件
- 更新了 `backend/README.md` 中的路径引用（`api/` → `backend/`）
- 创建了项目根 `README.md`，包含完整的项目说明

#### .gitignore
- 更新了根目录 `.gitignore`，添加了 Python、Node.js、IDE 等常见忽略规则

## 最终项目结构

```
technical-solution/
├── README.md                    # 项目根说明文档
├── backend/                     # 后端API服务
│   ├── app/                     # 应用代码
│   │   ├── main.py             # FastAPI应用入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic模式
│   │   ├── services/           # 业务逻辑层
│   │   ├── repositories/       # 数据访问层
│   │   └── routers/            # 路由
│   ├── tests/                   # 测试文件
│   ├── requirements.txt         # Python依赖
│   ├── env.example             # 环境变量模板
│   ├── run.py                  # 启动脚本
│   └── README.md               # 后端说明文档
├── frontend/                    # 前端应用
│   ├── src/                     # 源代码
│   ├── package.json            # 项目配置
│   ├── vite.config.ts          # Vite配置
│   └── README.md               # 前端说明文档
├── services/                    # 服务和工具
│   ├── pipeline/                # 数据处理管道
│   │   ├── crawl_stage.py
│   │   ├── import_stage.py
│   │   ├── validator.py
│   │   └── utils.py
│   └── spider/                  # 爬虫服务
│       ├── api_client.py
│       ├── detail_parser.py
│       └── csrf_token_manager.py
├── scripts/                     # 脚本工具
│   ├── crawl.py                # 爬取脚本
│   ├── import.py               # 导入脚本
│   ├── validate.py             # 验证脚本
│   ├── update_vectors.py       # 向量更新脚本
│   └── README.md               # 脚本说明文档
├── database/                    # 数据库相关
│   ├── init.sql                # 初始化脚本
│   ├── init_without_vector.sql
│   └── README.md               # 数据库文档
├── data/                        # 数据文件
│   ├── json/                    # JSON数据文件
│   └── samples/                 # 示例文件
└── docs/                        # 项目文档
    ├── design/                  # 设计文档
    ├── api/                     # API文档（预留）
    └── verification/            # 验证文档
```

## 验证结果

所有导入路径已更新并通过验证：
- ✅ Backend imports work correctly
- ✅ Services imports work correctly

## 注意事项

1. **导入路径**：所有脚本和服务模块的导入路径已更新为新的目录结构
2. **相对路径**：services 模块内部使用相对导入（`from .utils import`），不受影响
3. **sys.path**：scripts 中的脚本使用 `sys.path.insert(0, str(Path(__file__).parent.parent))`，确保能找到 services 模块
4. **环境变量**：各模块的环境变量配置文件位置未变（`backend/env.example`, `frontend/env.example`）

## 后续建议

1. 考虑添加 `docs/api/` 目录用于 API 文档（OpenAPI/Swagger 自动生成）
2. 考虑添加 `tests/` 目录用于项目级集成测试
3. 考虑将 `scripts/examples/` 目录用于脚本使用示例
