#!/usr/bin/env python3
"""
500px 图片源模块
API: https://500px.com/developers/api
需要 API Key（免费版有请求限制）
"""
import logging
from .collector import ImageCollector

logger = logging.getLogger(__name__)

# 500px API v1
PX500_API_URL = "https://api.500px.com/v1/photos"


class FiveHundredPxSource:
    """500px 图片源"""

    name = "500px"
    display_name = "500px"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key

    def search(self, keyword, count=20):
        """搜索图片"""
        if not self.api_key:
            logger.warning("500px 需要 API Key，使用备用方案...")
            return self._fallback_search(keyword, count)

        results = []
        page = 1
        rpp = min(100, count)  # results per page

        while len(results) < count:
            try:
                params = {
                    'term': keyword,
                    'page': page,
                    'rpp': rpp,
                    'sort': 'released',  # 最新发布
                    'image_size': ['4', '5', '6'],  # 4=400px, 5=600px, 6=2048px
                    'exclude': 'NSFW'
                }

                # 添加 API Key
                params['consumer_key'] = self.api_key

                response = self.collector.session.get(
                    PX500_API_URL,
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

                        # 获取最高质量图片URL
                        images = photo.get('images', [])
                        img_url = None
                        for img in images:
                            if img.get('size') == 6:
                                img_url = img.get('url')
                                break
                        if not img_url and images:
                            img_url = images[0].get('url')

                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"500px_{photo.get('id')}.jpg",
                                'width': photo.get('width'),
                                'height': photo.get('height'),
                                'author': photo.get('user', {}).get('fullname'),
                                'camera': photo.get('camera', ''),
                                'referer': 'https://500px.com/'
                            })

                    page += 1
                    logger.info(f"500px: 获取第 {page-1} 页, 累计 {len(results)} 张")

                else:
                    logger.warning(f"500px API 错误: {response.status_code}")
                    break

            except Exception as e:
                logger.error(f"500px 搜索失败: {str(e)}")
                break

        return results

    def _fallback_search(self, keyword, count):
        """备用方案：网页爬取"""
        logger.info("使用 500px 网页备用方案...")
        results = []

        try:
            # 搜索页面
            search_url = f"https://500px.com/search?photo=true&q={keyword}&type=photos"
            response = self.collector.session.get(search_url, timeout=30)

            if response.status_code == 200:
                import re
                # 提取图片信息 - 500px的HTML中包含图片JSON
                # 查找 data-photo-id 或 photo 相关信息
                import json

                # 查找 JSON 数据
                pattern = r'photo_ids\s*:\s*\[([^\]]+)\]'
                match = re.search(pattern, response.text)

                if match:
                    photo_ids = match.group(1).split(',')
                    for pid in photo_ids[:count]:
                        results.append({
                            'url': f'https://images.500px.io/photos/{pid}/sizes/6/nocache/1',
                            'filename': f"500px_{pid}.jpg",
                            'referer': 'https://500px.com/'
                        })

            logger.info(f"500px (备用): 获取 {len(results)} 张")

        except Exception as e:
            logger.error(f"500px 备用方案失败: {str(e)}")

        return results

    def get_photo_details(self, photo_id):
        """获取单张照片详情"""
        if not self.api_key:
            return None

        try:
            params = {
                'photo_id': photo_id,
                'consumer_key': self.api_key,
                'image_size': ['4', '5', '6']
            }

            response = self.collector.session.get(
                f"{PX500_API_URL}/{photo_id}",
                params=params,
                timeout=self.collector.timeout
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.error(f"获取 500px 照片详情失败: {str(e)}")

        return None