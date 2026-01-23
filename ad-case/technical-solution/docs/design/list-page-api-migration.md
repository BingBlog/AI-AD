# 列表页接口迁移技术方案

## 1. 背景

### 1.1 问题描述

- 原列表页接口 `https://m.adquan.com/creative` 已被封禁
- 需要迁移到新的接口 `https://www.adquan.com/case_library/index`
- 新接口返回格式发生变化：`data` 字段从 JSON 对象变为 HTML 字符串

### 1.2 新接口信息

**接口地址**：`https://www.adquan.com/case_library/index`

**请求方式**：GET

**请求参数**：

- `page`: 页码（从 0 开始）
- `industry`: 行业筛选（0 表示全部）
- `typeclass`: 类型筛选（0 表示全部）
- `area`: 地区筛选（空字符串表示全部）
- `year`: 年份筛选（0 表示全部）
- `filter`: 筛选条件（0 表示全部）
- `keyword`: 关键词搜索（空字符串表示不搜索）

**必需 Headers**：

```
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: keep-alive
Referer: https://www.adquan.com/case_library/index
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
X-CSRF-TOKEN: <从Cookie中的XSRF-TOKEN解析>
X-Requested-With: XMLHttpRequest
sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
```

**必需 Cookies**：

- `_c_WBKFRo`: 会话标识
- `Hm_lvt_b9772bb26f0ebb4e77be78655c6aba4e`: 访问统计
- `HMACCOUNT`: 账户标识
- `XSRF-TOKEN`: CSRF Token（需要解析后作为 X-CSRF-TOKEN header）
- `adquan_session_production`: 会话信息
- `SERVERID`: 服务器标识
- `Hm_lpvt_b9772bb26f0ebb4e77be78655c6aba4e`: 访问统计

**返回格式**：

```json
{
  "code": 0,
  "message": "请求成功",
  "data": "<div class=\"article_1\">...</div>..." // HTML字符串
}
```

## 2. 技术方案

### 2.1 架构设计

#### 2.1.1 组件结构

```
AdquanAPIClient (api_client.py)
├── CSRFTokenManager (csrf_token_manager.py) - 需要更新
│   └── 从 Cookie 中提取 XSRF-TOKEN 并解析
└── ListPageHTMLParser (新增) - HTML 解析器
    └── 解析返回的 HTML 字符串，提取案例列表
```

#### 2.1.2 数据流

```
1. 访问列表页 HTML 页面（获取 Cookie 和 CSRF Token）
   ↓
2. 从 Cookie 中提取 XSRF-TOKEN
   ↓
3. 解析 XSRF-TOKEN（Laravel 加密格式）
   ↓
4. 调用新 API 接口（携带完整 Headers 和 Cookies）
   ↓
5. 接收 JSON 响应（data 字段为 HTML 字符串）
   ↓
6. 解析 HTML 字符串，提取案例列表
   ↓
7. 转换为原有数据格式（保持向后兼容）
```

### 2.2 实现步骤

#### 步骤 1：更新 CSRFTokenManager

**文件**：`backend/services/spider/csrf_token_manager.py`

**变更内容**：

1. 更新 `base_url` 默认值为 `https://www.adquan.com/case_library/index`
2. 添加从 Cookie 中提取和解析 XSRF-TOKEN 的逻辑
3. 更新 User-Agent 为桌面端浏览器
4. 添加 Cookie 管理功能

**关键实现**：

```python
def _extract_csrf_from_cookie(self) -> Optional[str]:
    """从 Cookie 中提取并解析 XSRF-TOKEN"""
    # 1. 从 session.cookies 中获取 XSRF-TOKEN
    # 2. 解析 Laravel 加密的 token（base64 解码）
    # 3. 提取实际的 token 值
    pass
```

#### 步骤 2：创建 ListPageHTMLParser

**新文件**：`backend/services/spider/list_page_html_parser.py`

**功能**：

- 解析 HTML 字符串，提取案例列表
- 提取每个案例的关键信息：
  - 标题
  - 链接（article URL）
  - 图片（主图）
  - 日期
  - 评分
  - 公司信息（品牌、代理公司等）

**HTML 结构分析**（基于提供的示例）：

