#!/usr/bin/env python3
"""
代理管理器
支持通过 Clash Verge API 定时切换代理节点，避免被封禁
"""

import requests
import logging
import time
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProxyManager:
    """代理管理器类"""
    
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:9097",
        secret: Optional[str] = None,
        proxy_group: str = "GLOBAL",
        switch_mode: str = "hybrid",  # count/time/hybrid
        switch_interval: int = 50,  # 请求次数阈值
        switch_interval_minutes: int = 10,  # 时间间隔（分钟）
        auto_switch_on_error: bool = True,  # 错误时自动切换
        exclude_nodes: Optional[List[str]] = None,  # 排除的节点（如 DIRECT, REJECT）
    ):
        """
        初始化代理管理器
        
        Args:
            api_url: Clash API 地址
            secret: Clash API 认证密钥
            proxy_group: 代理组名称（如 GLOBAL, Proxy）
            switch_mode: 切换模式 (count/time/hybrid)
            switch_interval: 请求次数阈值（switch_mode 为 count 或 hybrid 时使用）
            switch_interval_minutes: 时间间隔（分钟，switch_mode 为 time 或 hybrid 时使用）
            auto_switch_on_error: 是否在错误时自动切换
            exclude_nodes: 要排除的节点列表（如 ['DIRECT', 'REJECT', 'Auto']）
        """
        self.api_url = api_url.rstrip('/')
        self.secret = secret
        self.proxy_group = proxy_group
        self.switch_mode = switch_mode
        self.switch_interval = switch_interval
        self.switch_interval_minutes = switch_interval_minutes
        self.auto_switch_on_error = auto_switch_on_error
        self.exclude_nodes = exclude_nodes or ['DIRECT', 'REJECT', 'Auto']
        
        # 状态跟踪
        self.request_count = 0
        self.last_switch_time: Optional[datetime] = None
        self.current_node: Optional[str] = None
        self.available_nodes: List[str] = []
        self.failed_nodes: set = set()  # 记录失败的节点
        
        # 初始化
        self._init_headers()
        self._load_available_nodes()
        self._get_current_node()
        
        logger.info(f"代理管理器初始化完成")
        logger.info(f"  API 地址: {self.api_url}")
        logger.info(f"  代理组: {self.proxy_group}")
        logger.info(f"  可用节点数: {len(self.available_nodes)}")
        logger.info(f"  当前节点: {self.current_node}")
        logger.info(f"  切换模式: {self.switch_mode}")
        logger.info(f"  切换间隔: {self.switch_interval} 次请求 / {self.switch_interval_minutes} 分钟")
    
    def _init_headers(self):
        """初始化请求头"""
        self.headers = {"Content-Type": "application/json"}
        if self.secret:
            self.headers["Authorization"] = f"Bearer {self.secret}"
    
    def _load_available_nodes(self) -> bool:
        """加载可用节点列表"""
        try:
            response = requests.get(
                f"{self.api_url}/proxies/{self.proxy_group}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                all_nodes = data.get("all", [])
                
                # 过滤掉排除的节点
                self.available_nodes = [
                    node for node in all_nodes 
                    if node not in self.exclude_nodes
                ]
                
                if not self.available_nodes:
                    logger.warning("没有可用的代理节点（所有节点都被排除）")
                    self.available_nodes = all_nodes  # 使用所有节点作为备用
                
                logger.info(f"加载了 {len(self.available_nodes)} 个可用节点")
                return True
            else:
                logger.error(f"获取节点列表失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"加载节点列表失败: {e}")
            return False
    
    def _get_current_node(self) -> Optional[str]:
        """获取当前节点"""
        try:
            response = requests.get(
                f"{self.api_url}/proxies/{self.proxy_group}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_node = data.get("now")
                return self.current_node
            else:
                logger.warning(f"获取当前节点失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"获取当前节点失败: {e}")
            return None
    
    def _switch_to_node(self, node_name: str) -> bool:
        """切换到指定节点"""
        try:
            response = requests.put(
                f"{self.api_url}/proxies/{self.proxy_group}",
                headers=self.headers,
                json={"name": node_name},
                timeout=5
            )
            
            if response.status_code == 204:
                self.current_node = node_name
                self.last_switch_time = datetime.now()
                logger.info(f"✓ 成功切换到节点: {node_name}")
                return True
            else:
                logger.error(f"切换节点失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"切换节点失败: {e}")
            return False
    
    def _should_switch(self) -> bool:
        """判断是否应该切换节点"""
        if not self.available_nodes:
            return False
        
        # 检查切换条件
        should_switch = False
        reasons = []
        
        if self.switch_mode in ["count", "hybrid"]:
            if self.request_count >= self.switch_interval:
                should_switch = True
                reasons.append(f"请求次数达到 {self.request_count}/{self.switch_interval}")
        
        if self.switch_mode in ["time", "hybrid"]:
            if self.last_switch_time:
                elapsed = datetime.now() - self.last_switch_time
                if elapsed >= timedelta(minutes=self.switch_interval_minutes):
                    should_switch = True
                    reasons.append(f"时间间隔达到 {elapsed.total_seconds()/60:.1f} 分钟")
            else:
                # 如果从未切换过，也应该切换一次
                should_switch = True
                reasons.append("首次切换")
        
        if should_switch and reasons:
            logger.info(f"需要切换节点: {', '.join(reasons)}")
        
        return should_switch
    
    def _select_next_node(self) -> Optional[str]:
        """选择下一个节点"""
        if not self.available_nodes:
            return None
        
        # 过滤掉失败的节点（如果失败节点太多，则重置）
        available = [
            node for node in self.available_nodes 
            if node not in self.failed_nodes
        ]
        
        if not available:
            # 如果所有节点都失败了，重置失败列表
            logger.warning("所有节点都标记为失败，重置失败列表")
            self.failed_nodes.clear()
            available = self.available_nodes
        
        # 排除当前节点
        candidates = [node for node in available if node != self.current_node]
        
        if not candidates:
            # 如果只有当前节点可用，使用所有节点
            candidates = available
        
        # 随机选择一个节点
        selected = random.choice(candidates)
        return selected
    
    def switch_proxy(self, force: bool = False) -> bool:
        """
        切换代理节点
        
        Args:
            force: 是否强制切换（忽略切换条件）
            
        Returns:
            是否切换成功
        """
        if not self.available_nodes:
            logger.warning("没有可用节点，无法切换")
            return False
        
        if not force and not self._should_switch():
            return False
        
        # 选择下一个节点
        next_node = self._select_next_node()
        if not next_node:
            logger.warning("无法选择下一个节点")
            return False
        
        # 切换节点
        success = self._switch_to_node(next_node)
        
        if success:
            # 重置计数器
            self.request_count = 0
            # 等待一下，确保切换生效
            time.sleep(0.5)
        
        return success
    
    def record_request(self, success: bool = True):
        """
        记录一次请求
        
        Args:
            success: 请求是否成功
        """
        self.request_count += 1
        
        # 如果请求失败且启用了自动切换，立即切换
        if not success and self.auto_switch_on_error:
            logger.warning(f"请求失败，自动切换节点（请求计数: {self.request_count}）")
            if self.current_node:
                self.failed_nodes.add(self.current_node)
            self.switch_proxy(force=True)
        # 否则检查是否需要切换
        elif self._should_switch():
            self.switch_proxy()
    
    def handle_error(self, error: Exception):
        """
        处理请求错误，自动切换节点
        
        Args:
            error: 异常对象
        """
        error_str = str(error)
        
        # 检查是否是代理相关的错误
        is_proxy_error = any(keyword in error_str for keyword in [
            "ProxyError",
            "proxy",
            "connection",
            "timeout",
            "refused",
            "403",
            "429",  # 请求过多
        ])
        
        if is_proxy_error:
            logger.warning(f"检测到代理相关错误: {error_str[:100]}")
            self.record_request(success=False)
    
    def get_proxy_url(self) -> Optional[str]:
        """
        获取当前代理 URL（用于 requests）
        
        Returns:
            代理 URL，格式: http://127.0.0.1:7897
            如果使用系统代理，返回 None
        """
        # Clash Verge 通常使用系统代理，不需要手动设置代理 URL
        # 如果需要手动设置，可以返回代理地址
        # 例如: return "http://127.0.0.1:7897"
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "current_node": self.current_node,
            "request_count": self.request_count,
            "available_nodes_count": len(self.available_nodes),
            "failed_nodes_count": len(self.failed_nodes),
            "last_switch_time": self.last_switch_time.isoformat() if self.last_switch_time else None,
            "switch_mode": self.switch_mode,
            "switch_interval": self.switch_interval,
            "switch_interval_minutes": self.switch_interval_minutes,
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("代理管理器测试")
    print("=" * 60)
    
    try:
        # 创建代理管理器
        manager = ProxyManager(
            api_url="http://127.0.0.1:9097",
            secret="123456",
            proxy_group="GLOBAL",
            switch_mode="hybrid",
            switch_interval=5,  # 测试用，每5次请求切换
            switch_interval_minutes=1,  # 测试用，每1分钟切换
        )
        
        print(f"\n当前节点: {manager.current_node}")
        print(f"可用节点数: {len(manager.available_nodes)}")
        
        # 模拟几次请求
        print("\n模拟请求...")
        for i in range(10):
            manager.record_request(success=True)
            print(f"请求 {i+1}: 计数={manager.request_count}, 当前节点={manager.current_node}")
            time.sleep(0.5)
        
        # 获取统计信息
        print("\n统计信息:")
        stats = manager.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
