/**
 * 案例列表页
 */
import { useState, useEffect } from "react";
import { Layout, Pagination, Typography, Button } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import { useSearchStore } from "@/store/searchStore";
import { useCases } from "@/hooks/useCases";
import FilterSidebar from "@/components/Filter/FilterSidebar";
import CaseList from "@/components/Case/CaseList";
import SemanticSearchBox from "@/components/Search/SemanticSearchBox";
import { PAGE_SIZE_OPTIONS } from "@/utils/constants";
import styles from "./List.module.less";

const { Content, Sider } = Layout;
const { Text } = Typography;

const CasesList: React.FC = () => {
  // 默认在桌面端显示侧边栏，移动端隐藏
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 根据屏幕尺寸初始化侧边栏状态
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 992) {
        setSidebarCollapsed(true);
      } else {
        setSidebarCollapsed(false);
      }
    };

    // 初始化
    handleResize();

    // 监听窗口大小变化
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);
  const {
    query,
    sort_by,
    sort_order,
    page,
    page_size,
    setPage,
    setPageSize,
    setSortBy,
    setSortOrder,
  } = useSearchStore();

  const { data, isLoading, error } = useCases();

  // 调试信息（开发环境）
  if (process.env.NODE_ENV === "development") {
    console.log("CasesList - Search params:", {
      query,
      sort_by,
      sort_order,
      page,
      page_size,
    });
    console.log("CasesList - Data:", data);
    console.log("CasesList - Loading:", isLoading);
    console.log("CasesList - Error:", error);
  }

  const handlePageChange = (newPage: number, newPageSize?: number) => {
    setPage(newPage);
    if (newPageSize && newPageSize !== page_size) {
      setPageSize(newPageSize);
    }
  };

  return (
    <Layout className={styles.casesList}>
      {/* 筛选侧边栏 */}
      <Sider
        width={280}
        collapsed={sidebarCollapsed}
        collapsedWidth={0}
        theme="light"
        className={styles.sider}
        breakpoint="lg"
        onBreakpoint={(broken) => {
          // 在断点处自动折叠，但不强制隐藏
          if (broken && !sidebarCollapsed) {
            setSidebarCollapsed(true);
          }
        }}>
        <FilterSidebar />
      </Sider>

      {/* 主要内容区域 */}
      <Content className={styles.content}>
        {/* 搜索框 */}
        <div className={styles.searchBox}>
          <SemanticSearchBox
            onSearch={() => {
              // 搜索会自动触发，这里可以添加额外逻辑
            }}
            size="large"
          />
        </div>

        {/* 工具栏：筛选按钮 */}
        <div className={styles.toolbar}>
          <Button
            icon={<FilterOutlined />}
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className={styles.filterButton}
            type={sidebarCollapsed ? "primary" : "default"}>
            {sidebarCollapsed ? "显示筛选" : "隐藏筛选"}
          </Button>
        </div>

        {/* 结果统计 */}
        {data && (
          <div className={styles.stats}>
            <Text type="secondary">
              找到 <Text strong>{data.total}</Text> 个案例
              {query && (
                <>
                  {" "}
                  ，关键词：<Text strong>{query}</Text>
                </>
              )}
            </Text>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div style={{ padding: "20px", textAlign: "center" }}>
            <Text type="danger">
              加载失败：{error instanceof Error ? error.message : "未知错误"}
            </Text>
          </div>
        )}

        {/* 案例列表 */}
        <div className={styles.listContainer}>
          <CaseList
            cases={data?.results || []}
            loading={isLoading}
            query={query}
          />
        </div>

        {/* 分页器 */}
        {data && data.total > 0 && (
          <div className={styles.pagination}>
            <Pagination
              current={page}
              pageSize={page_size}
              total={data.total}
              showSizeChanger
              showQuickJumper
              showTotal={(total) => `共 ${total} 条`}
              pageSizeOptions={PAGE_SIZE_OPTIONS.map((n) => n.toString())}
              onChange={handlePageChange}
              onShowSizeChange={handlePageChange}
            />
          </div>
        )}
      </Content>
    </Layout>
  );
};

export default CasesList;