```html
<div class="article_1">
  <a href="https://www.adquan.com/article/358273" target="_blank">
    <img class="article_1_img" src="..." alt="" />
    <div class="article_1_fu">
      <p>标题或描述</p>
      <p>2026/01/23</p>
    </div>
  </a>
  <a
    class="article_2_href"
    href="https://www.adquan.com/article/358273"
    target="_blank">
    <p class="article_2_p">标题</p>
  </a>
  <div class="article_2">
    <div class="article_3">
      <div class="article_4">
        <img class="article_3_img" src="..." alt="" />
        <!-- 公司logo -->
        <span>关联X家公司</span>
      </div>
      <div class="article_4">
        <img class="xing_img" src="..." alt="" />
        <normal>评分</normal>
      </div>
    </div>
  </div>
</div>
```

**解析逻辑**：

```python
def parse_html(self, html: str) -> List[Dict[str, Any]]:
    """解析 HTML 字符串，返回案例列表"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('div', class_='article_1')

    cases = []
    for article in articles:
        case = {
            'title': self._extract_title(article),
            'url': self._extract_url(article),
            'thumb': self._extract_thumb(article),
            'publish_time': self._extract_publish_time(article),
            'score': self._extract_score(article),
            'companies': self._extract_companies(article),
        }
        cases.append(case)

    return cases
```

#### 步骤 3：更新 AdquanAPIClient

**文件**：`backend/services/spider/api_client.py`

**变更内容**：

1. 更新 `base_url` 默认值为 `https://www.adquan.com/case_library/index`
2. 更新 `get_creative_list` 方法：
   - 修改请求参数（支持新的参数格式）
   - 处理 HTML 响应（调用 ListPageHTMLParser）
   - 转换为原有数据格式（保持向后兼容）
3. 更新 `_setup_api_headers` 方法：
   - 添加新的必需 headers
   - 更新 User-Agent 为桌面端
4. 添加参数映射逻辑（兼容旧参数格式）

**参数映射**：

```python
def _map_params(self, page: int, case_type: int = 1, **kwargs) -> Dict[str, Any]:
    """将旧参数格式映射到新参数格式"""
    return {
        'page': page,
        'industry': kwargs.get('industry', 0),
        'typeclass': kwargs.get('typeclass', 0),
        'area': kwargs.get('area', ''),
        'year': kwargs.get('year', 0),
        'filter': kwargs.get('filter', 0),
        'keyword': kwargs.get('keyword', ''),
    }
```

**响应处理**：

```python
def get_creative_list(self, page: int = 0, case_type: int = 1, **kwargs) -> Dict[str, Any]:
    """获取创意案例列表"""
    # 1. 构建请求参数
    params = self._map_params(page, case_type, **kwargs)

    # 2. 发送请求
    response = self.session.get(self.base_url, params=params, headers=headers, timeout=30)

    # 3. 解析 JSON 响应
    data = response.json()

    # 4. 检查 API 状态码
    if data.get('code') != 0:
        raise ValueError(f"API错误: {data.get('message')}")

    # 5. 解析 HTML 字符串
    html_content = data.get('data', '')
    parser = ListPageHTMLParser()
    items = parser.parse_html(html_content)

    # 6. 转换为原有数据格式（保持向后兼容）
    return {
        'code': 0,
        'message': '请求成功',
        'data': {
            'items': items,
            'page': page,
            # 其他分页信息（如果需要）
        }
    }
```

### 2.3 向后兼容性

#### 2.3.1 数据格式兼容

- 保持返回数据格式与原有格式一致
- `data.items` 数组结构保持不变
- 每个 item 的字段尽量保持一致（如有差异，需要映射）

#### 2.3.2 API 接口兼容

- `get_creative_list` 方法签名保持不变
- 参数支持新旧两种格式（通过 `**kwargs` 扩展）
- 返回值格式保持一致

### 2.4 错误处理

#### 2.4.1 Token 获取失败

- 如果无法从 Cookie 中提取 XSRF-TOKEN，尝试重新访问 HTML 页面
- 如果解析失败，记录错误并重试

#### 2.4.2 HTML 解析失败

- 如果 HTML 格式不符合预期，记录警告并尝试容错解析
- 如果完全无法解析，抛出异常并记录详细错误信息

#### 2.4.3 API 请求失败

- 检查响应状态码和 API 返回的 code
- 如果是认证错误（401/403），尝试刷新 Token 并重试
- 如果是其他错误，记录错误信息并抛出异常

### 2.5 测试策略

#### 2.5.1 单元测试

- 测试 CSRFTokenManager 的 Cookie 解析功能
- 测试 ListPageHTMLParser 的 HTML 解析功能
- 测试参数映射逻辑
- 测试数据格式转换

