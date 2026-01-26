#!/usr/bin/env python3
"""
测试 Clash Verge API 连接
检查是否可以访问本地 Clash API 并获取代理节点信息
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

# Clash API 默认配置
DEFAULT_API_URL = "http://127.0.0.1:9090"
DEFAULT_SECRET = None  # 如果设置了 secret，需要在这里配置


def get_clash_headers(secret: Optional[str] = None) -> Dict[str, str]:
    """获取 Clash API 请求头"""
    headers = {"Content-Type": "application/json"}
    if secret:
        # Clash 可能使用不同的认证方式
        headers["Authorization"] = f"Bearer {secret}"
        # 也尝试直接使用 secret 作为 header
        # headers["secret"] = secret
    return headers


def test_api_connection(api_url: str, secret: Optional[str] = None) -> bool:
    """测试 API 连接"""
    print("=" * 60)
    print("测试 1: 检查 Clash API 连接")
    print("=" * 60)
    print(f"API 地址: {api_url}")
    
    # 尝试多个可能的端点
    endpoints_to_try = [
        "/proxies",
        "/version",
        "/configs",
        "/",
    ]
    
    for endpoint in endpoints_to_try:
        try:
            url = f"{api_url}{endpoint}"
            print(f"\n尝试访问: {url}")
            
            # 先尝试不带认证
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✓ API 连接成功（端点: {endpoint}）")
                if endpoint == "/version":
                    print(f"  版本信息: {response.text}")
                return True
            elif response.status_code == 401:
                print(f"⚠ 端点 {endpoint} 需要认证")
                if secret:
                    # 尝试带认证
                    headers = get_clash_headers(secret)
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        print(f"✓ 使用认证后连接成功（端点: {endpoint}）")
                        return True
            elif response.status_code == 400:
                print(f"⚠ 端点 {endpoint} 返回 400（可能需要认证或路径不正确）")
            else:
                print(f"⚠ 端点 {endpoint} 返回状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ 无法连接到 {endpoint}")
            continue
        except Exception as e:
            print(f"⚠ 访问 {endpoint} 时出错: {e}")
            continue
    
    # 如果所有端点都失败，检查是否需要认证
    print("\n所有端点测试失败，可能的原因：")
    print("1. Clash Verge 的 API 端口不是 7897（请确认）")
    print("2. 需要设置 Secret（在 Clash Verge 设置中查看）")
    print("3. Clash Verge 可能使用不同的 API 路径")
    print("\n请检查 Clash Verge 设置中的 'External Controller' 配置")
    print("特别是 'Secret' 字段，如果有值，请通过参数传入")
    
    return False


def get_proxy_groups(api_url: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取所有代理组"""
    print("\n" + "=" * 60)
    print("测试 2: 获取代理组列表")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{api_url}/proxies",
            headers=get_clash_headers(secret),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 成功获取代理组信息")
            
            # 打印所有代理组
            if "proxies" in data:
                print(f"\n找到 {len(data['proxies'])} 个代理组/节点:")
                for key, value in data["proxies"].items():
                    if isinstance(value, dict):
                        proxy_type = value.get("type", "unknown")
                        if proxy_type == "Selector":  # 代理组
                            current = value.get("now", "N/A")
                            all_proxies = value.get("all", [])
                            print(f"  - {key} (类型: {proxy_type})")
                            print(f"    当前节点: {current}")
                            print(f"    可用节点数: {len(all_proxies)}")
                            if all_proxies:
                                print(f"    节点列表: {', '.join(all_proxies[:5])}{'...' if len(all_proxies) > 5 else ''}")
                        elif proxy_type in ["Shadowsocks", "VMess", "Trojan", "Vless"]:  # 单个节点
                            print(f"  - {key} (类型: {proxy_type})")
            
            return data
        else:
            print(f"✗ 获取代理组失败，状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"✗ 获取代理组失败: {e}")
        return None


def get_current_proxy(api_url: str, group_name: str, secret: Optional[str] = None) -> Optional[str]:
    """获取指定代理组的当前节点"""
    print("\n" + "=" * 60)
    print(f"测试 3: 获取代理组 '{group_name}' 的当前节点")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{api_url}/proxies/{group_name}",
            headers=get_clash_headers(secret),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("now", "N/A")
            print(f"✓ 当前节点: {current}")
            return current
        else:
            print(f"✗ 获取当前节点失败，状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"✗ 获取当前节点失败: {e}")
        return None


def test_switch_proxy(api_url: str, group_name: str, proxy_name: str, secret: Optional[str] = None) -> bool:
    """测试切换代理节点"""
    print("\n" + "=" * 60)
    print(f"测试 4: 测试切换代理节点")
    print("=" * 60)
    print(f"代理组: {group_name}")
    print(f"目标节点: {proxy_name}")
    
    try:
        response = requests.put(
            f"{api_url}/proxies/{group_name}",
            headers=get_clash_headers(secret),
            json={"name": proxy_name},
            timeout=5
        )
        
        if response.status_code == 204:
            print("✓ 切换节点成功")
            return True
        else:
            print(f"✗ 切换节点失败，状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ 切换节点失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Clash Verge API 连接测试")
    print("=" * 60)
    
    # 从命令行参数或环境变量获取配置
    api_url = DEFAULT_API_URL
    secret = DEFAULT_SECRET
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    if len(sys.argv) > 2:
        secret = sys.argv[2]
    
    # 测试 1: 连接
    if not test_api_connection(api_url, secret):
        print("\n" + "=" * 60)
        print("测试失败：无法连接到 Clash API")
        print("=" * 60)
        print("\n请检查：")
        print("1. Clash Verge 是否正在运行")
        print("2. 在 Clash Verge 设置中查看 API 端口（默认 9090）")
        print("3. 确保开启了 'External Controller' 或 '允许局域网连接'")
        print("4. 如果设置了 secret，请在脚本中配置或通过参数传入")
        print("\n使用方法:")
        print("  python test_clash_api.py [api_url] [secret]")
        print("  例如: python test_clash_api.py http://127.0.0.1:9090 your_secret")
        return
    
    # 测试 2: 获取代理组
    proxies_data = get_proxy_groups(api_url, secret)
    if not proxies_data:
        return
    
    # 查找可用的代理组（通常是 "GLOBAL" 或 "PROXY"）
    available_groups = []
    if "proxies" in proxies_data:
        for key, value in proxies_data["proxies"].items():
            if isinstance(value, dict) and value.get("type") == "Selector":
                available_groups.append(key)
    
    if not available_groups:
        print("\n✗ 未找到可用的代理组（Selector 类型）")
        return
    
    print(f"\n找到可用代理组: {', '.join(available_groups)}")
    
    # 使用第一个代理组进行测试（通常是 "GLOBAL" 或 "PROXY"）
    test_group = available_groups[0]
    if "GLOBAL" in available_groups:
        test_group = "GLOBAL"
    elif "PROXY" in available_groups:
        test_group = "PROXY"
    
    # 测试 3: 获取当前节点
    current_proxy = get_current_proxy(api_url, test_group, secret)
    
    # 测试 4: 测试切换（如果有多个节点）
    if proxies_data and "proxies" in proxies_data:
        group_info = proxies_data["proxies"].get(test_group, {})
        all_proxies = group_info.get("all", [])
        
        if len(all_proxies) > 1:
            # 切换到另一个节点（不是当前节点）
            other_proxy = None
            for proxy in all_proxies:
                if proxy != current_proxy:
                    other_proxy = proxy
                    break
            
            if other_proxy:
                print(f"\n尝试切换到节点: {other_proxy}")
                if test_switch_proxy(api_url, test_group, other_proxy, secret):
                    # 验证切换是否成功
                    new_current = get_current_proxy(api_url, test_group, secret)
                    if new_current == other_proxy:
                        print(f"✓ 验证成功：当前节点已切换为 {new_current}")
                    else:
                        print(f"⚠ 警告：切换后当前节点为 {new_current}，与预期不符")
                    
                    # 切换回原来的节点
                    if current_proxy:
                        print(f"\n切换回原节点: {current_proxy}")
                        test_switch_proxy(api_url, test_group, current_proxy, secret)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print(f"\n建议配置:")
    print(f"  CLASH_API_URL={api_url}")
    if secret:
        print(f"  CLASH_SECRET={secret}")
    print(f"  CLASH_PROXY_GROUP={test_group}")


if __name__ == "__main__":
    main()
