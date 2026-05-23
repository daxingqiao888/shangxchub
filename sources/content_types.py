#!/usr/bin/env python3
"""
内容类型与来源配置
"""
CONTENT_TYPES = {
    'image': {
        'name': '图片',
        'icon': '🖼',
        'sources': {
            'baidu':    {'name': '百度图片', 'url': 'https://image.baidu.com/search/index?tn=baiduimage&word={keyword}', 'selector': 'img.main_img, img[src*="http"]'},
            'bing':     {'name': 'Bing Images', 'url': 'https://cn.bing.com/images/search?q={keyword}', 'selector': 'img.mimg'},
            'unsplash': {'name': 'Unsplash', 'url': 'https://unsplash.com/s/photos/{keyword}', 'selector': 'img[src*="images.unsplash.com"]'},
            'pexels':   {'name': 'Pexels', 'url': 'https://www.pexels.com/search/{keyword}/', 'selector': 'img[src*="images.pexels.com"]'},
            'google':   {'name': 'Google (需代理)', 'url': 'https://www.google.com/search?tbm=isch&q={keyword}', 'selector': 'img[src*="http"]', 'proxy': True},
            '500px':    {'name': '500px (需代理)', 'url': 'https://500px.com/search?q={keyword}&type=photos', 'selector': 'img[src*="500px"]', 'proxy': True},
        }
    },
    'video': {
        'name': '视频',
        'icon': '🎬',
        'sources': {
            'pexels_video': {'name': 'Pexels Video ✓', 'url': 'https://www.pexels.com/search/videos/{keyword}/', 'selector': 'source[src*="pexels"], video[src*="pexels"]'},
            'pixabay_video': {'name': 'Pixabay Video', 'url': 'https://pixabay.com/videos/search/{keyword}/', 'selector': 'source[src*="pixabay"]', 'beta': True},
            'mixkit': {'name': 'Mixkit', 'url': 'https://mixkit.co/free-stock-video/{keyword}/', 'selector': 'video[src], source[src]', 'beta': True},
            'coverr': {'name': 'Coverr', 'url': 'https://coverr.co/s?q={keyword}', 'selector': 'video[src]', 'beta': True},
        }
    },
    'audio': {
        'name': '音频',
        'icon': '🎵',
        'sources': {
            'pixabay_music': {'name': 'Pixabay 音乐', 'url': 'https://pixabay.com/music/search/{keyword}/', 'selector': 'audio[src], source[src], a[href*="download"]', 'beta': True},
            'freesound': {'name': 'Freesound', 'url': 'https://freesound.org/search/?q={keyword}', 'selector': 'a[href*="download"]', 'beta': True},
        }
    },
    'document': {
        'name': '文档',
        'icon': '📄',
        'sources': {
            'baidu_wenku': {'name': '百度文库', 'url': 'https://wenku.baidu.com/search?word={keyword}', 'selector': 'a[href*="view"]', 'beta': True},
            'doc88': {'name': '道客巴巴', 'url': 'https://www.doc88.com/search?q={keyword}', 'selector': 'a[href*="doc"]', 'beta': True},
        }
    },
    'icon': {
        'name': '图标',
        'icon': '🔷',
        'sources': {
            'iconfont': {'name': 'Iconfont', 'url': 'https://www.iconfont.cn/search/index?searchType=icon&q={keyword}', 'selector': 'img[src*="icon"], svg[class*="icon"]', 'beta': True},
            'flaticon': {'name': 'Flaticon', 'url': 'https://www.flaticon.com/search?word={keyword}', 'selector': 'img[src*="flaticon"]', 'beta': True},
        }
    },
    'gif': {
        'name': 'GIF动图',
        'icon': '🎞',
        'sources': {
            'giphy': {'name': 'GIPHY ✓', 'url': 'https://giphy.com/search/{keyword}', 'selector': 'img[src*="giphy"], picture img'},
            'tenor': {'name': 'Tenor', 'url': 'https://tenor.com/search/{keyword}-gifs', 'selector': 'img[src*="tenor"], img[src*="gif"]', 'beta': True},
            'doutula': {'name': '斗图啦', 'url': 'https://www.doutula.com/search?keyword={keyword}', 'selector': 'img[data-src]', 'beta': True},
        }
    },
    'wallpaper': {
        'name': '壁纸',
        'icon': '🖥',
        'sources': {
            'bing_wallpaper': {'name': 'Bing 壁纸 ✓', 'url': 'https://cn.bing.com/images/search?q={keyword}+wallpaper&qft=+filterui:imagesize-wallpaper', 'selector': 'img.mimg'},
            'wallhaven': {'name': 'Wallhaven', 'url': 'https://wallhaven.cc/search?q={keyword}', 'selector': 'img[src*="wallhaven"]', 'beta': True},
            'wallpaper_abyss': {'name': 'Wallpaper Abyss', 'url': 'https://wall.alphacoders.com/search.php?search={keyword}', 'selector': 'img[src*="alphacoders"]', 'beta': True},
        }
    },
    'platform': {
        'name': '平台',
        'icon': '🌐',
        'sources': {
            'pinterest':    {'name': 'Pinterest', 'url': 'https://www.pinterest.com/search/pins/?q={keyword}', 'selector': 'img[src*="pinimg"]', 'proxy': True},
            'flickr':       {'name': 'Flickr', 'url': 'https://www.flickr.com/search/?text={keyword}', 'selector': 'img[src*="staticflickr"]'},
            'tuchong':      {'name': '图虫', 'url': 'https://tuchong.com/search?term={keyword}', 'selector': 'img[src*="tuchong"]', 'beta': True},
            'huaban':       {'name': '花瓣网', 'url': 'https://huaban.com/search/?q={keyword}', 'selector': 'img[src*="huaban"]', 'beta': True},
            'zcool':        {'name': '站酷', 'url': 'https://www.zcool.com.cn/search/content?word={keyword}', 'selector': 'img[src*="zcool"]', 'beta': True},
            'dribbble':     {'name': 'Dribbble', 'url': 'https://dribbble.com/search/{keyword}', 'selector': 'img[src*="dribbble"]', 'beta': True},
            'behance':      {'name': 'Behance', 'url': 'https://www.behance.net/search/projects?search={keyword}', 'selector': 'img[src*="behance"]', 'proxy': True},
            'deviantart':   {'name': 'DeviantArt', 'url': 'https://www.deviantart.com/search?q={keyword}', 'selector': 'img[src*="deviantart"]', 'proxy': True},
            'bilibili':     {'name': 'B站', 'url': 'https://search.bilibili.com/all?keyword={keyword}', 'selector': 'img[src*="hdslb"], video[src]', 'beta': True},
            'vimeo':        {'name': 'Vimeo', 'url': 'https://vimeo.com/search?q={keyword}', 'selector': 'video[src], img[src*="vimeo"]', 'proxy': True},
            'weibo':        {'name': '微博', 'url': 'https://s.weibo.com/weibo?q={keyword}', 'selector': 'img[src*="sinaimg"]', 'beta': True},
        }
    },
}

