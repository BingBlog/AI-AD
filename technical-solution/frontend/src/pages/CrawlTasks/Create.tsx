/**
 * 创建爬取任务页
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Space,
  Divider,
} from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { createTask, getLastCrawledPage } from "@/services/crawlTaskService";
import type { CreateTaskRequest } from "@/types/crawlTask";
import styles from "./Create.module.less";

const { TextArea } = Input;

const CrawlTasksCreate: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [loadingLastPage, setLoadingLastPage] = useState(false);

  // 提交表单
  const handleSubmit = async () => {
    try {
      // 验证所有字段
      const values = await form.validateFields();
      setLoading(true);

      // 构建请求对象
      const request: CreateTaskRequest = {
        name: String(values.name).trim(),
        data_source: values.data_source || "adquan",
        description: values.description
          ? String(values.description).trim()
          : undefined,
        start_page:
          values.start_page !== undefined && values.start_page !== null
            ? values.start_page
            : undefined,
        end_page: values.end_page,
        case_type:
          values.case_type !== undefined && values.case_type !== null
            ? values.case_type
            : undefined,
        search_value: values.search_value
          ? String(values.search_value).trim()
          : undefined,
        batch_size: values.batch_size ?? 100,
        delay_min: values.delay_min ?? 2.0,
        delay_max: values.delay_max ?? 5.0,
        enable_resume: values.enable_resume !== false,
        execute_immediately: values.execute_immediately !== false,
      };

      await createTask(request);
      message.success("任务创建成功");
      navigate("/crawl-tasks");
    } catch (error: unknown) {
      if (error && typeof error === "object" && "errorFields" in error) {
        // 表单验证错误
        message.error("请检查表单输入");
      } else {
        const errorMessage =
          error instanceof Error ? error.message : "未知错误";
        message.error(`创建任务失败: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取上一次爬取到的页数
  const loadLastPage = React.useCallback(async () => {
    try {
      setLoadingLastPage(true);
      const result = await getLastCrawledPage("adquan");
      if (result.suggested_start_page !== undefined) {
        form.setFieldsValue({ start_page: result.suggested_start_page });
      }
    } catch (error: unknown) {
      console.error("获取上一次爬取页数失败:", error);
      // 失败时设置为 0
      form.setFieldsValue({ start_page: 0 });
    } finally {
      setLoadingLastPage(false);
    }
  }, [form]);

  // 组件挂载时加载上一次爬取页数
  React.useEffect(() => {
    loadLastPage();
  }, [loadLastPage]);

  // 组件挂载时加载上一次爬取页数
  React.useEffect(() => {
    loadLastPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
            <span>创建爬取任务</span>
          </Space>
        }>
        <Form
          form={form}
          layout="vertical"
          className={styles.form}
          initialValues={{
            data_source: "adquan",
            start_page: undefined, // 留空，由后端自动设置
            batch_size: 100,
            delay_min: 2.0,
            delay_max: 5.0,
            enable_resume: true,
            execute_immediately: true,
          }}>
          {/* 基础配置 */}
          <div>
            <h3>基础配置</h3>
            <Form.Item
              name="name"
              label="任务名称"
              rules={[
                { required: true, message: "请输入任务名称" },
                { whitespace: true, message: "任务名称不能为空" },
                { min: 1, message: "任务名称至少需要1个字符" },
              ]}>
              <Input placeholder="例如：爬取广告门精选案例" />
            </Form.Item>

            <Form.Item
              name="data_source"
              label="数据源"
              rules={[{ required: true, message: "请选择数据源" }]}
              initialValue="adquan">
              <Input disabled />
            </Form.Item>

            <Form.Item name="description" label="任务描述">
              <TextArea rows={4} placeholder="可选：描述任务的目的和用途" />
            </Form.Item>
          </div>

          <Divider />

          {/* 爬取范围 */}
          <div>
            <h3>爬取范围</h3>
            <Form.Item
              name="start_page"
              label="起始页码"
              rules={[
                { type: "number", min: 0, message: "起始页码必须大于等于 0" },
              ]}
              extra="留空时自动设置为上一次爬取到的页数">
              <InputNumber
                style={{ width: "100%" }}
                placeholder="从第几页开始爬取（留空自动设置）"
                disabled={loadingLastPage}
                addonAfter={
                  loadingLastPage ? (
                    <span>加载中...</span>
                  ) : (
                    <Button
                      type="link"
                      size="small"
                      onClick={loadLastPage}
                      style={{ padding: 0 }}>
                      刷新
                    </Button>
                  )
                }
              />
            </Form.Item>

            <Form.Item
              name="end_page"
              label="结束页码"
              rules={[
                { required: true, message: "请输入结束页码" },
                { type: "number", min: 0, message: "结束页码必须大于等于 0" },
              ]}
              extra="必填：爬取到第几页">
              <InputNumber
                style={{ width: "100%" }}
                placeholder="爬取到第几页（必填）"
              />
            </Form.Item>
          </div>

          <Divider />

          {/* 筛选条件 */}
          <div>
            <h3>筛选条件（可选）</h3>
            <Form.Item
              name="case_type"
              label="案例类型"
              extra="0=全部, 3=精选案例（默认）">
              <InputNumber
                style={{ width: "100%" }}
                placeholder="案例类型（可选）"
              />
            </Form.Item>

            <Form.Item name="search_value" label="搜索关键词">
              <Input placeholder="只爬取包含特定关键词的案例（可选）" />
            </Form.Item>
          </div>

          <Divider />

          {/* 高级配置 */}
          <div>
            <h3>高级配置</h3>
            <Form.Item
              name="batch_size"
              label="批次大小"
              extra="每批保存到 JSON 的案例数量"
              rules={[
                { required: true, message: "请输入批次大小" },
                { type: "number", min: 1, message: "批次大小必须大于 0" },
              ]}>
              <InputNumber style={{ width: "100%" }} placeholder="默认：100" />
            </Form.Item>

            <Form.Item
              name="delay_min"
              label="最小延迟时间（秒）"
              rules={[
                { required: true, message: "请输入最小延迟时间" },
                { type: "number", min: 0, message: "延迟时间必须大于等于 0" },
              ]}>
              <InputNumber
                style={{ width: "100%" }}
                step={0.1}
                placeholder="默认：2.0"
              />
            </Form.Item>

            <Form.Item
              name="delay_max"
              label="最大延迟时间（秒）"
              rules={[
                { required: true, message: "请输入最大延迟时间" },
                { type: "number", min: 0, message: "延迟时间必须大于等于 0" },
              ]}>
              <InputNumber
                style={{ width: "100%" }}
                step={0.1}
                placeholder="默认：5.0"
              />
            </Form.Item>

            <Form.Item
              name="enable_resume"
              label="启用断点续传"
              valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item
              name="execute_immediately"
              label="立即执行"
              valuePropName="checked"
              extra="创建后立即开始执行任务">
              <Switch />
            </Form.Item>
          </div>

          {/* 操作按钮 */}
          <div className={styles.actions}>
            <Space>
              <Button onClick={() => navigate("/crawl-tasks")}>取消</Button>
              <Button type="primary" loading={loading} onClick={handleSubmit}>
                创建任务
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default CrawlTasksCreate;
