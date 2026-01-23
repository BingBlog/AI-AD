# 列表页接口替换逻辑详细说明

## 1. 替换概览

### 1.1 变更点汇总

| 组件               | 文件路径                                           | 变更类型 | 说明                                |
| ------------------ | -------------------------------------------------- | -------- | ----------------------------------- |
| CSRFTokenManager   | `backend/services/spider/csrf_token_manager.py`    | 修改     | 更新 base_url，添加 Cookie 解析逻辑 |
| AdquanAPIClient    | `backend/services/spider/api_client.py`            | 修改     | 更新接口地址、参数格式、响应处理    |
| ListPageHTMLParser | `backend/services/spider/list_page_html_parser.py` | 新增     | HTML 解析器，解析返回的 HTML 字符串 |

### 1.2 数据流对比

**旧流程**：

```
请求 → JSON 响应 → 直接使用 data.items
```

**新流程**：

```
请求 → JSON 响应（data 为 HTML） → 解析 HTML → 提取 items → 转换为旧格式
```

## 2. 详细替换逻辑

### 2.1 CSRFTokenManager 更新

#### 2.1.1 变更点 1：base_url 更新

**位置**：`__init__` 方法

**旧代码**：

```python
def __init__(self, base_url: str = 'https://m.adquan.com/creative', ...):
```

**新代码**：

```python
def __init__(self, base_url: str = 'https://www.adquan.com/case_library/index', ...):
```

#### 2.1.2 变更点 2：User-Agent 更新

**位置**：`__init__` 方法中的 headers 设置

**旧代码**：

```python
'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) ...',
```

**新代码**：

```python
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
```

#### 2.1.3 变更点 3：添加 Cookie 解析方法

**新增方法**：

```python
def _extract_csrf_from_cookie(self) -> Optional[str]:
    """
    从 Cookie 中提取并解析 XSRF-TOKEN

    Returns:
        CSRF Token 字符串，如果提取失败则返回 None
    """
    try:
        # 从 session.cookies 中获取 XSRF-TOKEN
        xsrf_token = None
        for cookie in self.session.cookies:
            if cookie.name == 'XSRF-TOKEN':
                xsrf_token = cookie.value
                break

        if not xsrf_token:
            logger.warning("Cookie 中未找到 XSRF-TOKEN")
            return None

        # Laravel 的 XSRF-TOKEN 是 base64 编码的 JSON
        # 格式: {"iv":"...","value":"...","mac":"..."}
        # 需要解码并提取实际的 token 值
        import base64
        import json

        try:
            # URL 解码（Laravel 使用 URL-safe base64）
            decoded = base64.urlsafe_b64decode(xsrf_token + '==')  # 补全 padding
            token_data = json.loads(decoded.decode('utf-8'))

            # 提取实际的 token 值
            # 注意：这里可能需要根据实际的 Laravel 加密格式调整
            actual_token = token_data.get('value', '')

            if actual_token:
                logger.info(f"成功从 Cookie 中提取 CSRF Token: {actual_token[:20]}...")
                return actual_token
            else:
                logger.warning("XSRF-TOKEN 中未找到 value 字段")
                return None

        except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"解析 XSRF-TOKEN 失败: {e}")
            # 如果解析失败，尝试直接使用原始值（某些情况下可能直接是 token）
            return xsrf_token

    except Exception as e:
        logger.error(f"提取 CSRF Token 时发生错误: {e}")
        return None
```

#### 2.1.4 变更点 4：更新 get_token 方法

**修改逻辑**：

```python
def get_token(self, force_refresh: bool = False) -> str:
    """获取CSRF Token"""
    # 优先从 Cookie 中提取
    if not force_refresh:
        cookie_token = self._extract_csrf_from_cookie()
        if cookie_token:
            self._token = cookie_token
            return cookie_token

    # 如果 Cookie 中没有，则从 HTML 页面获取
    self._fetch_token()

    if not self._token:
        raise ValueError("无法获取CSRF Token")

    return self._token
```

### 2.2 AdquanAPIClient 更新

#### 2.2.1 变更点 1：base_url 更新

**位置**：`__init__` 方法

**旧代码**：

```python
def __init__(self, base_url: str = 'https://m.adquan.com/creative', ...):
```

**新代码**：

```python
def __init__(self, base_url: str = 'https://www.adquan.com/case_library/index', ...):
```

#### 2.2.2 变更点 2：更新 \_setup_api_headers 方法

**新代码**：

```python
def _setup_api_headers(self):
    """设置API请求的默认Headers"""
    api_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.adquan.com/case_library/index',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    self.session.headers.update(api_headers)
```

#### 2.2.3 变更点 3：添加参数映射方法

**新增方法**：

