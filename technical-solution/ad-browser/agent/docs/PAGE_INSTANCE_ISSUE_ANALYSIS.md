# Page 实例获取失败问题分析

## 问题描述

在执行任务时，`BrowserAdapter` 无法从 `browser_use.Agent` 获取 Playwright `Page` 实例，导致后续操作失败。

### 错误信息

```
RuntimeWarning: coroutine 'Browser.get_playwright_browser' was never awaited
  await self._try_save_page(agent)

[BROWSER_ADAPTER_ERROR] Page 实例不存在，请先调用 open_page() 打开页面
```

## 问题根源分析

### 1. 协程检查逻辑错误

**位置**: `adapter.py` 第 196-202 行

**问题代码**:

```python
playwright_browser_fn = agent.browser.get_playwright_browser
if hasattr(playwright_browser_fn, "__await__"):
    playwright_browser = await playwright_browser_fn()
else:
    playwright_browser = playwright_browser_fn()
```

**问题分析**:

- `get_playwright_browser` 是一个**协程函数**（coroutine function），不是协程对象
- 协程函数本身没有 `__await__` 属性，只有调用后返回的协程对象才有
- 代码检查的是函数对象，而不是调用后的结果
- 因此 `hasattr(playwright_browser_fn, "__await__")` 返回 `False`，导致直接调用 `playwright_browser_fn()`，返回了一个协程对象但没有被 await

### 2. 执行流程问题

**执行顺序**:

1. `_default_runner()` 创建 Agent 并执行任务 ✅
2. Agent 成功打开页面 ✅
3. 调用 `await self._try_save_page(agent)` 尝试保存 page 实例
4. `_try_save_page()` 尝试多种方法获取 page，但都失败 ❌
5. `self._page` 仍然是 `None`
6. 后续 `search()` 方法检查 `self._page` 时失败 ❌

### 3. 根本原因

**核心问题**: `browser_use` 库的 API 可能已经变化，或者获取 page 实例的方式不正确。

从日志看：

- `agent.browser_context` 存在 ✅
- `agent.browser` 存在 ✅
- 但无法通过现有方法获取到 `page` 实例 ❌

可能的原因：

1. `browser_use` 版本更新，API 变化
2. page 实例的获取路径不正确
3. 需要在特定时机才能获取到 page 实例

## 解决方案建议

### 方案 1: 修复协程检查逻辑

使用 `inspect.iscoroutinefunction()` 来正确检查协程函数：

```python
import inspect

if hasattr(agent.browser, "get_playwright_browser"):
    try:
        playwright_browser_fn = agent.browser.get_playwright_browser
        if inspect.iscoroutinefunction(playwright_browser_fn):
            playwright_browser = await playwright_browser_fn()
        else:
            playwright_browser = playwright_browser_fn()
        # ... 后续处理
    except Exception as e:
        logger.debug(f"get_playwright_browser() 失败: {e}")
```

### 方案 2: 直接尝试 await（更安全）

无论是否是协程，都先尝试 await，如果失败再直接调用：

```python
if hasattr(agent.browser, "get_playwright_browser"):
    try:
        playwright_browser_fn = agent.browser.get_playwright_browser
        try:
            playwright_browser = await playwright_browser_fn()
        except TypeError:
            # 如果不是协程，直接调用
            playwright_browser = playwright_browser_fn()
        # ... 后续处理
    except Exception as e:
        logger.debug(f"get_playwright_browser() 失败: {e}")
```

### 方案 3: 检查 browser_use 源码，找到正确的获取方式

需要查看 `browser_use` 库的源码，确认：

1. Agent 执行后，page 实例存储在哪里
2. 正确的获取方式是什么
3. 是否有公开的 API 可以获取 page

### 方案 4: 使用 browser_use 的内部属性（临时方案）

如果其他方法都失败，可以尝试直接访问内部属性：

```python
# 尝试访问可能的内部属性
if hasattr(agent, "_page"):
    self._page = agent._page
elif hasattr(agent.browser_context, "_page"):
    self._page = agent.browser_context._page
elif hasattr(agent.browser, "_page"):
    self._page = agent.browser._page
```

## 修复完成 ✅

### 已实施的修复

1. **添加 `inspect` 模块导入**：用于正确检查协程函数
2. **修复协程检查逻辑**：

   - 使用 `inspect.iscoroutinefunction()` 检查协程函数
   - 使用 `inspect.iscoroutine()` 检查协程对象
   - 添加 try-except 备用方案，如果检查失败则直接尝试 await

3. **修复位置**：
   - `browser_context.get_page()` 的协程检查（第 145-161 行）
   - `browser.get_playwright_browser()` 的协程检查（第 197-224 行）

### 修复后的代码逻辑

```python
# 修复前（错误）
if hasattr(playwright_browser_fn, "__await__"):  # ❌ 检查函数对象
    playwright_browser = await playwright_browser_fn()
else:
    playwright_browser = playwright_browser_fn()  # ❌ 返回协程但没 await

# 修复后（正确）
if inspect.iscoroutinefunction(playwright_browser_fn):  # ✅ 检查协程函数
    playwright_browser = await playwright_browser_fn()
elif inspect.iscoroutine(playwright_browser_fn):  # ✅ 检查协程对象
    playwright_browser = await playwright_browser_fn
else:
    playwright_browser = playwright_browser_fn()
```

### 下一步验证

1. **运行测试**: 执行 `./run_direct_test.sh` 验证修复是否生效
2. **检查日志**: 确认不再出现 `coroutine was never awaited` 警告
3. **验证功能**: 确认 page 实例能够正确保存和使用

## 相关代码位置

- `adapter.py` 第 130-258 行: `_try_save_page()` 方法
- `adapter.py` 第 196-221 行: 通过 `browser.get_playwright_browser()` 获取 page（问题代码）
- `adapter.py` 第 122 行: 调用 `_try_save_page()` 的位置
- `adapter.py` 第 406-410 行: `search()` 方法检查 page 实例
