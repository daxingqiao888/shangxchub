#!/usr/bin/env python3
"""
媒体采集工具 - GUI 界面 v2.4
"""
import os, sys, threading, json, logging, subprocess
from pathlib import Path

import PySimpleGUI as sg
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from sources import get_content_types, get_sources_for_type, create_source, ImageCollector
from sources.content_types import CONTENT_TYPES, TOPIC_CATEGORIES, TYPE_FILTERS
from utils.cloud_manager import CloudDriveManager
from utils.proxy import detect_system_proxy, detect_local_proxy

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename=str(Path(__file__).parent.parent / 'image_collector.log'), encoding='utf-8'
)
logger = logging.getLogger(__name__)

FREE_SEARCH = '（自由搜索）'


class ImageCollectorGUI:
    QUICK_PATHS = {
        '桌面': '~/Desktop', '下载': '~/Downloads',
        '文稿': '~/Documents', '图片': '~/Pictures',
    }

    def __init__(self):
        self.is_downloading = False
        self.content_type = 'image'
        sg.theme('DarkBlue13')
        self.config = self._load_config()
        self.cloud = CloudDriveManager()
        self._source_frames = {}
        self._source_checkboxes = {}
        self._filter_frames = {}
        self._filter_widgets = {}
        self._type_keys = []

    def _load_config(self):
        config_path = Path(__file__).parent.parent / 'config.json'
        default = {
            'default_count': 20,
            'storage_path': str(Path.home() / '媒体采集'),
            'content_type': 'image',
            'enabled_sources': {},
            'cloud_drive': '',
        }
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding='utf-8'))
                # 兼容旧格式：enabled_sources 是 list 时转为 dict
                if isinstance(cfg.get('enabled_sources'), list):
                    cfg['enabled_sources'] = {'image': cfg['enabled_sources']}
                default.update(cfg)
            except:
                pass
        return default

    def _save_config(self):
        config_path = Path(__file__).parent.parent / 'config.json'
        config_path.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding='utf-8')

    def _open_folder(self, path):
        p = Path(path).expanduser()
        if p.exists():
            subprocess.run(['open', str(p)])

    def _build_source_frames(self):
        """预创建所有内容类型的来源框架"""
        self._source_frames = {}
        self._source_checkboxes = {}

        for type_key, type_name, icon in get_content_types():
            sources = get_sources_for_type(type_key)
            enabled = self.config.get('enabled_sources', {}).get(type_key, [])
            cks = []
            rows = []
            row = []

            for i, (skey, sinfo) in enumerate(sources):
                ck = f'src_{type_key}_{skey}'
                cks.append(ck)
                checked = skey in enabled if enabled else (i < 2)
                label = sinfo['name']
                row.append(sg.Checkbox(label, key=ck, default=checked, size=(20, 1), font=('', 10)))
                if len(row) == 3:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)

            # 全选/全不选紧凑按钮
            rows.insert(0, [
                sg.Text('', size=(40, 1)),
                sg.Button('全选', key=f'selall_{type_key}', size=(4, 1), font=('', 8)),
                sg.Button('全不选', key=f'dselall_{type_key}', size=(5, 1), font=('', 8)),
            ])

            self._source_checkboxes[type_key] = cks
            self._source_frames[type_key] = sg.Frame(
                f'媒体源头 - {type_name}',
                rows,
                key=f'source_frame_{type_key}',
                visible=(type_key == self.content_type),
                element_justification='left'
            )

    def _build_filter_frames(self):
        """预创建所有类型的筛选维度框架"""
        self._filter_frames = {}
        self._filter_widgets = {}  # {type_key: {dim_name: combo_key}}

        for type_key, filters in TYPE_FILTERS.items():
            if not filters:
                self._filter_frames[type_key] = sg.Frame('筛选维度', [[sg.Text('无')]],
                                                          key=f'filter_frame_{type_key}',
                                                          visible=False)
                self._filter_widgets[type_key] = {}
                continue

            row = []
            widgets = {}
            for dim_name, options in filters.items():
                key = f'filter_{type_key}_{dim_name}'
                widgets[dim_name] = key
                row.append(sg.Text(f'{dim_name}:', size=(5, 1)))
                row.append(sg.Combo(options, default_value='不限', key=key,
                                   size=(10, 1), readonly=True, enable_events=True))

            self._filter_widgets[type_key] = widgets
            self._filter_frames[type_key] = sg.Frame('筛选维度', [row],
                                                      key=f'filter_frame_{type_key}',
                                                      visible=(type_key == self.content_type))

    def create_window(self):
        self.content_type = self.config.get('content_type', 'image')
        self._build_source_frames()
        self._build_filter_frames()

        # === 采集类型 (两行，按钮式) ===
        type_row1, type_row2 = [], []
        self._type_keys = []
        SEL_COLOR = ('#FFFFFF', '#1565C0')
        DEF_COLOR = (sg.theme_text_color(), sg.theme_button_color()[1])

        for i, (key, name, icon) in enumerate(get_content_types()):
            tk = f'type_{key}'
            self._type_keys.append(tk)
            is_sel = (key == self.content_type)
            btn = sg.Button(f'{icon} {name}', key=tk, size=(8, 1),
                          button_color=SEL_COLOR if is_sel else DEF_COLOR,
                          font=('', 10))
            (type_row1 if i < 4 else type_row2).append(btn)

        type_frame = sg.Frame('采集类型', [type_row1, type_row2])

        # === 采集配置 ===
        storage_path = self.config.get('storage_path', str(Path.home() / '媒体采集'))
        quick_btns = [sg.Button(l, key=f'quick_{l}', size=(5, 1)) for l in self.QUICK_PATHS]

        topics = TOPIC_CATEGORIES.get(self.content_type, [])
        topic_default = self.config.get('topic', '')

        config_frame = sg.Frame('采集配置', [
            [sg.Text('主题:', size=(5, 1), font=('', 10)),
             sg.Combo([FREE_SEARCH] + topics, default_value=topic_default if topic_default else FREE_SEARCH,
                      key='topic', size=(18, 1), enable_events=True, readonly=True, font=('', 10)),
             sg.Text('关键词:', size=(5, 1), font=('', 10)), sg.Input('', key='keyword', size=(16, 1), focus=True, font=('', 10)),
             sg.Text('数量:', size=(5, 1), font=('', 10)), sg.Input(str(self.config.get('default_count', 20)), key='count', size=(6, 1), font=('', 10)),
             sg.Text('个/源', size=(5, 1), font=('', 10))],
            [sg.Text('路径:', size=(5, 1), font=('', 10)), sg.Input(storage_path, key='storage_path', size=(52, 1), font=('', 10)),
             sg.FolderBrowse('选'), sg.Button('开', key='open_folder', size=(3, 1))],
            [sg.Text('快捷:', size=(5, 1), font=('', 10))] + quick_btns,
        ])

        # === 来源框架 + 筛选框架 ===
        source_frames_list = list(self._source_frames.values())
        filter_frames_list = list(self._filter_frames.values())

        # === 核心操作按钮 ===
        action_row = [
            sg.Button('▶ 开始采集', key='start', size=(14, 1), button_color=('white', 'green'), font=('', 10, 'bold')),
            sg.Button('■ 停止', key='stop', size=(8, 1), disabled=True, button_color=('white', 'red')),
        ]

        # === 右侧栏: 网址直采 / 网盘 / 代理 ===
        cloud_drives = self.cloud.list_drives()
        cloud_names = ['（不使用网盘）']
        for d in cloud_drives:
            cloud_names.append(f"{d['name']} {'✓已装' if d['installed'] else '✗未装'}")

        sel_cloud = self.config.get('cloud_drive', '')
        cloud_def = '（不使用网盘）'
        for n in cloud_names:
            if sel_cloud and sel_cloud in n:
                cloud_def = n; break

        custom_url_frame = sg.Frame('网址直采', [
            [sg.Checkbox('启用网址直采', key='custom_url_enabled', size=(18, 1), enable_events=True, font=('', 10))],
            [sg.Text('URL:', size=(3, 1)), sg.Input('', key='custom_url', size=(28, 1), disabled=True)],
            [sg.Text('选择器:', size=(5, 1)), sg.Input('img[src*="http"]', key='custom_selector', size=(26, 1), disabled=True)],
        ])

        cloud_frame = sg.Frame('网盘同步', [
            [sg.Combo(cloud_names, default_value=cloud_def, key='cloud_drive', size=(32, 1),
                      enable_events=True, readonly=True)],
            [sg.Button('链接网盘', key='setup_cloud', size=(10, 1)),
             sg.Text('', key='cloud_status', text_color='cyan', font=('', 9))],
        ])

        proxy = self.config.get('proxy', {})
        proxy_frame = sg.Frame('代理', [
            [sg.Checkbox('启用代理（自动检测）', key='proxy_enabled',
                         default=proxy.get('enabled', False), enable_events=True)],
            [sg.Button('检测代理', key='detect_proxy', size=(10, 1)),
             sg.Text('', key='proxy_status', text_color='cyan', font=('', 9))],
        ])

        # === 进度 + 状态合并行 ===
        progress_row = [
            sg.ProgressBar(100, key='progress_bar', size=(60, 16), expand_x=True),
            sg.Text('  就绪', key='status_text', size=(30, 1), text_color='white', font=('', 9)),
        ]

        # === 底部按钮 ===
        btn_row = [
            sg.Button('清空日志', key='clear_log', size=(8, 1)),
            sg.Checkbox('显示日志', key='toggle_log', default=True, enable_events=True, font=('', 9)),
            sg.Text('', size=(10, 1), expand_x=True),
            sg.Text('v2.5', text_color='gray', font=('', 8)),
            sg.Button('退出', key='exit', size=(6, 1)),
        ]

        # === 日志（可折叠） ===
        log_frame = sg.Frame('日志', [
            [sg.Multiline(size=(90, 6), key='log_output', autoscroll=True, disabled=True, expand_x=True)]
        ], key='log_frame')

        # === 布局: 左侧主体 + 右侧边栏 ===
        # 顺序: 采集类型 → 采集配置 → 操作按钮 → 媒体源头 → 筛选维度
        left_col = sg.Column([
            [type_frame],
            [sg.Text('', font=('', 2))],
            [config_frame],
            [sg.Text('', font=('', 2))],
            [sg.Column([action_row], element_justification='center')],
            [sg.Text('', font=('', 2))],
            source_frames_list,
            [sg.Text('', font=('', 2))],
            filter_frames_list,
        ], expand_x=True, element_justification='left')

        right_col = sg.Column([
            [custom_url_frame],
            [cloud_frame],
            [proxy_frame],
        ])

        layout = [
            [sg.Text('媒体采集工具', font=('Any', 18, 'bold'), justification='left',
                     text_color='#4FC3F7', pad=(10, (10, 0)))],
            [left_col, sg.VerticalSeparator(), right_col],
            [sg.HorizontalSeparator()],
            progress_row,
            [sg.HorizontalSeparator()],
            btn_row,
            [log_frame],
        ]

        return sg.Window('媒体采集工具 v2.5', layout, finalize=True, resizable=True)

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        window['log_output'].print(f"[{ts}] {msg}\n", end='')
        logger.info(msg)

    def _get_filter_keywords(self):
        """从当前筛选选择中获取附加的中文关键词"""
        keywords = []
        widgets = self._filter_widgets.get(self.content_type, {})
        for dim_name, key in widgets.items():
            try:
                val = window[key].get()
            except Exception:
                continue
            if val and val != '不限':
                keywords.append(val)
        return keywords

    def _handle_cloud(self, val):
        if not val or val == '（不使用网盘）':
            window['cloud_status'].update('')
            return
        for d in self.cloud.list_drives():
            if d['name'] in val:
                if not d['installed']:
                    window['cloud_status'].update(f'{d["name"]} 未安装')
                    if sg.popup_yes_no(f'{d["name"]} 未安装。\n打开下载页面？', title='安装'):
                        self.cloud.open_install(d['key'])
                    return
                ok, msg = self.cloud.setup_link(d['key'])
                if ok:
                    window['cloud_status'].update(f'已链接 {d["name"]}')
                    window['storage_path'].update(msg)
                    self.log(f'网盘 {d["name"]} 已成功链接到: {msg}')
                else:
                    window['cloud_status'].update(f'链接失败: {msg}')
                    self.log(f'网盘链接失败: {msg}')
                return

    def run(self):
        global window
        window = self.create_window()
        self.log('媒体采集工具 v2.5 已启动')

        installed = [d['name'] for d in self.cloud.list_drives() if d['installed']]
        if installed:
            self.log(f'检测到网盘: {", ".join(installed)}')

        while True:
            event, values = window.read()

            if event in (sg.WINDOW_CLOSED, 'exit'):
                if self.is_downloading:
                    self.log('请先停止任务再退出')
                else:
                    break

            elif event.startswith('type_'):
                new_type = event.replace('type_', '')
                if new_type != self.content_type:
                    old_frame = self._source_frames.get(self.content_type)
                    if old_frame:
                        old_frame.update(visible=False)
                    new_frame = self._source_frames.get(new_type)
                    if new_frame:
                        new_frame.update(visible=True)
                    old_filter = self._filter_frames.get(self.content_type)
                    if old_filter:
                        old_filter.update(visible=False)
                    new_filter = self._filter_frames.get(new_type)
                    if new_filter:
                        new_filter.update(visible=True)
                    self.content_type = new_type
                    self._update_type_buttons()
                    topics = TOPIC_CATEGORIES.get(new_type, [])
                    window['topic'].update(values=[FREE_SEARCH] + topics,
                                           value=FREE_SEARCH)
                    window['keyword'].update('')
                    type_name = CONTENT_TYPES[new_type]['name']
                    self.log(f'切换到: {type_name}')

            elif event == 'topic':
                topic = values['topic']
                if topic and topic != FREE_SEARCH:
                    window['keyword'].update(topic)
                    self.log(f'主题: {topic}')

            elif event == 'custom_url_enabled':
                enabled = values['custom_url_enabled']
                window['custom_url'].update(disabled=not enabled)
                window['custom_selector'].update(disabled=not enabled)
                if enabled:
                    window['keyword'].update(disabled=True)
                    window['topic'].update(disabled=True)
                    self.log('网址直采模式: 请输入目标URL和CSS选择器')
                else:
                    window['keyword'].update(disabled=False)
                    window['topic'].update(disabled=False)

            elif event == 'clear_log':
                window['log_output'].update('')

            elif event == 'detect_proxy':
                sys_proxy = detect_system_proxy()
                if sys_proxy:
                    window['proxy_status'].update(f'已检测到系统代理: {sys_proxy}')
                    self.log(f'代理检测: 系统代理 {sys_proxy}')
                else:
                    local = detect_local_proxy()
                    if local:
                        window['proxy_status'].update(f'已检测到本地代理: {local}')
                        self.log(f'代理检测: 本地代理 {local}')
                    else:
                        window['proxy_status'].update('未检测到代理，请确保代理软件已运行')
                        self.log('代理检测: 未发现可用代理')
                window['proxy_enabled'].update(True)

            elif event == 'proxy_enabled':
                if values['proxy_enabled']:
                    window['detect_proxy'].click()

            elif event == 'cloud_drive':
                self._handle_cloud(values['cloud_drive'])
            elif event == 'setup_cloud':
                cv = values.get('cloud_drive', '')
                if cv and cv != '（不使用网盘）':
                    self._handle_cloud(cv)

            elif event == 'open_folder':
                p = values.get('storage_path', '')
                if p: self._open_folder(p)

            elif event.startswith('quick_'):
                label = event.replace('quick_', '')
                if label in self.QUICK_PATHS:
                    window['storage_path'].update(str(Path(self.QUICK_PATHS[label]).expanduser()))

            elif event.startswith('selall_'):
                type_key = event.replace('selall_', '')
                for ck in self._source_checkboxes.get(type_key, []):
                    window[ck].update(True)
            elif event.startswith('dselall_'):
                type_key = event.replace('dselall_', '')
                for ck in self._source_checkboxes.get(type_key, []):
                    window[ck].update(False)

            elif event == 'toggle_log':
                window['log_frame'].update(visible=values['toggle_log'])

            elif event == 'start':
                self._start_download(values)
            elif event == 'stop':
                self._stop_download()

        window.close()

    def _update_type_buttons(self):
        """高亮当前选中的采集类型按钮"""
        SEL = ('#FFFFFF', '#1565C0')
        DEF = (sg.theme_text_color(), sg.theme_button_color()[1])
        for tk in self._type_keys:
            window[tk].update(button_color=SEL if tk == f'type_{self.content_type}' else DEF)

    def _set_ui_busy(self, busy):
        """统一设置 UI 控件的启用/禁用状态"""
        window['start'].update(disabled=busy)
        window['stop'].update(disabled=not busy)
        for k in ['keyword', 'count']:
            window[k].update(disabled=busy)
        for ck in self._source_checkboxes.get(self.content_type, []):
            window[ck].update(disabled=busy)
        for tk in self._type_keys:
            window[tk].update(disabled=busy)
        for btn in [f'selall_{self.content_type}', f'dselall_{self.content_type}']:
            window[btn].update(disabled=busy)

    def _start_download(self, values):
        keyword = values.get('keyword', '').strip()
        count = values.get('count', '20')
        storage_path = values.get('storage_path', '').strip()
        ctype = self.content_type
        custom_enabled = values.get('custom_url_enabled', False)
        custom_url = values.get('custom_url', '').strip()
        custom_selector = values.get('custom_selector', 'img[src*="http"]').strip()

        if custom_enabled:
            if not custom_url:
                sg.popup_error('请输入目标网页URL!')
                return
            keyword = custom_url.split('/')[2] if '://' in custom_url else custom_url
        else:
            if not keyword:
                sg.popup_error('请输入关键词!')
                return

        if not storage_path:
            sg.popup_error('请选择存储路径!')
            return
        try:
            count = int(count)
            if count <= 0: raise ValueError()
        except:
            sg.popup_error('请输入有效的数量!')
            return

        # 合并筛选关键词
        if not custom_enabled:
            filter_kws = self._get_filter_keywords()
            if filter_kws:
                keyword = keyword + ' ' + ' '.join(filter_kws)
                self.log(f'筛选: {" ".join(filter_kws)}')

        if custom_enabled:
            selected = ['__custom__']
        else:
            selected = [ck.split('_', 2)[2] for ck in self._source_checkboxes.get(self.content_type, [])
                        if values.get(ck, False)]
            if not selected:
                sg.popup_error('请至少选择一个来源!')
                return

        # 保存配置
        if 'enabled_sources' not in self.config:
            self.config['enabled_sources'] = {}
        if not custom_enabled:
            self.config['enabled_sources'][self.content_type] = selected
        self.config['storage_path'] = storage_path
        self.config['default_count'] = count
        self.config['content_type'] = self.content_type
        topic = values.get('topic', '')
        self.config['topic'] = '' if topic == FREE_SEARCH else topic

        cv = values.get('cloud_drive', '')
        self.config['cloud_drive'] = ''
        if cv and cv != '（不使用网盘）':
            for d in self.cloud.list_drives():
                if d['name'] in cv:
                    self.config['cloud_drive'] = d['key']; break

        if values.get('proxy_enabled'):
            self.config['proxy'] = {'enabled': True}
        else:
            self.config.pop('proxy', None)
        self._save_config()

        self.is_downloading = True
        self._set_ui_busy(True)

        if custom_enabled and custom_url:
            t = threading.Thread(target=self._worker_custom_url,
                                 args=(keyword, count, storage_path, ctype, custom_url, custom_selector),
                                 daemon=True)
        else:
            t = threading.Thread(target=self._worker_sources,
                                 args=(keyword, count, storage_path, selected, ctype),
                                 daemon=True)
        t.start()

    def _worker_sources(self, keyword, count, path, sources, ctype):
        collector = ImageCollector(path)
        tname = CONTENT_TYPES.get(ctype, {}).get('name', ctype)
        ok = skip = 0
        try:
            self.log(f'开始: [{tname}] 关键词={keyword} 数量={count}/源')
            total = len(sources) * count

            for sk in sources:
                if not self.is_downloading:
                    break
                self.log(f'搜索 {sk}...')
                try:
                    src = create_source(sk, collector, content_type=ctype)
                    items = src.search(keyword, count)
                except Exception as e:
                    self.log(f'  {sk}: 搜索失败 - {e}')
                    continue

                self.log(f'  {sk}: 找到 {len(items)} 个')
                for item in items:
                    if not self.is_downloading:
                        break
                    fp, _ = collector.download_image(
                        item['url'], item['filename'],
                        keyword, sk, item.get('referer'))
                    if fp:
                        ok += 1
                    else:
                        skip += 1
                    done = ok + skip
                    window['progress_bar'].update(int(done / total * 100) if total else 0)
                    window['status_text'].update(f'{done}/{total} ✓{ok} ✗{skip} [{sk}]')

            self.log(f'完成! ✓{ok} ✗{skip}')
            self.log(f'保存位置: {Path(path) / keyword}')
        except Exception as e:
            self.log(f'错误: {e}')
            logger.exception('worker异常')
        finally:
            window['status_text'].update('就绪')
            self._set_ui_busy(False)
            self.is_downloading = False

    def _worker_custom_url(self, keyword, count, path, ctype, custom_url, custom_selector):
        collector = ImageCollector(path)
        ok = skip = 0
        try:
            self.log(f'自定义网页采集: {custom_url}')
            from sources.browser import scrape_images as browser_scrape
            urls = browser_scrape(
                custom_url, keyword, count,
                selectors={'img_selector': custom_selector, 'url_attr': 'src'},
                timeout=30
            )
            items = []
            for i, url in enumerate(urls):
                if not url or not url.startswith('http') or url.startswith('data:'):
                    continue
                ext = '.jpg'
                for e in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg',
                          '.mp4', '.webm', '.mov', '.mp3', '.wav', '.pdf', '.ico']:
                    if e in url.split('?')[0].lower():
                        ext = e
                        break
                items.append({
                    'url': url,
                    'filename': f'custom_{i:04d}{ext}',
                    'referer': custom_url,
                    'title': keyword,
                })
            total = count
            self.log(f'  网页找到 {len(items)} 个')
            for item in items:
                if not self.is_downloading:
                    break
                fp, _ = collector.download_image(
                    item['url'], item['filename'],
                    keyword, 'custom', item.get('referer'))
                if fp:
                    ok += 1
                else:
                    skip += 1
                done = ok + skip
                window['progress_bar'].update(int(done / total * 100) if total else 0)
                window['status_text'].update(f'{done}/{total} ✓{ok} ✗{skip} [网页]')

            self.log(f'完成! ✓{ok} ✗{skip}')
            self.log(f'保存位置: {Path(path) / keyword}')
        except Exception as e:
            self.log(f'错误: {e}')
            logger.exception('worker异常')
        finally:
            window['status_text'].update('就绪')
            self._set_ui_busy(False)
            self.is_downloading = False

    def _stop_download(self):
        self.is_downloading = False
        self.log('正在停止...')


def main():
    try:
        ImageCollectorGUI().run()
    except Exception as e:
        sg.popup_error(f'启动失败: {e}')
        logger.exception('启动异常')


if __name__ == '__main__':
    main()