"""agent.extractor.detail_parser

详情页解析器

职责：
- 解析详情页内容
- 提取结构化数据
- 调用 LLM 进行提取
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import aiohttp

from agent.browser.adapter import BrowserAdapter
from agent.exceptions import BrowserAdapterException, LLMException
from agent.llm.client import LLMClient
from agent.models.case_schema import MarketingCase
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class DetailParser:
    """详情页解析器"""

    def __init__(
        self,
        browser_adapter: BrowserAdapter,
        llm_client: LLMClient,
    ):
        self.browser_adapter = browser_adapter
        self.llm_client = llm_client

    async def parse_detail_page(
        self,
        url: str,
        platform: str = "xiaohongshu",
    ) -> MarketingCase:
        """
        解析详情页并提取结构化信息
        
        对于小红书PC端，如果当前在搜索结果页，会点击标题打开弹层并从弹层提取信息。
        否则，尝试直接打开详情页URL。

        Args:
            url: 详情页 URL
            platform: 平台名称（用于填充 MarketingCase.platform）

        Returns:
            MarketingCase 对象

        Raises:
            BrowserAdapterException: 浏览器操作失败
            LLMException: LLM 提取失败
        """
        try:
            # 获取 Playwright page 实例
            page = self._get_page()
            if not page:
                raise BrowserAdapterException(
                    "无法获取 Page 实例",
                    action="parse_detail",
                    url=url,
                )
            
            current_url = page.url
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run5",
                        "hypothesisId": "G",
                        "location": "detail_parser.py:60",
                        "message": "Starting detail page parsing",
                        "data": {
                            "targetUrl": url,
                            "currentUrl": current_url,
                            "isSearchResultPage": "search_result" in current_url
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 对于小红书，必须从搜索结果页的弹层提取，不能直接打开 /explore/ URL（会导致404）
            if platform == "xiaohongshu":
                # 检查是否在搜索结果页
                if "search_result" not in current_url:
                    logger.warning(f"当前不在搜索结果页，无法提取详情: {url}, 当前URL: {current_url}")
                    # 返回最小化案例，避免尝试打开会导致404的URL
                    return MarketingCase(
                        platform=platform,
                        brand="",
                        theme="",
                        creative_type="",
                        strategy=[],
                        insights=[],
                        source_url=url,
                        title=None,
                    )
                
                # 在搜索结果页，点击标题打开弹层
                try:
                    modal_data = await self._extract_from_modal(page, url)
                    if modal_data and modal_data.get("content") and len(modal_data["content"].strip()) > 10:
                        content = modal_data["content"]
                        title = modal_data.get("title")
                        images = modal_data.get("images", [])
                        # #region debug log
                        try:
                            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "run5",
                                    "hypothesisId": "G",
                                    "location": "detail_parser.py:115",
                                    "message": "Successfully extracted from modal",
                                    "data": {
                                        "contentLength": len(content),
                                        "contentPreview": content[:200],
                                        "title": title,
                                        "imagesCount": len(images)
                                    },
                                    "timestamp": int(time.time() * 1000)
                                }) + '\n')
                        except Exception:
                            pass
                        # #endregion
                        case = await self._extract_case_from_content(content, url, platform, title=title)
                        # 将图片信息保存到案例中（可以通过扩展 MarketingCase 模型或记录日志）
                        if images:
                            logger.info(f"案例包含 {len(images)} 张图片: {url}")
                        return case
                    else:
                        logger.warning(f"从弹层提取的内容为空或过短: {url}")
                        return MarketingCase(
                            platform=platform,
                            brand="",
                            theme="",
                            creative_type="",
                            strategy=[],
                            insights=[],
                            source_url=url,
                            title=None,
                        )
                except Exception as e:
                    logger.error(f"从弹层提取失败: {e}, URL: {url}")
                    # 返回最小化案例，避免尝试打开会导致404的URL
                    return MarketingCase(
                        platform=platform,
                        brand="",
                        theme="",
                        creative_type="",
                        strategy=[],
                        insights=[],
                        source_url=url,
                        title=None,
                    )
            else:
                # 其他平台，使用传统方式打开详情页
                open_result = await self.browser_adapter.open_page(url)
            if not open_result.get("success"):
                raise BrowserAdapterException(
                    f"打开详情页失败: {open_result.get('error')}",
                    action="open_page",
                    url=url,
                )

                # 提取页面内容
            extract_result = await self.browser_adapter.extract(
                "提取页面主要内容，包括标题、正文、图片、视频等所有可见内容。"
                "尽量提取完整的文本内容。"
            )

            if not extract_result.get("success"):
                raise BrowserAdapterException(
                    f"提取页面内容失败: {extract_result.get('error')}",
                    action="extract",
                    url=url,
                )

                content = extract_result["content"]["text"]
                return await self._extract_case_from_content(content, url, platform)

        except BrowserAdapterException:
            raise
        except Exception as e:
            logger.error(f"详情页解析异常: {e}, URL: {url}")
            raise BrowserAdapterException(
                f"详情页解析失败: {e}",
                action="parse_detail",
                url=url,
            )
    
    def _get_page(self):
        """获取 Playwright Page 实例"""
        # 通过反射访问私有属性 _page
        if hasattr(self.browser_adapter, '_page'):
            return self.browser_adapter._page
        return None
    
    async def _extract_from_modal(self, page, url: str) -> Optional[dict]:
        """
        从弹层提取内容
        
        Args:
            page: Playwright Page 实例
            url: 目标URL（用于匹配对应的标题链接）
        
        Returns:
            包含 'title' 和 'content' 的字典，如果失败返回 None
        """
        # #region debug log - function entry
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run5",
                    "hypothesisId": "L",
                    "location": "detail_parser.py:198",
                    "message": "_extract_from_modal called",
                    "data": {
                        "url": url,
                        "pageExists": page is not None
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        try:
            # 从URL提取 note_id
            note_id = None
            if '/explore/' in url:
                match = re.search(r'/explore/([^/?]+)', url)
                if match:
                    note_id = match.group(1)
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run5",
                        "hypothesisId": "G",
                        "location": "detail_parser.py:240",
                        "message": "Looking for title link to click",
                        "data": {
                            "noteId": note_id,
                            "url": url
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 查找对应的标题链接（a.title）
            # 注意：a.title 可能没有 href 属性，但点击它可以打开弹层
            title_link = None
            if note_id:
                # 先滚动页面，确保所有内容都加载
                try:
                    # 滚动到页面底部，触发懒加载
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(1)
                    # 滚动回顶部
                    await page.evaluate('window.scrollTo(0, 0)')
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
                
                # 策略：在 section.note-item 中查找包含 note_id 的链接（包括隐藏的），然后找到对应的 a.title
                note_items = await page.query_selector_all('section.note-item')
                
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "H",
                            "location": "detail_parser.py:240",
                            "message": "Searching for note-item with matching note_id",
                            "data": {
                                "noteId": note_id,
                                "totalNoteItems": len(note_items)
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                
                # 如果第一次查找没找到，尝试滚动页面并重新查找
                max_retries = 2
                for retry in range(max_retries):
                    if retry > 0:
                        # 滚动页面，触发更多内容加载
                        try:
                            await page.evaluate('window.scrollBy(0, 500)')
                            await asyncio.sleep(1)
                            # 重新获取所有 note-items
                            note_items = await page.query_selector_all('section.note-item')
                            
                            # #region debug log - retry
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run5",
                                        "hypothesisId": "M",
                                        "location": "detail_parser.py:295",
                                        "message": "Retrying after scroll",
                                        "data": {
                                            "retry": retry,
                                            "noteId": note_id,
                                            "totalNoteItems": len(note_items)
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                            # #endregion
                        except Exception:
                            break
                    
                    for idx, item in enumerate(note_items):
                        try:
                            # 查找所有链接（包括隐藏的）
                            all_links = await item.query_selector_all('a')
                            found_matching_link = False
                            
                            for link in all_links:
                                try:
                                    href = await link.get_attribute('href')
                                    if href and note_id in href:
                                        # 找到匹配的链接
                                        found_matching_link = True
                                        
                                        # #region debug log
                                        if idx < 3:  # 只记录前3个
                                            try:
                                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                                    f.write(json.dumps({
                                                        "sessionId": "debug-session",
                                                        "runId": "run5",
                                                        "hypothesisId": "H",
                                                        "location": "detail_parser.py:338",
                                                        "message": "Found matching link in note-item",
                                                        "data": {
                                                            "itemIndex": idx,
                                                            "href": href,
                                                            "noteId": note_id
                                                        },
                                                        "timestamp": int(time.time() * 1000)
                                                    }) + '\n')
                                            except Exception:
                                                pass
                                        # #endregion
                                        
                                        # 找到匹配的链接，获取对应的 a.title
                                        title_elem = await item.query_selector('a.title')
                                        if title_elem:
                                            title_link = title_elem
                                            
                                            # #region debug log
                                            try:
                                                title_text = await title_elem.inner_text()
                                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                                    f.write(json.dumps({
                                                        "sessionId": "debug-session",
                                                        "runId": "run5",
                                                        "hypothesisId": "H",
                                                        "location": "detail_parser.py:360",
                                                        "message": "Found title link to click",
                                                        "data": {
                                                            "itemIndex": idx,
                                                            "titleText": title_text[:50] if title_text else None,
                                                            "noteId": note_id
                                                        },
                                                        "timestamp": int(time.time() * 1000)
                                                    }) + '\n')
                                            except Exception:
                                                pass
                                            # #endregion
                                            
                                            break
                                except Exception:
                                    continue
                            
                            if title_link:
                                break
                        except Exception as e:
                            # #region debug log
                            if idx < 3:
                                try:
                                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                        f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run5",
                                        "hypothesisId": "H",
                                        "location": "detail_parser.py:300",
                                        "message": "Error processing note-item",
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
                    
                    # 如果找到了 title_link，跳出 retry 循环
                    if title_link:
                        break
            
            if not title_link:
                logger.warning(f"未找到对应的标题链接: {url}, note_id: {note_id}")
                # #region debug log - 详细调试信息
                try:
                    # 记录所有 note-item 中的链接信息
                    note_items = await page.query_selector_all('section.note-item')
                    debug_info = {
                        "targetNoteId": note_id,
                        "targetUrl": url,
                        "totalNoteItems": len(note_items),
                        "foundNoteIds": [],  # 记录所有找到的 note_id
                        "noteItemsInfo": []
                    }
                    
                    # 先收集所有找到的 note_id
                    for item in note_items:
                        try:
                            all_links = await item.query_selector_all('a')
                            for link in all_links:
                                try:
                                    href = await link.get_attribute('href')
                                    if href and '/explore/' in href:
                                        # 提取 note_id
                                        match = re.search(r'/explore/([^/?]+)', href)
                                        if match:
                                            found_note_id = match.group(1)
                                            if found_note_id not in debug_info["foundNoteIds"]:
                                                debug_info["foundNoteIds"].append(found_note_id)
                                except Exception:
                                    continue
                        except Exception:
                            continue
                    
                    for idx, item in enumerate(note_items[:3]):  # 只记录前3个
                        try:
                            # 查找所有链接
                            all_links = await item.query_selector_all('a')
                            links_info = []
                            for link in all_links:
                                try:
                                    href = await link.get_attribute('href')
                                    class_name = await link.get_attribute('class')
                                    is_visible = await link.is_visible()
                                    links_info.append({
                                        "href": href,
                                        "class": class_name,
                                        "visible": is_visible
                                    })
                                except Exception:
                                    pass
                            
                            # 查找 a.title
                            title_elem = await item.query_selector('a.title')
                            title_info = None
                            if title_elem:
                                try:
                                    title_href = await title_elem.get_attribute('href')
                                    title_text = await title_elem.inner_text()
                                    title_info = {
                                        "href": title_href,
                                        "text": title_text[:50] if title_text else None,
                                        "visible": await title_elem.is_visible()
                                    }
                                except Exception:
                                    pass
                            
                            debug_info["noteItemsInfo"].append({
                                "index": idx,
                                "links": links_info,
                                "title": title_info
                            })
                        except Exception:
                            pass
                    
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "G",
                            "location": "detail_parser.py:300",
                            "message": "Title link not found - detailed debug",
                            "data": debug_info,
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception as e:
                    try:
                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run5",
                                "hypothesisId": "G",
                                "location": "detail_parser.py:320",
                                "message": "Debug log error",
                                "data": {"error": str(e)[:200]},
                                "timestamp": int(time.time() * 1000)
                            }) + '\n')
                    except Exception:
                        pass
                # #endregion
                return None
            
            # #region debug log - before clicking
            try:
                title_text = await title_link.inner_text()
                title_href = await title_link.get_attribute('href')
                is_visible = await title_link.is_visible()
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run5",
                        "hypothesisId": "H",
                        "location": "detail_parser.py:430",
                        "message": "Found title link, about to click",
                        "data": {
                            "href": title_href,
                            "text": title_text[:50] if title_text else None,
                            "visible": is_visible,
                            "noteId": note_id
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 点击标题链接（使用 JavaScript 点击，更可靠）
            try:
                # 先滚动到元素可见
                await title_link.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                
                # 使用 JavaScript 点击，更可靠
                await title_link.evaluate('el => el.click()')
                
                # #region debug log - after clicking
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "H",
                            "location": "detail_parser.py:455",
                            "message": "Clicked title link",
                            "data": {
                                "noteId": note_id
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                
                # 等待弹层出现（使用多个选择器）
                await asyncio.sleep(2)  # 先等待一下，让弹层有时间打开
                
                # 尝试多个弹层选择器（根据实际HTML结构，优先使用遮罩层和弹层容器）
                modal_selectors = [
                    '.note-detail-mask',  # 遮罩层（最外层）
                    '#noteContainer',  # 弹层容器（ID选择器）
                    '.note-container',  # 弹层容器（类选择器）
                    '[id="noteContainer"]',  # 弹层容器（属性选择器）
                    '.note-detail-container',
                    '.detail-modal',
                    '.modal-container',
                    '[class*="modal"]',
                    '[class*="note-detail"]'
                ]
                
                modal_elem = None
                modal_selector_used = None
                
                for selector in modal_selectors:
                    try:
                        # 等待弹层出现
                        await page.wait_for_selector(selector, timeout=3000, state='visible')
                        modal_elem = await page.query_selector(selector)
                        if modal_elem:
                            modal_visible = await modal_elem.is_visible()
                            
                            # #region debug log - checking modal
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run5",
                                        "hypothesisId": "K",
                                        "location": "detail_parser.py:525",
                                        "message": "Checking modal element",
                                        "data": {
                                            "selector": selector,
                                            "modalExists": modal_elem is not None,
                                            "modalVisible": modal_visible,
                                            "noteId": note_id
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                            # #endregion
                            
                            if modal_visible:
                                modal_selector_used = selector
                                
                                # 如果是遮罩层，尝试找到内部的弹层容器
                                if selector == '.note-detail-mask':
                                    container_elem = await modal_elem.query_selector('#noteContainer, .note-container')
                                    if container_elem:
                                        modal_elem = container_elem
                                
                                # #region debug log - modal appeared
                                try:
                                    # 获取弹层的详细信息
                                    bounding_box = await modal_elem.bounding_box()
                                    modal_text_preview = await modal_elem.inner_text()
                                    modal_text_preview = modal_text_preview[:200] if modal_text_preview else ""
                                    
                                    # 检查标题和描述是否存在
                                    title_elem = await page.query_selector('#detail-title')
                                    desc_elem = await page.query_selector('#detail-desc')
                                    
                                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                        f.write(json.dumps({
                                            "sessionId": "debug-session",
                                            "runId": "run5",
                                            "hypothesisId": "K",
                                            "location": "detail_parser.py:560",
                                            "message": "Modal appeared after click - detailed",
                                            "data": {
                                                "modalExists": True,
                                                "modalVisible": True,
                                                "selector": modal_selector_used,
                                                "boundingBox": bounding_box,
                                                "textPreview": modal_text_preview[:200],
                                                "titleExists": title_elem is not None,
                                                "descExists": desc_elem is not None,
                                                "noteId": note_id
                                            },
                                            "timestamp": int(time.time() * 1000)
                                        }) + '\n')
                                except Exception as e:
                                    try:
                                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                            f.write(json.dumps({
                                                "sessionId": "debug-session",
                                                "runId": "run5",
                                                "hypothesisId": "K",
                                                "location": "detail_parser.py:585",
                                                "message": "Modal debug info error",
                                                "data": {
                                                    "error": str(e)[:200],
                                                    "selector": selector
                                                },
                                                "timestamp": int(time.time() * 1000)
                                            }) + '\n')
                                    except Exception:
                                        pass
                                # #endregion
                                break
                    except Exception as e:
                        # #region debug log - selector failed
                        try:
                            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "run5",
                                    "hypothesisId": "K",
                                    "location": "detail_parser.py:595",
                                    "message": "Modal selector failed",
                                    "data": {
                                        "selector": selector,
                                        "error": str(e)[:200],
                                        "noteId": note_id
                                    },
                                    "timestamp": int(time.time() * 1000)
                                }) + '\n')
                        except Exception:
                            pass
                        # #endregion
                        continue
                
                # 如果没找到弹层，记录所有尝试的选择器
                if not modal_elem:
                    # #region debug log - modal not found
                    try:
                        # 检查页面中是否有任何弹层相关的元素
                        all_modals = await page.query_selector_all('[class*="modal"], [id*="modal"], [class*="overlay"], [class*="dialog"]')
                        modal_info = []
                        for idx, elem in enumerate(all_modals[:5]):  # 只检查前5个
                            try:
                                is_visible = await elem.is_visible()
                                tag_name = await elem.evaluate('el => el.tagName')
                                class_name = await elem.get_attribute('class')
                                elem_id = await elem.get_attribute('id')
                                modal_info.append({
                                    "index": idx,
                                    "tagName": tag_name,
                                    "class": class_name,
                                    "id": elem_id,
                                    "visible": is_visible
                                })
                            except Exception:
                                pass
                        
                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run5",
                                "hypothesisId": "J",
                                "location": "detail_parser.py:560",
                                "message": "Modal not found - checking all modal-like elements",
                                "data": {
                                    "triedSelectors": modal_selectors,
                                    "foundModalLikeElements": modal_info,
                                    "totalModalLikeElements": len(all_modals),
                                    "noteId": note_id
                                },
                                "timestamp": int(time.time() * 1000)
                            }) + '\n')
                    except Exception:
                        pass
                    # #endregion
                
                # 如果没找到弹层，记录错误并返回
                if not modal_elem:
                    logger.warning(f"点击后弹层未出现: {url}")
                    # #region debug log - modal not found after all attempts
                    try:
                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run5",
                                "hypothesisId": "J",
                                "location": "detail_parser.py:620",
                                "message": "Modal not found after all attempts",
                                "data": {
                                    "triedSelectors": modal_selectors,
                                    "noteId": note_id,
                                    "url": url
                                },
                                "timestamp": int(time.time() * 1000)
                            }) + '\n')
                    except Exception:
                        pass
                    # #endregion
                    return None
                
                # 弹层找到了，延长打开时间让用户能看到（等待3秒）
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"点击标题链接失败: {e}")
                # #region debug log - click error
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "H",
                            "location": "detail_parser.py:515",
                            "message": "Click error",
                            "data": {
                                "error": str(e)[:200],
                                "noteId": note_id
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                return None
            
            # 从弹层提取内容
            # 等待弹层内容完全加载
            await asyncio.sleep(1)
            
            content_parts = []
            extracted_title = None  # 保存提取的标题
            
            # 提取标题
            try:
                title_elem = await page.query_selector('#detail-title')
                if title_elem:
                    title_text = await title_elem.inner_text()
                    if title_text:
                        extracted_title = title_text.strip()  # 保存标题
                        content_parts.append(f"标题: {extracted_title}")
                        
                        # #region debug log
                        try:
                            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "run5",
                                    "hypothesisId": "I",
                                    "location": "detail_parser.py:570",
                                    "message": "Extracted title from modal",
                                    "data": {
                                        "titleLength": len(title_text),
                                        "titlePreview": title_text[:100]
                                    },
                                    "timestamp": int(time.time() * 1000)
                                }) + '\n')
                        except Exception:
                            pass
                        # #endregion
            except Exception as e:
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "I",
                            "location": "detail_parser.py:585",
                            "message": "Title extraction error",
                            "data": {
                                "error": str(e)[:200]
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                pass
            
            # 提取描述（尝试多个选择器）- 提取所有文字内容，包括标签文本
            desc_text = None
            desc_selectors = [
                '#detail-desc',
                '[id="detail-desc"]',
                '.note-content .desc',
                '.note-content',
                '.desc',
            ]
            
            for desc_sel in desc_selectors:
                try:
                    desc_elem = await page.query_selector(desc_sel)
                    if desc_elem:
                        # 使用 inner_text() 获取所有可见文本（包括标签文本）
                        desc_text = await desc_elem.inner_text()
                        if desc_text and len(desc_text.strip()) > 10:  # 至少10个字符
                            # #region debug log
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run5",
                                        "hypothesisId": "I",
                                        "location": "detail_parser.py:610",
                                        "message": "Extracted description from modal",
                                        "data": {
                                            "selector": desc_sel,
                                            "descLength": len(desc_text),
                                            "descPreview": desc_text[:200]
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                            # #endregion
                            break
                except Exception:
                    continue
            
            if desc_text:
                # 清理文本：移除多余的空白字符，但保留换行
                cleaned_text = re.sub(r'\s+', ' ', desc_text.strip())
                content_parts.append(f"正文: {cleaned_text}")
            else:
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "I",
                            "location": "detail_parser.py:630",
                            "message": "Description not found",
                            "data": {
                                "triedSelectors": desc_selectors
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
            
            # 提取作者信息
            try:
                author_elem = await page.query_selector('.author .username')
                if author_elem:
                    author_text = await author_elem.inner_text()
                    if author_text:
                        content_parts.append(f"作者: {author_text.strip()}")
            except Exception:
                pass
            
            # 提取并下载所有图片
            downloaded_images = []
            try:
                image_urls = await self._extract_images_from_modal(page)
                if image_urls:
                    downloaded_images = await self._download_images(image_urls, url)
                    if downloaded_images:
                        content_parts.append(f"图片: 已下载 {len(downloaded_images)} 张图片")
                        logger.info(f"成功下载 {len(downloaded_images)} 张图片: {url}")
            except Exception as e:
                logger.warning(f"图片提取或下载失败: {e}, URL: {url}")
            
            # 如果主要内容都提取到了，关闭弹层
            if content_parts:
                # #region debug log - before closing modal
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run5",
                            "hypothesisId": "J",
                            "location": "detail_parser.py:790",
                            "message": "About to close modal",
                            "data": {
                                "contentPartsCount": len(content_parts),
                                "contentPreview": "\n\n".join(content_parts)[:200] if content_parts else "",
                                "noteId": note_id
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                
                # 延长弹层打开时间，让用户能看到（再等待2秒）
                await asyncio.sleep(2)
                
                try:
                    # 按 ESC 键关闭弹层
                    await page.keyboard.press('Escape')
                    await asyncio.sleep(0.5)
                    
                    # #region debug log - after closing modal
                    try:
                        # 检查弹层是否真的关闭了（检查遮罩层和弹层容器）
                        mask_still_exists = await page.query_selector('.note-detail-mask')
                        container_still_exists = await page.query_selector('#noteContainer, .note-container')
                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run5",
                                "hypothesisId": "K",
                                "location": "detail_parser.py:875",
                                "message": "Modal closed",
                                "data": {
                                    "maskStillExists": mask_still_exists is not None,
                                    "containerStillExists": container_still_exists is not None,
                                    "noteId": note_id
                                },
                                "timestamp": int(time.time() * 1000)
                            }) + '\n')
                    except Exception:
                        pass
                    # #endregion
                except Exception as e:
                    # #region debug log - close modal error
                    try:
                        with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run5",
                                "hypothesisId": "J",
                                "location": "detail_parser.py:825",
                                "message": "Close modal error",
                                "data": {
                                    "error": str(e)[:200],
                                    "noteId": note_id
                                },
                                "timestamp": int(time.time() * 1000)
                            }) + '\n')
                    except Exception:
                        pass
                    # #endregion
                    pass
            
            content = "\n\n".join(content_parts)
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run5",
                        "hypothesisId": "G",
                        "location": "detail_parser.py:250",
                        "message": "Extracted content from modal",
                        "data": {
                            "contentLength": len(content),
                            "contentPreview": content[:200],
                            "partsCount": len(content_parts)
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            if content.strip():
                return {
                    "title": extracted_title,
                    "content": content,
                    "images": downloaded_images
                }
            return None
            
        except Exception as e:
            logger.error(f"从弹层提取失败: {e}")
            # #region debug log - extract from modal exception
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run5",
                        "hypothesisId": "L",
                        "location": "detail_parser.py:959",
                        "message": "_extract_from_modal exception",
                        "data": {
                            "error": str(e),
                            "errorType": type(e).__name__,
                            "url": url
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            # 尝试关闭弹层
            try:
                page = self._get_page()
                if page:
                    await page.keyboard.press('Escape')
            except Exception:
                pass
            return None
    
    async def _extract_images_from_modal(self, page) -> List[str]:
        """
        从弹层中提取所有图片 URL
        
        Args:
            page: Playwright Page 实例
        
        Returns:
            图片 URL 列表
        """
        image_urls = []
        try:
            # 查找所有 img-container 中的图片
            # 图片在 .img-container > .note-slider-img > img 中
            img_containers = await page.query_selector_all('.img-container')
            
            for container in img_containers:
                try:
                    # 在 img-container 中查找 img 标签
                    img_elem = await container.query_selector('img')
                    if img_elem:
                        img_src = await img_elem.get_attribute('src')
                        if img_src and img_src.startswith('http'):
                            # 去重
                            if img_src not in image_urls:
                                image_urls.append(img_src)
                except Exception:
                    continue
            
            # 如果没找到，尝试直接查找所有 img 标签（在弹层内）
            if not image_urls:
                try:
                    # 在弹层容器内查找所有图片
                    modal_container = await page.query_selector('#noteContainer, .note-container')
                    if modal_container:
                        all_imgs = await modal_container.query_selector_all('img')
                        for img in all_imgs:
                            try:
                                img_src = await img.get_attribute('src')
                                if img_src and img_src.startswith('http'):
                                    # 排除表情图片（通常包含 emoji 或 fe-platform）
                                    if 'emoji' not in img_src.lower() and 'fe-platform' not in img_src:
                                        if img_src not in image_urls:
                                            image_urls.append(img_src)
                            except Exception:
                                continue
                except Exception:
                    pass
            
            logger.info(f"从弹层提取到 {len(image_urls)} 张图片")
        except Exception as e:
            logger.warning(f"提取图片 URL 失败: {e}")
        
        return image_urls
    
    async def _download_images(self, image_urls: List[str], source_url: str) -> List[str]:
        """
        下载图片到本地
        
        Args:
            image_urls: 图片 URL 列表
            source_url: 来源 URL（用于生成保存目录）
        
        Returns:
            已下载图片的本地路径列表
        """
        if not image_urls:
            return []
        
        # 创建保存目录
        # 从 source_url 提取 note_id 作为目录名
        note_id = None
        if '/explore/' in source_url:
            match = re.search(r'/explore/([^/?]+)', source_url)
            if match:
                note_id = match.group(1)
        
        if not note_id:
            # 使用时间戳作为目录名
            note_id = f"note_{int(time.time())}"
        
        # 保存目录：data/images/{note_id}/
        base_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'images' / note_id
        base_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_paths = []
        
        async with aiohttp.ClientSession() as session:
            for idx, img_url in enumerate(image_urls):
                try:
                    # 获取图片扩展名
                    parsed_url = urlparse(img_url)
                    path = parsed_url.path
                    ext = 'jpg'  # 默认扩展名
                    
                    if '.' in path:
                        ext = path.split('.')[-1].lower()
                        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            ext = 'jpg'
                    
                    # 生成文件名
                    filename = f"image_{idx + 1}.{ext}"
                    file_path = base_dir / filename
                    
                    # 下载图片
                    async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            file_path.write_bytes(image_data)
                            downloaded_paths.append(str(file_path))
                            logger.debug(f"下载图片成功: {img_url} -> {file_path}")
                        else:
                            logger.warning(f"下载图片失败: HTTP {response.status}, URL: {img_url}")
                
                except Exception as e:
                    logger.warning(f"下载图片异常: {e}, URL: {img_url}")
                    continue
        
        return downloaded_paths
    
    async def _extract_case_from_content(self, content: str, url: str, platform: str, title: Optional[str] = None) -> MarketingCase:
        """从内容提取案例信息"""
        if not content or len(content.strip()) < 10:
            logger.warning(f"页面内容过短: {url}")
            # 返回最小化的案例
            return MarketingCase(
                    platform=platform,
                    brand="",
                    theme="",
                    creative_type="",
                    strategy=[],
                    insights=[],
                    source_url=url,
                    title=title,
                )

        # 使用 LLM 提取结构化信息
        try:
            case = await self.llm_client.extract_marketing_case(
                content, platform=platform, source_url=url
            )
            # 如果提取到了 title，设置它
            if title and not case.title:
                case.title = title
            return case
        except LLMException as e:
            logger.error(f"LLM 提取失败: {e}, URL: {url}")
            # 重试一次（符合第 15 节：最多重试 1 次）
            try:
                case = await self.llm_client.extract_marketing_case(
                    content, platform=platform, source_url=url
                )
                # 如果提取到了 title，设置它
                if title and not case.title:
                    case.title = title
                return case
            except Exception:
                # 重试失败，返回最小化案例
                logger.warning(f"LLM 重试失败，返回最小化案例: {url}")
                return MarketingCase(
                    platform=platform,
                    brand="",
                    theme="",
                    creative_type="",
                    strategy=[],
                    insights=[],
                    source_url=url,
                    title=title,
                )
