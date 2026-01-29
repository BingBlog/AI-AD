"""agent.browser.actions

动作级 API（对外暴露），对应技术文档 `AGET-TECH_MVP.md` 第 8.2 节。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BrowserActions(ABC):
    @abstractmethod
    async def open_page(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def scroll(self, times: int = 1) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def open_item(self, index: int) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def extract(self, rule: str) -> Dict[str, Any]:
        raise NotImplementedError
