"""
真实用例测试：小红书新能源汽车营销案例检索

测试步骤：
1. 启动 Agent 服务器（需要单独运行）
2. 连接 WebSocket
3. 发送任务请求：检索10个新能源汽车营销案例
4. 接收并显示结果
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import websockets
except ImportError:
    print("❌ websockets 模块未安装，请运行: pip install websockets")
    sys.exit(1)


async def test_real_case():
    """测试真实用例：小红书新能源汽车营销案例检索"""
    uri = "ws://localhost:8765"
    
    print("=" * 60)
    print("真实用例测试：小红书新能源汽车营销案例检索")
    print("=" * 60)
    print()
    print("⚠️  请确保 Agent 服务器已启动：")
    print("   python3 agent/main.py")
    print()
    print("正在连接到 Agent 服务器...")
    
    try:
        # 禁用代理，直接连接本地服务器
        import os
        # 临时清除所有可能的代理环境变量
        proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 
                      'all_proxy', 'ALL_PROXY', 'socks_proxy', 'SOCKS_PROXY',
                      'socks5_proxy', 'SOCKS5_PROXY']
        original_proxy = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxy[var] = os.environ[var]
                del os.environ[var]
        
        try:
            # 使用 create_connection 并明确禁用代理
            # websockets.connect 在本地连接时不应该使用代理
            # 明确禁用代理：proxy=None 表示不使用任何代理
            async with websockets.connect(
                uri,
                ping_interval=None,
                proxy=None,  # 明确禁用代理（默认是 True，会检测系统代理）
                additional_headers={"User-Agent": "Ad-Browser-Agent-Test"},
            ) as websocket:
                print(f"✅ 已连接到 Agent 服务器: {uri}")
            print()
            
            # 发送启动任务消息
            message = {
                "type": "START_TASK",
                "task_id": "real-case-001",
                "payload": {
                    "platform": "xiaohongshu",
                    "keywords": ["新能源汽车", "营销案例", "解析"],
                    "max_items": 10
                }
            }
            
            print("📤 发送任务请求：")
            print(f"   任务ID: {message['task_id']}")
            print(f"   平台: {message['payload']['platform']}")
            print(f"   关键词: {message['payload']['keywords']}")
            print(f"   最大数量: {message['payload']['max_items']}")
            print()
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            print("✅ 任务请求已发送，等待执行...")
            print()
            print("-" * 60)
            
            # 接收消息
            result_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "STATUS_UPDATE":
                        state = data.get("state", "UNKNOWN")
                        progress = data.get("progress", 0)
                        msg = data.get("message", "")
                        print(f"📊 状态更新: {state} | 进度: {progress}% | {msg}")
                        
                    elif msg_type == "TASK_RESULT":
                        results = data.get("results", [])
                        result_count = len(results)
                        print()
                        print("=" * 60)
                        print(f"✅ 任务完成！共提取 {result_count} 个营销案例")
                        print("=" * 60)
                        print()
                        
                        for i, result in enumerate(results, 1):
                            print(f"案例 {i}:")
                            print(f"  品牌: {result.get('brand', '未知')}")
                            print(f"  主题: {result.get('theme', '未知')}")
                            print(f"  创意类型: {result.get('creative_type', '未知')}")
                            print(f"  策略: {', '.join(result.get('strategy', []))}")
                            print(f"  洞察: {', '.join(result.get('insights', []))}")
                            print(f"  来源: {result.get('source_url', '未知')}")
                            print()
                        
                        break
                        
                    elif msg_type == "ERROR":
                        error = data.get("error", "未知错误")
                        task_id = data.get("task_id", "未知")
                        print()
                        print("=" * 60)
                        print(f"❌ 任务执行失败")
                        print("=" * 60)
                        print(f"任务ID: {task_id}")
                        print(f"错误信息: {error}")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️  消息解析失败: {e}")
                    print(f"   原始消息: {message[:200]}")
                except Exception as e:
                    print(f"⚠️  处理消息时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            print()
            print("=" * 60)
            if result_count > 0:
                print(f"✅ 测试完成！成功提取 {result_count} 个案例")
            else:
                print("⚠️  测试完成，但未提取到案例")
            print("=" * 60)
        finally:
            # 恢复原始代理设置（如果存在）
            for var, value in original_proxy.items():
                os.environ[var] = value
            
    except (ConnectionRefusedError, OSError) as e:
        print()
        print("❌ 连接被拒绝，请确保 Agent 服务器已启动：")
        print("   cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser")
        print("   python3 -m agent.main")
        print(f"   错误详情: {e}")
        sys.exit(1)
    except ImportError as e:
        if "python-socks" in str(e):
            print()
            print("❌ WebSocket 连接失败：检测到代理配置")
            print("   如果不需要代理，请取消设置代理环境变量：")
            print("   unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY")
            print(f"   错误详情: {e}")
        else:
            print()
            print(f"❌ 导入错误: {e}")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print()
    asyncio.run(test_real_case())
