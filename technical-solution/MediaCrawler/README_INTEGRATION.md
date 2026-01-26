# MediaCrawler 集成说明

本目录包含 MediaCrawler 项目，作为 AI-AD 项目的子模块使用。

## 项目结构

```
technical-solution/
├── backend/          # 后端服务
├── frontend/         # 前端应用
└── MediaCrawler/     # MediaCrawler 爬虫框架（本目录）
```

## 初始化

如果 MediaCrawler 目录不存在，需要克隆：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution
git clone https://github.com/NanmiCoder/MediaCrawler.git MediaCrawler
```

## 依赖安装

MediaCrawler 的依赖需要安装到 backend 的虚拟环境中：

```bash
cd backend
source venv/bin/activate
pip install -r ../MediaCrawler/requirements.txt
playwright install chromium
```

## 使用方式

MediaCrawler 通过 backend 的适配层使用，无需直接调用。

适配层会自动将 MediaCrawler 添加到 Python 路径，并封装其 API。

## 更新 MediaCrawler

如果需要更新到最新版本：

```bash
cd MediaCrawler
git pull origin main
```

## 参考

- MediaCrawler 官方文档: https://github.com/NanmiCoder/MediaCrawler
- MediaCrawler 使用指南: 查看 MediaCrawler/README.md
