# 广告案例库前端项目

## 项目简介

广告案例库前端应用，提供案例检索、筛选、浏览和详情查看功能。

## 技术栈

- **框架**: React 18 + TypeScript 5
- **UI 组件库**: Ant Design 5
- **状态管理**: Zustand 4
- **数据获取**: React Query (TanStack Query) 5
- **路由**: React Router v6
- **HTTP 客户端**: Axios
- **构建工具**: Vite 5
- **样式方案**: Ant Design (Less) + CSS Modules

## 快速开始

### 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0 或 yarn >= 1.22.0 或 pnpm >= 8.0.0

### 安装依赖

```bash
pnpm install
```

### 配置环境变量

复制 `env.example` 为 `.env.local`：

```bash
cp env.example .env.local
```

根据需要修改 `.env.local` 中的配置。

### 启动开发服务器

```bash
pnpm run dev
```

应用将在 http://localhost:3000 启动。

### 构建生产版本

```bash
pnpm run build
```

### 预览生产构建

```bash
pnpm run preview
```

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── assets/            # 资源文件
│   ├── components/        # 公共组件
│   │   └── Layout/        # 布局组件
│   ├── pages/             # 页面组件
│   ├── hooks/             # 自定义 Hooks
│   ├── services/          # API 服务
│   ├── store/             # 状态管理
│   ├── utils/             # 工具函数
│   ├── types/             # TypeScript 类型
│   ├── styles/            # 样式文件
│   ├── router/            # 路由配置
│   ├── App.tsx            # 根组件
│   └── main.tsx           # 入口文件
├── .env.example           # 环境变量模板
├── index.html             # HTML 模板
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── vite.config.ts         # Vite 配置
└── README.md              # 项目说明
```

## 开发指南

### 路径别名

项目配置了路径别名 `@`，指向 `src` 目录：

```typescript
import { Button } from "@/components/Button";
import { useSearchStore } from "@/store/searchStore";
```

### 代码规范

项目使用 ESLint 进行代码检查：

```bash
pnpm run lint
```

### 环境变量

在 `.env.local` 中配置环境变量，变量名必须以 `VITE_` 开头：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

在代码中使用：

```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## API 代理配置

开发环境已配置 API 代理，所有 `/api` 请求会自动代理到后端服务器（http://localhost:8000）。

配置位置：`vite.config.ts`

## 浏览器支持

- Chrome (最新版本)
- Firefox (最新版本)
- Safari (最新版本)
- Edge (最新版本)

## 许可证

MIT
