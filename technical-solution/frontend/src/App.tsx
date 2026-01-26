/**
 * 主应用组件
 */
import { Suspense } from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Outlet } from 'react-router-dom';
import { Spin } from 'antd';
import Layout from '@/components/Layout';
import '@/styles/variables.css';
import '@/styles/global.less';

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 分钟
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
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
        <Layout>
          <Suspense
            fallback={
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </Layout>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
