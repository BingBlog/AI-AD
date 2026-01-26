/**
 * 头部组件
 */
import { Layout, Menu, Dropdown } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import {
  SearchOutlined,
  CloudDownloadOutlined,
  PlusOutlined,
  SettingOutlined,
  DownOutlined,
  FileTextOutlined,
  BulbOutlined,
  PictureOutlined,
} from "@ant-design/icons";
import { useSearchStore } from "@/store/searchStore";
import styles from "./index.module.less";

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setSearchType } = useSearchStore();

  // 检索下拉菜单
  const searchMenuItems = [
    {
      key: "keyword",
      label: "关键词检索",
      icon: <SearchOutlined />,
      onClick: () => {
        setSearchType("keyword");
        navigate("/cases");
      },
    },
    {
      key: "semantic",
      label: "语义检索",
      icon: <SearchOutlined />,
      onClick: () => {
        setSearchType("semantic");
        navigate("/cases");
      },
    },
    {
      key: "hybrid",
      label: "混合检索",
      icon: <SearchOutlined />,
      onClick: () => {
        setSearchType("hybrid");
        navigate("/cases");
      },
    },
  ];

  // 系统功能下拉菜单（任务管理相关）
  const systemMenuItems = [
    {
      key: "create-task",
      label: "创建任务",
      icon: <PlusOutlined />,
      onClick: () => {
        navigate("/crawl-tasks?action=create");
      },
    },
    {
      key: "manage-tasks",
      label: "任务管理",
      icon: <CloudDownloadOutlined />,
      onClick: () => {
        navigate("/crawl-tasks");
      },
    },
  ];

  return (
    <AntHeader className={styles.header}>
      <div className={styles.headerContent}>
        {/* Logo - 移到最左边 */}
        <div className={styles.logo} onClick={() => navigate("/")}>
          AI广告创意平台
        </div>

        {/* 核心功能导航菜单 */}
        <div className={styles.coreNavMenu}>
          <div
            className={`${styles.coreNavItem} ${
              location.pathname === "/cases" ? styles.active : ""
            }`}
            onClick={() => navigate("/cases")}>
            <SearchOutlined className={styles.coreNavIcon} />
            <span className={styles.coreNavText}>搜索案例</span>
          </div>

          <div
            className={styles.coreNavItem}
            onClick={() => {
              // TODO: 跳转到brief解读页面
              console.log("跳转到brief解读");
            }}>
            <FileTextOutlined className={styles.coreNavIcon} />
            <span className={styles.coreNavText}>Brief解读</span>
          </div>

          <div
            className={styles.coreNavItem}
            onClick={() => {
              // TODO: 跳转到创意设计页面
              console.log("跳转到创意设计");
            }}>
            <BulbOutlined className={styles.coreNavIcon} />
            <span className={styles.coreNavText}>创意设计</span>
          </div>

          <div
            className={styles.coreNavItem}
            onClick={() => {
              // TODO: 跳转到物料生成页面
              console.log("跳转到物料生成");
            }}>
            <PictureOutlined className={styles.coreNavIcon} />
            <span className={styles.coreNavText}>物料生成</span>
          </div>
        </div>

        {/* 系统功能（最右侧） */}
        <div className={styles.systemMenu}>
          <Dropdown
            menu={{ items: systemMenuItems }}
            trigger={["hover", "click"]}
            placement="bottomRight">
            <div className={styles.systemIcon}>
              <SettingOutlined />
            </div>
          </Dropdown>
        </div>
      </div>
    </AntHeader>
  );
};

export default Header;
