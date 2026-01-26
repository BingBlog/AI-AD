"""
测试图片下载可行性脚本
用于验证从广告门下载图片的方案是否可行
"""
import asyncio
import asyncpg
import os
import sys
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_image_download():
    """测试图片下载可行性"""
    # 连接数据库
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'ad_case_db')
    )
    
    try:
        # 1. 统计有 main_image 的记录数
        result = await conn.fetchrow(
            'SELECT COUNT(*) as total, COUNT(main_image) as with_image FROM ad_cases WHERE main_image IS NOT NULL AND main_image != \'\''
        )
        print(f"数据库统计:")
        print(f"  总记录数: {result['total']}")
        print(f"  有 main_image 的记录数: {result['with_image']}")
        
        # 2. 获取一些示例 URL
        samples = await conn.fetch(
            'SELECT case_id, main_image FROM ad_cases WHERE main_image IS NOT NULL AND main_image != \'\' LIMIT 10'
        )
        print(f"\n示例 main_image URL (前10个):")
        for row in samples:
            print(f"  case_id={row['case_id']}: {row['main_image']}")
        
        # 3. 测试下载一个图片
        if samples:
            test_url = samples[0]['main_image']
            print(f"\n测试下载图片:")
            print(f"  URL: {test_url}")
            
            async with aiohttp.ClientSession() as session:
                try:
                    # 设置 User-Agent，模拟浏览器请求
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.adquan.com/'
                    }
                    
                    async with session.get(test_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            content_length = response.headers.get('Content-Length', '0')
                            
                            print(f"  ✓ 下载成功")
                            print(f"  Content-Type: {content_type}")
                            print(f"  Content-Length: {content_length} bytes")
                            
                            # 保存测试图片到临时目录
                            test_dir = Path(__file__).parent.parent / 'data' / 'test_images'
                            test_dir.mkdir(parents=True, exist_ok=True)
                            
                            # 从 URL 提取文件名
                            filename = test_url.split('/')[-1].split('?')[0]
                            if not filename or '.' not in filename:
                                # 根据 Content-Type 确定扩展名
                                if 'jpeg' in content_type or 'jpg' in content_type:
                                    filename = f"test_{samples[0]['case_id']}.jpg"
                                elif 'png' in content_type:
                                    filename = f"test_{samples[0]['case_id']}.png"
                                elif 'gif' in content_type:
                                    filename = f"test_{samples[0]['case_id']}.gif"
                                elif 'webp' in content_type:
                                    filename = f"test_{samples[0]['case_id']}.webp"
                                else:
                                    filename = f"test_{samples[0]['case_id']}.jpg"
                            
                            file_path = test_dir / filename
                            image_data = await response.read()
                            file_path.write_bytes(image_data)
                            
                            print(f"  ✓ 图片已保存到: {file_path}")
                            print(f"  文件大小: {len(image_data)} bytes")
                        else:
                            print(f"  ✗ 下载失败: HTTP {response.status}")
                            print(f"  Response: {await response.text()}")
                            
                except aiohttp.ClientError as e:
                    print(f"  ✗ 下载失败: {type(e).__name__}: {e}")
                except Exception as e:
                    print(f"  ✗ 下载失败: {type(e).__name__}: {e}")
        
        # 4. 分析 URL 模式
        print(f"\nURL 模式分析:")
        url_patterns = {}
        for row in samples:
            url = row['main_image']
            if url:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else 'unknown'
                url_patterns[domain] = url_patterns.get(domain, 0) + 1
        
        for domain, count in url_patterns.items():
            print(f"  {domain}: {count} 个")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(test_image_download())
