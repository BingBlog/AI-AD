#!/usr/bin/env python3
"""
检查广告门API返回的最大条数
通过调用列表接口，查看API返回的数据结构，特别是是否有total、count等字段
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.spider.api_client import AdquanAPIClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("检查广告门API返回的最大条数")
    print("=" * 60)
    
    try:
        # 创建API客户端
        client = AdquanAPIClient()
        
        # 获取第一页数据
        print("\n【步骤1】获取第一页数据（page=0）...")
        data = client.get_creative_list(page=0)
        
        print("\n【步骤2】分析返回数据结构...")
        print(f"返回数据类型: {type(data)}")
        
        if isinstance(data, dict):
            print(f"\n顶层键: {list(data.keys())}")
            
            # 打印完整的JSON结构（格式化）
            print("\n完整返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])  # 只打印前2000字符
            
            # 检查是否有total、count等字段
            print("\n【步骤3】检查总数相关字段...")
            
            # 检查顶层
            for key in ['total', 'count', 'total_count', 'max', 'max_count', 'total_items']:
                if key in data:
                    print(f"  顶层找到 '{key}': {data[key]}")
            
            # 检查data字段
            if 'data' in data and isinstance(data['data'], dict):
                print(f"\ndata字段的键: {list(data['data'].keys())}")
                
                for key in ['total', 'count', 'total_count', 'max', 'max_count', 'total_items', 'page', 'page_size', 'pages']:
                    if key in data['data']:
                        print(f"  data['{key}']: {data['data'][key]}")
                
                # 检查items数量
                if 'items' in data['data']:
                    items = data['data']['items']
                    print(f"\n  items数量: {len(items)}")
                    if items:
                        print(f"  第一个item的键: {list(items[0].keys())}")
            
            # 尝试获取多页数据，看是否能找到最大条数
            print("\n【步骤4】尝试获取多页数据，查找最大条数...")
            print("获取前3页数据...")
            
            all_items = []
            for page in range(3):
                page_data = client.get_creative_list(page=page)
                if isinstance(page_data, dict) and 'data' in page_data:
                    items = page_data['data'].get('items', [])
                    all_items.extend(items)
                    print(f"  第{page}页: {len(items)} 个案例")
                    
                    # 再次检查这一页的数据结构
                    if page == 0:
                        print(f"  第{page}页数据结构:")
                        print(json.dumps(page_data, indent=2, ensure_ascii=False)[:1500])
            
            print(f"\n累计获取: {len(all_items)} 个案例")
            
            # 尝试获取一个很大的页码，看API如何响应
            print("\n【步骤5】尝试获取一个很大的页码（page=1000），查看API响应...")
            try:
                large_page_data = client.get_creative_list(page=1000)
                if isinstance(large_page_data, dict):
                    print(f"  返回数据结构: {list(large_page_data.keys())}")
                    if 'data' in large_page_data:
                        items = large_page_data['data'].get('items', [])
                        print(f"  第1000页返回的items数量: {len(items)}")
                        if len(items) == 0:
                            print("  ✓ 第1000页没有数据，说明API有边界限制")
            except Exception as e:
                print(f"  获取第1000页时出错: {e}")
        
        print("\n" + "=" * 60)
        print("检查完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
