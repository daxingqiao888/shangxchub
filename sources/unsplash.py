#!/usr/bin/env python3
"""
Unsplash 图片源模块
API: https://unsplash.com/developers
免费商用，无需授权
"""
import random
import logging
from .collector import ImageCollector

logger = logging.getLogger(__name__)

# Unsplash API (无需KEY也可以使用，但有频率限制)
# 免费版：50次/小时
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


class UnsplashSource:
    """Unsplash 图片源"""

    name = "unsplash"
    display_name = "Unsplash"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key
        if api_key:
            collector.session.headers['Authorization'] = f'Client-ID {api_key}'

    def search(self, keyword, count=20):
        """搜索图片"""
        results = []
        page = 1
        per_page = min(30, count)

        while len(results) < count:
            try:
                params = {
                    'query': keyword,
                    'page': page,
                    'per_page': per_page,
                    'orientation': 'landscape'
                }

                response = self.collector.session.get(
                    UNSPLASH_API_URL,
                    params=params,
                    timeout=self.collector.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    photos = data.get('results', [])

                    if not photos:
                        break

                    for photo in photos:
                        if len(results) >= count:
                            break

                        # 获取不同尺寸的图片URL
                        urls = photo.get('urls', {})
                        img_url = urls.get('regular') or urls.get('small') or urls.get('full')

                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"{photo.get('id', 'unsplash')}.jpg",
                                'width': photo.get('width'),
                                'height': photo.get('height'),
                                'author': photo.get('user', {}).get('name'),
                                'referer': 'https://unsplash.com/'
                            })

                    page += 1
                    logger.info(f"Unsplash: 获取第 {page-1} 页, 累计 {len(results)} 张")

                elif response.status_code == 403:
                    logger.warning("Unsplash API 达到限额，尝试备用方案...")
                    # 无API Key时的备用方案：直接爬取网页
                    results.extend(self._fallback_search(keyword, count))
                    break
                else:
                    logger.warning(f"Unsplash API 错误: {response.status_code}")
                    break

            except Exception as e:
                logger.error(f"Unsplash 搜索失败: {str(e)}")
                break

        return results

    def _fallback_search(self, keyword, count):
        """备用方案：无API Key时从网页获取"""
        logger.info("使用 Unsplash 网页备用方案...")
        results = []

        try:
            # 搜索页面
            search_url = f"https://unsplash.com/s/photos/{keyword}"
            response = self.collector.session.get(search_url, timeout=30)

            if response.status_code == 200:
                # 简单解析（需要更复杂的解析库）
                import re
                # 提取图片URL模式
                pattern = r'https://images\.unsplash\.com/photo-[^"?]+'
                matches = re.findall(pattern, response.text)
                seen = set()

                for url in matches:
                    if len(results) >= count:
                        break
                    if url not in seen:
                        seen.add(url)
                        results.append({
                            'url': url + '?w=800',
                            'filename': f"unsplash_{hash(url) % 100000}.jpg",
                            'referer': 'https://unsplash.com/'
                        })

        except Exception as e:
            logger.error(f"Unsplash 备用方案失败: {str(e)}")

        return results