"""
网页内容抓取扩展
功能: 抓取网页内容并提取有用信息
作者: System
版本: 1.0.0
依赖: requests, beautifulsoup4 (可选)
"""

import requests
import re
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime

def get_default_config():
    """返回默认配置"""
    return {
        "timeout": 30,
        "max_redirects": 5,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "max_content_length": 1024 * 1024  # 1MB
    }

def get_config_form():
    """返回配置表单"""
    return """
    <div class="mb-3">
        <label for="config.timeout" class="form-label">请求超时时间(秒)</label>
        <input type="number" class="form-control" id="config.timeout" 
               name="config.timeout" value="{{ config.timeout }}" 
               min="5" max="120">
    </div>
    
    <div class="mb-3">
        <label for="config.user_agent" class="form-label">User-Agent</label>
        <input type="text" class="form-control" id="config.user_agent" 
               name="config.user_agent" value="{{ config.user_agent }}">
        <div class="form-text">浏览器标识，某些网站需要特定的User-Agent</div>
    </div>
    
    <div class="mb-3">
        <label for="config.max_content_length" class="form-label">最大内容长度(字节)</label>
        <input type="number" class="form-control" id="config.max_content_length" 
               name="config.max_content_length" value="{{ config.max_content_length }}" 
               min="1024" max="10485760">
        <div class="form-text">限制下载的内容大小，防止内存溢出</div>
    </div>
    """

def get_query_form():
    """返回查询表单"""
    return """
    <div class="mb-3">
        <label for="url" class="form-label">网页URL</label>
        <input type="url" class="form-control" id="url" name="url" 
               placeholder="https://example.com" required>
        <div class="form-text">请输入完整的网页地址</div>
    </div>
    
    <div class="mb-3">
        <label for="extract_type" class="form-label">提取内容类型</label>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="basic_info" name="extract_type" value="basic" checked>
            <label class="form-check-label" for="basic_info">基础信息 (标题、描述等)</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="links" name="extract_type" value="links">
            <label class="form-check-label" for="links">链接列表</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="images" name="extract_type" value="images">
            <label class="form-check-label" for="images">图片列表</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="text_content" name="extract_type" value="text">
            <label class="form-check-label" for="text_content">文本内容</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="meta_tags" name="extract_type" value="meta">
            <label class="form-check-label" for="meta_tags">Meta标签</label>
        </div>
    </div>
    
    <div class="mb-3">
        <label for="custom_selector" class="form-label">自定义CSS选择器 (可选)</label>
        <input type="text" class="form-control" id="custom_selector" name="custom_selector" 
               placeholder="例如: .article-content, #main-text">
        <div class="form-text">使用CSS选择器提取特定元素</div>
    </div>
    
    <div class="mb-3">
        <label for="headers" class="form-label">自定义请求头 (JSON格式, 可选)</label>
        <textarea class="form-control" id="headers" name="headers" rows="3" 
                  placeholder='{"Authorization": "Bearer token", "Accept": "text/html"}'></textarea>
    </div>
    """

def extract_basic_info(html_content, url):
    """提取基础信息"""
    info = {}
    
    # 提取标题
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        info['title'] = title_match.group(1).strip()
    
    # 提取描述
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if desc_match:
        info['description'] = desc_match.group(1)
    
    # 提取关键词
    keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if keywords_match:
        info['keywords'] = keywords_match.group(1)
    
    # 提取字符编码
    charset_match = re.search(r'<meta[^>]*charset=["\']?([^"\'>\s]*)', html_content, re.IGNORECASE)
    if charset_match:
        info['charset'] = charset_match.group(1)
    
    return info

def extract_links(html_content, base_url):
    """提取链接"""
    links = []
    link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
    
    for match in re.finditer(link_pattern, html_content, re.IGNORECASE | re.DOTALL):
        href = match.group(1)
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        
        # 转换为绝对URL
        absolute_url = urljoin(base_url, href)
        
        links.append({
            'url': absolute_url,
            'text': text,
            'original_href': href
        })
    
    return links

