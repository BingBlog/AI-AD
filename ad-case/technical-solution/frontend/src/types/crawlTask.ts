/**
 * 爬取任务相关类型定义
 */

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'terminated';

export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

/**
 * 任务配置
 */
export interface CrawlTaskConfig {
  start_page: number;
  end_page?: number;
  case_type?: number;
  search_value?: string;
  batch_size: number;
  delay_min: number;
  delay_max: number;
  enable_resume: boolean;
}

/**
 * 任务进度
 */
export interface CrawlTaskProgress {
  total_pages?: number;
  completed_pages: number;
  current_page?: number;
  percentage: number;
  estimated_remaining_time?: number;
}

/**
 * 任务统计
 */
export interface CrawlTaskStats {
  total_crawled: number;
  total_saved: number;
  total_failed: number;
  batches_saved: number;
  success_rate: number;
  avg_speed?: number;
  avg_delay?: number;
  error_rate?: number;
}

/**
 * 任务时间线
 */
export interface CrawlTaskTimeline {
  created_at: string;
  started_at?: string;
  paused_at?: string;
  completed_at?: string;
}

/**
 * 任务基础信息
 */
export interface CrawlTaskBase {
  task_id: string;
  name: string;
  data_source: string;
  description?: string;
  status: TaskStatus;
  config: CrawlTaskConfig;
  progress: CrawlTaskProgress;
  stats: CrawlTaskStats;
  timeline: CrawlTaskTimeline;
}

/**
 * 任务列表项
 */
export interface CrawlTaskListItem {
  task_id: string;
  name: string;
  data_source: string;
  status: TaskStatus;
  progress: CrawlTaskProgress;
  stats: CrawlTaskStats;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

/**
 * 任务详情
 */
export interface CrawlTaskDetail extends CrawlTaskBase {
  error_message?: string;
  error_stack?: string;
}

/**
 * 创建任务请求
 */
export interface CreateTaskRequest {
  name: string;
  data_source?: string;
  description?: string;
  start_page?: number; // 可选，为空时自动设置为上一次爬取到的页数
  end_page: number; // 必填
  case_type?: number;
  search_value?: string;
  batch_size?: number;
  delay_min?: number;
  delay_max?: number;
  enable_resume?: boolean;
  execute_immediately?: boolean;
}

/**
 * 任务列表响应
 */
export interface CrawlTaskListResponse {
  tasks: CrawlTaskListItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 任务日志
 */
export interface CrawlTaskLog {
  id: number;
  level: LogLevel;
  message: string;
  details?: Record<string, any>;
  created_at: string;
}

/**
 * 任务日志响应
 */
export interface CrawlTaskLogsResponse {
  logs: CrawlTaskLog[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 任务列表查询参数
 */
export interface TaskListParams {
  status?: TaskStatus;
  data_source?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'started_at' | 'status' | 'progress';
  sort_order?: 'asc' | 'desc';
}

/**
 * 列表页记录状态
 */
export type ListPageStatus = 'success' | 'failed' | 'skipped' | 'pending';

/**
 * 列表页爬取记录
 */
export interface CrawlListPageRecord {
  id: number;
  task_id: string;
  page_number: number;
  status: ListPageStatus;
  error_message?: string;
  error_type?: string;
  items_count: number;
  crawled_at?: string;
  duration_seconds?: number;
  retry_count: number;
  last_retry_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 列表页记录响应
 */
export interface CrawlListPageRecordsResponse {
  records: CrawlListPageRecord[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 案例记录状态
 */
export type CaseRecordStatus = 'success' | 'failed' | 'skipped' | 'validation_failed' | 'pending';

/**
 * 案例爬取记录
 */
export interface CrawlCaseRecord {
  id: number;
  task_id: string;
  list_page_id?: number;
  case_id?: number;
  case_url?: string;
  case_title?: string;
  status: CaseRecordStatus;
  error_message?: string;
  error_type?: string;
  error_stack?: string;
  crawled_at?: string;
  duration_seconds?: number;
  has_detail_data: boolean;
  has_validation_error: boolean;
  validation_errors?: Record<string, any>;
  saved_to_json: boolean;
  batch_file_name?: string;
  retry_count: number;
  last_retry_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 案例记录响应
 */
export interface CrawlCaseRecordsResponse {
  records: CrawlCaseRecord[];
  total: number;
  page: number;
  page_size: number;
}
