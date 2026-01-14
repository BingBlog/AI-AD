/**
 * 筛选侧边栏组件
 */
import { Card, Select, DatePicker, Slider, Space, Button, Divider, Input } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useSearchStore } from '@/store/searchStore';
import { SORT_OPTIONS, SORT_ORDER_OPTIONS } from '@/utils/constants';
import dayjs from 'dayjs';
import styles from './FilterSidebar.module.less';

const { RangePicker } = DatePicker;

const FilterSidebar: React.FC = () => {
  const {
    brand_name,
    brand_industry,
    activity_type,
    location,
    start_date,
    end_date,
    min_score,
    sort_by,
    sort_order,
    setFilters,
    resetFilters,
  } = useSearchStore();

  const handleFilterChange = (key: string, value: any) => {
    setFilters({ [key]: value });
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setFilters({
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
      });
    } else {
      setFilters({
        start_date: undefined,
        end_date: undefined,
      });
    }
  };

  const dateRangeValue =
    start_date && end_date
      ? [dayjs(start_date), dayjs(end_date)]
      : null;

  return (
    <div className={styles.filterSidebar}>
      <Card
        title="筛选条件"
        extra={
          <Button
            type="link"
            icon={<ReloadOutlined />}
            onClick={resetFilters}
            size="small"
          >
            重置
          </Button>
        }
        className={styles.filterCard}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 排序 */}
          <div>
            <div className={styles.filterLabel}>排序方式</div>
            <Select
              value={sort_by}
              onChange={(value) => handleFilterChange('sort_by', value)}
              style={{ width: '100%' }}
              options={SORT_OPTIONS}
            />
          </div>

          <div>
            <div className={styles.filterLabel}>排序顺序</div>
            <Select
              value={sort_order}
              onChange={(value) => handleFilterChange('sort_order', value)}
              style={{ width: '100%' }}
              options={SORT_ORDER_OPTIONS}
            />
          </div>

          <Divider />

          {/* 品牌筛选 */}
          <div>
            <div className={styles.filterLabel}>品牌名称</div>
            <Input
              placeholder="输入品牌名称"
              value={brand_name}
              onChange={(e) => handleFilterChange('brand_name', e.target.value)}
              allowClear
            />
          </div>

          {/* 行业筛选 */}
          <div>
            <div className={styles.filterLabel}>品牌行业</div>
            <Input
              placeholder="输入行业"
              value={brand_industry}
              onChange={(e) =>
                handleFilterChange('brand_industry', e.target.value)
              }
              allowClear
            />
          </div>

          {/* 活动类型 */}
          <div>
            <div className={styles.filterLabel}>活动类型</div>
            <Input
              placeholder="输入活动类型"
              value={activity_type}
              onChange={(e) =>
                handleFilterChange('activity_type', e.target.value)
              }
              allowClear
            />
          </div>

          {/* 地点 */}
          <div>
            <div className={styles.filterLabel}>活动地点</div>
            <Input
              placeholder="输入地点"
              value={location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              allowClear
            />
          </div>

          <Divider />

          {/* 时间范围 */}
          <div>
            <div className={styles.filterLabel}>发布时间</div>
            <RangePicker
              value={dateRangeValue}
              onChange={handleDateRangeChange}
              style={{ width: '100%' }}
              format="YYYY-MM-DD"
            />
          </div>

          {/* 评分筛选 */}
          <div>
            <div className={styles.filterLabel}>最低评分: {min_score || 1}</div>
            <Slider
              min={1}
              max={5}
              marks={{
                1: '1',
                3: '3',
                5: '5',
              }}
              value={min_score || 1}
              onChange={(value) => handleFilterChange('min_score', value)}
            />
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default FilterSidebar;