```python
def _map_params(self, page: int, case_type: int = 1, **kwargs) -> Dict[str, Any]:
    """
    将旧参数格式映射到新参数格式

    Args:
        page: 页码（从 0 开始）
        case_type: 案例类型（兼容旧参数，映射到 typeclass）
        **kwargs: 其他参数（industry, typeclass, area, year, filter, keyword）

    Returns:
        新接口所需的参数字典
    """
    # 参数映射规则：
    # - case_type 映射到 typeclass（如果未提供 typeclass）
    # - 其他参数直接使用 kwargs 中的值，或使用默认值

    return {
        'page': page,
        'industry': kwargs.get('industry', 0),
        'typeclass': kwargs.get('typeclass', case_type),  # 兼容旧参数
        'area': kwargs.get('area', ''),
        'year': kwargs.get('year', 0),
        'filter': kwargs.get('filter', 0),
        'keyword': kwargs.get('keyword', ''),
    }
```

#### 2.2.4 变更点 4：更新 get_creative_list 方法

**关键修改**：

1. **参数处理**：

```python
# 旧代码
params = {
    'page': page + 1,
    'type': case_type,
}

# 新代码
params = self._map_params(page, case_type, **kwargs)
```

2. **响应处理**：

```python
# 旧代码
data = response.json()
if isinstance(data, dict) and 'data' in data:
    items = data['data'].get('items', [])

# 新代码
data = response.json()
if data.get('code') != 0:
    raise ValueError(f"API错误: {data.get('message')}")

# 解析 HTML 字符串
html_content = data.get('data', '')
if not html_content:
    logger.warning("API 返回的 data 字段为空")
    return {
        'code': 0,
        'message': '请求成功',
        'data': {
            'items': [],
            'page': page,
        }
    }

# 使用 HTML 解析器
from .list_page_html_parser import ListPageHTMLParser
parser = ListPageHTMLParser()
items = parser.parse_html(html_content)

# 转换为旧格式
return {
    'code': 0,
    'message': '请求成功',
    'data': {
        'items': items,
        'page': page,
    }
}
```

#### 2.2.5 变更点 5：更新 parse_case_item 方法（如果需要）

**检查点**：确认新接口返回的数据字段是否与旧接口一致，如果不一致，需要更新映射逻辑。

### 2.3 新增 ListPageHTMLParser

#### 2.3.1 文件结构

**新文件**：`backend/services/spider/list_page_html_parser.py`

**基本结构**：

```python
#!/usr/bin/env python3
"""
列表页 HTML 解析器
负责解析新接口返回的 HTML 字符串，提取案例列表
"""

import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ListPageHTMLParser:
    """列表页 HTML 解析器类"""

    def __init__(self, base_url: str = 'https://www.adquan.com'):
        """
        初始化解析器

        Args:
            base_url: 基础 URL，用于转换相对路径
        """
        self.base_url = base_url

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        解析 HTML 字符串，返回案例列表

        Args:
            html: HTML 字符串

        Returns:
            案例列表，每个案例是一个字典
        """
        if not html or not html.strip():
            logger.warning("HTML 内容为空")
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.find_all('div', class_='article_1')

            if not articles:
                logger.warning("未找到 article_1 元素，可能 HTML 结构已变化")
                return []

            cases = []
            for article in articles:
                try:
                    case = self._parse_article(article)
                    if case:
                        cases.append(case)
                except Exception as e:
                    logger.error(f"解析单个案例时发生错误: {e}")
                    continue

            logger.info(f"成功解析 {len(cases)} 个案例")
            return cases

        except Exception as e:
            logger.error(f"解析 HTML 时发生错误: {e}")
            raise

    def _parse_article(self, article: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """解析单个 article_1 元素"""
        # 实现见下方
        pass

    def _extract_title(self, article: BeautifulSoup) -> Optional[str]:
        """提取标题"""
        # 优先级 1: article_2_p
        title_elem = article.find('p', class_='article_2_p')
        if title_elem:
            title = title_elem.get_text(strip=True)
            if title:
                return title

        # 优先级 2: article_1_fu 中的第一个 p
        fu_elem = article.find('div', class_='article_1_fu')
        if fu_elem:
            first_p = fu_elem.find('p')
            if first_p:
                title = first_p.get_text(strip=True)
                if title:
                    return title

        return None

    def _extract_url(self, article: BeautifulSoup) -> Optional[str]:
        """提取案例链接"""
        # 查找 article_2_href 或 article_1 中的第一个 a 标签
        href_elem = article.find('a', class_='article_2_href')
        if href_elem and href_elem.get('href'):
            url = href_elem.get('href')
            return urljoin(self.base_url, url)

        # 备用：查找 article_1 中的第一个 a 标签
        first_a = article.find('a')
        if first_a and first_a.get('href'):
            url = first_a.get('href')
            return urljoin(self.base_url, url)

        return None

    def _extract_thumb(self, article: BeautifulSoup) -> Optional[str]:
        """提取缩略图"""
        img_elem = article.find('img', class_='article_1_img')
        if img_elem and img_elem.get('src'):
            return img_elem.get('src')
        return None

    def _extract_publish_time(self, article: BeautifulSoup) -> Optional[str]:
        """提取发布时间"""
        fu_elem = article.find('div', class_='article_1_fu')
        if fu_elem:
            # 查找第二个 p 标签（通常是日期）
            p_tags = fu_elem.find_all('p')
            if len(p_tags) >= 2:
                date_text = p_tags[1].get_text(strip=True)
                # 格式: 2026/01/23
                if re.match(r'\d{4}/\d{2}/\d{2}', date_text):
                    return date_text.replace('/', '-')  # 转换为 2026-01-23
        return None

    def _extract_score(self, article: BeautifulSoup) -> Optional[float]:
        """提取评分"""
        article_3 = article.find('div', class_='article_3')
        if article_3:
            # 查找包含评分的元素
            normal_elem = article_3.find('normal')
            if normal_elem:
                score_text = normal_elem.get_text(strip=True)
                # 格式可能是: "6.0分" 或 "6.0" 或 "暂无"
                if '暂无' in score_text:
                    return None
                # 提取数字
                match = re.search(r'(\d+\.?\d*)', score_text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        pass
        return None

    def _extract_companies(self, article: BeautifulSoup) -> List[Dict[str, str]]:
        """提取公司信息"""
        companies = []

        # 查找 article_3 中的公司 logo
        article_3 = article.find('div', class_='article_3')
        if article_3:
            company_imgs = article_3.find_all('img', class_='article_3_img')
            for img in company_imgs:
                company = {
                    'logo': img.get('src', ''),
                    'name': img.get('alt', ''),
                }
                companies.append(company)

        return companies
```

