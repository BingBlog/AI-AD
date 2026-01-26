/**
 * 爬取任务列表页
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Tag,
  Progress,
  Space,
  Input,
  Select,
  message,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  DeleteOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { getTaskList, startTask, pauseTask, resumeTask, terminateTask, deleteTask } from '@/services/crawlTaskService';
import type { CrawlTaskListItem, TaskStatus } from '@/types/crawlTask';
import styles from './List.module.less';

const { Search } = Input;
const { Option } = Select;

const CrawlTasksList: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState<CrawlTaskListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | undefined>();
  const [keyword, setKeyword] = useState('');

  // 获取任务列表
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await getTaskList({
        status: statusFilter,
        keyword: keyword || undefined,
        page,
        page_size: pageSize,
        sort_by: 'created_at',
        sort_order: 'desc',
      });
      setTasks(response.tasks);
      setTotal(response.total);
    } catch (error: any) {
      message.error(`获取任务列表失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [page, pageSize, statusFilter]);

  // 状态颜色映射
  const getStatusColor = (status: TaskStatus): string => {
    const colorMap: Record<TaskStatus, string> = {
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
  const getStatusText = (status: TaskStatus): string => {
    const textMap: Record<TaskStatus, string> = {
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

  // 处理任务操作
  const handleStart = async (taskId: string) => {
    try {
      await startTask(taskId);
      message.success('任务已开始');
      fetchTasks();
    } catch (error: any) {
      message.error(`开始任务失败: ${error.message}`);
    }
  };

  const handlePause = async (taskId: string) => {
    try {
      await pauseTask(taskId);
      message.success('任务已暂停');
      fetchTasks();
    } catch (error: any) {
      message.error(`暂停任务失败: ${error.message}`);
    }
  };

  const handleResume = async (taskId: string) => {
    try {
      await resumeTask(taskId);
      message.success('任务已恢复');
      fetchTasks();
    } catch (error: any) {
      message.error(`恢复任务失败: ${error.message}`);
    }
  };

  const handleTerminate = async (taskId: string) => {
    try {
      await terminateTask(taskId);
      message.success('任务已终止');
      fetchTasks();
    } catch (error: any) {
      message.error(`终止任务失败: ${error.message}`);
    }
  };

  const handleDelete = async (taskId: string) => {
    try {
      await deleteTask(taskId);
      message.success('任务已删除');
      fetchTasks();
    } catch (error: any) {
      message.error(`删除任务失败: ${error.message}`);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: CrawlTaskListItem) => (
        <Button
          type="link"
          onClick={() => navigate(`/crawl-tasks/${record.task_id}`)}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_: any, record: CrawlTaskListItem) => {
        const { progress } = record;
        return (
          <div>
            <Progress
              percent={progress.percentage}
              size="small"
              status={record.status === 'failed' ? 'exception' : 'active'}
            />
            <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
              {progress.completed_pages} / {progress.total_pages || '?'} 页
            </div>
          </div>
        );
      },
    },
    {
      title: '统计',
      key: 'stats',
      width: 150,
      render: (_: any, record: CrawlTaskListItem) => {
        const { stats } = record;
        return (
          <div style={{ fontSize: '12px' }}>
            <div>已爬取: {stats.total_crawled}</div>
            <div>已保存: {stats.total_saved}</div>
            <div>失败: {stats.total_failed}</div>
          </div>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: CrawlTaskListItem) => {
        const { status, task_id } = record;
        return (
          <Space>
            {status === 'pending' && (
              <Button
                type="link"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStart(task_id)}
              >
                开始
              </Button>
            )}
            {status === 'running' && (
              <>
                <Button
                  type="link"
                  icon={<PauseCircleOutlined />}
                  onClick={() => handlePause(task_id)}
                >
                  暂停
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={() => handleTerminate(task_id)}
                >
                  <Button type="link" danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === 'paused' && (
              <>
                <Button
                  type="link"
                  icon={<PlayCircleOutlined />}
                  onClick={() => handleResume(task_id)}
                >
                  恢复
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={() => handleTerminate(task_id)}
                >
                  <Button type="link" danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === 'failed' && (
              <Button
                type="link"
                icon={<ReloadOutlined />}
                onClick={() => navigate(`/crawl-tasks/${task_id}`)}
              >
                重试
              </Button>
            )}
            {(status === 'completed' || status === 'failed' || status === 'cancelled') && (
              <Popconfirm
                title="确定要删除任务吗？"
                onConfirm={() => handleDelete(task_id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div className={styles.container}>
      <Card
        title="爬取任务管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/crawl-tasks/create')}
          >
            创建任务
          </Button>
        }
      >
        {/* 筛选栏 */}
        <div className={styles.filters}>
          <Space>
            <Search
              placeholder="搜索任务名称或描述"
              allowClear
              style={{ width: 300 }}
              onSearch={(value) => {
                setKeyword(value);
                setPage(1);
                fetchTasks();
              }}
            />
            <Select
              placeholder="筛选状态"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => {
                setStatusFilter(value);
                setPage(1);
              }}
            >
              <Option value="pending">等待中</Option>
              <Option value="running">运行中</Option>
              <Option value="paused">已暂停</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">已失败</Option>
              <Option value="cancelled">已取消</Option>
              <Option value="terminated">已终止</Option>
            </Select>
          </Space>
        </div>

        {/* 任务列表 */}
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize) {
                setPageSize(newPageSize);
              }
            },
          }}
        />
      </Card>
    </div>
  );
};

export default CrawlTasksList;
