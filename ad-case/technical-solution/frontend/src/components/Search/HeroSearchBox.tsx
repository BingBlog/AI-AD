/**
 * Hero区域搜索框组件（大尺寸，仅搜索框，支持混合检索）
 */
import { useState } from "react";
import { Input } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useSearchStore } from "@/store/searchStore";
import { useNavigate } from "react-router-dom";
import styles from "./HeroSearchBox.module.less";

interface HeroSearchBoxProps {
  onSearch?: () => void;
}

const HeroSearchBox: React.FC<HeroSearchBoxProps> = ({ onSearch }) => {
  const navigate = useNavigate();
  const { setSemanticQuery, setSearchType, setQuery } = useSearchStore();
  const [searchValue, setSearchValue] = useState("");

  const handleSearch = () => {
    if (!searchValue.trim()) return;

    // 设置为混合检索
    setSearchType("hybrid");
    // 设置语义查询（混合检索会同时使用关键词和语义）
    setSemanticQuery(searchValue.trim());
    // 也设置关键词（混合检索需要）
    setQuery(searchValue.trim());

    // 跳转到搜索列表页
    navigate("/cases");

    // 触发回调
    if (onSearch) {
      onSearch();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className={styles.heroSearchBox}>
      <Input
        size="large"
        placeholder="输入关键词或自然语言描述，如：找一些关于情感营销的案例"
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        onPressEnter={handleKeyPress}
        prefix={<SearchOutlined className={styles.searchIcon} />}
        className={styles.searchInput}
      />
    </div>
  );
};

export default HeroSearchBox;
