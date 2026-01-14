/**
 * API 相关类型定义
 */

export interface BaseResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

export interface ErrorResponse {
  code: number;
  message: string;
  data: null;
  errors?: Array<{
    field?: string;
    message: string;
  }>;
}
