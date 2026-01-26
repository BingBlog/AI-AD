/**
 * 语义搜索框组件（支持关键词、语义、混合检索）
 */
import { useState } from 'react';
import { Input, Button, Radio, Space, Collapse, Slider, Typography, Popover } from 'antd';
import { SearchOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';
import { useSearchStore } from '@/store/searchStore';
import { debounce } from '@/utils/debounce';
import { useCallback } from 'react';
import styles from './SemanticSearchBox.module.less';

const { Text } = Typography;
const { Panel } = Collapse;

interface SemanticSearchBoxProps {
  onSearch?: () => void;
  size?: 'small' | 'middle' | 'large';
  compact?: boolean; // 紧凑模式，用于 Header
}

const SemanticSearchBox: React.FC<SemanticSearchBoxProps> = ({
  onSearch,
  size = 'large',
  compact = false,
}) => {
  const {
    query,
    semantic_query,
    search_type,
    min_similarity,
    setQuery,
    setSemanticQuery,
    setSearchType,
    setMinSimilarity,
  } = useSearchStore();

  const [showAdvanced, setShowAdvanced] = useState(false);

  // 防抖处理搜索（1000ms = 1秒）
  const debouncedSearch = useCallback(
    debounce(() => {
      if (onSearch) {
        onSearch();
      }
    }, 1000),
    [onSearch]
  );

  const handleKeywordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch();
  };

  const handleSemanticChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSemanticQuery(value);
    debouncedSearch();
  };

  const handleSearch = () => {
    if (onSearch) {
      onSearch();
    }
  };

  const handleSearchTypeChange = (e: any) => {
    setSearchType(e.target.value);
    debouncedSearch();
  };

  const handleSimilarityChange = (value: number) => {
    setMinSimilarity(value);
    debouncedSearch();
  };

  const getPlaceholder = () => {
    switch (search_type) {
      case 'semantic':
        return '请输入自然语言描述，如"找一些关于情感营销的案例"';
      case 'hybrid':
        return '请输入关键词或自然语言描述';
      default:
        return '搜索案例...';
    }
  };

  return (
    <div className={styles.semanticSearchBox}>
      {/* 检索类型选择 + 搜索输入框 + 搜索按钮（同一行） */}
      <div className={styles.searchRow}>
        {/* 检索类型选择 */}
        <div className={styles.searchTypeSelector}>
          <Radio.Group
            value={search_type}
            onChange={handleSearchTypeChange}
            buttonStyle="solid"
            size={size === 'large' ? 'middle' : size}
          >
            <Radio.Button value="keyword">关键词检索</Radio.Button>
            <Radio.Button value="semantic">语义检索</Radio.Button>
            <Radio.Button value="hybrid">混合检索</Radio.Button>
          </Radio.Group>
        </div>

        {/* 搜索输入框 */}
        <div className={styles.searchInputs}>
        {search_type === 'keyword' && (
          <Input
            placeholder={getPlaceholder()}
            allowClear
            size={size}
            value={query}
            onChange={handleKeywordChange}
            onPressEnter={handleSearch}
            style={{ width: '100%' }}
          />
        )}

        {search_type === 'semantic' && (
          <Input
            placeholder={getPlaceholder()}
            allowClear
            size={size}
            value={semantic_query}
            onChange={handleSemanticChange}
            onPressEnter={handleSearch}
            style={{ width: '100%' }}
          />
        )}

        {search_type === 'hybrid' && (
          <Input
            placeholder="自然语言描述（如：找一些关于情感营销的案例）"
            allowClear
            size={size}
            value={semantic_query}
            onChange={handleSemanticChange}
            onPressEnter={handleSearch}
            style={{ width: '100%' }}
          />
        )}
        </div>

        {/* 搜索按钮 */}
        <div className={styles.searchButton}>
          <Button 
            type="primary" 
            icon={<SearchOutlined />}
            size={size}
            onClick={handleSearch}
          >
            搜索
          </Button>
        </div>

        {/* 展开参数按钮（仅在语义检索或混合检索时显示，使用 Popover） */}
        {(search_type === 'semantic' || search_type === 'hybrid') && (
          <div className={styles.advancedButton}>
            <Popover
              content={
                <div className={styles.advancedContent}>
                  <div className={styles.similaritySlider}>
                    <Text>最小相似度: {min_similarity.toFixed(2)}</Text>
                    <Slider
                      min={0}
                      max={1}
                      step={0.05}
                      value={min_similarity}
                      onChange={handleSimilarityChange}
                      marks={{
                        0: '0',
                        0.5: '0.5',
                        1: '1.0',
                      }}
                    />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      相似度越高，结果越相关（0-1）
                    </Text>
                  </div>
                </div>
              }
              title="高级参数"
              trigger="click"
              placement="bottomRight"
              open={showAdvanced}
              onOpenChange={setShowAdvanced}
              overlayClassName={styles.advancedPopover}
            >
              <Button
                type="link"
                icon={showAdvanced ? <UpOutlined /> : <DownOutlined />}
                size={size}
              >
                {showAdvanced ? '收起参数' : '展开参数'}
              </Button>
            </Popover>
          </div>
        )}
      </div>

      {/* 检索类型说明（紧凑模式下隐藏） */}
      {!compact && (
        <div className={styles.searchTypeHint}>
          {search_type === 'keyword' && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              关键词检索：匹配包含关键词的案例
            </Text>
          )}
          {search_type === 'semantic' && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              语义检索：基于语义相似度匹配相关案例
            </Text>
          )}
          {search_type === 'hybrid' && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              混合检索：结合关键词和语义检索的优势
            </Text>
          )}
        </div>
      )}
    </div>
  );
};

export default SemanticSearchBox;
