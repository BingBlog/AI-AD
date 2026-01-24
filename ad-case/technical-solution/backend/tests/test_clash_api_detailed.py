#!/usr/bin/env python3
"""
详细测试 Clash Verge API
尝试不同的认证方式和 API 路径
"""

import requests
import json
import sys

def test_with_auth(url: str, secret: str):
    """尝试不同的认证方式"""
    methods = [
        ("Bearer", f"Bearer {secret}"),
        ("Authorization", f"Bearer {secret}"),
        ("secret", secret),
        ("X-API-Key", secret),
    ]
    
    for method_name, auth_value in methods:
        headers = {}
        if method_name == "Bearer" or method_name == "Authorization":
            headers["Authorization"] = auth_value
        else:
            headers[method_name] = auth_value
        
        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                print(f"✓ 成功！认证方式: {method_name}")
                return True, response
            elif response.status_code == 401:
                print(f"⚠ {method_name}: 401 未授权")
            else:
                print(f"⚠ {method_name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {method_name}: {e}")
    
    return False, None

def main():
    print("=" * 60)
    print("Clash Verge API 详细测试")
    print("=" * 60)
    
    # 常见 API 端口
    api_ports = [9090, 9091, 7890, 7897]
    
    # 如果提供了参数
    if len(sys.argv) > 1:
        api_ports = [int(sys.argv[1])]
    
    secret = None
    if len(sys.argv) > 2:
        secret = sys.argv[2]
    
    endpoints = ["/proxies", "/version", "/configs", "/"]
    
    for port in api_ports:
        print(f"\n{'='*60}")
        print(f"测试端口: {port}")
        print(f"{'='*60}")
        
        for endpoint in endpoints:
            url = f"http://127.0.0.1:{port}{endpoint}"
            print(f"\n测试: {url}")
            
            # 先尝试无认证
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print(f"✓ 成功！无需认证")
                    print(f"  响应: {response.text[:200]}")
                    return
                elif response.status_code == 401:
                    print(f"⚠ 需要认证")
                    if secret:
                        success, resp = test_with_auth(url, secret)
                        if success:
                            print(f"  响应: {resp.text[:200]}")
                            return
                else:
                    print(f"⚠ 状态码: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"✗ 连接失败（端口可能不是 API 端口）")
                break
            except Exception as e:
                print(f"✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n如果所有测试都失败，请：")
    print("1. 在 Clash Verge 设置中查看 'External Controller' 或 'API' 配置")
    print("2. 确认 API 端口（不是代理端口）")
    print("3. 查看是否有 Secret 设置")
    print("\n使用方法:")
    print("  python test_clash_api_detailed.py [port] [secret]")

if __name__ == "__main__":
    main()
