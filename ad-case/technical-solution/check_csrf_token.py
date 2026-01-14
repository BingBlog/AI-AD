#!/usr/bin/env python3
"""
检查广告门网站CSRF Token的位置
用于确认Token在HTML中的具体存放位置
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def check_csrf_token():
    """检查CSRF Token在HTML中的位置"""
    
    url = 'https://m.adquan.com/creative'
    
    # 设置请求头，模拟移动端浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    print(f"正在访问: {url}")
    print("-" * 60)
    
    try:
        # 创建Session
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)} 字符")
        print("-" * 60)
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 方法1: 检查meta标签
        print("\n【方法1】检查 <meta> 标签中的CSRF Token:")
        meta_tags = soup.find_all('meta', attrs={'name': re.compile(r'csrf', re.I)})
        if meta_tags:
            for meta in meta_tags:
                print(f"  找到: {meta}")
                if meta.get('content'):
                    print(f"  Token值: {meta.get('content')}")
        else:
            print("  未找到包含'csrf'的meta标签")
        
        # 检查所有meta标签（用于调试）
        all_meta = soup.find_all('meta')
        csrf_meta = [m for m in all_meta if 'token' in str(m).lower() or 'csrf' in str(m).lower()]
        if csrf_meta:
            print(f"  相关meta标签: {len(csrf_meta)} 个")
            for m in csrf_meta:
                print(f"    {m}")
        
        # 方法2: 检查隐藏的input标签
        print("\n【方法2】检查隐藏的 <input> 标签中的CSRF Token:")
        hidden_inputs = soup.find_all('input', type='hidden')
        csrf_inputs = []
        for inp in hidden_inputs:
            name = inp.get('name', '').lower()
            if 'csrf' in name or 'token' in name or '_token' in name:
                csrf_inputs.append(inp)
                print(f"  找到: {inp}")
                if inp.get('value'):
                    print(f"  Token值: {inp.get('value')}")
        
        if not csrf_inputs:
            print("  未找到包含'token'或'csrf'的隐藏input标签")
            print(f"  所有隐藏input标签数量: {len(hidden_inputs)}")
            if hidden_inputs:
                print("  前5个隐藏input标签:")
                for inp in hidden_inputs[:5]:
                    print(f"    {inp}")
        
        # 方法3: 检查JavaScript变量
        print("\n【方法3】检查 <script> 标签中的CSRF Token变量:")
        scripts = soup.find_all('script')
        csrf_patterns = [
            r'csrf[_-]?token\s*[:=]\s*["\']([^"\']+)["\']',
            r'X-CSRF-TOKEN["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'_token\s*[:=]\s*["\']([^"\']+)["\']',
            r'csrfToken\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        found_in_script = False
        for script in scripts:
            if script.string:
                script_content = script.string
                for pattern in csrf_patterns:
                    matches = re.findall(pattern, script_content, re.I)
                    if matches:
                        found_in_script = True
                        print(f"  找到匹配: {pattern}")
                        for match in matches[:3]:  # 只显示前3个
                            print(f"    Token值: {match}")
        
        if not found_in_script:
            print("  未在script标签中找到CSRF Token变量")
            # 检查是否有包含token的script标签
            token_scripts = [s for s in scripts if s.string and ('token' in s.string.lower() or 'csrf' in s.string.lower())]
            if token_scripts:
                print(f"  找到 {len(token_scripts)} 个可能相关的script标签")
                print("  前3个相关script标签的前200字符:")
                for s in token_scripts[:3]:
                    preview = s.string[:200].replace('\n', ' ')
                    print(f"    {preview}...")
        
        # 方法4: 检查data属性
        print("\n【方法4】检查 data-* 属性中的CSRF Token:")
        all_elements = soup.find_all(attrs={'data-csrf-token': True})
        all_elements.extend(soup.find_all(attrs={'data-token': True}))
        if all_elements:
            for elem in all_elements:
                token = elem.get('data-csrf-token') or elem.get('data-token')
                print(f"  找到: {elem.name} 标签")
                print(f"  Token值: {token}")
        else:
            print("  未找到包含CSRF Token的data属性")
        
        # 方法5: 使用正则表达式全文搜索（最后手段）
        print("\n【方法5】全文正则搜索CSRF Token模式:")
        # 常见的Token格式：32-40个字符的字母数字组合
        token_pattern = r'[A-Za-z0-9]{32,40}'
        potential_tokens = re.findall(token_pattern, response.text)
        
        # 查找在token相关上下文中的字符串
        csrf_context_pattern = r'(?:csrf|token|X-CSRF)[^"\']*["\']([A-Za-z0-9]{32,40})["\']'
        context_tokens = re.findall(csrf_context_pattern, response.text, re.I)
        
        if context_tokens:
            print(f"  在token相关上下文中找到 {len(set(context_tokens))} 个可能的Token:")
            for token in list(set(context_tokens))[:5]:  # 去重并只显示前5个
                print(f"    {token}")
        else:
            print("  未找到符合Token格式的字符串")
        
        # 方法6: 检查Cookie中的Token（某些网站会在Cookie中设置）
        print("\n【方法6】检查Cookie中的CSRF Token:")
        cookies = session.cookies
        csrf_cookies = [c for c in cookies if 'csrf' in c.name.lower() or 'token' in c.name.lower()]
        if csrf_cookies:
            for cookie in csrf_cookies:
                print(f"  Cookie名称: {cookie.name}")
                print(f"  Cookie值: {cookie.value}")
        else:
            print("  未找到包含CSRF Token的Cookie")
            print(f"  所有Cookie: {list(cookies.keys())}")
        
        # 方法7: 检查响应头
        print("\n【方法7】检查响应头中的CSRF Token:")
        csrf_headers = {k: v for k, v in response.headers.items() if 'csrf' in k.lower() or 'token' in k.lower()}
        if csrf_headers:
            for k, v in csrf_headers.items():
                print(f"  {k}: {v}")
        else:
            print("  响应头中未找到CSRF Token")
        
        # 总结
        print("\n" + "=" * 60)
        print("【总结】")
        print("=" * 60)
        
        # 保存HTML到文件，便于手动检查
        output_file = 'adquan_page_source.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"HTML源码已保存到: {output_file}")
        print("\n建议:")
        print("1. 查看保存的HTML文件，手动搜索 'csrf' 或 'token'")
        print("2. 使用浏览器开发者工具查看Network请求，检查X-CSRF-TOKEN header的值来源")
        print("3. 检查页面加载的JavaScript文件，Token可能在JS中动态设置")
        
    except requests.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_csrf_token()

