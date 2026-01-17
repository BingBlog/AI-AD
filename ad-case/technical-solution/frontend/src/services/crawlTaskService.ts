/**
 * 爬取任务相关 API 服务
 */
import api from '@/utils/request';
import type {
  CreateTaskRequest,
  CrawlTaskDetail,
  CrawlTaskListResponse,
  CrawlTaskLogsResponse,
  TaskListParams,
} from '@/types/crawlTask';
import type { BaseResponse } from '@/types/api';

/**
 * 获取上一次爬取到的页数
 */
export const getLastCrawledPage = async (
  dataSource: string = 'adquan'
): Promise<{ last_page: number | null; suggested_start_page: number }> => {
  const response = await api.get<
    BaseResponse<{ last_page: number | null; suggested_start_page: number }>
  >('/v1/crawl-tasks/last-page', {
    params: { data_source: dataSource },
  });
  return response;
};

/**
 * 创建任务
 */
export const createTask = async (
  request: CreateTaskRequest
): Promise<{ task_id: string; status: string; created_at: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string; created_at: string }>
  >('/v1/crawl-tasks', request);
  return response;
};

/**
 * 获取任务列表
 */
export const getTaskList = async (
  params: TaskListParams = {}
): Promise<CrawlTaskListResponse> => {
  const response = await api.get<BaseResponse<CrawlTaskListResponse>>(
    '/v1/crawl-tasks',
    { params }
  );
  return response;
};

/**
 * 获取任务详情
 */
export const getTaskDetail = async (
  taskId: string
): Promise<CrawlTaskDetail> => {
  const response = await api.get<BaseResponse<CrawlTaskDetail>>(
    `/v1/crawl-tasks/${taskId}`
  );
  return response;
};

/**
 * 开始任务
 */
export const startTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/start`);
  return response;
};

/**
 * 暂停任务
 */
export const pauseTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/pause`);
  return response;
};

/**
 * 恢复任务
 */
export const resumeTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/resume`);
  return response;
};

/**
 * 取消任务
 */
export const cancelTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/cancel`);
  return response;
};

/**
 * 终止任务
 */
export const terminateTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/terminate`);
  return response;
};

/**
 * 重试任务
 */
export const retryTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/retry`);
  return response;
};

/**
 * 获取任务日志
 */
export const getTaskLogs = async (
  taskId: string,
  level?: string,
  page: number = 1,
  pageSize: number = 50
): Promise<CrawlTaskLogsResponse> => {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (level) {
    params.level = level;
  }
  const response = await api.get<BaseResponse<CrawlTaskLogsResponse>>(
    `/v1/crawl-tasks/${taskId}/logs`,
    { params }
  );
  return response;
};

/**
 * 删除任务
 */
export const deleteTask = async (
  taskId: string
): Promise<{ task_id: string; deleted: boolean }> => {
  const response = await api.delete<
    BaseResponse<{ task_id: string; deleted: boolean }>
  >(`/v1/crawl-tasks/${taskId}`);
  return response;
};
