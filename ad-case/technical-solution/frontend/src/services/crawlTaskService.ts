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
  CrawlListPageRecordsResponse,
  CrawlCaseRecordsResponse,
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

/**
 * 获取任务的列表页记录
 */
export const getTaskListPages = async (
  taskId: string,
  status?: string,
  page: number = 1,
  pageSize: number = 50
): Promise<CrawlListPageRecordsResponse> => {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (status) {
    params.status = status;
  }
  const response = await api.get<BaseResponse<CrawlListPageRecordsResponse>>(
    `/v1/crawl-tasks/${taskId}/list-pages`,
    { params }
  );
  // 响应拦截器已经处理了 BaseResponse，直接返回 data
  return response as unknown as CrawlListPageRecordsResponse;
};

/**
 * 获取任务的案例记录
 */
export const getTaskCaseRecords = async (
  taskId: string,
  status?: string,
  listPageId?: number,
  page: number = 1,
  pageSize: number = 50
): Promise<CrawlCaseRecordsResponse> => {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (status) {
    params.status = status;
  }
  if (listPageId !== undefined) {
    params.list_page_id = listPageId;
  }
  const response = await api.get<BaseResponse<CrawlCaseRecordsResponse>>(
    `/v1/crawl-tasks/${taskId}/cases`,
    { params }
  );
  // 响应拦截器已经处理了 BaseResponse，直接返回 data
  return response as unknown as CrawlCaseRecordsResponse;
};

/**
 * 检查任务的真实状态
 */
export interface TaskRealStatus {
  exists: boolean;
  db_status?: string;
  executor_exists?: boolean;
  executor_running?: boolean;
  executor_paused?: boolean;
  status_mismatch?: boolean;
  progress_stalled?: boolean;
  warnings?: string[];
  recommendations?: string[];
  message?: string;
  fixed?: boolean;
}

export const checkTaskRealStatus = async (
  taskId: string,
  autoFix: boolean = false
): Promise<TaskRealStatus> => {
  const response = await api.get<BaseResponse<TaskRealStatus>>(
    `/v1/crawl-tasks/${taskId}/real-status`,
    { params: { auto_fix: autoFix } }
  );
  return response;
};

/**
 * 从JSON文件同步案例记录到数据库
 */
export const syncCaseRecords = async (
  taskId: string
): Promise<{ success: boolean; message: string; total_synced?: number; total_errors?: number }> => {
  const response = await api.post<
    BaseResponse<{ success: boolean; message: string; total_synced?: number; total_errors?: number }>
  >(`/v1/crawl-tasks/${taskId}/sync-case-records`);
  return response;
};
