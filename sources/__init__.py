#!/usr/bin/env python3
"""
图片来源模块
"""
from .collector import ImageCollector
from .unsplash import UnsplashSource
from .pexels import PexelsSource
from .bing import BingSource
from .google import GoogleSource
from .px500 import FiveHundredPxSource

__all__ = [
    'ImageCollector',
    'UnsplashSource',
    'PexelsSource',
    'BingSource',
    'GoogleSource',
    'FiveHundredPxSource',
]

# 图片源注册表
SOURCES = {
    'unsplash': UnsplashSource,
    'pexels': PexelsSource,
    'bing': BingSource,
    'google': GoogleSource,
    '500px': FiveHundredPxSource,
}


def create_source(name, collector, **kwargs):
    """创建图片来源实例"""
    source_class = SOURCES.get(name.lower())
    if source_class:
        return source_class(collector, **kwargs)
    raise ValueError(f"未知的图片来源: {name}")