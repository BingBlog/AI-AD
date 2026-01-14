/**
 * 路由配置
 */
import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import App from '@/App';

// 路由懒加载
const Home = lazy(() => import('@/pages/Home'));
const CasesList = lazy(() => import('@/pages/Cases/List'));
const CaseDetail = lazy(() => import('@/pages/Cases/Detail'));

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: 'cases',
        element: <CasesList />,
      },
      {
        path: 'cases/:id',
        element: <CaseDetail />,
      },
    ],
  },
]);
