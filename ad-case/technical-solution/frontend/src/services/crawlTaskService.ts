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
 * 重试任务（仅重试失败的案例）
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
 * 重新执行任务（从起始页重新开始整个任务）
 */
export const restartTask = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/restart`);
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
  savedToJson?: boolean,
  imported?: boolean,
  importStatus?: string,
  verified?: boolean,
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
  if (savedToJson !== undefined) {
    params.saved_to_json = savedToJson;
  }
  if (imported !== undefined) {
    params.imported = imported;
  }
  if (importStatus) {
    params.import_status = importStatus;
  }
  if (verified !== undefined) {
    params.verified = verified;
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
  filesystem?: {
    resume_file_exists?: boolean;
    resume_file_stalled?: boolean;
    resume_file_hours_since_update?: number;
    resume_file_crawled_ids_count?: number;
    resume_file_total_count?: number;
    resume_file_last_updated?: string;
    batch_files_count?: number;
    first_batch_file?: string;
    last_batch_file?: string;
    last_batch_file_size_mb?: number;
    last_batch_file_mtime?: string;
  };
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

/**
 * 将任务数据同步到 cases 数据库表（启动导入任务，使用默认配置）
 */
export const syncToCasesDb = async (
  taskId: string
): Promise<{ import_id: string; task_id: string; status: string; started_at?: string }> => {
  const response = await api.post<
    BaseResponse<{ import_id: string; task_id: string; status: string; started_at?: string }>
  >(`/v1/crawl-tasks/${taskId}/sync-to-cases-db`);
  return response;
};

/**
 * 导入选项配置
 */
export interface ImportStartRequest {
  import_mode?: "full" | "selective";
  selected_batches?: string[];
  import_failed_only?: boolean;
  skip_existing?: boolean;
  update_existing?: boolean;
  generate_vectors?: boolean;
  skip_invalid?: boolean;
  batch_size?: number;
  normalize_data?: boolean;
}

/**
 * 启动导入任务（带配置选项）
 */
export const startImport = async (
  taskId: string,
  config: ImportStartRequest
): Promise<{ import_id: string; task_id: string; status: string; started_at?: string }> => {
  const response = await api.post<
    BaseResponse<{ import_id: string; task_id: string; status: string; started_at?: string }>
  >(`/v1/crawl-tasks/${taskId}/import`, config);
  return response;
};

/**
 * 获取任务的批次文件列表
 */
export const getBatchFiles = async (taskId: string): Promise<string[]> => {
  const response = await api.get<BaseResponse<string[]>>(
    `/v1/crawl-tasks/${taskId}/import/batch-files`
  );
  return response;
};

/**
 * 导入状态相关类型定义
 */
export interface ImportProgress {
  total_cases: number;
  loaded_cases: number;
  valid_cases: number;
  invalid_cases: number;
  existing_cases: number;
  imported_cases: number;
  failed_cases: number;
  current_file?: string;
  percentage: number;
  estimated_remaining_time?: number;
}

export interface ImportStats {
  total_loaded: number;
  total_valid: number;
  total_invalid: number;
  total_existing: number;
  total_imported: number;
  total_failed: number;
}

export interface ImportStatus {
  import_id: string;
  task_id: string;
  status: string;
  progress: ImportProgress;
  stats: ImportStats;
  started_at?: string;
  updated_at?: string;
}

/**
 * 获取导入状态和进度
 */
export const getImportStatus = async (
  taskId: string
): Promise<ImportStatus | null> => {
  try {
    const response = await api.get<BaseResponse<ImportStatus>>(
      `/v1/crawl-tasks/${taskId}/import/status`
    );
    return response;
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null; // 未找到导入记录
    }
    throw error;
  }
};

/**
 * 取消导入任务
 */
export const cancelImport = async (
  taskId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post<
    BaseResponse<{ task_id: string; status: string }>
  >(`/v1/crawl-tasks/${taskId}/import/cancel`);
  return response;
};

/**
 * 验证导入状态（检查案例是否在案例库中存在）
 */
export const verifyImports = async (
  taskId: string
): Promise<{ total_checked: number; verified_count: number; unverified_count: number }> => {
  const response = await api.post<
    BaseResponse<{ total_checked: number; verified_count: number; unverified_count: number }>
  >(`/v1/crawl-tasks/${taskId}/verify-imports`);
  return response;
};

/**
 * 验证单个案例数据
 */
export const validateSingleCase = async (
  taskId: string,
  caseId: number,
  normalizeData: boolean = true
): Promise<{
  is_valid: boolean;
  error_message?: string;
  formatted_case?: any;
  validation_errors?: any;
}> => {
  const response = await api.post<
    BaseResponse<{
      is_valid: boolean;
      error_message?: string;
      formatted_case?: any;
      validation_errors?: any;
    }>
  >(`/v1/crawl-tasks/${taskId}/case-records/${caseId}/validate`, null, {
    params: { normalize_data: normalizeData },
  });
  return response;
};

/**
 * 导入单个案例
 */
export const importSingleCase = async (
  taskId: string,
  caseId: number,
  normalizeData: boolean = true,
  generateVectors: boolean = true
): Promise<{
  success: boolean;
  error_message?: string;
  imported_case_id?: number;
}> => {
  const response = await api.post<
    BaseResponse<{
      success: boolean;
      error_message?: string;
      imported_case_id?: number;
    }>
  >(`/v1/crawl-tasks/${taskId}/case-records/${caseId}/import`, null, {
    params: {
      normalize_data: normalizeData,
      generate_vectors: generateVectors,
    },
  });
  return response;
};