#### 2.5.2 集成测试

- 测试完整的请求流程
- 测试错误处理和重试机制
- 测试向后兼容性

#### 2.5.3 手动测试

- 使用真实接口进行测试
- 验证返回数据格式
- 验证数据完整性

## 3. 实施计划

### 3.1 阶段 1：准备工作（1-2 天）

- [ ] 分析新接口的 HTML 结构
- [ ] 设计数据映射方案
- [ ] 准备测试数据

### 3.2 阶段 2：核心功能开发（2-3 天）

- [x] 更新 CSRFTokenManager
  - [x] base_url 更新为 `https://www.adquan.com/case_library/index`
  - [x] User-Agent 更新为桌面端浏览器
  - [x] 添加从 Cookie 中提取 XSRF-TOKEN 的逻辑
  - [x] 修复 session 属性问题
- [x] 创建 ListPageHTMLParser
  - [x] 实现 HTML 解析逻辑
  - [x] 实现数据格式转换（保持向后兼容）
  - [x] 提取案例信息（标题、链接、图片、评分、公司等）
- [x] 更新 AdquanAPIClient
  - [x] base_url 更新
  - [x] headers 更新（添加所有必需 headers）
  - [x] 参数映射方法实现
  - [x] 响应处理更新（HTML 解析集成）

### 3.3 阶段 3：测试和优化（1-2 天）

- [ ] 编写单元测试
- [ ] 进行集成测试
- [ ] 修复发现的问题
- [ ] 性能优化

### 3.4 阶段 4：部署和验证（1 天）

- [ ] 代码审查
- [ ] 部署到测试环境
- [ ] 验证功能
- [ ] 部署到生产环境

## 4. 风险评估

### 4.1 技术风险

- **HTML 结构变化**：如果网站更新 HTML 结构，解析器可能失效
  - **缓解措施**：使用容错解析，记录详细日志
- **Cookie 失效**：Cookie 可能有时效性
  - **缓解措施**：实现 Cookie 刷新机制
- **Token 解析失败**：XSRF-TOKEN 的解析可能失败
  - **缓解措施**：实现多种解析策略，提供降级方案

### 4.2 兼容性风险

- **数据格式差异**：新旧接口返回的数据字段可能不完全一致
  - **缓解措施**：实现字段映射和默认值处理

### 4.3 性能风险

- **HTML 解析性能**：解析大量 HTML 可能影响性能
  - **缓解措施**：优化解析逻辑，使用高效的解析库

## 5. 回滚方案

如果新接口出现问题，可以：

1. 通过配置开关快速切换回旧接口（如果仍可用）
2. 保留旧代码版本，支持快速回滚
3. 实现接口降级机制，自动切换到备用方案

## 6. 待确认事项

1. **XSRF-TOKEN 解析**：需要确认 Laravel 加密 token 的具体格式和解析方式
2. **HTML 结构稳定性**：需要确认 HTML 结构是否稳定，是否有动态变化
3. **参数映射**：需要确认新旧参数的对应关系
4. **数据字段映射**：需要确认新接口返回的数据字段与旧接口的对应关系
5. **分页信息**：需要确认新接口是否提供分页信息（总数、总页数等）
6. **Cookie 获取方式**：需要确认如何获取和维护有效的 Cookie

## 7. 流式处理优化

### 7.1 实现说明

已实现流式处理机制，边获取边处理列表页数据，避免一次性加载所有数据到内存。

**实现方式**：

- 创建 `_get_list_items_streaming` 生成器方法，逐页获取并 yield 数据
- 修改 `crawl` 方法，使用生成器逐页处理
- 每获取一页数据后立即处理，不等待所有页面获取完成

**优势**：

- ✅ **内存占用低**：只保留当前页数据在内存中
- ✅ **容错性好**：单页失败不影响已处理的数据
- ✅ **实时处理**：可以立即看到处理进度
- ✅ **可中断恢复**：支持断点续传，失败后可重试

### 7.2 数据流

```
获取第1页 → 处理第1页 → 保存批次
   ↓
获取第2页 → 处理第2页 → 保存批次
   ↓
获取第3页 → 处理第3页 → 保存批次
   ...
```

## 8. 后续优化

1. **缓存机制**：缓存解析后的数据，减少重复解析
2. **增量更新**：支持增量获取新数据
3. **监控告警**：添加接口健康监控和告警机制
4. **性能优化**：优化 HTML 解析性能，支持并发处理