#### 2.3.2 数据格式转换

**目标格式**（与旧接口保持一致）：

```python
{
    'id': case_id,  # 从 URL 中提取
    'title': title,
    'url': url,
    'thumb': thumb,
    'score': score,
    'score_decimal': str(score) if score else '0.0',
    'favourite': 0,
    'company_name': companies[0]['name'] if companies else '',
    'company_logo': companies[0]['logo'] if companies else '',
    'vip_img': '',
    'publish_time': publish_time,
}
```

## 3. 测试用例

### 3.1 单元测试

#### 测试 CSRFTokenManager

```python
def test_extract_csrf_from_cookie():
    """测试从 Cookie 中提取 CSRF Token"""
    # 设置测试 Cookie
    # 调用提取方法
    # 验证结果
    pass
```

#### 测试 ListPageHTMLParser

```python
def test_parse_html():
    """测试 HTML 解析"""
    # 使用示例 HTML
    # 调用解析方法
    # 验证返回的数据格式和内容
    pass
```

#### 测试参数映射

```python
def test_map_params():
    """测试参数映射"""
    # 测试旧参数格式
    # 验证映射结果
    pass
```

### 3.2 集成测试

```python
def test_get_creative_list():
    """测试完整的列表获取流程"""
    # 创建 API 客户端
    # 调用 get_creative_list
    # 验证返回数据格式
    # 验证数据内容
    pass
```

## 4. 流式处理实现

### 4.1 实现说明

已实现流式处理机制，边获取边处理列表页数据，避免一次性加载所有数据到内存。

**主要变更**：

- 新增 `_get_list_items_streaming` 生成器方法
- 修改 `crawl` 方法，使用生成器逐页处理
- 保留 `_get_list_items_with_status_recording` 方法用于向后兼容（内部调用流式方法）

**数据流对比**：

**旧流程**（已废弃）：

```
获取所有列表页 → 存储在内存 → 遍历处理
```

**新流程**（流式处理）：

```
获取第1页 → 立即处理 → 获取第2页 → 立即处理 → ...
```

### 4.2 优势

- ✅ **内存占用低**：只保留当前页数据在内存中
- ✅ **容错性好**：单页失败不影响已处理的数据
- ✅ **实时处理**：可以立即看到处理进度
- ✅ **可中断恢复**：支持断点续传，失败后可重试

## 5. 部署检查清单

- [x] 更新 CSRFTokenManager

  - [x] base_url 更新为 `https://www.adquan.com/case_library/index`
  - [x] User-Agent 更新为桌面端浏览器
  - [x] Cookie 解析逻辑实现（`_extract_csrf_from_cookie` 方法）
  - [x] 修复 session 属性问题
  - [ ] 单元测试通过（待阶段 3）

- [x] 创建 ListPageHTMLParser

  - [x] 文件创建 (`backend/services/spider/list_page_html_parser.py`)
  - [x] HTML 解析逻辑实现
  - [x] 数据格式转换实现（保持与旧接口格式一致）
  - [ ] 单元测试通过（待阶段 3）

- [x] 更新 AdquanAPIClient

  - [x] base_url 更新为 `https://www.adquan.com/case_library/index`
  - [x] headers 更新（添加所有必需 headers）
  - [x] 参数映射实现（`_map_params` 方法）
  - [x] 响应处理更新（HTML 解析集成）
  - [ ] 集成测试通过（待阶段 3）

- [ ] 整体测试

  - [ ] 端到端测试
  - [ ] 错误处理测试
  - [ ] 性能测试

- [ ] 文档更新
  - [ ] 代码注释更新
  - [ ] README 更新（如有）

## 6. 注意事项

1. **Cookie 管理**：确保 Cookie 的有效性和自动刷新机制
2. **错误处理**：HTML 解析失败时要有降级方案
3. **向后兼容**：保持返回数据格式与旧接口一致
4. **日志记录**：详细记录解析过程和错误信息
5. **性能考虑**：HTML 解析可能比 JSON 解析慢，需要优化
