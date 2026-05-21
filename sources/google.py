#!/usr/bin/env python3
"""
Google Images 图片源模块
方案1: 使用 SerpAPI (推荐，需要API Key)
方案2: 直接爬取 (容易被屏蔽)
"""
import re
import logging
import time
from .collector import ImageCollector

logger = logging.getLogger(__name__)

# SerpAPI (付费但稳定，推荐) - https://serpapi.com/
SERPAPI_URL = "https://serpapi.com/search"
# 免费替代: https://ddg-api.herokuapp.com/search (不稳定)
DDG_API_URL = "https://ddg-api.herokuapp.com/search"


class GoogleSource:
    """Google Images 图片源"""

    name = "google"
    display_name = "Google Images"

    def __init__(self, collector: ImageCollector, api_key=None, use_ddg=False):
        self.collector = collector
        self.api_key = api_key
        self.use_ddg = use_ddg

    def search(self, keyword, count=20):
        """搜索图片"""
        if self.api_key:
            return self._serpapi_search(keyword, count)
        elif self.use_ddg:
            return self._ddg_search(keyword, count)
        else:
            return self._direct_search(keyword, count)

    def _serpapi_search(self, keyword, count):
        """使用 SerpAPI"""
        results = []

        try:
            params = {
                'q': keyword,
                'tbm': 'isch',
                'ijn': 0,
                'api_key': self.api_key
            }

            response = self.collector.session.get(
                SERPAPI_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                images_results = data.get('images_results', [])

                for img in images_results:
                    if len(results) >= count:
                        break

                    img_url = img.get('original') or img.get('source')
                    if img_url:
                        results.append({
                            'url': img_url,
                            'filename': f"google_{hash(img_url) % 100000}.jpg",
                            'title': img.get('title', ''),
                            'source': img.get('source', ''),
                            'referer': 'https://www.google.com/'
                        })

                logger.info(f"Google (SerpAPI): 获取 {len(results)} 张")

        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {str(e)}")

        return results

    def _ddg_search(self, keyword, count):
        """使用 DuckDuckGo 免费 API"""
        results = []

        try:
            params = {
                'q': keyword,
                'format': 'json',
                'size': 'large'
            }

            response = self.collector.session.get(
                DDG_API_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if len(results) >= count:
                        break

                    img_url = item.get('Image')
                    if img_url:
                        results.append({
                            'url': img_url,
                            'filename': f"google_{hash(img_url) % 100000}.jpg",
                            'title': item.get('Title', ''),
                            'source': item.get('Domain', ''),
                            'referer': 'https://www.google.com/'
                        })

                logger.info(f"Google (DDG): 获取 {len(results)} 张")

        except Exception as e:
            logger.error(f"DuckDuckGo 搜索失败: {str(e)}")

        return results

    def _direct_search(self, keyword, count):
        """直接爬取 Google Images（容易被屏蔽）"""
        results = []

        try:
            # Google 图片搜索URL
            search_url = f"https://www.google.com/search?q={keyword}&tbm=isch&hl=zh-CN"

            response = self.collector.session.get(
                search_url,
                timeout=30
            )

            if response.status_code == 200:
                # Google 返回的是 JavaScript 渲染的数据
                # 尝试提取 JSON 数据
                import json as json_module

                # 查找模式
                patterns = [
                    r'"murl":"(https://[^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)"',
                    r'src="(https://[^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)"',
                    r'https://encrypted-tbn[0-9]?\.gstatic\.com/[^\s"<>]+',
                ]

                seen = set()
                for pattern in patterns:
                    matches = re.findall(pattern, response.text)
                    for url in matches:
                        url = url.replace('\\/', '/')
                        if len(results) >= count:
                            break
                        if url not in seen and self._is_valid_image_url(url):
                            seen.add(url)
                            results.append({
                                'url': url,
                                'filename': f"google_{hash(url) % 100000}.jpg",
                                'referer': 'https://www.google.com/'
                            })

                logger.info(f"Google (直接): 获取 {len(results)} 张")

        except Exception as e:
            logger.error(f"Google 直接搜索失败: {str(e)}")

        return results

    def _is_valid_image_url(self, url):
        """验证是否为有效图片URL"""
        if not url or not url.startswith('http'):
            return False
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
        return any(url.lower().endswith(ext) for ext in valid_extensions) or 'gstatic.com' in url