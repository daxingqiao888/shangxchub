#!/usr/bin/env python3
"""
媒体采集源模块 - 支持多种内容类型
"""
from .collector import ImageCollector
from .content_types import CONTENT_TYPES, TYPE_EXTENSIONS
from .generic import GenericSource

# 图片源（保留专用类，性能更优）
from .unsplash import UnsplashSource
from .pexels import PexelsSource
from .bing import BingSource
from .google import GoogleSource
from .px500 import FiveHundredPxSource
from .baidu import BaiduSource

# 专用图片源注册表（保留兼容）
IMAGE_SOURCES = {
    'unsplash': UnsplashSource,
    'pexels': PexelsSource,
    'bing': BingSource,
    'google': GoogleSource,
    '500px': FiveHundredPxSource,
    'baidu': BaiduSource,
}


def get_sources_for_type(content_type):
    """获取指定类型的所有来源"""
    if content_type not in CONTENT_TYPES:
        return []
    return list(CONTENT_TYPES[content_type]['sources'].items())


def get_content_types():
    """获取所有内容类型"""
    return [(k, v['name'], v['icon']) for k, v in CONTENT_TYPES.items()]


def create_source(source_key, collector, content_type='image', **kwargs):
    """创建来源实例 - 智能选择专用类或通用类"""
    # 图片类型优先使用专用类
    if content_type == 'image' and source_key in IMAGE_SOURCES:
        return IMAGE_SOURCES[source_key](collector, **kwargs)

    # 其他类型使用通用类
    type_config = CONTENT_TYPES.get(content_type, {})
    source_configs = type_config.get('sources', {})
    if source_key in source_configs:
        return GenericSource(collector, source_key, source_configs[source_key])

    raise ValueError(f"未知来源: {source_key}")


# 向后兼容的 SOURCES 别名
SOURCES = IMAGE_SOURCES