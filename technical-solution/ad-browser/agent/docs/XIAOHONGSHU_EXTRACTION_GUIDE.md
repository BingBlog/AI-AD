# 小红书平台数据提取完整说明文档

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [搜索流程](#搜索流程)
4. [列表页提取](#列表页提取)
5. [详情页提取](#详情页提取)
6. [依赖关系分析](#依赖关系分析)
7. [问题解决方案](#问题解决方案)
8. [技术细节](#技术细节)

---

## 概述

本文档详细说明小红书平台从搜索、列表页提取到详情页提取的完整流程，包括技术实现细节、依赖关系以及各种问题的解决方案。

### 核心特点

- **Playwright 主导架构**：浏览器生命周期由 Playwright 管理，确保页面实例持续可用
- **弹层提取策略**：小红书 PC 端必须从搜索结果页的弹层提取详情，不能直接打开 `/explore/` URL
- **智能回退机制**：browser-use Agent 失败时自动回退到 Playwright 直接操作
- **登录状态保持**：使用系统 Chrome 浏览器，保持用户登录状态

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    TaskController                       │
│  (任务控制器，协调整个提取流程)                          │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ListParser   │ │DetailParser  │ │ BrowserAdapter│
│ (列表页解析)  │ │(详情页解析)  │ │ (浏览器适配器)│
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                 │
       │                │                 │
       └────────────────┼─────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Playwright  │ │ browser-use  │ │   LLMClient   │
│  (主导)      │ │  (备用)      │ │  (内容提取)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 核心原则

1. **Playwright 是浏览器的"唯一主人"**

   - 所有浏览器操作的基础都依赖 Playwright
   - 浏览器生命周期由 Playwright 管理
   - Page 实例的生命周期独立于 browser-use Agent

2. **browser-use Agent 作为"临时操作者"**

   - 仅在需要复杂 AI 决策时使用
   - Agent 执行完成后，Page 实例仍然可用
   - Agent 失败时自动回退到 Playwright 直接操作

3. **弹层提取策略（小红书特殊处理）**
   - 不能直接打开 `/explore/{note_id}` URL（会导致 404）
   - 必须在搜索结果页点击标题打开弹层
   - 从弹层中提取完整内容

---

## 搜索流程

### 流程概览

```
1. 打开平台首页
   ↓
2. 检测登录状态
   ↓
3. 查找搜索框
   ↓
4. 输入关键词
   ↓
5. 触发搜索（Enter 键或点击按钮）
   ↓
6. 等待搜索结果页加载
   ↓
7. 验证 URL 包含 search_result
```

### 详细实现

#### 1. 打开平台首页

**位置**: `agent/browser/adapter.py` - `open_page()`

**实现方式**: 使用 Playwright 直接打开页面

```python
async def open_page(self, url: str) -> Dict[str, Any]:
    # 确保有可用的浏览器会话
    browser, context, page = await self._ensure_browser()

    # 使用 Playwright 直接打开页面
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)

    # 等待页面加载
    await page.wait_for_load_state('networkidle', timeout=5000)

    # 检测是否需要登录
    login_required = await self.check_login_required()
    if login_required:
        await self.wait_for_login()
```

**关键点**:

- 使用 `domcontentloaded` 等待策略，避免超时
- 如果 `networkidle` 超时，回退到 `domcontentloaded`
- 自动检测登录状态，等待用户登录

#### 2. 登录检测

**位置**: `agent/browser/adapter.py` - `check_login_required()`

**检测策略**:

- 检查登录弹窗元素（`.login-container`, `.login-box`, `.login-modal`）
- 检查二维码登录元素（`.qrcode`, `.qr-code`）
- 检查登录按钮（`button:has-text("登录")`）
- 检查 URL 是否包含登录相关路径
- 检查页面文本是否包含登录提示

**等待登录**:

- 轮询检测登录状态（每 2 秒检查一次）
- 超时时间：5 分钟（可配置）
- 登录完成后等待页面稳定（2 秒）

#### 3. 搜索关键词

**位置**: `agent/browser/adapter.py` - `search()` 和 `_search_with_playwright()`

**实现方式**: 使用 Playwright 直接操作搜索框

**搜索框查找策略**（按优先级）:

```python
search_selectors = [
    'input[type="search"]',
    'input[placeholder*="搜索"]',
    'input[placeholder*="Search"]',
    'input[class*="search"]',
    'input[id*="search"]',
    'input[name*="search"]',
    '.search-input input',
    '#search-input',
]
```

**搜索触发方式**:

1. **方法 1**: 按 Enter 键

   ```python
   await search_input.fill(query)
   await search_input.press("Enter")
   ```

2. **方法 2**: 点击搜索按钮（如果 Enter 无效）

   ```python
   search_button_selectors = [
       'button[type="submit"]',
       'button:has-text("搜索")',
       '.search-button',
       '.search-btn',
   ]
   ```

3. **方法 3**: 直接导航到搜索结果 URL（如果前两种方法失败）
   ```python
   encoded_keyword = urllib.parse.quote(query, safe='')
   search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
   await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
   ```

**等待搜索结果**:

- 等待 URL 包含 `search_result`
- 使用 `wait_for_function()` 检查 URL 变化
- 如果超时，至少等待页面稳定

**依赖关系**:

- ✅ **Playwright**: 所有搜索操作都依赖 Playwright
- ❌ **browser-use**: 仅在找不到搜索框时作为备用方案（实际很少使用）

---

## 列表页提取

### 流程概览

```
1. 等待搜索结果加载（3秒）
   ↓
2. 查找所有 note-item 元素
   ↓
3. 提取每个 item 的链接和标题
   ↓
4. 处理链接格式（/explore/ 或 /search_result/）
   ↓
5. 构建完整 URL
   ↓
6. 返回列表项信息
```

### 详细实现

#### 1. 查找搜索结果元素

**位置**: `agent/extractor/list_parser.py` - `parse_list_page()`

**实现方式**: 使用 Playwright 直接查找 DOM 元素

```python
# 等待搜索结果加载
await asyncio.sleep(3)  # 等待动态内容加载

# 查找所有 note-item 卡片
note_items = await page.query_selector_all('section.note-item')
```

**关键点**:

- 等待 3 秒确保动态内容加载完成
- 使用 `section.note-item` 选择器（小红书搜索结果的标准结构）

#### 2. 提取链接和标题

**链接提取策略**:

```python
# 优先查找 /explore/ 链接
link_elem = await note_item.query_selector('a[href*="/explore/"]')
if link_elem:
    href = await link_elem.get_attribute('href')
else:
    # 如果没有，查找 /search_result/ 链接并转换
    link_elem = await note_item.query_selector('a[href*="/search_result/"]')
    if link_elem:
        href = await link_elem.get_attribute('href')
        # 从 /search_result/xxx 提取 note_id，转换为 /explore/xxx
        if href and '/search_result/' in href:
            match = re.search(r'/search_result/([^/?]+)', href)
            if match:
                note_id = match.group(1)
                href = f"/explore/{note_id}"
```

**标题提取策略**:

```python
# 查找标题：a.title > span
title_elem = await note_item.query_selector('a.title span')
if title_elem:
    title = await title_elem.inner_text()
else:
    # 如果没找到，尝试直接查找 a.title
    title_elem = await note_item.query_selector('a.title')
    if title_elem:
        title = await title_elem.inner_text()
```

**URL 构建**:

```python
# 构建完整URL
if href.startswith('/'):
    href = f"https://www.xiaohongshu.com{href}"
```

#### 3. 分页处理

**滚动加载**:

```python
# 如果还需要更多项且未达到最大页数，尝试滚动
while len(items) < max_items and page_count < max_pages:
    scroll_result = await self.browser_adapter.scroll(times=2)
    if not scroll_result.get("success"):
        break

    # 再次提取
    result = await self.browser_adapter.extract(...)
    new_items = self._parse_items(result["content"]["text"])

    # 去重（基于 URL）
    existing_urls = {item.get("url") for item in items}
    new_items = [item for item in new_items if item.get("url") not in existing_urls]

    if not new_items:
        break

    items.extend(new_items)
    page_count += 1
```

**备用方案**:
如果直接查找失败，回退到使用 `browser_adapter.extract()` 方法（依赖 browser-use Agent 或 Playwright 提取文本，然后解析 JSON）。

**依赖关系**:

- ✅ **Playwright**: 主要依赖，用于查找 DOM 元素和提取属性
- ⚠️ **browser-use**: 仅在直接查找失败时作为备用方案

---

## 详情页提取

### 流程概览

```
1. 检查当前是否在搜索结果页
   ↓
2. 从 URL 提取 note_id
   ↓
3. 在搜索结果页找到对应的标题链接
   ↓
4. 点击标题链接打开弹层
   ↓
5. 等待弹层出现
   ↓
6. 从弹层提取内容（标题、描述、图片）
   ↓
7. 关闭弹层
   ↓
8. 使用 LLM 提取结构化信息
```

### 详细实现

#### 1. 小红书特殊处理

**位置**: `agent/extractor/detail_parser.py` - `parse_detail_page()`

**关键限制**:

```python
# 对于小红书，必须从搜索结果页的弹层提取，不能直接打开 /explore/ URL（会导致404）
if platform == "xiaohongshu":
    # 检查是否在搜索结果页
    if "search_result" not in current_url:
        logger.warning(f"当前不在搜索结果页，无法提取详情: {url}")
        # 返回最小化案例，避免尝试打开会导致404的URL
        return MarketingCase(...)
```

**为什么不能直接打开 `/explore/{note_id}` URL**:

- 小红书 PC 端的 `/explore/{note_id}` URL 需要特定的上下文（如从搜索结果页跳转）
- 直接访问会导致 404 错误
- 必须通过点击搜索结果页的标题链接来打开弹层

#### 2. 查找标题链接

**位置**: `agent/extractor/detail_parser.py` - `_extract_from_modal()`

**查找策略**:

```python
# 从URL提取 note_id
if '/explore/' in url:
    match = re.search(r'/explore/([^/?]+)', url)
    if match:
        note_id = match.group(1)

# 在搜索结果页查找包含 note_id 的链接
note_items = await page.query_selector_all('section.note-item')

for item in note_items:
    # 查找所有链接（包括隐藏的）
    all_links = await item.query_selector_all('a')
    for link in all_links:
        href = await link.get_attribute('href')
        if href and note_id in href:
            # 找到匹配的链接，获取对应的 a.title
            title_elem = await item.query_selector('a.title')
            if title_elem:
                title_link = title_elem
                break
```

**滚动处理**:

- 如果第一次查找没找到，尝试滚动页面并重新查找
- 最多重试 2 次
- 每次重试前滚动 500px

#### 3. 点击标题打开弹层

**点击方式**:

```python
# 先滚动到元素可见
await title_link.scroll_into_view_if_needed()
await asyncio.sleep(0.3)

# 使用 JavaScript 点击，更可靠
await title_link.evaluate('el => el.click()')
```

**为什么使用 JavaScript 点击**:

- 更可靠，避免元素被遮挡或不可见的问题
- 绕过某些事件监听器的限制

#### 4. 等待弹层出现

**弹层选择器**（按优先级）:

```python
modal_selectors = [
    '.note-detail-mask',      # 遮罩层（最外层）
    '#noteContainer',         # 弹层容器（ID选择器）
    '.note-container',        # 弹层容器（类选择器）
    '[id="noteContainer"]',   # 弹层容器（属性选择器）
    '.note-detail-container',
    '.detail-modal',
    '.modal-container',
    '[class*="modal"]',
    '[class*="note-detail"]'
]
```

**等待策略**:

```python
# 先等待一下，让弹层有时间打开
await asyncio.sleep(2)

# 尝试多个选择器
for selector in modal_selectors:
    try:
        await page.wait_for_selector(selector, timeout=3000, state='visible')
        modal_elem = await page.query_selector(selector)
        if modal_elem and await modal_elem.is_visible():
            # 如果是遮罩层，尝试找到内部的弹层容器
            if selector == '.note-detail-mask':
                container_elem = await modal_elem.query_selector('#noteContainer, .note-container')
                if container_elem:
                    modal_elem = container_elem
            break
    except Exception:
        continue
```

#### 5. 从弹层提取内容

**标题提取**:

```python
title_elem = await page.query_selector('#detail-title')
if title_elem:
    title_text = await title_elem.inner_text()
    extracted_title = title_text.strip()
```

**描述提取**（尝试多个选择器）:

```python
desc_selectors = [
    '#detail-desc',
    '[id="detail-desc"]',
    '.note-content .desc',
    '.note-content',
    '.desc',
]

for desc_sel in desc_selectors:
    desc_elem = await page.query_selector(desc_sel)
    if desc_elem:
        desc_text = await desc_elem.inner_text()
        if desc_text and len(desc_text.strip()) > 10:
            break
```

**图片提取**:

```python
# 查找所有 img-container 中的图片
img_containers = await page.query_selector_all('.img-container')
for container in img_containers:
    img_elem = await container.query_selector('img')
    if img_elem:
        img_src = await img_elem.get_attribute('src')
        if img_src and img_src.startswith('http'):
            image_urls.append(img_src)
```

**图片下载**:

- 图片保存到 `data/images/{note_id}/` 目录
- 使用 `aiohttp` 异步下载
- 支持多种图片格式（jpg, jpeg, png, gif, webp）

#### 6. 关闭弹层

**关闭方式**:

```python
# 按 ESC 键关闭弹层
await page.keyboard.press('Escape')
await asyncio.sleep(0.5)
```

#### 7. LLM 提取结构化信息

**位置**: `agent/extractor/detail_parser.py` - `_extract_case_from_content()`

**提取流程**:

```python
# 使用 LLM 提取结构化信息
case = await self.llm_client.extract_marketing_case(
    content, platform=platform, source_url=url
)

# 如果提取到了 title，设置它
if title and not case.title:
    case.title = title
```

**提取字段**:

- `brand`: 品牌名称
- `theme`: 主题
- `creative_type`: 创意类型
- `strategy`: 策略列表
- `insights`: 洞察列表
- `title`: 标题（优先使用从弹层提取的标题）

**错误处理**:

- LLM 提取失败时，最多重试 1 次
- 重试失败后，返回最小化案例（只包含 platform 和 source_url）

**依赖关系**:

- ✅ **LLMClient**: 必需，用于结构化信息提取
- ✅ **Playwright**: 必需，用于获取页面内容

---

## 依赖关系分析

### 总体依赖关系

| 功能模块         | Playwright | browser-use | LLMClient | 说明                                                   |
| ---------------- | ---------- | ----------- | --------- | ------------------------------------------------------ |
| **浏览器初始化** | ✅ 必需    | ❌ 不使用   | ❌ 不使用 | Playwright 管理浏览器生命周期                          |
| **打开页面**     | ✅ 必需    | ❌ 不使用   | ❌ 不使用 | 使用 `page.goto()`                                     |
| **登录检测**     | ✅ 必需    | ❌ 不使用   | ❌ 不使用 | 使用 Playwright 查找登录元素                           |
| **搜索关键词**   | ✅ 必需    | ⚠️ 备用     | ❌ 不使用 | 主要使用 Playwright，找不到搜索框时回退到 browser-use  |
| **列表页提取**   | ✅ 必需    | ⚠️ 备用     | ❌ 不使用 | 主要使用 Playwright 查找 DOM，失败时回退到 browser-use |
| **详情页提取**   | ✅ 必需    | ❌ 不使用   | ✅ 必需   | Playwright 提取内容，LLM 提取结构化信息                |
| **滚动页面**     | ✅ 必需    | ❌ 不使用   | ❌ 不使用 | 使用 `page.evaluate()`                                 |
| **内容提取**     | ✅ 必需    | ⚠️ 备用     | ❌ 不使用 | 主要使用 Playwright，失败时回退到 browser-use          |

### Playwright 依赖详情

**所有核心操作都依赖 Playwright**:

1. **浏览器生命周期管理**

   - 创建浏览器实例
   - 创建浏览器上下文
   - 创建页面实例
   - 管理页面生命周期

2. **页面操作**

   - `page.goto()`: 导航到 URL
   - `page.query_selector()`: 查找单个元素
   - `page.query_selector_all()`: 查找多个元素
   - `page.wait_for_selector()`: 等待元素出现
   - `page.evaluate()`: 执行 JavaScript
   - `page.keyboard.press()`: 模拟键盘操作

3. **元素操作**
   - `element.click()`: 点击元素
   - `element.fill()`: 填写输入框
   - `element.inner_text()`: 获取文本内容
   - `element.get_attribute()`: 获取属性值
   - `element.is_visible()`: 检查元素是否可见
   - `element.scroll_into_view_if_needed()`: 滚动到元素可见

**代码位置**:

- `agent/browser/adapter.py`: BrowserAdapter 类
- `agent/browser/playwright_manager.py`: PlaywrightManager 类（可选，用于统一管理）

### browser-use 依赖详情

**browser-use 仅作为备用方案**，在以下情况下使用：

1. **搜索失败回退**

   - 当 Playwright 找不到搜索框时
   - 使用 browser-use Agent 执行自然语言搜索任务

2. **列表页提取失败回退**

   - 当 Playwright 直接查找 DOM 失败时
   - 使用 browser-use Agent 提取页面文本，然后解析 JSON

3. **内容提取失败回退**
   - 当 Playwright 提取内容失败时
   - 使用 browser-use Agent 提取页面文本

**关键限制**:

- browser-use Agent 是"一次性执行器"，执行完成后浏览器会话会被回收
- 因此，我们采用 **Playwright 主导 + Agent 注入式架构**
- Agent 尝试使用我们的 page 实例，但不管理 page 的生命周期

**代码位置**:

- `agent/browser/adapter.py`: `_create_agent_with_page()`, `_default_runner()`

### LLMClient 依赖详情

**LLMClient 用于内容理解和结构化提取**:

1. **相关性判断**

   - 判断列表项是否与关键词相关
   - 位置: `agent/llm/client.py` - `judge_relevance()`

2. **结构化信息提取**

   - 从页面内容提取品牌、主题、创意类型、策略、洞察等
   - 位置: `agent/llm/client.py` - `extract_marketing_case()`

3. **洞察生成**
   - 生成营销洞察（可选功能）
   - 位置: `agent/llm/client.py` - `generate_insights()`

**LLM 配置**:

- 默认使用 DeepSeek Chat API
- 支持自定义 API Base URL 和 Model
- 配置位置: `agent/config.py`

---

## 问题解决方案

### 问题 1: Page 实例获取失败

**问题描述**:

- 之前尝试在 `browser-use Agent.run()` 执行完成后获取 page 实例
- 但 Agent 执行完成后，浏览器会话会被回收，page 实例被销毁

**解决方案**: Playwright 主导架构

**核心思路**:

1. Playwright 是浏览器的"唯一主人"，管理浏览器生命周期
2. browser-use Agent 只能作为"临时操作者"，使用我们的 page 实例
3. Agent 执行完成后，page 实例仍然可用

**实现细节**:

```python
# 1. 先创建 Playwright 浏览器会话
browser, context, page = await self._ensure_browser()

# 2. 尝试将 page 注入到 Agent
agent = await self._create_agent_with_page(task, page)

# 3. Agent 执行完成后，page 仍然可用
if agent is None:
    # Agent 无法注入 page，使用 Playwright 直接执行
    return await self._execute_with_playwright(task, page)
```

**相关文档**:

- `agent/docs/ARCHITECTURE_FIX.md`: 架构修复详细说明
- `agent/docs/PAGE_INSTANCE_ISSUE_ANALYSIS.md`: 问题分析文档

### 问题 2: 小红书详情页 404 错误

**问题描述**:

- 直接打开 `/explore/{note_id}` URL 会导致 404 错误
- 小红书 PC 端需要特定的上下文才能访问详情页

**解决方案**: 弹层提取策略

**核心思路**:

1. 必须在搜索结果页点击标题链接打开弹层
2. 从弹层中提取完整内容
3. 不能直接导航到 `/explore/` URL

**实现细节**:

```python
# 检查是否在搜索结果页
if "search_result" not in current_url:
    # 返回最小化案例，避免尝试打开会导致404的URL
    return MarketingCase(...)

# 在搜索结果页，点击标题打开弹层
modal_data = await self._extract_from_modal(page, url)
```

**关键点**:

- 使用 JavaScript 点击更可靠: `await title_link.evaluate('el => el.click()')`
- 等待弹层出现: 使用多个选择器尝试
- 从弹层提取内容: 标题、描述、图片

### 问题 3: 搜索框找不到

**问题描述**:

- 页面结构可能变化，搜索框选择器失效
- 动态加载导致搜索框延迟出现

**解决方案**: 多选择器策略 + 直接导航备用

**实现细节**:

```python
# 1. 尝试多个搜索框选择器
search_selectors = [
    'input[type="search"]',
    'input[placeholder*="搜索"]',
    'input[class*="search"]',
    # ... 更多选择器
]

# 2. 如果找不到搜索框，回退到 browser-use Agent
if not search_input:
    return await self._run_action(f"搜索: {query}", action_name="search")

# 3. 如果搜索框方式失败，直接导航到搜索结果 URL
if "search_result" not in final_url:
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}"
    await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
```

### 问题 4: 弹层不出现

**问题描述**:

- 点击标题链接后，弹层可能延迟出现
- 弹层选择器可能变化

**解决方案**: 多选择器策略 + 重试机制

**实现细节**:

```python
# 1. 点击后等待一段时间
await asyncio.sleep(2)

# 2. 尝试多个弹层选择器
modal_selectors = [
    '.note-detail-mask',      # 遮罩层
    '#noteContainer',         # 弹层容器
    '.note-container',        # 弹层容器
    # ... 更多选择器
]

# 3. 逐个尝试选择器
for selector in modal_selectors:
    try:
        await page.wait_for_selector(selector, timeout=3000, state='visible')
        modal_elem = await page.query_selector(selector)
        if modal_elem and await modal_elem.is_visible():
            break
    except Exception:
        continue
```

### 问题 5: 登录状态丢失

**问题描述**:

- 使用 Chromium 浏览器时，登录状态无法保持
- 每次启动都需要重新登录

**解决方案**: 使用系统 Chrome 浏览器

**实现细节**:

```python
# 使用系统安装的 Chrome 浏览器，而不是 Chromium
browser = await playwright.chromium.launch(
    headless=False,
    channel="chrome",  # 使用系统 Chrome
    args=['--no-sandbox', '--disable-dev-shm-usage']
)
```

**优势**:

- 保持用户登录状态
- 使用用户已有的 Cookie 和 Session
- 减少登录检测和等待时间

### 问题 6: 协程检查错误

**问题描述**:

- 之前使用 `hasattr(fn, "__await__")` 检查协程函数，但这是错误的
- 协程函数本身没有 `__await__` 属性，只有调用后的协程对象才有

**解决方案**: 使用 `inspect` 模块正确检查

**实现细节**:

```python
import inspect

# 正确检查协程函数
if inspect.iscoroutinefunction(playwright_browser_fn):
    playwright_browser = await playwright_browser_fn()
elif inspect.iscoroutine(playwright_browser_fn):
    playwright_browser = await playwright_browser_fn
else:
    playwright_browser = playwright_browser_fn()
```

**相关文档**:

- `agent/docs/PAGE_INSTANCE_ISSUE_ANALYSIS.md`: 详细问题分析

### 问题 7: 网络超时

**问题描述**:

- 页面加载可能超时
- 网络延迟导致操作失败

**解决方案**: 宽松的等待策略 + 多层回退

**实现细节**:

```python
# 1. 使用宽松的等待策略
try:
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
except Exception:
    # 如果 domcontentloaded 超时，尝试更宽松的条件
    try:
        await page.goto(url, wait_until='commit', timeout=30000)
    except Exception:
        await page.goto(url, wait_until='load', timeout=30000)

# 2. 等待页面加载（多层回退）
try:
    await page.wait_for_load_state('networkidle', timeout=5000)
except Exception:
    try:
        await page.wait_for_load_state('domcontentloaded', timeout=5000)
    except Exception:
        await asyncio.sleep(2)  # 至少等待一段时间
```

---

## 技术细节

### 浏览器配置

**浏览器类型**: Chrome（系统安装）

**启动参数**:

```python
args=['--no-sandbox', '--disable-dev-shm-usage']
```

**视口大小**:

```python
viewport={'width': 1280, 'height': 720}
```

**User-Agent**:

```python
user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

### 等待策略

**页面加载等待**:

1. 优先使用 `domcontentloaded`（更宽松，避免超时）
2. 如果超时，回退到 `commit` 或 `load`
3. 最后至少等待 2 秒

**元素等待**:

1. 使用 `wait_for_selector()` 等待元素出现
2. 设置合理的超时时间（通常 2-5 秒）
3. 如果超时，尝试下一个选择器或备用方案

**动态内容等待**:

1. 等待固定时间（如 3 秒）让动态内容加载
2. 使用 `wait_for_load_state('networkidle')` 等待网络空闲
3. 如果超时，回退到 `domcontentloaded` 或固定等待

### 选择器策略

**多选择器尝试**:

- 所有元素查找都使用多个选择器
- 按优先级排序，逐个尝试
- 找到第一个匹配的元素即停止

**选择器优先级**:

1. ID 选择器（最精确）
2. 类选择器（较精确）
3. 属性选择器（较灵活）
4. 标签选择器（最通用）

**示例**:

```python
# 搜索框选择器（按优先级）
search_selectors = [
    'input[type="search"]',           # 属性选择器
    'input[placeholder*="搜索"]',     # 属性选择器（部分匹配）
    'input[class*="search"]',         # 类选择器（部分匹配）
    '.search-input input',            # 类选择器 + 标签选择器
    '#search-input',                  # ID 选择器
]
```

### 错误处理策略

**分层错误处理**:

1. **操作级错误处理**: 每个操作都有 try-except
2. **模块级错误处理**: 每个模块都有错误恢复机制
3. **任务级错误处理**: 任务失败时返回已提取的结果

**错误恢复**:

1. **重试机制**: 关键操作最多重试 1-2 次
2. **备用方案**: 主要方案失败时使用备用方案
3. **优雅降级**: 无法恢复时返回最小化结果

**错误日志**:

- 所有错误都记录到日志
- 关键错误记录详细信息（URL、选择器、错误类型等）
- 支持调试日志输出到文件

### 性能优化

**异步操作**:

- 所有 I/O 操作都使用异步（async/await）
- 图片下载使用 `aiohttp` 异步下载
- 避免阻塞主线程

**批量操作**:

- 列表页提取时批量查找元素
- 图片下载时批量处理
- 减少网络请求次数

**缓存策略**:

- 浏览器会话保持，避免重复创建
- Page 实例复用，避免重复初始化
- 登录状态保持，减少登录检测

### 调试支持

**调试日志**:

- 支持输出到文件: `/Users/bing/Documents/AI-AD/.cursor/debug.log`
- JSON 格式，包含时间戳、位置、消息、数据
- 便于问题追踪和分析

**日志级别**:

- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

**调试工具**:

- 浏览器可视化模式（headless=False）
- 详细的错误堆栈信息
- 关键步骤的日志输出

---

## 总结

### 核心要点

1. **Playwright 主导架构**: 所有浏览器操作的基础都依赖 Playwright，确保页面实例持续可用

2. **弹层提取策略**: 小红书 PC 端必须从搜索结果页的弹层提取详情，不能直接打开 `/explore/` URL

3. **智能回退机制**: browser-use Agent 失败时自动回退到 Playwright 直接操作，确保流程不中断

4. **多选择器策略**: 所有元素查找都使用多个选择器，按优先级尝试，提高成功率

5. **宽松等待策略**: 使用多层回退的等待策略，避免网络超时导致失败

### 依赖关系总结

- **Playwright**: ✅ 必需，所有核心操作的基础
- **browser-use**: ⚠️ 备用，仅在特定情况下使用
- **LLMClient**: ✅ 必需，用于内容理解和结构化提取

### 关键问题解决方案

1. ✅ Page 实例获取失败 → Playwright 主导架构
2. ✅ 详情页 404 错误 → 弹层提取策略
3. ✅ 搜索框找不到 → 多选择器策略 + 直接导航备用
4. ✅ 弹层不出现 → 多选择器策略 + 重试机制
5. ✅ 登录状态丢失 → 使用系统 Chrome 浏览器
6. ✅ 协程检查错误 → 使用 `inspect` 模块
7. ✅ 网络超时 → 宽松等待策略 + 多层回退

### 最佳实践

1. **始终使用 Playwright 进行基础操作**
2. **使用多选择器策略提高成功率**
3. **实现智能回退机制，确保流程不中断**
4. **使用宽松的等待策略，避免超时**
5. **保持浏览器会话，减少重复初始化**
6. **记录详细的调试日志，便于问题追踪**

---

**文档版本**: v1.0  
**最后更新**: 2024-12  
**维护者**: AI-AD 项目组
