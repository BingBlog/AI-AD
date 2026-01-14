# 广告门详情页解析方案

## 1. 页面渲染方式分析

### 1.1 渲染机制

- **主要方式**：HTML 直接渲染，所有关键信息都在初始 HTML 中
- **JavaScript 作用**：主要用于交互功能（点赞、收藏、分享、评论等），不用于加载主要内容
- **异步加载**：页面中有少量 AJAX 调用，但仅用于：
  - 点赞/收藏功能
  - 评论加载
  - 分享功能
  - **不影响主要内容的获取**

### 1.2 结论

**可以直接解析 HTML 获取所有需要的信息，无需等待 JavaScript 执行或调用额外 API**

## 2. 页面结构分析

### 2.1 主要容器结构

```
<div id="case_main">                    # 主容器
  ├── <img class="case_title_pic">     # 标题图片（主图）
  ├── <div class="case_inner">         # 案例内容容器
  │   ├── <div class="case_text">      # 案例文本容器
  │   │   ├── <h3 id="title">          # 案例标题
  │   │   ├── <div class="case_info">  # 作者和时间信息
  │   │   └── <div class="swiper-container"> # 图片轮播
  │   └── <div class="new_neirong">    # 【重要】主要内容容器
  │       ├── <p>描述文本段落</p>
  │       ├── <p><img src="..."></p>   # 内容中的图片
  │       ├── <p><iframe src="..."></iframe></p>  # 视频
  │       └── <p class="hidden-watermark">水印</p>
  └── <div class="agent" id="list1">   # 相关信息（品牌、行业、标签等）
```

### 2.2 关键信息位置

#### 基本信息

- **标题**：
  - 位置 1：`<h3 id="title">` 在 `case_text` 中
  - 位置 2：`<title>` 标签（带网站后缀，需要清理）
  - 位置 3：`<meta property="og:title">`（最可靠）
- **描述**：

  - **位置 1（最高优先级，必须优先使用）**：`<div class="new_neirong">` 中的文字内容（完整描述，仅提取文字，忽略图片和视频）
  - 位置 2（备用）：`<meta property="og:description">`（仅在 `new_neirong` 不可用时使用）

- **主图**：
  - 位置 1：`<img class="case_title_pic">` 在 `case_main` 中
  - 位置 2：`<meta property="og:image">`

#### 案例图片集合

- **位置**：`<div class="swiper-container">` 在 `case_inner` 中
- **结构**：
  ```html
  <div class="swiper-container">
    <div class="swiper-wrapper">
      <div class="swiper-slide">
        <img src="..." />
      </div>
      ...
    </div>
  </div>
  ```
- **注意**：需要提取所有 `swiper-slide` 中的 `img` 标签

#### 视频

- **位置**：`<iframe>` 标签（可能在 `case_inner` 中）
- **格式**：腾讯视频等第三方视频平台

#### 作者和时间

- **位置**：`<div class="case_info info_info">` 在 `case_text` 中
- **结构**：
  ```html
  <div class="case_info info_info">
    <img class="info_img1" src="..." /> # 作者头像
    <span class="span_01">作者名</span>
    <span class="span_02">2020-02-14</span> # 发布时间
  </div>
  ```

#### 相关信息（品牌、行业、标签等）

- **位置**：`<div class="agent" id="list1">`
- **结构**：包含多个信息项，每个信息项可能的结构：
  - 文本标签 + 内容
  - 需要解析文本内容来提取：
    - 所属行业
    - 形式类别
    - 所在地区
    - 标签
    - 品牌/广告主
    - 时间

## 3. 解析方案

### 3.1 解析流程

```
1. 访问详情页URL，获取HTML
   ↓
2. 使用BeautifulSoup解析HTML
   ↓
3. 按优先级提取各字段：
   a. **描述字段**：必须优先从 `<div class="new_neirong">` 提取（最高优先级）
   b. 从meta标签提取（用于标题、主图等）
   c. 从特定class/id的元素提取
   d. 从文本内容解析（最后手段）
   ↓
4. 数据清洗和格式化
   ↓
5. 返回结构化数据
```

### 3.2 字段提取规则

#### 3.2.1 标题（title）

**优先级 1**：`<meta property="og:title">` 的 content 属性
**优先级 2**：`<h3 id="title">` 的文本内容
**优先级 3**：`<title>` 标签（需要去除 " | 广告门" 后缀）