def extract_images(html_content, base_url):
    """提取图片"""
    images = []
    img_pattern = r'<img[^>]*src=["\']([^"\']*)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
    
    for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
        src = match.group(1)
        alt = match.group(2) if match.group(2) else ""
        
        # 转换为绝对URL
        absolute_url = urljoin(base_url, src)
        
        images.append({
            'url': absolute_url,
            'alt': alt,
            'original_src': src
        })
    
    return images

def extract_text_content(html_content):
    """提取文本内容"""
    # 移除脚本和样式标签
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # 清理空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_meta_tags(html_content):
    """提取Meta标签"""
    meta_tags = []
    meta_pattern = r'<meta[^>]*(?:name=["\']([^"\']*)["\'])?[^>]*(?:content=["\']([^"\']*)["\'])?[^>]*>'
    
    for match in re.finditer(meta_pattern, html_content, re.IGNORECASE):
        name = match.group(1) if match.group(1) else ""
        content = match.group(2) if match.group(2) else ""
        
        if name or content:
            meta_tags.append({
                'name': name,
                'content': content
            })
    
    return meta_tags

def execute_query(params, config=None):
    """执行网页抓取"""
    try:
        url = params.get("url", "").strip()
        extract_types = params.getlist("extract_type") if hasattr(params, 'getlist') else [params.get("extract_type", "basic")]
        custom_selector = params.get("custom_selector", "").strip()
        headers_str = params.get("headers", "").strip()
        
        if not url:
            return {"error": "URL不能为空"}
        
        # 验证URL格式
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {"error": "URL格式不正确"}
        
        # 准备请求头
        headers = {
            'User-Agent': config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        }
        
        # 添加自定义请求头
        if headers_str:
            try:
                custom_headers = json.loads(headers_str)
                headers.update(custom_headers)
            except json.JSONDecodeError:
                return {"error": "自定义请求头JSON格式错误"}
        
        # 发送请求
        timeout = config.get("timeout", 30)
        max_content_length = config.get("max_content_length", 1024 * 1024)
        
        response = requests.get(
            url, 
            headers=headers, 
            timeout=timeout,
            allow_redirects=True,
            stream=True
        )
        
        # 检查响应状态
        if response.status_code != 200:
            return {"error": f"HTTP错误: {response.status_code}"}
        
        # 检查内容长度
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_content_length:
            return {"error": f"内容过大: {content_length} 字节"}
        
        # 读取内容
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_content_length:
                return {"error": "内容过大，已截断"}
        
        # 尝试解码内容
        try:
            html_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                html_content = content.decode('gbk')
            except UnicodeDecodeError:
                html_content = content.decode('latin-1')
        
        # 构建结果
        result = {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(content),
            "content_type": response.headers.get('content-type', ''),
            "final_url": response.url,
            "extraction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 根据选择的类型提取内容
        if "basic" in extract_types:
            result["basic_info"] = extract_basic_info(html_content, url)
        
        if "links" in extract_types:
            result["links"] = extract_links(html_content, url)
        
        if "images" in extract_types:
            result["images"] = extract_images(html_content, url)
        
        if "text" in extract_types:
            text_content = extract_text_content(html_content)
            result["text_content"] = {
                "full_text": text_content,
                "length": len(text_content),
                "word_count": len(text_content.split()),
                "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
            }
        
        if "meta" in extract_types:
            result["meta_tags"] = extract_meta_tags(html_content)
        
        # 自定义选择器提取
        if custom_selector:
            try:
                # 这里需要BeautifulSoup，如果没有安装则跳过
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                elements = soup.select(custom_selector)
                
                custom_content = []
                for element in elements[:20]:  # 限制最多20个元素
                    custom_content.append({
                        'tag': element.name,
                        'text': element.get_text().strip(),
                        'html': str(element)[:500]  # 限制HTML长度
                    })
                
                result["custom_selector_content"] = custom_content
                
            except ImportError:
                result["custom_selector_error"] = "BeautifulSoup4未安装，无法使用CSS选择器"
            except Exception as e:
                result["custom_selector_error"] = f"选择器错误: {str(e)}"
        
        return {
            "success": True,
            "data": result
        }
        
    except requests.RequestException as e:
        return {"error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        return {"error": f"抓取失败: {str(e)}"}
