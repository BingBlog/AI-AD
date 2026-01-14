/**
 * 搜索框组件
 */
import { Input, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useSearchStore } from '@/store/searchStore';
import { debounce } from '@/utils/debounce';
import { useCallback } from 'react';

interface SearchBoxProps {
  onSearch?: (value: string) => void;
  placeholder?: string;
  size?: 'small' | 'middle' | 'large';
}

const SearchBox: React.FC<SearchBoxProps> = ({
  onSearch,
  placeholder = '搜索案例...',
  size = 'large',
}) => {
  const { query, setQuery } = useSearchStore();

  // 防抖处理搜索
  const debouncedSearch = useCallback(
    debounce((value: string) => {
      if (onSearch && value.trim()) {
        onSearch(value);
      }
    }, 500),
    [onSearch]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  const handleSearch = (value: string) => {
    setQuery(value);
    if (onSearch) {
      onSearch(value);
    }
  };

  return (
    <Input.Search
      placeholder={placeholder}
      allowClear
      enterButton={
        <Button type="primary" icon={<SearchOutlined />}>
          搜索
        </Button>
      }
      size={size}
      value={query}
      onChange={handleChange}
      onSearch={handleSearch}
    />
  );
};

export default SearchBox;