# 文件扩展名映射
TYPE_EXTENSIONS = {
    'image':     ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg'],
    'video':     ['.mp4', '.webm', '.mov', '.avi', '.mkv'],
    'audio':     ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
    'document':  ['.pdf', '.ppt', '.pptx', '.doc', '.docx', '.xls', '.xlsx'],
    'icon':      ['.svg', '.png', '.ico', '.icns'],
    'gif':       ['.gif', '.webp'],
    'wallpaper': ['.jpg', '.jpeg', '.png', '.webp'],
    'platform':  ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.webm', '.mov', '.mp3', '.wav', '.svg'],
}

# 各类型主题分类
TOPIC_CATEGORIES = {
    'image': [
        '自然风景', '城市建筑', '人物肖像', '动物宠物', '美食饮品',
        '科技数码', '时尚穿搭', '体育运动', '植物花卉', '节日庆典',
        '交通工具', '抽象纹理', '太空宇宙', '海洋世界', '复古怀旧',
    ],
    'video': [
        '航拍风景', '城市延时', '自然动物', '人物活动', '商业办公',
        '科技特效', '慢动作', '海底世界', '旅行Vlog', '美食制作',
    ],
    'audio': [
        '背景音乐', '环境音效', '自然声音', '人声音轨', '电子舞曲',
        '古典乐器', '节奏鼓点', '卡通趣味', '科技科幻', '氛围放松',
    ],
    'document': [
        '教育课件', '商业计划', '技术开发', '法律合同', '医学健康',
        '工程建筑', '论文研究', '营销策划',
    ],
    'icon': [
        '箭头符号', '社交媒体', '购物支付', 'UI控件', '天气季节',
        '文件类型', '手势操作', '品牌Logo', '医疗健康', '教育学习',
    ],
    'gif': [
        '搞笑表情', '动物萌宠', '影视片段', '运动瞬间', '艺术创作',
        '反应动图', '节日祝福', '明星名人', '美食诱惑', '科技炫酷',
    ],
    'wallpaper': [
        '自然风光', '动漫二次元', '游戏CG', '极简几何', '科幻未来',
        '城市夜景', '抽象艺术', '动物世界', '赛博朋克', '日系和风',
    ],
    'platform': [
        '摄影作品', '设计灵感', 'UI图标', '插画艺术', '创意视频',
        '美食摄影', '旅行风光', '时尚穿搭', '建筑设计', '手绘艺术',
        '创意广告', '卡通动漫', '科技产品', '品牌设计', '城市街拍',
    ],
}

