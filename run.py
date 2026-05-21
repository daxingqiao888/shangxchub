#!/usr/bin/env python3
"""
图片采集工具 - 启动入口
快速启动: python run.py
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_gui import main

if __name__ == '__main__':
    main()