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
const CrawlTasksList = lazy(() => import('@/pages/CrawlTasks/List'));
const CrawlTasksCreate = lazy(() => import('@/pages/CrawlTasks/Create'));
const CrawlTasksDetail = lazy(() => import('@/pages/CrawlTasks/Detail'));

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
      {
        path: 'crawl-tasks',
        element: <CrawlTasksList />,
      },
      {
        path: 'crawl-tasks/create',
        element: <CrawlTasksCreate />,
      },
      {
        path: 'crawl-tasks/:taskId',
        element: <CrawlTasksDetail />,
      },
    ],
  },
]);
