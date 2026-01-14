# 前端技术栈最终确认

## ✅ 技术选型确认

### 核心框架
- **前端框架**：React 18+
- **语言**：TypeScript 5+
- **构建工具**：Vite 5+

### UI 组件库
- **组件库**：Ant Design 5（完全使用）
- **样式方案**：Ant Design (Less) + CSS Modules
- **主题定制**：通过 `ConfigProvider` 和 Less 变量

### 状态管理
- **客户端状态**：Zustand 4+
- **服务端状态**：React Query (TanStack Query) 5+

### 路由和网络
- **路由管理**：React Router v6
- **HTTP 客户端**：Axios 1+

## 📦 依赖安装

```bash
# 创建项目
npm create vite@latest frontend -- --template react-ts

# 安装核心依赖
npm install react react-dom
npm install -D @types/react @types/react-dom

# 安装 UI 组件库
npm install antd

# 安装状态管理
npm install zustand @tanstack/react-query

# 安装路由
npm install react-router-dom
npm install -D @types/react-router-dom

# 安装 HTTP 客户端
npm install axios

# 安装样式相关
npm install -D less

# 安装工具库
npm install dayjs  # 日期处理（Ant Design 推荐）
```

## 🎨 样式配置

### 1. CSS 变量定义

```css
/* src/styles/variables.css */
:root {
  --primary-color: #1890ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #ff4d4f;
  --border-radius: 6px;
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
}
```

### 2. Ant Design 主题配置

```tsx
// src/App.tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './styles/variables.css';

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: 'var(--primary-color)',
          borderRadius: 6,
          fontFamily: 'var(--font-family)',
        },
      }}
    >
      {/* 应用内容 */}
    </ConfigProvider>
  );
}
```

### 3. Vite 配置（按需引入）

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  css: {
    modules: {
      localsConvention: 'camelCase',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

## 📁 项目结构

```
frontend/
├── public/
├── src/
│   ├── assets/
│   │   ├── images/
│   │   └── styles/
│   │       ├── variables.css
│   │       └── global.less
│   ├── components/
│   │   ├── Layout/
│   │   ├── Search/
│   │   ├── Filter/
│   │   └── Case/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── store/
│   ├── utils/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 1. 创建项目

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

### 2. 安装依赖

```bash
npm install antd zustand @tanstack/react-query react-router-dom axios dayjs
npm install -D less
```

### 3. 配置主题

参考上面的样式配置部分。

### 4. 启动开发服务器

```bash
npm run dev
```

## 📝 使用示例

### Ant Design 组件使用

```tsx
import { Button, Input, Card, Pagination } from 'antd';

function Example() {
  return (
    <>
      <Input placeholder="搜索..." />
      <Button type="primary">搜索</Button>
      <Card title="案例卡片">内容</Card>
      <Pagination total={100} />
    </>
  );
}
```

### Zustand 状态管理

```tsx
// store/searchStore.ts
import { create } from 'zustand';

interface SearchState {
  keyword: string;
  setKeyword: (keyword: string) => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  keyword: '',
  setKeyword: (keyword) => set({ keyword }),
}));
```

### React Query 数据获取

```tsx
import { useQuery } from '@tanstack/react-query';
import { caseService } from '@/services/caseService';

function CaseList() {
  const { data, isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => caseService.search({}),
  });

  if (isLoading) return <div>加载中...</div>;
  return <div>{/* 渲染数据 */}</div>;
}
```

## ✅ 优势总结

1. **统一组件库**：完全使用 Ant Design，学习成本低，维护简单
2. **开发效率高**：组件丰富，开箱即用，快速开发
3. **类型安全**：TypeScript + Ant Design 完整类型定义
4. **性能优化**：按需引入，Tree Shaking，打包体积可控
5. **主题定制**：灵活的 Less 变量和 ConfigProvider 配置
6. **响应式设计**：内置响应式栅格系统
7. **中文支持**：完善的中文文档和国际化支持

---

**确认时间**: 2024-01-XX  
**状态**: ✅ 最终确认
