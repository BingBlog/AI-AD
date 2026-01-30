"""agent.extractor.list_parser

列表页解析器

职责：
- 解析列表页结构
- 提取列表项链接和基本信息
- 实现分页逻辑（符合 MVP 硬约束）
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from agent.browser.adapter import BrowserAdapter
from agent.config import settings
from agent.exceptions import BrowserAdapterException
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class ListParser:
    """列表页解析器"""

    def __init__(self, browser_adapter: BrowserAdapter):
        self.browser_adapter = browser_adapter

    async def parse_list_page(
        self,
        max_items: int = None,
        max_pages: int = None,
    ) -> List[Dict[str, Any]]:
        """
        解析列表页

        Args:
            max_items: 最大提取数量（默认使用配置值）
            max_pages: 最大页数（默认使用配置值）

        Returns:
            列表项信息列表，每个项包含：
            - title: 标题
            - url: 链接
            - description: 描述（可选）
            - preview_image: 预览图（可选）
        """
        max_items = max_items or settings.max_items
        max_pages = max_pages or settings.max_pages

        items: List[Dict[str, Any]] = []
        page_count = 0

        try:
            # 等待搜索结果页面加载完成
            import asyncio
            import json
            import time
            
            # 使用 Playwright 直接提取搜索结果（更可靠）
            page = self.browser_adapter._page
            if not page:
                logger.warning("Page 实例不存在")
                return items
            
            # 等待搜索结果加载
            await asyncio.sleep(3)  # 等待动态内容加载
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run4",
                        "hypothesisId": "D",
                        "location": "list_parser.py:60",
                        "message": "Before extracting search results",
                        "data": {
                            "currentUrl": page.url if page else "N/A"
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 尝试使用 Playwright 直接查找搜索结果元素
            # 根据实际HTML结构：section.note-item 包含链接和标题
            found_items = []
            try:
                # 查找所有 note-item 卡片
                note_items = await page.query_selector_all('section.note-item')
                
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run4",
                            "hypothesisId": "F",
                            "location": "list_parser.py:90",
                            "message": "Found note-item sections",
                            "data": {
                                "noteItemCount": len(note_items)
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                
                for idx, note_item in enumerate(note_items[:max_items]):  # 限制数量
                    try:
                        # 在 note-item 中查找链接
                        # 优先查找 /explore/ 链接，如果没有则查找 /search_result/ 链接
                        href = None
                        link_elem = await note_item.query_selector('a[href*="/explore/"]')
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                        else:
                            link_elem = await note_item.query_selector('a[href*="/search_result/"]')
                            if link_elem:
                                href = await link_elem.get_attribute('href')
                                # 从 /search_result/xxx 提取 note_id，转换为 /explore/xxx
                                if href and '/search_result/' in href:
                                    import re
                                    match = re.search(r'/search_result/([^/?]+)', href)
                                    if match:
                                        note_id = match.group(1)
                                        href = f"/explore/{note_id}"
                        
                        if not href:
                            continue
                        
                        # 构建完整URL
                        if href.startswith('/'):
                            href = f"https://www.xiaohongshu.com{href}"
                        
                        # 查找标题：a.title > span
                        title = ""
                        try:
                            title_elem = await note_item.query_selector('a.title span')
                            if title_elem:
                                title = await title_elem.inner_text()
                                title = title.strip() if title else ""
                            
                            # 如果没找到，尝试直接查找 a.title
                            if not title:
                                title_elem = await note_item.query_selector('a.title')
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    title = title.strip() if title else ""
                        except Exception:
                            pass
                        
                        # #region debug log - item extraction
                        if idx < 3:  # 只记录前3个元素
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run4",
                                        "hypothesisId": "F",
                                        "location": "list_parser.py:140",
                                        "message": "Extracted item",
                                        "data": {
                                            "itemIndex": idx,
                                            "href": href,
                                            "title": title[:100] if title else "",
                                            "titleLength": len(title) if title else 0
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                        # #endregion
                        
                        if href:
                            found_items.append({
                                "title": title[:200] if title else "未命名",
                                "url": href,
                                "description": "",
                                "preview_image": ""
                            })
                    except Exception as e:
                        # #region debug log - item processing error
                        if idx < 3:
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run4",
                                        "hypothesisId": "F",
                                        "location": "list_parser.py:170",
                                        "message": "Item processing error",
                                        "data": {
                                            "itemIndex": idx,
                                            "error": str(e)[:200]
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                        # #endregion
                        continue
            except Exception as e:
                # #region debug log - note-item query error
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run4",
                            "hypothesisId": "F",
                            "location": "list_parser.py:185",
                            "message": "Note-item query error",
                            "data": {
                                "error": str(e)[:200]
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                pass
            
            # 如果直接查找失败，回退到 extract() 方法
            if not found_items:
                logger.info("直接查找失败，回退到 extract() 方法")
                result = await self.browser_adapter.extract(
                    "提取所有搜索结果列表项，包括标题、链接、预览图URL。"
                    "返回 JSON 数组格式，每个对象包含：title（标题）、url（链接）、description（描述，可选）、preview_image（预览图URL，可选）。"
                )
                
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run4",
                            "hypothesisId": "D",
                            "location": "list_parser.py:175",
                            "message": "After calling extract() (fallback)",
                            "data": {
                                "extractSuccess": result.get("success"),
                                "extractError": result.get("error"),
                                "extractTextLength": len(result.get("content", {}).get("text", "")) if result.get("content") else 0,
                                "extractTextPreview": result.get("content", {}).get("text", "")[:200] if result.get("content") else ""
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion

                if not result.get("success"):
                    logger.warning(f"列表页提取失败: {result.get('error')}")
                    return items

                # 解析提取结果
                page_items = self._parse_items(result["content"]["text"])
            else:
                # 使用直接找到的项
                page_items = found_items
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run4",
                            "hypothesisId": "D",
                            "location": "list_parser.py:200",
                            "message": "Using directly found items",
                            "data": {
                                "foundItemsCount": len(found_items),
                                "foundItems": found_items[:3]  # 只记录前3个
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run4",
                        "hypothesisId": "D",
                        "location": "list_parser.py:95",
                        "message": "After parsing items",
                        "data": {
                            "parsedItemsCount": len(page_items),
                            "parsedItems": page_items[:3] if page_items else []  # 只记录前3个
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            items.extend(page_items)
            page_count += 1

            # 如果还需要更多项且未达到最大页数，尝试翻页
            while len(items) < max_items and page_count < max_pages:
                # 尝试滚动或翻页
                scroll_result = await self.browser_adapter.scroll(times=2)
                if not scroll_result.get("success"):
                    logger.warning("滚动失败，停止翻页")
                    break

                # 再次提取
                result = await self.browser_adapter.extract(
                    "提取当前页面可见的所有搜索结果列表项，包括标题、链接。"
                    "返回 JSON 数组格式。"
                )

                if not result.get("success"):
                    break

                new_items = self._parse_items(result["content"]["text"])
                # 去重（基于 URL）
                existing_urls = {item.get("url") for item in items}
                new_items = [item for item in new_items if item.get("url") not in existing_urls]

                if not new_items:
                    logger.info("没有新项，停止翻页")
                    break

                items.extend(new_items)
                page_count += 1

            # 限制数量
            return items[:max_items]

        except BrowserAdapterException:
            raise
        except Exception as e:
            logger.error(f"列表页解析异常: {e}")
            # 返回已提取的项，不抛出异常（符合第 15 节策略）
            return items

    def _parse_items(self, text: str) -> List[Dict[str, Any]]:
        """
        解析提取的文本，提取列表项

        Args:
            text: Browser-Use 提取的文本内容

        Returns:
            列表项列表
        """
        # #region debug log
        import json as json_module
        import time
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json_module.dumps({
                    "sessionId": "debug-session",
                    "runId": "run4",
                    "hypothesisId": "D",
                    "location": "list_parser.py:111",
                    "message": "_parse_items() called",
                    "data": {
                        "textLength": len(text) if text else 0,
                        "textPreview": text[:500] if text else ""
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        if not text:
            return []

        items: List[Dict[str, Any]] = []

        try:
            # 尝试解析 JSON 数组
            data = json.loads(text)
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json_module.dumps({
                        "sessionId": "debug-session",
                        "runId": "run4",
                        "hypothesisId": "D",
                        "location": "list_parser.py:130",
                        "message": "JSON parsed successfully",
                        "data": {
                            "isList": isinstance(data, list),
                            "dataType": type(data).__name__,
                            "dataLength": len(data) if isinstance(data, (list, dict)) else 0
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("url"):
                        items.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "description": item.get("description", ""),
                            "preview_image": item.get("preview_image", ""),
                        })
                return items
        except (json.JSONDecodeError, ValueError) as e:
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json_module.dumps({
                        "sessionId": "debug-session",
                        "runId": "run4",
                        "hypothesisId": "D",
                        "location": "list_parser.py:145",
                        "message": "JSON parse failed, trying regex",
                        "data": {
                            "error": str(e)
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            pass

        # 如果 JSON 解析失败，尝试正则提取 URL 和标题
        # 这是一个容错策略
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)

        for url in urls[:10]:  # 限制数量
            # 尝试从 URL 附近提取标题
            url_pos = text.find(url)
            if url_pos > 0:
                # 提取 URL 前 100 个字符作为可能的标题
                title_candidate = text[max(0, url_pos - 100):url_pos].strip()
                # 取最后一行或最后一段作为标题
                title = title_candidate.split("\n")[-1].strip()[:100]
            else:
                title = ""

            items.append({
                "title": title or "未命名",
                "url": url,
                "description": "",
                "preview_image": "",
            })

        return items