#### 3.2.2 描述（description）

**⚠️ 最高优先级（必须优先使用）**：从 `<div class="new_neirong">` 中提取完整文字描述

- **核心策略**：仅提取文字内容，忽略所有图片和视频
- **提取位置**：`<div class="new_neirong">` 容器（这是案例的主要内容容器）
- **提取步骤**（已优化，确保完整提取所有文本内容）：

  1. **预处理阶段**：

     - 创建 HTML 副本，避免修改原始对象
     - 移除所有 `<img>` 和 `<iframe>` 标签（图片和视频）
     - 移除所有 `class="hidden-watermark"` 的标签（水印）
     - 移除所有 `<script>` 和 `<style>` 标签
     - 移除所有空的 `<section>` 和 `<div>` 标签（但保留有内容的）

  2. **主要提取策略**：

     - **优先级 1**：提取所有 `<p>` 标签的文本（包括嵌套在 `<section>` 等容器中的 `<p>` 标签）
     - 对每个 `<p>` 标签：
       - 正确处理 `<br>` 和 `<br/>` 标签，将其转换为换行符（`\n`）
       - 保持内联标签（如 `<em>`、`<strong>`、`<span>`）的文本内容
       - 使用 `get_text(separator=' ', strip=False)` 提取文本，保留换行结构
       - 清理每行的前后空白，但保留段落内的换行
     - **去重机制**：使用 `seen_texts` 集合记录已提取的文本，避免重复提取
     - **过滤规则**：排除包含"本文来源于广告门"或"adquan.com"的文本段落

  3. **备用提取策略**（如果主要策略未找到内容）：

     - **优先级 2**：遍历 `new_neirong` 的直接子元素，使用递归方法提取文本
     - **优先级 3**：如果仍然没有内容，使用 `get_text(separator='\n')` 提取所有文本，然后按段落分割

  4. **后处理阶段**：
     - 合并所有提取的段落，段落之间用双换行符（`\n\n`）分隔
     - 使用正则表达式再次过滤水印文本（支持多行匹配）
     - 清理多余的空行（将 3 个或更多连续换行符替换为双换行符）
     - 调用 `_clean_text()` 方法进行最终文本清洗

- **结果**：完整的案例文字描述，包含案例背景、创意亮点、执行细节等，保持段落结构
- **优化亮点**：
  - ✅ 支持嵌套结构（如 `<section><p>...</p></section>`）
  - ✅ 正确处理 `<br>` 标签，保持换行格式
  - ✅ 避免重复提取相同内容
  - ✅ 多层备用策略，确保即使结构变化也能提取文本
  - ✅ 完整过滤水印和广告文本

**备用方案**：如果 `<div class="new_neirong">` 不存在或提取失败，则使用 `<meta property="og:description">` 的 content 属性作为备用

#### 3.2.3 主图（main_image）

**优先级 1**：`<meta property="og:image">` 的 content 属性
**优先级 2**：`<img class="case_title_pic">` 的 src 属性

#### 3.2.4 图片集合（images）

**提取位置**：`<div class="swiper-container">` 中的所有 `swiper-slide > img`
**处理**：

- 提取所有 `img` 标签的 `src` 属性
- 过滤掉空 src 和占位图
- 相对路径转换为绝对路径
- 去重

#### 3.2.5 视频（video）

**提取位置**：`<iframe>` 标签
**处理**：

- 提取 `src` 属性
- 识别视频平台（腾讯视频、优酷等）
- 提取视频 ID（如需要）

#### 3.2.6 作者（author）

**提取位置**：`<div class="case_info info_info">` 中的 `<span class="span_01">`

#### 3.2.7 发布时间（publish_time）

**提取位置**：`<div class="case_info info_info">` 中的 `<span class="span_02">`
**格式**：YYYY-MM-DD

#### 3.2.8 相关信息（品牌、行业、标签等）

**提取位置**：`<div class="agent" id="list1">`

**实际 HTML 结构**（基于实际页面分析）：

