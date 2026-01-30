# 目录结构优化说明

## 优化日期

2025-01-30

## 优化目标

将 `ad-browser` 目录结构优化为更符合最佳实践的组织方式，提高项目的可维护性和可读性。

## 优化内容

### 1. 文档组织优化

**优化前**：
- 所有文档文件（.md）都位于项目根目录
- 文档没有分类，难以查找

**优化后**：
- 创建 `docs/` 目录，按类型分类存放文档：
  - `docs/requirements/` - 需求文档
  - `docs/design/` - 设计文档（PRD、技术设计）
  - `docs/development/` - 开发文档（开发计划、进度跟踪）
  - `docs/references/` - 参考资料

**移动的文件**：
- `requirement.md` → `docs/requirements/requirement.md`
- `PRD-MVP.md` → `docs/design/PRD-MVP.md`
- `AGET-TECH_MVP.md` → `docs/design/AGET-TECH_MVP.md`
- `DEVELOPMENT_PLAN.md` → `docs/development/DEVELOPMENT_PLAN.md`
- `NEXT_STEPS.md` → `docs/development/NEXT_STEPS.md`
- `REAL_CASE_TEST.md` → `docs/development/REAL_CASE_TEST.md`
- `REFERENCES.md` → `docs/references/REFERENCES.md`

### 2. 脚本组织优化

**优化前**：
- 所有脚本文件（.sh）都位于项目根目录

**优化后**：
- 创建 `scripts/` 目录，统一存放所有脚本文件

**移动的文件**：
- `start_agent.sh` → `scripts/start_agent.sh`
- `run_direct_test.sh` → `scripts/run_direct_test.sh`
- `run_real_test.sh` → `scripts/run_real_test.sh`
- `check_port.sh` → `scripts/check_port.sh`

**脚本路径更新**：
- 所有脚本已更新为从 `scripts/` 目录正确切换到项目根目录
- 使用 `SCRIPT_DIR` 和 `PROJECT_ROOT` 变量确保路径正确

### 3. 项目入口文档

**新增**：
- 创建根目录 `README.md` 作为项目入口文档
- 包含项目简介、快速开始、文档索引等关键信息

### 4. 路径引用更新

**更新的文档**：
- `docs/development/DEVELOPMENT_PLAN.md` - 更新文档间引用路径
- `docs/development/NEXT_STEPS.md` - 更新文档间引用路径
- `docs/design/AGET-TECH_MVP.md` - 更新文档间引用路径
- `docs/design/PRD-MVP.md` - 更新文档间引用路径
- `agent/README.md` - 更新文档间引用路径

## 优化后的目录结构

```
ad-browser/
├── README.md                  # 项目入口文档（新增）
├── agent/                      # Agent 核心模块（保持不变）
│   ├── browser/
│   ├── controller/
│   ├── extractor/
│   ├── llm/
│   ├── models/
│   ├── server/
│   ├── tests/
│   ├── utils/
│   ├── docs/                   # Agent 技术文档（保持不变）
│   ├── README.md
│   ├── USAGE.md
│   └── ...
├── docs/                       # 项目文档（新增）
│   ├── design/                 # 设计文档
│   │   ├── AGET-TECH_MVP.md
│   │   └── PRD-MVP.md
│   ├── development/            # 开发文档
│   │   ├── DEVELOPMENT_PLAN.md
│   │   ├── NEXT_STEPS.md
│   │   ├── REAL_CASE_TEST.md
│   │   └── DIRECTORY_STRUCTURE_OPTIMIZATION.md
│   ├── references/             # 参考资料
│   │   └── REFERENCES.md
│   └── requirements/           # 需求文档
│       └── requirement.md
└── scripts/                     # 工具脚本（新增）
    ├── start_agent.sh
    ├── run_direct_test.sh
    ├── run_real_test.sh
    └── check_port.sh
```

## 最佳实践遵循

✅ **文档分类**：按类型组织文档，便于查找和维护  
✅ **脚本集中管理**：所有脚本统一存放在 `scripts/` 目录  
✅ **清晰的入口**：根目录 `README.md` 提供项目概览和快速开始  
✅ **路径一致性**：所有文档和脚本中的路径引用已更新  
✅ **保持模块化**：`agent/` 目录结构保持不变，符合 Python 包结构

## 使用说明

### 运行脚本

所有脚本现在位于 `scripts/` 目录，可以从项目根目录运行：

```bash
# 启动 Agent 服务器
./scripts/start_agent.sh

# 运行测试
./scripts/run_direct_test.sh
./scripts/run_real_test.sh

# 检查端口
./scripts/check_port.sh
```

### 查看文档

- **项目概览**：查看根目录 `README.md`
- **需求文档**：`docs/requirements/requirement.md`
- **设计文档**：`docs/design/`
- **开发文档**：`docs/development/`
- **参考资料**：`docs/references/REFERENCES.md`

## 注意事项

1. 所有脚本已更新路径处理逻辑，确保从 `scripts/` 目录正确切换到项目根目录
2. 文档间的引用路径已全部更新，确保链接正常工作
3. `agent/` 目录内的技术文档（`agent/docs/`）保持不变，这些是 Agent 模块的内部文档
4. 代码文件中对文档的引用（如 `AGET-TECH_MVP.md`）保持不变，因为这些只是文档名称引用，不影响功能

## 后续建议

1. 考虑添加 `.gitignore` 规则忽略 `__pycache__` 和 `.pyc` 文件
2. 考虑添加 `CONTRIBUTING.md` 贡献指南
3. 考虑添加 `CHANGELOG.md` 记录版本变更
