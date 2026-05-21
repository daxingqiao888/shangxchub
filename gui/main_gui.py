#!/usr/bin/env python3
"""
图片采集工具 - GUI 界面
基于 PySimpleGUI
"""
import os
import sys
import threading
import json
import logging
from pathlib import Path

import PySimpleGUI as sg
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources import SOURCES, ImageCollector, create_source

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='image_collector.log',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class ImageCollectorGUI:
    """图片采集工具 GUI"""

    # 可用的图片来源
    AVAILABLE_SOURCES = [
        ('unsplash', 'Unsplash', True),
        ('pexels', 'Pexels', True),
        ('bing', 'Bing Images', False),
        ('google', 'Google Images', False),
        ('500px', '500px', False),
    ]

    def __init__(self):
        self.collector = None
        self.is_downloading = False
        self.download_thread = None

        # 配置主题
        sg.theme('DarkBlue13')

        # 加载配置
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent.parent / 'config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'default_count': 20,
            'storage_path': '',
            'enabled_sources': ['unsplash', 'pexels']
        }

    def _save_config(self):
        """保存配置"""
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def create_window(self):
        """创建主窗口"""
        # 来源选择 - 使用复选框组
        source_checkboxes = []
        for key, label, default in self.AVAILABLE_SOURCES:
            checked = key in self.config.get('enabled_sources', [])
            source_checkboxes.append(
                sg.Checkbox(label, key=f'source_{key}', default=checked, size=(15, 1))
            )

        # 来源面板
        source_frame = sg.Frame(
            '图片来源 (可多选)',
            [source_checkboxes],
            element_justification='left'
        )

        # 配置面板
        config_frame = sg.Frame(
            '采集配置',
            [
                [sg.Text('关键词:', size=(10, 1)), sg.Input(key='keyword', size=(40, 1), focus=True)],
                [sg.Text('采集数量:', size=(10, 1)), sg.InputText(
                    str(self.config.get('default_count', 20)),
                    key='count', size=(10, 1)
                ), sg.Text('张/每个来源')],
                [sg.Text('存储路径:', size=(10, 1)),
                 sg.Input(key='storage_path', size=(35, 1)),
                 sg.FolderBrowse(button_text='选择', key='browse_folder')],
            ],
            element_justification='left'
        )

        # API 配置（可选）
        api_frame = sg.Frame(
            'API 配置 (可选)',
            [
                [sg.Text('Unsplash API Key:', size=(15, 1)),
                 sg.Input(password_char='*', key='unsplash_key', size=(30, 1)),
                 sg.Text('无则免费限流', text_color='gray')],
                [sg.Text('Pexels API Key:', size=(15, 1)),
                 sg.Input(password_char='*', key='pexels_key', size=(30, 1))],
                [sg.Text('SerpAPI Key:', size=(15, 1)),
                 sg.Input(password_char='*', key='google_key', size=(30, 1)),
                 sg.Text('Google必填', text_color='gray')],
                [sg.Text('500px API Key:', size=(15, 1)),
                 sg.Input(password_char='*', key='500px_key', size=(30, 1))],
            ],
            element_justification='left'
        )

        # 进度显示
        progress_frame = sg.Frame(
            '进度',
            [
                [sg.ProgressBar(100, key='progress_bar', size=(50, 20), expand_x=True)],
                [sg.Text('等待任务...', key='status_text', size=(60, 1))],
            ]
        )

        # 日志输出
        log_frame = sg.Frame(
            '日志输出',
            [
                [sg.Multiline(size=(70, 12), key='log_output', autoscroll=True, disabled=True)]
            ]
        )

        # 布局
        layout = [
            [sg.TitleBar('图片采集工具 v1.0')],
            [source_frame],
            [config_frame],
            [api_frame],
            [progress_frame],
            [sg.HorizontalSeparator()],
            [
                sg.Button('开始采集', key='start', size=(15, 1), button_color=('white', 'green')),
                sg.Button('停止', key='stop', size=(15, 1), disabled=True, button_color=('white', 'red')),
                sg.Button('清空日志', key='clear_log', size=(15, 1)),
                sg.Button('退出', key='exit', size=(15, 1)),
            ],
            [sg.HorizontalSeparator()],
            [log_frame],
        ]

        return sg.Window('图片采集工具 v1.0', layout, finalize=True)

    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        window['log_output'].print(log_message, end='')
        logger.info(message)

    def run(self):
        """运行GUI"""
        global window
        window = self.create_window()

        # 自动填充存储路径
        if self.config.get('storage_path'):
            window['storage_path'].update(self.config['storage_path'])

        self.log("图片采集工具已启动")
        self.log("请选择图片来源、输入关键词和数量，然后点击开始采集")

        while True:
            event, values = window.read()

            if event in (sg.WINDOW_CLOSED, 'exit'):
                if self.is_downloading:
                    self.log("请先停止当前任务再退出")
                else:
                    break

            elif event == 'clear_log':
                window['log_output'].update('')

            elif event == 'browse_folder':
                # 文件夹选择后自动更新配置
                pass

            elif event == 'start':
                self._start_download(values)

            elif event == 'stop':
                self._stop_download()

        window.close()

    def _start_download(self, values):
        """开始下载"""
        keyword = values.get('keyword', '').strip()
        count = values.get('count', '20')
        storage_path = values.get('storage_path', '').strip()

        # 验证输入
        if not keyword:
            sg.popup_error('请输入关键词!')
            return

        if not storage_path:
            sg.popup_error('请选择存储路径!')
            return

        try:
            count = int(count)
            if count <= 0:
                raise ValueError()
        except:
            sg.popup_error('请输入有效的采集数量!')
            return

        # 获取选中的来源
        selected_sources = []
        for key, label, _ in self.AVAILABLE_SOURCES:
            if values.get(f'source_{key}', False):
                selected_sources.append(key)

        if not selected_sources:
            sg.popup_error('请至少选择一个图片来源!')
            return

        # 保存配置
        self.config['enabled_sources'] = selected_sources
        self.config['storage_path'] = storage_path
        self.config['default_count'] = count
        self._save_config()

        # 保存API Keys
        api_keys = {
            'unsplash': values.get('unsplash_key', '').strip(),
            'pexels': values.get('pexels_key', '').strip(),
            'google': values.get('google_key', '').strip(),
            '500px': values.get('500px_key', '').strip(),
        }

        # 更新UI状态
        self.is_downloading = True
        window['start'].update(disabled=True)
        window['stop'].update(disabled=False)
        window['keyword'].update(disabled=True)
        window['count'].update(disabled=True)

        for key, _, _ in self.AVAILABLE_SOURCES:
            window[f'source_{key}'].update(disabled=True)

        # 在后台线程执行下载
        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(keyword, count, storage_path, selected_sources, api_keys),
            daemon=True
        )
        self.download_thread.start()

    def _download_worker(self, keyword, count, storage_path, sources, api_keys):
        """下载工作线程"""
        try:
            self.log(f"任务开始: 关键词={keyword}, 数量={count}, 来源={', '.join(sources)}")

            # 创建采集器
            self.collector = ImageCollector(storage_path)

            total_downloaded = 0
            total_skipped = 0
            tasks = len(sources) * count

            for source_name in sources:
                if not self.is_downloading:
                    self.log("任务已停止")
                    break

                self.log(f"正在从 {source_name} 获取图片...")

                # 创建图片来源实例
                source_class = SOURCES.get(source_name)
                if not source_class:
                    continue

                kwargs = {}
                if api_keys.get(source_name):
                    kwargs['api_key'] = api_keys[source_name]
                # Google 特殊处理
                if source_name == 'google' and not api_keys.get('google'):
                    kwargs['use_ddg'] = True

                source = source_class(self.collector, **kwargs)

                # 搜索图片
                images = source.search(keyword, count)
                self.log(f"{source_name}: 找到 {len(images)} 张图片")

                # 下载图片
                for i, img_info in enumerate(images):
                    if not self.is_downloading:
                        break

                    self.log(f"下载 {i+1}/{len(images)}: {img_info.get('filename', 'unknown')}")

                    file_path, _ = self.collector.download_image(
                        url=img_info['url'],
                        filename=img_info['filename'],
                        keyword=keyword,
                        source=source_name,
                        referer=img_info.get('referer')
                    )

                    if file_path:
                        total_downloaded += 1
                    else:
                        total_skipped += 1

                    # 更新进度
                    progress = int((total_downloaded + total_skipped) / tasks * 100)
                    window['progress_bar'].update(progress)
                    window['status_text'].update(
                        f"已完成 {total_downloaded + total_skipped}/{tasks}, "
                        f"成功 {total_downloaded}, 跳过 {total_skipped}"
                    )

            self.log(f"任务完成! 成功: {total_downloaded}, 跳过: {total_skipped}")

        except Exception as e:
            self.log(f"错误: {str(e)}")
            logger.exception("下载任务异常")

        finally:
            # 恢复UI状态
            window['start'].update(disabled=False)
            window['stop'].update(disabled=True)
            window['keyword'].update(disabled=False)
            window['count'].update(disabled=False)

            for key, _, _ in self.AVAILABLE_SOURCES:
                window[f'source_{key}'].update(disabled=False)

            window['status_text'].update('任务完成')
            self.is_downloading = False

    def _stop_download(self):
        """停止下载"""
        self.is_downloading = False
        self.log("正在停止任务...")


def main():
    """主函数"""
    try:
        app = ImageCollectorGUI()
        app.run()
    except Exception as e:
        sg.popup_error(f"启动失败: {str(e)}")
        logger.exception("程序启动异常")


if __name__ == '__main__':
    main()