```html
<div class="agent" id="list1">
  <span class="newp">相关信息</span>
  <div class="abouttext1">
    <p>所属行业</p>
    <span class="pr">
      <a data-class="industry" data-name="家居、家电">家居、家电</a>
    </span>
  </div>
  <div class="abouttext1">
    <p>形式类别</p>
    <span class="pr">
      <a data-class="typeclass" data-name="其它">其它</a>
    </span>
  </div>
  <div class="abouttext1">
    <p>所在地区</p>
    <span class="pr">
      <a data-class="area" data-name="其他地区">其他地区</a>
    </span>
  </div>
  <div class="abouttext4">
    <p>标签</p>
    <span>
      <a class="pr2" data-name="宜家">宜家</a>
      <a class="pr2" data-name="奥美">奥美</a>
    </span>
  </div>
  <div class="abouttext3">
    <p>时间</p>
    <span class="pr1">2020-02-14</span>
  </div>
</div>
```

**解析策略**（基于实际 HTML 结构）：

1. **所属行业**：

   - 查找包含文本"所属行业"的 `<p>` 标签
   - 在其父级 `<div class="abouttext1">` 中查找 `<a data-class="industry">` 标签
   - 提取 `data-name` 属性或文本内容

2. **形式类别**：

   - 查找包含文本"形式类别"的 `<p>` 标签
   - 在其父级 `<div class="abouttext1">` 中查找 `<a data-class="typeclass">` 标签
   - 提取 `data-name` 属性或文本内容

3. **所在地区**：

   - 查找包含文本"所在地区"的 `<p>` 标签
   - 在其父级 `<div class="abouttext1">` 中查找 `<a data-class="area">` 标签
   - 提取 `data-name` 属性或文本内容

4. **标签**：

   - 查找包含文本"标签"的 `<p>` 标签
   - 在其父级 `<div class="abouttext4">` 中查找所有 `<a class="pr2">` 标签
   - 提取所有标签的 `data-name` 属性或文本内容，组成列表

5. **时间**：
   - 查找包含文本"时间"的 `<p>` 标签
   - 在其父级 `<div class="abouttext3">` 中查找 `<span class="pr1">` 标签
   - 提取文本内容（格式：YYYY-MM-DD）

**注意**：

- 如果某个信息项不存在，对应的 div 可能不存在，需要处理缺失情况
- 某些案例可能还有"品牌"或"广告主"信息，需要检查是否有其他 `abouttext` 类型的 div

#### 3.2.9 广告公司/代理公司

**提取位置**：可能在 `agent` 区域，或需要从文本中解析
**策略**：如果 `agent` 区域有"广告公司"、"代理公司"等关键词，提取其后内容

#### 3.2.10 评分和收藏数

**注意**：这些信息在列表页 API 中已有，详情页可能不显示或显示方式不同
**策略**：优先使用列表页数据，详情页作为补充

### 3.3 数据清洗规则

#### 3.3.1 文本清洗

- 去除 HTML 实体编码（如 `&ldquo;` → `"`）
- 去除多余空白字符
- 去除换行符和制表符
- 统一编码为 UTF-8

#### 3.3.2 URL 处理

- 相对路径转换为绝对路径（基于 `https://m.adquan.com`）
- 去除 URL 中的追踪参数（如 `?v=xxx`）
- 验证 URL 格式

#### 3.3.3 时间格式化

- 统一格式为 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- 处理各种时间格式变体

#### 3.3.4 图片去重

- 基于 URL 去重
- 过滤掉明显不是案例图片的 URL（如 logo、图标等）

### 3.4 错误处理

#### 3.4.1 字段缺失

- 如果某个字段提取失败，使用空值或默认值
- 记录缺失字段，用于质量评分

#### 3.4.2 结构变化

- 如果预期的 class/id 不存在，尝试备用方案
- 记录解析失败的情况，便于后续优化

#### 3.4.3 数据验证

- 验证提取的数据格式是否正确
- 验证 URL 是否可访问（可选）

## 4. 实现建议

### 4.1 类设计

```python
class DetailPageParser:
    """详情页解析器"""

    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = 'https://m.adquan.com'

    def parse(self, url: str) -> Dict[str, Any]:
        """解析详情页，返回结构化数据"""
        pass

    def _extract_from_meta(self, soup: BeautifulSoup) -> Dict:
        """从meta标签提取信息"""
        pass

    def _extract_from_structure(self, soup: BeautifulSoup) -> Dict:
        """从HTML结构提取信息"""
        pass

    def _extract_agent_info(self, soup: BeautifulSoup) -> Dict:
        """从agent区域提取相关信息"""
        pass

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        pass

    def _normalize_url(self, url: str) -> str:
        """规范化URL"""
        pass
```

