/**
 * 导入选项弹层组件
 */
import { useState, useEffect } from "react";
import {
  Modal,
  Form,
  Radio,
  Checkbox,
  Select,
  InputNumber,
  Space,
  Button,
  message,
} from "antd";
import { CheckboxChangeEvent } from "antd/es/checkbox";
import { getBatchFiles } from "@/services/crawlTaskService";
import type { ImportStartRequest } from "@/services/crawlTaskService";

interface ImportDialogProps {
  visible: boolean;
  taskId: string;
  onCancel: () => void;
  onConfirm: (config: ImportStartRequest) => void;
  loading?: boolean;
}

const ImportDialog: React.FC<ImportDialogProps> = ({
  visible,
  taskId,
  onCancel,
  onConfirm,
  loading = false,
}) => {
  const [form] = Form.useForm<ImportStartRequest>();
  const [batchFiles, setBatchFiles] = useState<string[]>([]);
  const [loadingBatchFiles, setLoadingBatchFiles] = useState(false);
  const [importMode, setImportMode] = useState<"full" | "selective">("full");
  const [selectedBatches, setSelectedBatches] = useState<string[]>([]);

  // 加载批次文件列表
  useEffect(() => {
    if (visible && taskId) {
      loadBatchFiles();
    }
  }, [visible, taskId]);

  const loadBatchFiles = async () => {
    try {
      setLoadingBatchFiles(true);
      const files = await getBatchFiles(taskId);
      setBatchFiles(files);
    } catch (error: any) {
      message.error(`获取批次文件列表失败: ${error.message}`);
    } finally {
      setLoadingBatchFiles(false);
    }
  };

  const handleModeChange = (e: any) => {
    const mode = e.target.value;
    setImportMode(mode);
    if (mode === "full") {
      setSelectedBatches([]);
      form.setFieldsValue({ selected_batches: [] });
    }
  };

  const handleBatchSelectChange = (value: string[]) => {
    setSelectedBatches(value);
    form.setFieldsValue({ selected_batches: value });
  };

  const handleSelectAll = (e: CheckboxChangeEvent) => {
    if (e.target.checked) {
      setSelectedBatches([...batchFiles]);
      form.setFieldsValue({ selected_batches: batchFiles });
    } else {
      setSelectedBatches([]);
      form.setFieldsValue({ selected_batches: [] });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const config: ImportStartRequest = {
        import_mode: importMode,
        selected_batches: importMode === "selective" ? selectedBatches : undefined,
        import_failed_only: values.import_failed_only ?? false,
        skip_existing: values.skip_existing ?? false,
        update_existing: values.update_existing ?? false,
        generate_vectors: values.generate_vectors ?? true,
        skip_invalid: values.skip_invalid ?? false,
        batch_size: values.batch_size ?? 50,
        normalize_data: values.normalize_data ?? true,
      };
      onConfirm(config);
    } catch (error) {
      console.error("表单验证失败:", error);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setImportMode("full");
    setSelectedBatches([]);
    onCancel();
  };

  return (
    <Modal
      title="导入选项设置"
      open={visible}
      onCancel={handleCancel}
      width={600}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}>
          开始导入
        </Button>,
      ]}>
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          import_mode: "full",
          import_failed_only: false,
          skip_existing: false,
          update_existing: false,
          generate_vectors: true,
          skip_invalid: false,
          batch_size: 50,
          normalize_data: true,
        }}>
        <Form.Item
          label="导入模式"
          name="import_mode"
          rules={[{ required: true, message: "请选择导入模式" }]}>
          <Radio.Group onChange={handleModeChange}>
            <Radio value="full">全部导入</Radio>
            <Radio value="selective">选择批次导入</Radio>
          </Radio.Group>
        </Form.Item>

        {importMode === "selective" && (
          <Form.Item
            label="选择批次文件"
            name="selected_batches"
            rules={[
              {
                required: true,
                message: "请至少选择一个批次文件",
                validator: (_, value) => {
                  if (importMode === "selective" && (!value || value.length === 0)) {
                    return Promise.reject(new Error("请至少选择一个批次文件"));
                  }
                  return Promise.resolve();
                },
              },
            ]}>
            <div>
              <Space style={{ marginBottom: 8 }}>
                <Checkbox
                  indeterminate={
                    selectedBatches.length > 0 &&
                    selectedBatches.length < batchFiles.length
                  }
                  checked={
                    batchFiles.length > 0 &&
                    selectedBatches.length === batchFiles.length
                  }
                  onChange={handleSelectAll}>
                  全选
                </Checkbox>
                <span style={{ color: "#999", fontSize: 12 }}>
                  已选择 {selectedBatches.length} / {batchFiles.length} 个文件
                </span>
              </Space>
              <Select
                mode="multiple"
                placeholder="请选择要导入的批次文件"
                value={selectedBatches}
                onChange={handleBatchSelectChange}
                loading={loadingBatchFiles}
                style={{ width: "100%" }}
                maxTagCount="responsive">
                {batchFiles.map((file) => (
                  <Select.Option key={file} value={file}>
                    {file}
                  </Select.Option>
                ))}
              </Select>
            </div>
          </Form.Item>
        )}

        <Form.Item label="导入选项">
          <Space direction="vertical" style={{ width: "100%" }}>
            <Form.Item name="import_failed_only" valuePropName="checked" noStyle>
              <Checkbox>仅导入未导入成功的案例</Checkbox>
            </Form.Item>
            <Form.Item name="skip_existing" valuePropName="checked" noStyle>
              <Checkbox>跳过已存在的案例</Checkbox>
            </Form.Item>
            <Form.Item name="update_existing" valuePropName="checked" noStyle>
              <Checkbox>更新已存在的案例</Checkbox>
            </Form.Item>
            <Form.Item name="skip_invalid" valuePropName="checked" noStyle>
              <Checkbox>跳过无效数据</Checkbox>
            </Form.Item>
            <Form.Item name="normalize_data" valuePropName="checked" noStyle>
              <Checkbox defaultChecked>规范化数据（将非法值转为默认值或NULL）</Checkbox>
            </Form.Item>
          </Space>
        </Form.Item>

        <Form.Item
          label="生成向量"
          name="generate_vectors"
          valuePropName="checked">
          <Checkbox defaultChecked>生成向量（用于语义检索）</Checkbox>
        </Form.Item>

        <Form.Item
          label="批量导入大小"
          name="batch_size"
          rules={[
            { required: true, message: "请输入批量导入大小" },
            { type: "number", min: 1, max: 200, message: "批量大小应在 1-200 之间" },
          ]}>
          <InputNumber
            min={1}
            max={200}
            style={{ width: "100%" }}
            placeholder="每次导入的案例数量"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ImportDialog;
