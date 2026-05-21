#!/usr/bin/env python3
"""
Pexels 图片源模块
API: https://www.pexels.com/api/
免费商用，需申请API Key（可选）
"""
import logging
from .collector import ImageCollector

logger = logging.getLogger(__name__)

PEXELS_API_URL = "https://api.pexels.com/v1/search"


class PexelsSource:
    """Pexels 图片源"""

    name = "pexels"
    display_name = "Pexels"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key
        if api_key:
            collector.session.headers['Authorization'] = api_key

    def search(self, keyword, count=20):
        """搜索图片"""
        results = []
        page = 1
        per_page = min(80, count)

        while len(results) < count:
            try:
                params = {
                    'query': keyword,
                    'page': page,
                    'per_page': per_page,
                    'orientation': 'landscape'
                }

                response = self.collector.session.get(
                    PEXELS_API_URL,
                    params=params,
                    timeout=self.collector.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    photos = data.get('photos', [])

                    if not photos:
                        break

                    for photo in photos:
                        if len(results) >= count:
                            break

                        src = photo.get('src', {})
                        img_url = src.get('large2x') or src.get('large') or src.get('medium')

                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"{photo.get('id', 'pexels')}.jpg",
                                'width': photo.get('width'),
                                'height': photo.get('height'),
                                'author': photo.get('photographer'),
                                'referer': 'https://www.pexels.com/'
                            })

                    page += 1
                    logger.info(f"Pexels: 获取第 {page-1} 页, 累计 {len(results)} 张")

                elif response.status_code == 401:
                    logger.warning("Pexels API Key 无效，尝试备用方案...")
                    results.extend(self._fallback_search(keyword, count))
                    break
                else:
                    logger.warning(f"Pexels API 错误: {response.status_code}")
                    break

            except Exception as e:
                logger.error(f"Pexels 搜索失败: {str(e)}")
                break

        return results

    def _fallback_search(self, keyword, count):
        """备用方案：网页爬取"""
        logger.info("使用 Pexels 网页备用方案...")
        results = []

        try:
            search_url = f"https://www.pexels.com/search/{keyword}/"
            response = self.collector.session.get(search_url, timeout=30)

            if response.status_code == 200:
                import re
                # 提取图片URL
                pattern = r'https://images\.pexels\.com/photos/[^"?]+\?[^"?]+'
                matches = re.findall(pattern, response.text)
                seen = set()

                for url in matches:
                    if len(results) >= count:
                        break
                    if url not in seen:
                        seen.add(url)
                        results.append({
                            'url': url,
                            'filename': f"pexels_{hash(url) % 100000}.jpg",
                            'referer': 'https://www.pexels.com/'
                        })

        except Exception as e:
            logger.error(f"Pexels 备用方案失败: {str(e)}")

        return results