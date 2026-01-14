/**
 * 常量定义
 */

// API 基础 URL
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// 分页选项
export const PAGE_SIZE_OPTIONS = [20, 40, 60, 100];

// 排序选项
export const SORT_OPTIONS = [
  { value: 'relevance', label: '相关性' },
  { value: 'time', label: '时间' },
  { value: 'score', label: '评分' },
  { value: 'favourite', label: '收藏数' },
] as const;

// 排序顺序选项
export const SORT_ORDER_OPTIONS = [
  { value: 'desc', label: '降序' },
  { value: 'asc', label: '升序' },
] as const;

// 时间快捷选项
export const DATE_RANGE_PRESETS = [
  { label: '最近一周', value: 7 },
  { label: '最近一月', value: 30 },
  { label: '最近三月', value: 90 },
  { label: '最近一年', value: 365 },
] as const;