### 4.2 测试策略

1. **单元测试**：测试每个字段的提取逻辑
2. **集成测试**：测试完整解析流程
3. **边界测试**：测试缺失字段、异常结构等情况
4. **多案例测试**：测试不同类型的案例（有视频、无视频、不同结构等）

## 5. 注意事项

1. **页面结构可能变化**：需要定期检查页面结构，及时更新解析规则
2. **部分信息可能缺失**：不是所有案例都有完整信息，需要处理缺失情况
3. **图片可能很多**：需要合理限制图片数量或提供筛选机制
4. **性能考虑**：解析大量 HTML 时注意性能，可以考虑缓存解析结果

## 6. 文本提取优化（2026-01-13）

### 6.1 优化背景

在解析某些案例时，发现 `new_neirong` 中的文字提取存在不全的问题，特别是对于包含复杂嵌套结构（如 `<section>` 嵌套、多个 `<p>` 标签）的 HTML 内容。

### 6.2 优化内容

#### 6.2.1 改进的提取策略

1. **创建副本机制**：

   - 在提取前创建 HTML 副本，避免修改原始 BeautifulSoup 对象
   - 确保多次提取不会相互影响

2. **预处理优化**：

   - 先移除所有不需要的元素（图片、视频、水印、脚本等）
   - 移除空的容器标签（如空的 `<section>`、`<div>`），但保留有内容的
   - 为后续文本提取提供干净的 HTML 结构

3. **多层提取策略**：

   - **主要策略**：提取所有 `<p>` 标签（包括嵌套的），确保不遗漏任何段落
   - **备用策略 1**：如果没有 `<p>` 标签，遍历直接子元素递归提取
   - **备用策略 2**：最后手段，提取所有文本并按段落分割

4. **`<br>` 标签处理**：

   - 在提取 `<p>` 标签文本前，先将所有 `<br>` 和 `<br/>` 标签替换为换行符
   - 保持文本的换行结构，确保格式正确

5. **去重机制**：

   - 使用 `seen_texts` 集合记录已提取的文本
   - 避免重复提取相同内容（可能由于嵌套结构导致）

6. **水印过滤增强**：
   - 在提取阶段过滤包含"本文来源于广告门"或"adquan.com"的段落
   - 在后处理阶段使用正则表达式再次过滤（支持多行匹配）
   - 确保水印文本被完全移除

#### 6.2.2 新增方法

- **`_extract_text_from_p_tag(p_tag)`**：
  - 专门处理 `<p>` 标签的文本提取
  - 正确处理 `<br>` 标签转换为换行
  - 保持内联标签（`<em>`、`<strong>`、`<span>`）的文本内容
  - 清理每行的前后空白，但保留段落内的换行结构

#### 6.2.3 测试验证

优化后的代码已通过测试验证：

- ✅ 所有 15 个测试案例均成功解析（100% 成功率）
- ✅ 案例 292118（包含复杂嵌套结构）的所有文本内容均被完整提取
- ✅ 关键短语验证通过，包括：
  - "只要步履不停，我们总会遇见"
  - "诗意不在心里，也会在别的地方"
  - "在风里不是要飘扬，而是要张扬"
  - "学会独处也是一项才能"
  - 以及其他所有文本内容

### 6.3 优化效果

- **提取完整性**：解决了文本提取不全的问题，确保所有文本内容都被提取
- **格式保持**：正确处理 `<br>` 标签，保持文本的换行格式
- **去重能力**：避免重复提取，提高数据质量
- **容错性**：多层备用策略确保即使 HTML 结构变化也能提取文本

### 6.4 代码位置

优化代码位于 `spider/detail_parser.py`：

- `_extract_text_from_new_neirong()` 方法（第 133-214 行）
- `_extract_text_from_p_tag()` 方法（第 216-242 行）

## 7. 后续优化方向

1. **智能提取**：使用 NLP 技术从描述中提取更多结构化信息
2. **图片分析**：下载并分析图片，提取更多元数据
3. **视频处理**：提取视频缩略图、时长等信息
4. **标签生成**：基于内容自动生成标签
