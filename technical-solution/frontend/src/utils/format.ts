/**
 * 格式化工具函数
 */
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

// 配置 dayjs 插件
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

/**
 * 格式化日期
 */
export const formatDate = (date: string | undefined, format = 'YYYY-MM-DD') => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

/**
 * 格式化日期时间
 */
export const formatDateTime = (date: string | undefined) => {
  return formatDate(date, 'YYYY-MM-DD HH:mm:ss');
};

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (date: string | undefined) => {
  if (!date) return '-';
  return dayjs(date).fromNow();
};

/**
 * 截取文本
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};
