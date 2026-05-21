#!/usr/bin/env python3
"""
Bing Images 图片源模块
无需API Key，直接爬取
"""
import re
import logging
import json
from .collector import ImageCollector

logger = logging.getLogger(__name__)

BING_SEARCH_URL = "https://www.bing.com/images/search"


class BingSource:
    """Bing Images 图片源"""

    name = "bing"
    display_name = "Bing Images"

    def __init__(self, collector: ImageCollector):
        self.collector = collector

    def search(self, keyword, count=20):
        """搜索图片"""
        results = []
        offset = 0

        while len(results) < count:
            try:
                params = {
                    'q': keyword,
                    'first': offset,
                    'count': min(35, count),
                    'form': 'HDRSC2',
                    'セット': 'image'
                }

                response = self.collector.session.get(
                    BING_SEARCH_URL,
                    params=params,
                    timeout=self.collector.timeout
                )

                if response.status_code == 200:
                    # 从JSON数据中提取图片URL
                    # Bing返回的JSON嵌入在特定的script标签中
                    json_data = self._extract_json(response.text)

                    if json_data and 'images' in json_data:
                        images = json_data['images']
                        for img in images:
                            if len(results) >= count:
                                break

                            img_url = img.get('murl') or img.get('turl')
                            if img_url and self._is_valid_url(img_url):
                                results.append({
                                    'url': img_url,
                                    'filename': f"bing_{img.get('pid', hash(img_url) % 100000)}.jpg",
                                    'title': img.get('title', ''),
                                    'width': img.get('w', ''),
                                    'height': img.get('h', ''),
                                    'referer': 'https://www.bing.com/'
                                })
                    else:
                        # 备用：正则提取
                        results.extend(self._regex_extract(response.text, count - len(results)))

                    offset += 35
                    logger.info(f"Bing: 获取第 {offset // 35} 批, 累计 {len(results)} 张")

                else:
                    logger.warning(f"Bing 请求失败: {response.status_code}")
                    break

            except Exception as e:
                logger.error(f"Bing 搜索失败: {str(e)}")
                break

        return results

    def _extract_json(self, html):
        """从Bing页面提取JSON数据"""
        try:
            # 查找 "var aI = {...}" 格式的数据
            pattern = r'var\s+aI\s*=\s*(\[.*?\]);'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                return {'images': json.loads(match.group(1))}
        except:
            pass
        return None

    def _regex_extract(self, html, count):
        """备用：正则提取图片URL"""
        results = []
        # 匹配各种图片URL模式
        patterns = [
            r'"murl":"(https://[^"]+\.(?:jpg|jpeg|png|webp))"',
            r'src="(https://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for url in matches:
                if len(results) >= count:
                    break
                if self._is_valid_url(url):
                    results.append({
                        'url': url,
                        'filename': f"bing_{hash(url) % 100000}.jpg",
                        'referer': 'https://www.bing.com/'
                    })

        return results[:count]

    def _is_valid_url(self, url):
        """检查URL是否有效"""
        if not url or not url.startswith('http'):
            return False
        # 排除一些无效URL
        invalid_patterns = ['data:', 'void', 'javascript']
        return not any(p in url.lower() for p in invalid_patterns)