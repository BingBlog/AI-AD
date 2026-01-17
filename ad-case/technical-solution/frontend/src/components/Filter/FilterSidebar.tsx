/**
 * 筛选侧边栏组件
 */
import { Card, Select, DatePicker, Slider, Space, Button, Divider } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useSearchStore } from "@/store/searchStore";
import { SORT_OPTIONS, SORT_ORDER_OPTIONS } from "@/utils/constants";
import { getFilterOptions, type FilterOption } from "@/services/caseService";
import { useState, useCallback, useEffect } from "react";
import dayjs from "dayjs";
import styles from "./FilterSidebar.module.less";

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

  // 候选值状态
  const [brandNameOptions, setBrandNameOptions] = useState<FilterOption[]>([]);
  const [brandIndustryOptions, setBrandIndustryOptions] = useState<
    FilterOption[]
  >([]);
  const [activityTypeOptions, setActivityTypeOptions] = useState<
    FilterOption[]
  >([]);
  const [locationOptions, setLocationOptions] = useState<FilterOption[]>([]);

  // 加载状态
  const [loadingBrandName, setLoadingBrandName] = useState(false);
  const [loadingBrandIndustry, setLoadingBrandIndustry] = useState(false);
  const [loadingActivityType, setLoadingActivityType] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);

  // 获取候选值的函数
  const fetchFilterOptions = useCallback(
    async (
      field: string,
      setter: (options: FilterOption[]) => void,
      setLoading: (loading: boolean) => void
    ) => {
      setLoading(true);
      try {
        // 获取所有选项，limit设置为1000以获取更多选项
        const response = await getFilterOptions(field, undefined, 1000);
        setter(response.options || []);
      } catch (error) {
        console.error(`获取${field}候选值失败:`, error);
        setter([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // 组件挂载时加载所有选项
  useEffect(() => {
    fetchFilterOptions("brand_name", setBrandNameOptions, setLoadingBrandName);
    fetchFilterOptions(
      "brand_industry",
      setBrandIndustryOptions,
      setLoadingBrandIndustry
    );
    fetchFilterOptions(
      "activity_type",
      setActivityTypeOptions,
      setLoadingActivityType
    );
    fetchFilterOptions("location", setLocationOptions, setLoadingLocation);
  }, [fetchFilterOptions]);

  const handleFilterChange = (
    key: string,
    value: string | string[] | number
  ) => {
    setFilters({ [key]: value });
  };

  // Select的选项格式化函数
  const formatSelectOptions = (options: FilterOption[]) => {
    return options.map((option) => ({
      value: option.value,
      label: `${option.value} (${option.count})`,
    }));
  };

  // 处理下拉框打开事件，确保选项已加载
  const handleDropdownOpen = useCallback(
    (
      open: boolean,
      field: string,
      options: FilterOption[],
      setter: (options: FilterOption[]) => void,
      setLoading: (loading: boolean) => void
    ) => {
      if (open && options.length === 0) {
        fetchFilterOptions(field, setter, setLoading);
      }
    },
    [fetchFilterOptions]
  );

  const handleDateRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setFilters({
        start_date: dates[0].format("YYYY-MM-DD"),
        end_date: dates[1].format("YYYY-MM-DD"),
      });
    } else {
      setFilters({
        start_date: undefined,
        end_date: undefined,
      });
    }
  };

  const dateRangeValue =
    start_date && end_date ? [dayjs(start_date), dayjs(end_date)] : null;

  return (
    <div className={styles.filterSidebar}>
      <Card
        title="筛选条件"
        extra={
          <Button
            type="link"
            icon={<ReloadOutlined />}
            onClick={resetFilters}
            size="small">
            重置
          </Button>
        }
        className={styles.filterCard}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          {/* 排序 */}
          <div>
            <div className={styles.filterLabel}>排序方式</div>
            <Select
              value={sort_by}
              onChange={(value) => handleFilterChange("sort_by", value)}
              style={{ width: "100%" }}
              options={SORT_OPTIONS}
            />
          </div>

          <div>
            <div className={styles.filterLabel}>排序顺序</div>
            <Select
              value={sort_order}
              onChange={(value) => handleFilterChange("sort_order", value)}
              style={{ width: "100%" }}
              options={SORT_ORDER_OPTIONS}
            />
          </div>

          <Divider />

          {/* 品牌筛选 */}
          <div>
            <div className={styles.filterLabel}>品牌名称</div>
            <Select
              mode="multiple"
              placeholder="请选择品牌名称"
              value={
                brand_name
                  ? Array.isArray(brand_name)
                    ? brand_name
                    : [brand_name]
                  : undefined
              }
              onChange={(value) => handleFilterChange("brand_name", value)}
              options={formatSelectOptions(brandNameOptions)}
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              loading={loadingBrandName}
              onDropdownVisibleChange={(open) =>
                handleDropdownOpen(
                  open,
                  "brand_name",
                  brandNameOptions,
                  setBrandNameOptions,
                  setLoadingBrandName
                )
              }
              style={{ width: "100%" }}
              maxTagCount="responsive"
            />
          </div>

          {/* 行业筛选 */}
          <div>
            <div className={styles.filterLabel}>品牌行业</div>
            <Select
              mode="multiple"
              placeholder="请选择品牌行业"
              value={
                brand_industry
                  ? Array.isArray(brand_industry)
                    ? brand_industry
                    : [brand_industry]
                  : undefined
              }
              onChange={(value) => handleFilterChange("brand_industry", value)}
              options={formatSelectOptions(brandIndustryOptions)}
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              loading={loadingBrandIndustry}
              onDropdownVisibleChange={(open) =>
                handleDropdownOpen(
                  open,
                  "brand_industry",
                  brandIndustryOptions,
                  setBrandIndustryOptions,
                  setLoadingBrandIndustry
                )
              }
              style={{ width: "100%" }}
              maxTagCount="responsive"
            />
          </div>

          {/* 活动类型 */}
          <div>
            <div className={styles.filterLabel}>活动类型</div>
            <Select
              mode="multiple"
              placeholder="请选择活动类型"
              value={
                activity_type
                  ? Array.isArray(activity_type)
                    ? activity_type
                    : [activity_type]
                  : undefined
              }
              onChange={(value) => handleFilterChange("activity_type", value)}
              options={formatSelectOptions(activityTypeOptions)}
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              loading={loadingActivityType}
              onDropdownVisibleChange={(open) =>
                handleDropdownOpen(
                  open,
                  "activity_type",
                  activityTypeOptions,
                  setActivityTypeOptions,
                  setLoadingActivityType
                )
              }
              style={{ width: "100%" }}
              maxTagCount="responsive"
            />
          </div>

          {/* 地点 */}
          <div>
            <div className={styles.filterLabel}>活动地点</div>
            <Select
              mode="multiple"
              placeholder="请选择活动地点"
              value={
                location
                  ? Array.isArray(location)
                    ? location
                    : [location]
                  : undefined
              }
              onChange={(value) => handleFilterChange("location", value)}
              options={formatSelectOptions(locationOptions)}
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              loading={loadingLocation}
              onDropdownVisibleChange={(open) =>
                handleDropdownOpen(
                  open,
                  "location",
                  locationOptions,
                  setLocationOptions,
                  setLoadingLocation
                )
              }
              style={{ width: "100%" }}
              maxTagCount="responsive"
            />
          </div>

          <Divider />

          {/* 时间范围 */}
          <div>
            <div className={styles.filterLabel}>发布时间</div>
            <RangePicker
              value={dateRangeValue}
              onChange={handleDateRangeChange}
              style={{ width: "100%" }}
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
                1: "1",
                3: "3",
                5: "5",
              }}
              value={min_score || 1}
              onChange={(value) => handleFilterChange("min_score", value)}
            />
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default FilterSidebar;
