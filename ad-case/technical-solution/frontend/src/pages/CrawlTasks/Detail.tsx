/**
 * 爬取任务详情页
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Progress,
  Button,
  Space,
  message,
  Popconfirm,
  Tabs,
  Table,
  Select,
  Input,
  Collapse,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import {
  getTaskDetail,
  startTask,
  pauseTask,
  resumeTask,
  terminateTask,
  retryTask,
  deleteTask,
  getTaskLogs,
  getTaskListPages,
  getTaskCaseRecords,
} from '@/services/crawlTaskService';
import type {
  CrawlTaskDetail,
  CrawlTaskLog,
  LogLevel,
  CrawlListPageRecord,
  CrawlCaseRecord,
  ListPageStatus,
  CaseRecordStatus,
} from '@/types/crawlTask';
import styles from './Detail.module.less';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Panel } = Collapse;

const CrawlTasksDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [task, setTask] = useState<CrawlTaskDetail | null>(null);
  const [logs, setLogs] = useState<CrawlTaskLog[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logLevel, setLogLevel] = useState<string>('ALL');
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(50);

  // 列表页记录相关状态
  const [listPages, setListPages] = useState<CrawlListPageRecord[]>([]);
  const [listPagesLoading, setListPagesLoading] = useState(false);
  const [listPageStatus, setListPageStatus] = useState<string>('ALL');
  const [listPagePage, setListPagePage] = useState(1);
  const [listPagePageSize, setListPagePageSize] = useState(50);
  const [listPagesTotal, setListPagesTotal] = useState(0);

  // 案例记录相关状态
  const [caseRecords, setCaseRecords] = useState<CrawlCaseRecord[]>([]);
  const [caseRecordsLoading, setCaseRecordsLoading] = useState(false);
  const [caseRecordStatus, setCaseRecordStatus] = useState<string>('ALL');
  const [caseRecordPage, setCaseRecordPage] = useState(1);
  const [caseRecordPageSize, setCaseRecordPageSize] = useState(50);
  const [caseRecordsTotal, setCaseRecordsTotal] = useState(0);

  // 获取任务详情
  const fetchTaskDetail = async () => {
    if (!taskId) return;

    setLoading(true);
    try {
      const data = await getTaskDetail(taskId);
      setTask(data);
    } catch (error: any) {
      message.error(`获取任务详情失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 获取任务日志
  const fetchLogs = async () => {
    if (!taskId) return;

    setLogsLoading(true);
    try {
      const response = await getTaskLogs(
        taskId,
        logLevel === 'ALL' ? undefined : logLevel,
        logPage,
        logPageSize
      );
      setLogs(response.logs);
    } catch (error: any) {
      message.error(`获取任务日志失败: ${error.message}`);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchTaskDetail();
  }, [taskId]);

  useEffect(() => {
    fetchLogs();
  }, [taskId, logLevel, logPage, logPageSize]);

  // 获取列表页记录
  const fetchListPages = async () => {
    if (!taskId) return;

    setListPagesLoading(true);
    try {
      const response = await getTaskListPages(
        taskId,
        listPageStatus === 'ALL' ? undefined : listPageStatus,
        listPagePage,
        listPagePageSize
      );
      setListPages(response.records);
      setListPagesTotal(response.total);
    } catch (error: any) {
      message.error(`获取列表页记录失败: ${error.message}`);
    } finally {
      setListPagesLoading(false);
    }
  };

  // 获取案例记录
  const fetchCaseRecords = async () => {
    if (!taskId) return;

    setCaseRecordsLoading(true);
    try {
      const response = await getTaskCaseRecords(
        taskId,
        caseRecordStatus === 'ALL' ? undefined : caseRecordStatus,
        undefined,
        caseRecordPage,
        caseRecordPageSize
      );
      setCaseRecords(response.records);
      setCaseRecordsTotal(response.total);
    } catch (error: any) {
      message.error(`获取案例记录失败: ${error.message}`);
    } finally {
      setCaseRecordsLoading(false);
    }
  };

  useEffect(() => {
    fetchListPages();
  }, [taskId, listPageStatus, listPagePage, listPagePageSize]);

  useEffect(() => {
    fetchCaseRecords();
  }, [taskId, caseRecordStatus, caseRecordPage, caseRecordPageSize]);

  // 状态颜色映射
  const getStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      pending: 'blue',
      running: 'green',
      paused: 'orange',
      completed: 'green',
      failed: 'red',
      cancelled: 'default',
      terminated: 'default',
    };
    return colorMap[status] || 'default';
  };

  // 状态文本映射
  const getStatusText = (status: string): string => {
    const textMap: Record<string, string> = {
      pending: '等待中',
      running: '运行中',
      paused: '已暂停',
      completed: '已完成',
      failed: '已失败',
      cancelled: '已取消',
      terminated: '已终止',
    };
    return textMap[status] || status;
  };

  // 日志级别颜色映射
  const getLogLevelColor = (level: LogLevel): string => {
    const colorMap: Record<LogLevel, string> = {
      INFO: 'blue',
      WARNING: 'orange',
      ERROR: 'red',
      DEBUG: 'default',
    };
    return colorMap[level] || 'default';
  };

  // 列表页状态颜色映射
  const getListPageStatusColor = (status: ListPageStatus): string => {
    const colorMap: Record<ListPageStatus, string> = {
      success: 'green',
      failed: 'red',
      skipped: 'orange',
      pending: 'blue',
    };
    return colorMap[status] || 'default';
  };

  // 列表页状态文本映射
  const getListPageStatusText = (status: ListPageStatus): string => {
    const textMap: Record<ListPageStatus, string> = {
      success: '成功',
      failed: '失败',
      skipped: '跳过',
      pending: '等待中',
    };
    return textMap[status] || status;
  };

  // 案例记录状态颜色映射
  const getCaseRecordStatusColor = (status: CaseRecordStatus): string => {
    const colorMap: Record<CaseRecordStatus, string> = {
      success: 'green',
      failed: 'red',
      skipped: 'orange',
      validation_failed: 'purple',
      pending: 'blue',
    };
    return colorMap[status] || 'default';
  };

  // 案例记录状态文本映射
  const getCaseRecordStatusText = (status: CaseRecordStatus): string => {
    const textMap: Record<CaseRecordStatus, string> = {
      success: '成功',
      failed: '失败',
      skipped: '跳过',
      validation_failed: '验证失败',
      pending: '等待中',
    };
    return textMap[status] || status;
  };

  // 处理任务操作
  const handleStart = async () => {
    if (!taskId) return;
    try {
      await startTask(taskId);
      message.success('任务已开始');
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`开始任务失败: ${error.message}`);
    }
  };

  const handlePause = async () => {
    if (!taskId) return;
    try {
      await pauseTask(taskId);
      message.success('任务已暂停');
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`暂停任务失败: ${error.message}`);
    }
  };

  const handleResume = async () => {
    if (!taskId) return;
    try {
      await resumeTask(taskId);
      message.success('任务已恢复');
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`恢复任务失败: ${error.message}`);
    }
  };

  const handleTerminate = async () => {
    if (!taskId) return;
    try {
      await terminateTask(taskId);
      message.success('任务已终止');
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`终止任务失败: ${error.message}`);
    }
  };

  const handleRetry = async () => {
    if (!taskId) return;
    try {
      await retryTask(taskId);
      message.success('任务已重置，准备重试');
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`重试任务失败: ${error.message}`);
    }
  };

  const handleDelete = async () => {
    if (!taskId) return;
    try {
      await deleteTask(taskId);
      message.success('任务已删除');
      navigate('/crawl-tasks');
    } catch (error: any) {
      message.error(`删除任务失败: ${error.message}`);
    }
  };

  // 格式化时间
  const formatTime = (time?: string) => {
    if (!time) return '-';
    return new Date(time).toLocaleString('zh-CN');
  };

  // 格式化剩余时间
  const formatRemainingTime = (seconds?: number) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`;
    } else if (minutes > 0) {
      return `${minutes}分钟 ${secs}秒`;
    } else {
      return `${secs}秒`;
    }
  };

  if (!task) {
    return <div>加载中...</div>;
  }

  const { status, progress, stats, config, timeline, error_message, error_stack } = task;

  // 日志表格列
  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => formatTime(text),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: LogLevel) => (
        <Tag color={getLogLevelColor(level)}>{level}</Tag>
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
  ];

  // 列表页记录表格列
  const listPageColumns = [
    {
      title: '页码',
      dataIndex: 'page_number',
      key: 'page_number',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ListPageStatus) => (
        <Tag color={getListPageStatusColor(status)}>
          {getListPageStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '案例数量',
      dataIndex: 'items_count',
      key: 'items_count',
      width: 100,
    },
    {
      title: '爬取时间',
      dataIndex: 'crawled_at',
      key: 'crawled_at',
      width: 180,
      render: (text: string) => (text ? formatTime(text) : '-'),
    },
    {
      title: '耗时（秒）',
      dataIndex: 'duration_seconds',
      key: 'duration_seconds',
      width: 120,
      render: (value: number) => (value ? value.toFixed(2) : '-'),
    },
    {
      title: '错误类型',
      dataIndex: 'error_type',
      key: 'error_type',
      width: 150,
      render: (text: string) => text || '-',
    },
    {
      title: '错误消息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 100,
    },
  ];

  // 案例记录表格列
  const caseRecordColumns = [
    {
      title: '案例ID',
      dataIndex: 'case_id',
      key: 'case_id',
      width: 100,
      render: (value: number) => value || '-',
    },
    {
      title: '案例标题',
      dataIndex: 'case_title',
      key: 'case_title',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: CaseRecordStatus) => (
        <Tag color={getCaseRecordStatusColor(status)}>
          {getCaseRecordStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '爬取时间',
      dataIndex: 'crawled_at',
      key: 'crawled_at',
      width: 180,
      render: (text: string) => (text ? formatTime(text) : '-'),
    },
    {
      title: '耗时（秒）',
      dataIndex: 'duration_seconds',
      key: 'duration_seconds',
      width: 120,
      render: (value: number) => (value ? value.toFixed(2) : '-'),
    },
    {
      title: '错误类型',
      dataIndex: 'error_type',
      key: 'error_type',
      width: 150,
      render: (text: string) => text || '-',
    },
    {
      title: '错误消息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '已保存',
      dataIndex: 'saved_to_json',
      key: 'saved_to_json',
      width: 100,
      render: (value: boolean) => (
        <Tag color={value ? 'green' : 'default'}>
          {value ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 100,
    },
  ];

  return (
    <div className={styles.container}>
      <Card
        title={
          <Space>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/crawl-tasks')}
            >
              返回
            </Button>
            <span>{task.name}</span>
            <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
          </Space>
        }
        extra={
          <Space>
            {status === 'pending' && (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                开始执行
              </Button>
            )}
            {status === 'running' && (
              <>
                <Button icon={<PauseCircleOutlined />} onClick={handlePause}>
                  暂停
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={handleTerminate}
                >
                  <Button danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === 'paused' && (
              <>
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleResume}>
                  恢复
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={handleTerminate}
                >
                  <Button danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === 'failed' && (
              <Button type="primary" icon={<ReloadOutlined />} onClick={handleRetry}>
                重试
              </Button>
            )}
            {(status === 'completed' || status === 'failed' || status === 'cancelled') && (
              <Popconfirm title="确定要删除任务吗？" onConfirm={handleDelete}>
                <Button danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            )}
          </Space>
        }
        loading={loading}
      >
        <Tabs defaultActiveKey="info">
          <TabPane tab="基本信息" key="info">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="任务ID">{task.task_id}</Descriptions.Item>
              <Descriptions.Item label="任务名称">{task.name}</Descriptions.Item>
              <Descriptions.Item label="数据源">{task.data_source}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatTime(timeline.created_at)}</Descriptions.Item>
              <Descriptions.Item label="开始时间">{formatTime(timeline.started_at)}</Descriptions.Item>
              <Descriptions.Item label="完成时间">{formatTime(timeline.completed_at)}</Descriptions.Item>
              <Descriptions.Item label="暂停时间">{formatTime(timeline.paused_at)}</Descriptions.Item>
              {task.description && (
                <Descriptions.Item label="描述" span={2}>
                  {task.description}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Card title="任务配置" style={{ marginTop: 16 }}>
              <Descriptions column={2} bordered>
                <Descriptions.Item label="起始页码">{config.start_page}</Descriptions.Item>
                <Descriptions.Item label="结束页码">{config.end_page || '全部'}</Descriptions.Item>
                <Descriptions.Item label="案例类型">{config.case_type || '全部'}</Descriptions.Item>
                <Descriptions.Item label="搜索关键词">{config.search_value || '-'}</Descriptions.Item>
                <Descriptions.Item label="批次大小">{config.batch_size}</Descriptions.Item>
                <Descriptions.Item label="延迟时间">
                  {config.delay_min} - {config.delay_max} 秒
                </Descriptions.Item>
                <Descriptions.Item label="断点续传">
                  {config.enable_resume ? '是' : '否'}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </TabPane>

          <TabPane tab="进度信息" key="progress">
            <Card title="总体进度">
              <Progress
                percent={progress.percentage}
                status={status === 'failed' ? 'exception' : 'active'}
                strokeWidth={20}
              />
              <div style={{ marginTop: 16 }}>
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="总页数">{progress.total_pages || '-'}</Descriptions.Item>
                  <Descriptions.Item label="已完成页数">{progress.completed_pages}</Descriptions.Item>
                  <Descriptions.Item label="当前页码">{progress.current_page || '-'}</Descriptions.Item>
                  <Descriptions.Item label="预计剩余时间">
                    {formatRemainingTime(progress.estimated_remaining_time)}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            </Card>

            <Card title="统计信息" style={{ marginTop: 16 }}>
              <Descriptions column={2} bordered>
                <Descriptions.Item label="总爬取数">{stats.total_crawled}</Descriptions.Item>
                <Descriptions.Item label="总保存数">{stats.total_saved}</Descriptions.Item>
                <Descriptions.Item label="失败数">{stats.total_failed}</Descriptions.Item>
                <Descriptions.Item label="已保存批次数">{stats.batches_saved}</Descriptions.Item>
                <Descriptions.Item label="成功率">
                  {(stats.success_rate * 100).toFixed(2)}%
                </Descriptions.Item>
                <Descriptions.Item label="平均速度">
                  {stats.avg_speed ? `${stats.avg_speed.toFixed(2)} 案例/分钟` : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="平均延迟">
                  {stats.avg_delay ? `${stats.avg_delay.toFixed(2)} 秒` : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="错误率">
                  {stats.error_rate ? `${(stats.error_rate * 100).toFixed(2)}%` : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {error_message && (
              <Card title="错误信息" style={{ marginTop: 16 }}>
                <Collapse>
                  <Panel header="错误消息" key="1">
                    <TextArea value={error_message} readOnly rows={4} />
                  </Panel>
                  {error_stack && (
                    <Panel header="错误堆栈" key="2">
                      <TextArea value={error_stack} readOnly rows={10} />
                    </Panel>
                  )}
                </Collapse>
              </Card>
            )}
          </TabPane>

          <TabPane tab="任务日志" key="logs">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Select
                  value={logLevel}
                  style={{ width: 150 }}
                  onChange={setLogLevel}
                >
                  <Select.Option value="ALL">全部级别</Select.Option>
                  <Select.Option value="INFO">INFO</Select.Option>
                  <Select.Option value="WARNING">WARNING</Select.Option>
                  <Select.Option value="ERROR">ERROR</Select.Option>
                </Select>
                <Button onClick={fetchLogs}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={logColumns}
              dataSource={logs}
              rowKey="id"
              loading={logsLoading}
              pagination={{
                current: logPage,
                pageSize: logPageSize,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
                onChange: (page, pageSize) => {
                  setLogPage(page);
                  setLogPageSize(pageSize);
                },
              }}
            />
          </TabPane>

          <TabPane tab="列表页记录" key="list-pages">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Select
                  value={listPageStatus}
                  style={{ width: 150 }}
                  onChange={setListPageStatus}
                >
                  <Select.Option value="ALL">全部状态</Select.Option>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="failed">失败</Select.Option>
                  <Select.Option value="skipped">跳过</Select.Option>
                  <Select.Option value="pending">等待中</Select.Option>
                </Select>
                <Button onClick={fetchListPages}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={listPageColumns}
              dataSource={listPages}
              rowKey="id"
              loading={listPagesLoading}
              pagination={{
                current: listPagePage,
                pageSize: listPagePageSize,
                total: listPagesTotal,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
                onChange: (page, pageSize) => {
                  setListPagePage(page);
                  setListPagePageSize(pageSize);
                },
              }}
            />
          </TabPane>

          <TabPane tab="案例记录" key="cases">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Select
                  value={caseRecordStatus}
                  style={{ width: 150 }}
                  onChange={setCaseRecordStatus}
                >
                  <Select.Option value="ALL">全部状态</Select.Option>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="failed">失败</Select.Option>
                  <Select.Option value="validation_failed">验证失败</Select.Option>
                  <Select.Option value="skipped">跳过</Select.Option>
                  <Select.Option value="pending">等待中</Select.Option>
                </Select>
                <Button onClick={fetchCaseRecords}>刷新</Button>
              </Space>
            </div>
            <Table
              columns={caseRecordColumns}
              dataSource={caseRecords}
              rowKey="id"
              loading={caseRecordsLoading}
              pagination={{
                current: caseRecordPage,
                pageSize: caseRecordPageSize,
                total: caseRecordsTotal,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
                onChange: (page, pageSize) => {
                  setCaseRecordPage(page);
                  setCaseRecordPageSize(pageSize);
                },
              }}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default CrawlTasksDetail;