# 各类型筛选维度
TYPE_FILTERS = {
    'image': {
        '尺寸': ['不限', '大尺寸', '中尺寸', '小尺寸', '壁纸尺寸'],
        '颜色': ['不限', '红色', '橙色', '黄色', '绿色', '蓝色', '紫色', '黑白'],
        '方向': ['不限', '横向', '纵向', '方形'],
        '类型': ['不限', '照片', '插画', '剪贴画', '透明背景'],
    },
    'video': {
        '分辨率': ['不限', '4K', '1080p', '720p'],
        '时长': ['不限', '短视频', '中等时长', '长视频'],
        '方向': ['不限', '横向', '纵向'],
        '排序': ['不限', '最新', '最热', '相关度'],
    },
    'audio': {
        '时长': ['不限', '短音频', '中等时长', '长音频'],
        '类型': ['不限', '音乐', '音效', '人声'],
        '排序': ['不限', '最新', '最热', '下载量'],
    },
    'document': {
        '格式': ['不限', 'PDF', 'PPT', 'Word', 'Excel'],
        '排序': ['不限', '最新', '最热', '相关度'],
    },
    'icon': {
        '风格': ['不限', '线性', '填充', '彩色', '扁平'],
        '尺寸': ['不限', '小尺寸', '中尺寸', '大尺寸'],
        '格式': ['不限', 'SVG', 'PNG', 'ICO'],
    },
    'gif': {
        '风格': ['不限', '搞笑', '艺术', '影视', '卡通'],
        '排序': ['不限', '最新', '最热', '流行'],
    },
    'wallpaper': {
        '分辨率': ['不限', '4K', '1080p', '手机'],
        '颜色': ['不限', '暗色', '亮色', '彩色', '黑白'],
        '类型': ['不限', '自然', '动漫', '游戏', '极简'],
    },
    'platform': {
        '类型': ['不限', '图片', '视频', '设计', '插画'],
        '排序': ['不限', '最新', '最热', '流行'],
    },
}

# 筛选值到英文搜索关键词映射
FILTER_KEYWORD_MAP = {
    '大尺寸': 'large',
    '中尺寸': 'medium',
    '小尺寸': 'small',
    '壁纸尺寸': 'wallpaper',
    '红色': 'red',
    '橙色': 'orange',
    '黄色': 'yellow',
    '绿色': 'green',
    '蓝色': 'blue',
    '紫色': 'purple',
    '黑白': 'black white',
    '横向': 'horizontal',
    '纵向': 'vertical',
    '方形': 'square',
    '照片': 'photo',
    '插画': 'illustration',
    '剪贴画': 'clipart',
    '透明背景': 'transparent background',
    '4K': '4K',
    '1080p': '1080p',
    '720p': '720p',
    '短视频': 'short',
    '中等时长': 'medium',
    '长视频': 'long',
    '短音频': 'short',
    '长音频': 'long',
    '最新': 'latest',
    '最热': 'popular',
    '相关度': 'relevant',
    '下载量': 'most downloaded',
    '音乐': 'music',
    '音效': 'sound effect',
    '人声': 'vocal',
    'PDF': 'PDF',
    'PPT': 'PPT',
    'Word': 'Word',
    'Excel': 'Excel',
    '线性': 'linear',
    '填充': 'filled',
    '彩色': 'colorful',
    '扁平': 'flat',
    'SVG': 'SVG',
    'PNG': 'PNG',
    'ICO': 'ICO',
    '搞笑': 'funny',
    '艺术': 'artistic',
    '影视': 'movie',
    '卡通': 'cartoon',
    '流行': 'trending',
    '手机': 'mobile',
    '暗色': 'dark',
    '亮色': 'light',
    '自然': 'nature',
    '动漫': 'anime',
    '游戏': 'game',
    '极简': 'minimal',
}
