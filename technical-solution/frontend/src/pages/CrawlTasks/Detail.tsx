/**
 * 爬取任务详情页
 */
import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
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
} from "antd";
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import {
  getTaskDetail,
  startTask,
  pauseTask,
  resumeTask,
  terminateTask,
  retryTask,
  restartTask,
  deleteTask,
  getTaskLogs,
  getTaskListPages,
  getTaskCaseRecords,
  checkTaskRealStatus,
  syncCaseRecords,
  syncToCasesDb,
  getImportStatus,
  cancelImport,
  verifyImports,
  startImport,
  validateSingleCase,
  importSingleCase,
  TaskRealStatus,
  ImportStatus,
  type ImportStartRequest,
} from "@/services/crawlTaskService";
import ImportDialog from "@/components/ImportDialog/ImportDialog";
import type {
  CrawlTaskDetail,
  CrawlTaskLog,
  LogLevel,
  CrawlListPageRecord,
  CrawlCaseRecord,
  ListPageStatus,
  CaseRecordStatus,
} from "@/types/crawlTask";
import styles from "./Detail.module.less";

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Panel } = Collapse;

// 案例记录操作组件
const CaseRecordActions: React.FC<{
  taskId: string | undefined;
  record: CrawlCaseRecord;
  onRefresh: () => Promise<void>;
}> = ({ taskId, record, onRefresh }) => {
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);

  const handleValidate = async () => {
    if (!taskId || !record.case_id) return;
    setValidating(true);
    try {
      const result = await validateSingleCase(taskId, record.case_id, true);
      if (result.is_valid) {
        message.success("验证通过");
      } else {
        message.error(`验证失败: ${result.error_message || "未知错误"}`);
      }
      // 刷新数据
      await onRefresh();
    } catch (error: any) {
      message.error(`验证失败: ${error.message}`);
    } finally {
      setValidating(false);
    }
  };

  const handleImport = async () => {
    if (!taskId || !record.case_id) return;
    setImporting(true);
    try {
      const result = await importSingleCase(taskId, record.case_id, true, true);
      if (result.success) {
        message.success("导入成功");
      } else {
        message.error(`导入失败: ${result.error_message || "未知错误"}`);
      }
      // 刷新数据
      await onRefresh();
    } catch (error: any) {
      message.error(`导入失败: ${error.message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <Space size="small">
      <Button
        size="small"
        type="link"
        loading={validating}
        onClick={handleValidate}
        disabled={!record.case_id || !record.saved_to_json}
      >
        验证
      </Button>
      <Button
        size="small"
        type="link"
        loading={importing}
        onClick={handleImport}
        disabled={!record.case_id || !record.saved_to_json}
      >
        导入
      </Button>
    </Space>
  );
};

const CrawlTasksDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [task, setTask] = useState<CrawlTaskDetail | null>(null);
  const [logs, setLogs] = useState<CrawlTaskLog[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logLevel, setLogLevel] = useState<string>("ALL");
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(50);

  // 列表页记录相关状态
  const [listPages, setListPages] = useState<CrawlListPageRecord[]>([]);
  const [listPagesLoading, setListPagesLoading] = useState(false);
  const [listPageStatus, setListPageStatus] = useState<string>("ALL");
  const [listPagePage, setListPagePage] = useState(1);
  const [listPagePageSize, setListPagePageSize] = useState(50);
  const [listPagesTotal, setListPagesTotal] = useState(0);

  // 案例记录相关状态
  const [caseRecords, setCaseRecords] = useState<CrawlCaseRecord[]>([]);
  const [caseRecordsLoading, setCaseRecordsLoading] = useState(false);
  const [caseRecordStatus, setCaseRecordStatus] = useState<string>("ALL");
  const [caseRecordSavedToJson, setCaseRecordSavedToJson] = useState<string>("ALL");
  const [caseRecordImported, setCaseRecordImported] = useState<string>("ALL");
  const [caseRecordImportStatus, setCaseRecordImportStatus] = useState<string>("ALL");
  const [caseRecordVerified, setCaseRecordVerified] = useState<string>("ALL");
  const [caseRecordPage, setCaseRecordPage] = useState(1);
  const [caseRecordPageSize, setCaseRecordPageSize] = useState(50);
  const [caseRecordsTotal, setCaseRecordsTotal] = useState(0);

  // 真实状态检测相关状态
  const [realStatus, setRealStatus] = useState<TaskRealStatus | null>(null);
  const [realStatusLoading, setRealStatusLoading] = useState(false);

  // 轮询相关状态
  const [pollingEnabled, setPollingEnabled] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("info");

  // 导入弹层相关状态
  const [importDialogVisible, setImportDialogVisible] = useState(false);
  const [importLoading, setImportLoading] = useState(false);

  // 导入状态相关状态
  const [importStatus, setImportStatus] = useState<ImportStatus | null>(null);
  const [importStatusLoading, setImportStatusLoading] = useState(false);
  const [importPollingEnabled, setImportPollingEnabled] = useState(false);

  // 使用 ref 保存最新的状态，避免轮询时使用过期状态
  const stateRef = useRef({
    taskId,
    activeTab,
    logLevel,
    logPage,
    logPageSize,
    listPageStatus,
    listPagePage,
    listPagePageSize,
    caseRecordStatus,
    caseRecordPage,
    caseRecordPageSize,
  });

  // 更新 ref
  useEffect(() => {
    stateRef.current = {
      taskId,
      activeTab,
      logLevel,
      logPage,
      logPageSize,
      listPageStatus,
      listPagePage,
      listPagePageSize,
      caseRecordStatus,
      caseRecordPage,
      caseRecordPageSize,
    };
  }, [
    taskId,
    activeTab,
    logLevel,
    logPage,
    logPageSize,
    listPageStatus,
    listPagePage,
    listPagePageSize,
    caseRecordStatus,
    caseRecordSavedToJson,
    caseRecordImported,
    caseRecordImportStatus,
    caseRecordVerified,
    caseRecordPage,
    caseRecordPageSize,
  ]);

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
        logLevel === "ALL" ? undefined : logLevel,
        logPage,
        logPageSize
      );
      setLogs(response.logs);
      setLogsTotal(response.total);
    } catch (error: any) {
      message.error(`获取任务日志失败: ${error.message}`);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchTaskDetail();
  }, [taskId]);

  // 当日志级别改变时，重置页码为1
  useEffect(() => {
    setLogPage(1);
  }, [logLevel]);

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
        listPageStatus === "ALL" ? undefined : listPageStatus,
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
        caseRecordStatus === "ALL" ? undefined : caseRecordStatus,
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
  }, [taskId, caseRecordStatus, caseRecordSavedToJson, caseRecordImported, caseRecordImportStatus, caseRecordVerified, caseRecordPage, caseRecordPageSize]);

  // 初始化时检查是否有正在运行的导入任务
  useEffect(() => {
    if (taskId) {
      fetchImportStatus().then((status) => {
        // 如果有正在运行的导入任务，自动启动轮询
        if (status && status.status === "running") {
          setImportPollingEnabled(true);
        }
      });
    }
  }, [taskId]);

  // 获取真实状态
  const fetchRealStatus = async () => {
    if (!taskId) return;

    setRealStatusLoading(true);
    try {
      const data = await checkTaskRealStatus(taskId);
      setRealStatus(data);
    } catch (error: any) {
      message.error(`获取真实状态失败: ${error.message}`);
    } finally {
      setRealStatusLoading(false);
    }
  };

  // 轮询刷新逻辑
  useEffect(() => {
    if (!pollingEnabled || !stateRef.current.taskId) return;

    // 根据当前激活的Tab决定刷新哪些数据
    const refreshData = async () => {
      const currentState = stateRef.current;
      const currentTaskId = currentState.taskId;
      const currentTab = currentState.activeTab;

      if (currentTab === "info" || currentTab === "progress") {
        // 刷新任务详情
        try {
          const data = await getTaskDetail(currentTaskId);
          setTask(data);
        } catch (error: any) {
          console.error("刷新任务详情失败:", error);
        }

        if (currentTab === "progress") {
          // 刷新真实状态
          try {
            const data = await checkTaskRealStatus(currentTaskId);
            setRealStatus(data);
          } catch (error: any) {
            console.error("刷新真实状态失败:", error);
          }
        }
      } else if (currentTab === "logs") {
        // 使用 ref 中的最新状态获取日志
        setLogsLoading(true);
        try {
          const response = await getTaskLogs(
            currentTaskId,
            currentState.logLevel === "ALL" ? undefined : currentState.logLevel,
            currentState.logPage,
            currentState.logPageSize
          );
          setLogs(response.logs);
          setLogsTotal(response.total);
        } catch (error: any) {
          // 静默失败，不显示错误消息
          console.error("刷新日志失败:", error);
        } finally {
          setLogsLoading(false);
        }
      } else if (currentTab === "list-pages") {
        // 使用 ref 中的最新状态获取列表页记录
        setListPagesLoading(true);
        try {
          const response = await getTaskListPages(
            currentTaskId,
            currentState.listPageStatus === "ALL"
              ? undefined
              : currentState.listPageStatus,
            currentState.listPagePage,
            currentState.listPagePageSize
          );
          setListPages(response.records);
          setListPagesTotal(response.total);
        } catch (error: any) {
          console.error("刷新列表页记录失败:", error);
        } finally {
          setListPagesLoading(false);
        }
      } else if (currentTab === "cases") {
        // 使用 ref 中的最新状态获取案例记录
        setCaseRecordsLoading(true);
        try {
          const response = await getTaskCaseRecords(
            currentTaskId,
            currentState.caseRecordStatus === "ALL"
              ? undefined
              : currentState.caseRecordStatus,
            undefined,
            currentState.caseRecordPage,
            currentState.caseRecordPageSize
          );
          setCaseRecords(response.records);
          setCaseRecordsTotal(response.total);
        } catch (error: any) {
          console.error("刷新案例记录失败:", error);
        } finally {
          setCaseRecordsLoading(false);
        }
      }
    };

    // 立即刷新一次
    refreshData();

    // 每5秒刷新一次
    const interval = setInterval(refreshData, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [pollingEnabled]);

  // 状态颜色映射
  const getStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      pending: "blue",
      running: "green",
      paused: "orange",
      completed: "green",
      failed: "red",
      cancelled: "default",
      terminated: "default",
    };
    return colorMap[status] || "default";
  };

  // 状态文本映射
  const getStatusText = (status: string): string => {
    const textMap: Record<string, string> = {
      pending: "等待中",
      running: "运行中",
      paused: "已暂停",
      completed: "已完成",
      failed: "已失败",
      cancelled: "已取消",
      terminated: "已终止",
    };
    return textMap[status] || status;
  };

  // 日志级别颜色映射
  const getLogLevelColor = (level: LogLevel): string => {
    const colorMap: Record<LogLevel, string> = {
      INFO: "blue",
      WARNING: "orange",
      ERROR: "red",
      DEBUG: "default",
    };
    return colorMap[level] || "default";
  };

  // 列表页状态颜色映射
  const getListPageStatusColor = (status: ListPageStatus): string => {
    const colorMap: Record<ListPageStatus, string> = {
      success: "green",
      failed: "red",
      skipped: "orange",
      pending: "blue",
    };
    return colorMap[status] || "default";
  };

  // 列表页状态文本映射
  const getListPageStatusText = (status: ListPageStatus): string => {
    const textMap: Record<ListPageStatus, string> = {
      success: "成功",
      failed: "失败",
      skipped: "跳过",
      pending: "等待中",
    };
    return textMap[status] || status;
  };

  // 案例记录状态颜色映射
  const getCaseRecordStatusColor = (status: CaseRecordStatus): string => {
    const colorMap: Record<CaseRecordStatus, string> = {
      success: "green",
      failed: "red",
      skipped: "orange",
      validation_failed: "purple",
      pending: "blue",
    };
    return colorMap[status] || "default";
  };

  // 案例记录状态文本映射
  const getCaseRecordStatusText = (status: CaseRecordStatus): string => {
    const textMap: Record<CaseRecordStatus, string> = {
      success: "成功",
      failed: "失败",
      skipped: "跳过",
      validation_failed: "验证失败",
      pending: "等待中",
    };
    return textMap[status] || status;
  };

  // 处理任务操作
  const handleStart = async () => {
    if (!taskId) return;
    try {
      await startTask(taskId);
      message.success("任务已开始");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`开始任务失败: ${error.message}`);
    }
  };

  const handlePause = async () => {
    if (!taskId) return;
    try {
      await pauseTask(taskId);
      message.success("任务已暂停");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`暂停任务失败: ${error.message}`);
    }
  };

  const handleResume = async () => {
    if (!taskId) return;
    try {
      await resumeTask(taskId);
      message.success("任务已恢复");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`恢复任务失败: ${error.message}`);
    }
  };

  const handleTerminate = async () => {
    if (!taskId) return;
    try {
      await terminateTask(taskId);
      message.success("任务已终止");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`终止任务失败: ${error.message}`);
    }
  };

  const handleRetry = async () => {
    if (!taskId) return;
    try {
      await retryTask(taskId);
      message.success("任务已重置，准备重试");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`重试任务失败: ${error.message}`);
    }
  };

  const handleRestart = async () => {
    if (!taskId) return;
    try {
      await restartTask(taskId);
      message.success("任务已重置，准备重新执行");
      fetchTaskDetail();
    } catch (error: any) {
      message.error(`重新执行任务失败: ${error.message}`);
    }
  };

  const handleDelete = async () => {
    if (!taskId) return;
    try {
      await deleteTask(taskId);
      message.success("任务已删除");
      navigate("/crawl-tasks");
    } catch (error: any) {
      message.error(`删除任务失败: ${error.message}`);
    }
  };

  // 获取导入状态
  const fetchImportStatus = async () => {
    if (!taskId) return;
    setImportStatusLoading(true);
    try {
      const status = await getImportStatus(taskId);
      setImportStatus(status);
      // 如果导入任务已完成或失败，停止轮询
      if (
        status &&
        (status.status === "completed" ||
          status.status === "failed" ||
          status.status === "cancelled")
      ) {
        setImportPollingEnabled(false);
      }
    } catch (error: any) {
      console.error("获取导入状态失败:", error);
      // 如果404，说明没有导入任务，也停止轮询
      if (error.response?.status === 404) {
        setImportStatus(null);
        setImportPollingEnabled(false);
      }
    } finally {
      setImportStatusLoading(false);
    }
  };

  // 取消导入任务
  const handleCancelImport = async () => {
    if (!taskId) return;
    try {
      await cancelImport(taskId);
      message.success("导入任务已取消");
      setImportPollingEnabled(false);
      await fetchImportStatus();
    } catch (error: any) {
      message.error(`取消导入任务失败: ${error.message}`);
    }
  };

  // 同步到 cases 数据库（打开导入选项弹层）
  const handleSyncToCasesDb = async () => {
    setImportDialogVisible(true);
  };

  // 导入确认处理
  const handleImportConfirm = async (config: ImportStartRequest) => {
    if (!taskId) return;
    try {
      setImportLoading(true);
      const result = await startImport(taskId, config);
      message.success(`导入任务已启动（导入ID: ${result.import_id}）`);
      setImportDialogVisible(false);
      fetchTaskDetail();
      // 启动导入状态轮询
      setImportPollingEnabled(true);
      // 立即获取一次状态
      await fetchImportStatus();
    } catch (error: any) {
      message.error(`启动导入失败: ${error.message}`);
    } finally {
      setImportLoading(false);
    }
  };

  // 导入状态轮询
  useEffect(() => {
    if (!importPollingEnabled || !taskId) return;

    // 立即获取一次状态
    fetchImportStatus();

    // 每2秒刷新一次导入状态
    const interval = setInterval(() => {
      fetchImportStatus();
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [importPollingEnabled, taskId]);

  // 格式化时间
  const formatTime = (time?: string) => {
    if (!time) return "-";
    return new Date(time).toLocaleString("zh-CN");
  };

  // 格式化剩余时间
  const formatRemainingTime = (seconds?: number) => {
    if (!seconds) return "-";
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

  const {
    status,
    progress,
    stats,
    config,
    timeline,
    error_message,
    error_stack,
  } = task;

  // 日志表格列
  const logColumns = [
    {
      title: "时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (text: string) => formatTime(text),
    },
    {
      title: "级别",
      dataIndex: "level",
      key: "level",
      width: 100,
      render: (level: LogLevel) => (
        <Tag color={getLogLevelColor(level)}>{level}</Tag>
      ),
    },
    {
      title: "消息",
      dataIndex: "message",
      key: "message",
    },
  ];

  // 列表页记录表格列
  const listPageColumns = [
    {
      title: "页码",
      dataIndex: "page_number",
      key: "page_number",
      width: 100,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: ListPageStatus) => (
        <Tag color={getListPageStatusColor(status)}>
          {getListPageStatusText(status)}
        </Tag>
      ),
    },
    {
      title: "案例数量",
      dataIndex: "items_count",
      key: "items_count",
      width: 100,
    },
    {
      title: "爬取时间",
      dataIndex: "crawled_at",
      key: "crawled_at",
      width: 180,
      render: (text: string) => (text ? formatTime(text) : "-"),
    },
    {
      title: "耗时（秒）",
      dataIndex: "duration_seconds",
      key: "duration_seconds",
      width: 120,
      render: (value: number) => (value ? value.toFixed(2) : "-"),
    },
    {
      title: "错误类型",
      dataIndex: "error_type",
      key: "error_type",
      width: 150,
      render: (text: string) => text || "-",
    },
    {
      title: "错误消息",
      dataIndex: "error_message",
      key: "error_message",
      ellipsis: true,
      render: (text: string) => text || "-",
    },
    {
      title: "重试次数",
      dataIndex: "retry_count",
      key: "retry_count",
      width: 100,
    },
  ];

  // 案例记录表格列
  const caseRecordColumns = [
    {
      title: "案例ID",
      dataIndex: "case_id",
      key: "case_id",
      width: 100,
      render: (value: number) => value || "-",
    },
    {
      title: "案例标题",
      dataIndex: "case_title",
      key: "case_title",
      width: 200,
      ellipsis: true,
      render: (text: string) => text || "-",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: CaseRecordStatus) => (
        <Tag color={getCaseRecordStatusColor(status)}>
          {getCaseRecordStatusText(status)}
        </Tag>
      ),
    },
    {
      title: "爬取时间",
      dataIndex: "crawled_at",
      key: "crawled_at",
      width: 180,
      render: (text: string) => (text ? formatTime(text) : "-"),
    },
    {
      title: "耗时（秒）",
      dataIndex: "duration_seconds",
      key: "duration_seconds",
      width: 120,
      render: (value: number) => (value ? value.toFixed(2) : "-"),
    },
    {
      title: "错误类型",
      dataIndex: "error_type",
      key: "error_type",
      width: 150,
      render: (text: string) => text || "-",
    },
    {
      title: "错误消息",
      dataIndex: "error_message",
      key: "error_message",
      width: 200,
      ellipsis: true,
      render: (text: string) => text || "-",
    },
    {
      title: "已保存",
      dataIndex: "saved_to_json",
      key: "saved_to_json",
      width: 100,
      render: (value: boolean) => (
        <Tag color={value ? "green" : "default"}>{value ? "是" : "否"}</Tag>
      ),
    },
    {
      title: "已导入",
      dataIndex: "imported",
      key: "imported",
      width: 100,
      render: (value: boolean) => (
        <Tag color={value ? "blue" : "default"}>{value ? "是" : "否"}</Tag>
      ),
    },
    {
      title: "导入状态",
      dataIndex: "import_status",
      key: "import_status",
      width: 120,
      render: (status: string) => {
        if (!status) return "-";
        return (
          <Tag color={status === "success" ? "green" : "red"}>
            {status === "success" ? "成功" : "失败"}
          </Tag>
        );
      },
    },
    {
      title: "验证结果",
      dataIndex: "verified",
      key: "verified",
      width: 120,
      render: (value: boolean, record: CrawlCaseRecord) => {
        // 如果已验证，说明在 ad_cases 表中存在（无论 imported 状态如何）
        if (value) {
          return <Tag color="green">已验证</Tag>;
        }
        // 如果已导入但未验证
        if (record.imported) {
          return <Tag color="orange">未验证</Tag>;
        }
        // 如果未导入
        return <Tag color="default">未导入</Tag>;
      },
    },
    {
      title: "数据验证失败原因",
      dataIndex: "validation_errors",
      key: "validation_errors",
      width: 250,
      ellipsis: true,
      render: (errors: Record<string, any> | undefined, record: CrawlCaseRecord) => {
        if (record.has_validation_error && errors) {
          // 格式化验证错误信息
          let errorText = "";
          if (typeof errors === "string") {
            try {
              errors = JSON.parse(errors);
            } catch {
              errorText = errors;
            }
          }
          
          if (typeof errors === "object" && errors !== null) {
            // 如果是对象，提取错误消息
            const errorMessages: string[] = [];
            if (errors.validation_error) {
              errorMessages.push(errors.validation_error);
            }
            if (errors.error) {
              errorMessages.push(errors.error);
            }
            // 遍历所有字段，提取错误信息
            for (const [key, value] of Object.entries(errors)) {
              if (typeof value === "string" && value && !errorMessages.includes(value)) {
                errorMessages.push(value);
              }
            }
            errorText = errorMessages.length > 0 ? errorMessages.join("; ") : JSON.stringify(errors);
          } else if (typeof errors === "string") {
            errorText = errors;
          }
          
          if (errorText) {
            return (
              <span title={errorText} style={{ color: "#ff4d4f" }}>
                {errorText}
              </span>
            );
          }
        }
        return "-";
      },
    },
    {
      title: "导入失败原因",
      dataIndex: "import_error_message",
      key: "import_error_message",
      width: 250,
      ellipsis: true,
      render: (text: string, record: CrawlCaseRecord) => {
        if (record.import_status === "failed" && text) {
          return (
            <span title={text} style={{ color: "#ff4d4f" }}>
              {text}
            </span>
          );
        }
        return "-";
      },
    },
    {
      title: "重试次数",
      dataIndex: "retry_count",
      key: "retry_count",
      width: 100,
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      fixed: "right",
      render: (_: any, record: CrawlCaseRecord) => {
        return (
          <CaseRecordActions
            taskId={taskId}
            record={record}
            onRefresh={fetchCaseRecords}
          />
        );
      },
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
              onClick={() => navigate("/crawl-tasks")}>
              返回
            </Button>
            <span>{task.name}</span>
            <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
          </Space>
        }
        extra={
          <Space>
            {status === "pending" && (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleStart}>
                开始执行
              </Button>
            )}
            {status === "running" && (
              <>
                <Button icon={<PauseCircleOutlined />} onClick={handlePause}>
                  暂停
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={handleTerminate}>
                  <Button danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === "paused" && (
              <>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleResume}>
                  恢复
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleStart}>
                  重新开始
                </Button>
                <Popconfirm
                  title="确定要终止任务吗？终止后将无法恢复进度。"
                  onConfirm={handleTerminate}>
                  <Button danger icon={<StopOutlined />}>
                    终止
                  </Button>
                </Popconfirm>
              </>
            )}
            {status === "failed" && (
              <Space>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={handleRetry}>
                  重试失败案例
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleRestart}>
                  重新执行
                </Button>
              </Space>
            )}
            {status === "completed" && (
              <Space>
                <Button type="primary" onClick={handleSyncToCasesDb}>
                  同步到案例数据库
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleRestart}>
                  重新执行
                </Button>
              </Space>
            )}
            {(status === "terminated" || status === "cancelled") && (
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRestart}>
                重新执行
              </Button>
            )}
            {(status === "completed" ||
              status === "failed" ||
              status === "cancelled") && (
              <Popconfirm title="确定要删除任务吗？" onConfirm={handleDelete}>
                <Button danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            )}
          </Space>
        }
        loading={loading}>
        <Tabs
          defaultActiveKey="info"
          activeKey={activeTab}
          onChange={setActiveTab}>
          <TabPane tab="基本信息" key="info">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="任务ID">
                {task.task_id}
              </Descriptions.Item>
              <Descriptions.Item label="任务名称">
                {task.name}
              </Descriptions.Item>
              <Descriptions.Item label="数据源">
                {task.data_source}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusColor(status)}>
                  {getStatusText(status)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {formatTime(timeline.created_at)}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {formatTime(timeline.started_at)}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {formatTime(timeline.completed_at)}
              </Descriptions.Item>
              <Descriptions.Item label="暂停时间">
                {formatTime(timeline.paused_at)}
              </Descriptions.Item>
              {task.description && (
                <Descriptions.Item label="描述" span={2}>
                  {task.description}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Card title="任务配置" style={{ marginTop: 16 }}>
              <Descriptions column={2} bordered>
                <Descriptions.Item label="起始页码">
                  {config.start_page}
                </Descriptions.Item>
                <Descriptions.Item label="结束页码">
                  {config.end_page || "全部"}
                </Descriptions.Item>
                <Descriptions.Item label="案例类型">
                  {config.case_type || "全部"}
                </Descriptions.Item>
                <Descriptions.Item label="搜索关键词">
                  {config.search_value || "-"}
                </Descriptions.Item>
                <Descriptions.Item label="批次大小">
                  {config.batch_size}
                </Descriptions.Item>
                <Descriptions.Item label="延迟时间">
                  {config.delay_min} - {config.delay_max} 秒
                </Descriptions.Item>
                <Descriptions.Item label="断点续传">
                  {config.enable_resume ? "是" : "否"}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </TabPane>

          <TabPane tab="进度信息" key="progress">
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button onClick={fetchTaskDetail}>刷新进度</Button>
                <Button onClick={fetchRealStatus} loading={realStatusLoading}>
                  检测真实状态
                </Button>
                <Button
                  onClick={async () => {
                    setRealStatusLoading(true);
                    try {
                      const data = await checkTaskRealStatus(taskId!, true);
                      setRealStatus(data);
                      if (data.fixed) {
                        message.success("已自动修复：任务状态已更新为暂停");
                        await fetchTaskDetail();
                      }
                    } catch (error: any) {
                      message.error(`自动修复失败: ${error.message}`);
                    } finally {
                      setRealStatusLoading(false);
                    }
                  }}
                  loading={realStatusLoading}
                  type="primary"
                  danger>
                  自动修复状态
                </Button>
                <Button
                  type={pollingEnabled ? "default" : "primary"}
                  onClick={() => setPollingEnabled(!pollingEnabled)}>
                  {pollingEnabled ? "停止自动刷新" : "开启自动刷新"}
                </Button>
              </Space>
            </div>

            {realStatus && (
              <Card title="真实状态检测" style={{ marginBottom: 16 }}>
                {realStatus.warnings && realStatus.warnings.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    {realStatus.warnings.map((warning, index) => (
                      <div
                        key={index}
                        style={{ color: "#faad14", marginBottom: 8 }}>
                        ⚠️ {warning}
                      </div>
                    ))}
                  </div>
                )}
                {realStatus.recommendations &&
                  realStatus.recommendations.length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      {realStatus.recommendations.map(
                        (recommendation, index) => (
                          <div
                            key={index}
                            style={{ color: "#1890ff", marginBottom: 8 }}>
                            💡 {recommendation}
                          </div>
                        )
                      )}
                    </div>
                  )}
                <Descriptions column={2} bordered size="small">
                  <Descriptions.Item label="数据库状态">
                    <Tag color={getStatusColor(realStatus.db_status || "")}>
                      {getStatusText(realStatus.db_status || "")}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="执行器存在">
                    {realStatus.executor_exists ? (
                      <Tag color="green">是</Tag>
                    ) : (
                      <Tag color="red">否</Tag>
                    )}
                  </Descriptions.Item>
                  {realStatus.executor_exists && (
                    <>
                      <Descriptions.Item label="执行器运行中">
                        {realStatus.executor_running ? (
                          <Tag color="green">是</Tag>
                        ) : (
                          <Tag color="red">否</Tag>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="执行器暂停">
                        {realStatus.executor_paused ? (
                          <Tag color="orange">是</Tag>
                        ) : (
                          <Tag color="default">否</Tag>
                        )}
                      </Descriptions.Item>
                    </>
                  )}
                  {realStatus.status_mismatch && (
                    <Descriptions.Item label="状态不一致" span={2}>
                      <Tag color="red">是（数据库状态与执行器状态不一致）</Tag>
                    </Descriptions.Item>
                  )}
                  {realStatus.progress_stalled && (
                    <Descriptions.Item label="进度停滞" span={2}>
                      <Tag color="orange">是（任务可能已卡住）</Tag>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            )}

            <Card title="总体进度">
              <Progress
                percent={progress.percentage}
                status={status === "failed" ? "exception" : "active"}
                strokeWidth={20}
              />
              <div style={{ marginTop: 16 }}>
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="总页数">
                    {progress.total_pages || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="已完成页数">
                    {progress.completed_pages}
                  </Descriptions.Item>
                  <Descriptions.Item label="当前页码">
                    {progress.current_page || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="预计剩余时间">
                    {formatRemainingTime(progress.estimated_remaining_time)}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            </Card>

            <Card title="统计信息" style={{ marginTop: 16 }}>
              <Descriptions column={2} bordered>
                <Descriptions.Item label="总爬取数">
                  {stats.total_crawled}
                </Descriptions.Item>
                <Descriptions.Item label="总保存数">
                  {stats.total_saved}
                </Descriptions.Item>
                <Descriptions.Item label="失败数">
                  {stats.total_failed}
                </Descriptions.Item>
                <Descriptions.Item label="已保存批次数">
                  {stats.batches_saved}
                </Descriptions.Item>
                <Descriptions.Item label="成功率">
                  {(stats.success_rate * 100).toFixed(2)}%
                </Descriptions.Item>
                <Descriptions.Item label="平均速度">
                  {stats.avg_speed
                    ? `${stats.avg_speed.toFixed(2)} 案例/分钟`
                    : "-"}
                </Descriptions.Item>
                <Descriptions.Item label="平均延迟">
                  {stats.avg_delay ? `${stats.avg_delay.toFixed(2)} 秒` : "-"}
                </Descriptions.Item>
                <Descriptions.Item label="错误率">
                  {stats.error_rate
                    ? `${(stats.error_rate * 100).toFixed(2)}%`
                    : "-"}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* 导入进度显示 */}
            {importStatus && (
              <Card
                title="导入到案例数据库进度"
                style={{ marginTop: 16 }}
                extra={
                  importStatus.status === "running" && (
                    <Space>
                      <Popconfirm
                        title="确定要取消导入任务吗？"
                        onConfirm={handleCancelImport}>
                        <Button size="small" danger>
                          取消导入
                        </Button>
                      </Popconfirm>
                    </Space>
                  )
                }>
                <div style={{ marginBottom: 16 }}>
                  <Space>
                    <Tag
                      color={
                        importStatus.status === "running"
                          ? "processing"
                          : importStatus.status === "completed"
                          ? "success"
                          : importStatus.status === "failed"
                          ? "error"
                          : importStatus.status === "cancelled"
                          ? "default"
                          : "default"
                      }>
                      {importStatus.status === "running"
                        ? "导入中"
                        : importStatus.status === "completed"
                        ? "已完成"
                        : importStatus.status === "failed"
                        ? "已失败"
                        : importStatus.status === "cancelled"
                        ? "已取消"
                        : importStatus.status}
                    </Tag>
                    {importStatus.started_at && (
                      <span style={{ color: "#999", fontSize: 12 }}>
                        开始时间: {formatTime(importStatus.started_at)}
                      </span>
                    )}
                  </Space>
                </div>

                {importStatus.progress && (
                  <>
                    <div style={{ marginBottom: 16 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: 8,
                        }}>
                        <span>导入进度</span>
                        <span>
                          {importStatus.progress.percentage.toFixed(1)}%
                        </span>
                      </div>
                      <Progress
                        percent={importStatus.progress.percentage}
                        status={
                          importStatus.status === "running"
                            ? "active"
                            : importStatus.status === "completed"
                            ? "success"
                            : importStatus.status === "failed"
                            ? "exception"
                            : "normal"
                        }
                      />
                    </div>

                    <Descriptions column={2} bordered size="small">
                      <Descriptions.Item label="总案例数">
                        {importStatus.progress.total_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="已加载">
                        {importStatus.progress.loaded_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="有效案例">
                        {importStatus.progress.valid_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="无效案例">
                        {importStatus.progress.invalid_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="已存在">
                        {importStatus.progress.existing_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="已导入">
                        {importStatus.progress.imported_cases}
                      </Descriptions.Item>
                      <Descriptions.Item label="失败">
                        {importStatus.progress.failed_cases}
                      </Descriptions.Item>
                      {importStatus.progress.estimated_remaining_time && (
                        <Descriptions.Item label="预计剩余时间">
                          {formatRemainingTime(
                            importStatus.progress.estimated_remaining_time
                          )}
                        </Descriptions.Item>
                      )}
                      {importStatus.progress.current_file && (
                        <Descriptions.Item label="当前文件" span={2}>
                          {importStatus.progress.current_file}
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </>
                )}
              </Card>
            )}

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
                  onChange={setLogLevel}>
                  <Select.Option value="ALL">全部级别</Select.Option>
                  <Select.Option value="INFO">INFO</Select.Option>
                  <Select.Option value="WARNING">WARNING</Select.Option>
                  <Select.Option value="ERROR">ERROR</Select.Option>
                </Select>
                <Button onClick={fetchLogs}>刷新</Button>
                <Button
                  type={
                    pollingEnabled && activeTab === "logs"
                      ? "default"
                      : "primary"
                  }
                  onClick={() => {
                    if (activeTab !== "logs") {
                      setActiveTab("logs");
                    }
                    setPollingEnabled(!pollingEnabled || activeTab !== "logs");
                  }}>
                  {pollingEnabled && activeTab === "logs"
                    ? "停止自动刷新"
                    : "开启自动刷新"}
                </Button>
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
                total: logsTotal,
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
                  onChange={setListPageStatus}>
                  <Select.Option value="ALL">全部状态</Select.Option>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="failed">失败</Select.Option>
                  <Select.Option value="skipped">跳过</Select.Option>
                  <Select.Option value="pending">等待中</Select.Option>
                </Select>
                <Button onClick={fetchListPages}>刷新</Button>
                <Button
                  type={
                    pollingEnabled && activeTab === "list-pages"
                      ? "default"
                      : "primary"
                  }
                  onClick={() => {
                    if (activeTab !== "list-pages") {
                      setActiveTab("list-pages");
                    }
                    setPollingEnabled(
                      !pollingEnabled || activeTab !== "list-pages"
                    );
                  }}>
                  {pollingEnabled && activeTab === "list-pages"
                    ? "停止自动刷新"
                    : "开启自动刷新"}
                </Button>
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
              <Space wrap>
                <Select
                  value={caseRecordStatus}
                  style={{ width: 150 }}
                  onChange={setCaseRecordStatus}>
                  <Select.Option value="ALL">全部状态</Select.Option>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="failed">失败</Select.Option>
                  <Select.Option value="validation_failed">
                    验证失败
                  </Select.Option>
                  <Select.Option value="skipped">跳过</Select.Option>
                  <Select.Option value="pending">等待中</Select.Option>
                </Select>
                <Select
                  value={caseRecordSavedToJson}
                  style={{ width: 120 }}
                  onChange={setCaseRecordSavedToJson}>
                  <Select.Option value="ALL">已保存</Select.Option>
                  <Select.Option value="true">是</Select.Option>
                  <Select.Option value="false">否</Select.Option>
                </Select>
                <Select
                  value={caseRecordImported}
                  style={{ width: 120 }}
                  onChange={setCaseRecordImported}>
                  <Select.Option value="ALL">已导入</Select.Option>
                  <Select.Option value="true">是</Select.Option>
                  <Select.Option value="false">否</Select.Option>
                </Select>
                <Select
                  value={caseRecordImportStatus}
                  style={{ width: 120 }}
                  onChange={setCaseRecordImportStatus}>
                  <Select.Option value="ALL">导入状态</Select.Option>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="failed">失败</Select.Option>
                </Select>
                <Select
                  value={caseRecordVerified}
                  style={{ width: 120 }}
                  onChange={setCaseRecordVerified}>
                  <Select.Option value="ALL">验证结果</Select.Option>
                  <Select.Option value="true">已验证</Select.Option>
                  <Select.Option value="false">未验证</Select.Option>
                </Select>
                <Button onClick={fetchCaseRecords}>刷新</Button>
                <Button
                  onClick={async () => {
                    if (!taskId) return;
                    try {
                      const result = await syncCaseRecords(taskId);
                      if (result.success) {
                        message.success(result.message || "同步成功");
                        await fetchCaseRecords();
                      } else {
                        message.error(result.message || "同步失败");
                      }
                    } catch (error: any) {
                      message.error(`同步失败: ${error.message}`);
                    }
                  }}>
                  从JSON同步记录
                </Button>
                <Button
                  onClick={async () => {
                    if (!taskId) return;
                    try {
                      const result = await verifyImports(taskId);
                      message.success(
                        `验证完成：共检查 ${result.total_checked} 个案例，已验证 ${result.verified_count} 个，未验证 ${result.unverified_count} 个`
                      );
                      await fetchCaseRecords();
                    } catch (error: any) {
                      message.error(`验证导入失败: ${error.message}`);
                    }
                  }}>
                  数据验证
                </Button>
                <Button
                  type={
                    pollingEnabled && activeTab === "cases"
                      ? "default"
                      : "primary"
                  }
                  onClick={() => {
                    if (activeTab !== "cases") {
                      setActiveTab("cases");
                    }
                    setPollingEnabled(!pollingEnabled || activeTab !== "cases");
                  }}>
                  {pollingEnabled && activeTab === "cases"
                    ? "停止自动刷新"
                    : "开启自动刷新"}
                </Button>
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

      {/* 导入选项弹层 */}
      <ImportDialog
        visible={importDialogVisible}
        taskId={taskId || ""}
        onCancel={() => setImportDialogVisible(false)}
        onConfirm={handleImportConfirm}
        loading={importLoading}
      />
    </div>
  );
};

export default CrawlTasksDetail;
