import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
import json
from typing import Dict, List
import threading
from datetime import datetime
import logging
import os
import webbrowser

# 设置日志
def setup_logging():
    """设置日志系统"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(f'logs/netease_search_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class NeteaseSearchDownload:
    """网易云音乐搜索下载工具"""
    
    def __init__(self):
        self.base_url = "https://163api.qijieya.cn/search"
        
        # 搜索状态
        self.current_keywords = ""
        self.current_offset = 0
        self.current_limit = 20
        self.current_result = None
        self.song_details = []  # 存储详细的歌曲信息
        
        # 当前选中的歌曲
        self.selected_song = None
        
        # 歌曲命名设置 (新增)
        self.naming_format = "歌曲名-歌手"  # 默认格式
        
        # 下载位置设置 (新增)
        self.download_dir = "downloads"  # 默认下载位置
        self.load_settings()  # 加载设置
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("🎵 网易云音乐搜索下载工具")
        self.root.geometry("1100x800")
        
        # 创建菜单
        self.create_menu()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        logger.info("程序启动 - 搜索下载版")
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.naming_format = settings.get("naming_format", "歌曲名-歌手")
                    self.download_dir = settings.get("download_dir", "downloads")
        except Exception as e:
            logger.warning(f"加载设置失败: {e}")
            # 使用默认设置
            self.naming_format = "歌曲名-歌手"
            self.download_dir = "downloads"
    
    def save_settings(self):
        """保存设置"""
        try:
            settings = {
                "naming_format": self.naming_format,
                "download_dir": self.download_dir
            }
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info("设置已保存")
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 程序菜单
        program_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="程序", menu=program_menu)
        program_menu.add_command(label="重置搜索", command=self.reset_search)
        program_menu.add_separator()
        program_menu.add_command(label="退出", command=self.on_closing)
        
        # 下载菜单
        download_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="下载", menu=download_menu)
        download_menu.add_command(label="下载选中歌曲", command=self.download_selected_song)
        download_menu.add_command(label="批量下载本页", command=self.batch_download)
        # 新增：歌曲命名设置
        download_menu.add_command(label="歌曲命名设置", command=self.show_naming_settings)
        # 新增：下载位置设置
        download_menu.add_command(label="下载位置", command=self.show_download_location)
        download_menu.add_command(label="打开下载文件夹", command=self.open_download_folder)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about_window)
        help_menu.add_command(label="B站主页", command=lambda: webbrowser.open("https://space.bilibili.com/3461564273265329"))
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架 - 修复空隙问题
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重 - 优化权重分配
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # 给Notebook行分配权重
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="🎵 网易云音乐搜索下载工具",
            font=('微软雅黑', 14, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        # 搜索区域
        search_frame = ttk.LabelFrame(main_frame, text="搜索设置", padding="8")
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        # 关键词输入
        ttk.Label(search_frame, text="搜索关键词:").grid(row=0, column=0, padx=(0, 5))
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(search_frame, textvariable=self.keyword_var, width=40)
        self.keyword_entry.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        # 偏移量
        ttk.Label(search_frame, text="偏移量:").grid(row=0, column=2, padx=(0, 5))
        self.offset_var = tk.StringVar(value="0")
        self.offset_entry = ttk.Entry(search_frame, textvariable=self.offset_var, width=8)
        self.offset_entry.grid(row=0, column=3, padx=(0, 10))
        
        # 每页数量
        ttk.Label(search_frame, text="每页:").grid(row=0, column=4, padx=(0, 5))
        self.limit_var = tk.StringVar(value="20")
        limit_combo = ttk.Combobox(
            search_frame,
            textvariable=self.limit_var,
            values=["10", "20", "30", "50", "100"],
            width=6,
            state="readonly"
        )
        limit_combo.grid(row=0, column=5, padx=(0, 10))
        
        # 搜索按钮
        self.search_btn = ttk.Button(
            search_frame,
            text="🔍 搜索",
            command=self.on_search,
            width=10
        )
        self.search_btn.grid(row=0, column=6)
        
        # 下载控制区域 - 优化布局
        download_frame = ttk.LabelFrame(main_frame, text="下载控制", padding="5")
        download_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 下载按钮区域
        button_frame = ttk.Frame(download_frame)
        button_frame.grid(row=0, column=0, padx=5)
        
        # 下载选中歌曲按钮
        self.download_btn = ttk.Button(
            button_frame,
            text="⬇ 下载选中歌曲",
            command=self.download_selected_song,
            state="disabled",
            width=15
        )
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 批量下载按钮
        self.batch_download_btn = ttk.Button(
            button_frame,
            text="⬇ 批量下载本页",
            command=self.batch_download,
            state="disabled",
            width=15
        )
        self.batch_download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 测试下载按钮
        self.test_download_btn = ttk.Button(
            button_frame,
            text="🔗 测试歌曲链接",
            command=self.test_download_link,
            state="disabled",
            width=15
        )
        self.test_download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 下载状态区域
        status_frame = ttk.Frame(download_frame)
        status_frame.grid(row=0, column=1, padx=(10, 5), sticky=(tk.W, tk.E))
        download_frame.columnconfigure(1, weight=1)
        
        # 下载状态标签
        self.download_status_label = ttk.Label(
            status_frame,
            text="未选择歌曲",
            font=('微软雅黑', 9)
        )
        self.download_status_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # 当前下载位置显示 (新增)
        self.download_location_label = ttk.Label(
            status_frame,
            text=f"下载位置: {self.download_dir}",
            font=('微软雅黑', 9),
            foreground="blue"
        )
        self.download_location_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 分页控制区域
        page_frame = ttk.Frame(main_frame)
        page_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 上一页按钮
        self.prev_btn = ttk.Button(
            page_frame,
            text="◀ 上一页",
            command=self.prev_page,
            state="disabled",
            width=10
        )
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 页码显示
        self.page_label = ttk.Label(
            page_frame,
            text="偏移量: 0 | 总数: 0",
            font=('微软雅黑', 10)
        )
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 下一页按钮
        self.next_btn = ttk.Button(
            page_frame,
            text="下一页 ▶",
            command=self.next_page,
            state="disabled",
            width=10
        )
        self.next_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 跳转控制
        ttk.Label(page_frame, text="跳转偏移:").pack(side=tk.LEFT, padx=(20, 5))
        self.goto_var = tk.StringVar()
        self.goto_entry = ttk.Entry(page_frame, textvariable=self.goto_var, width=8)
        self.goto_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        self.goto_btn = ttk.Button(
            page_frame,
            text="跳转",
            command=self.goto_offset,
            width=6
        )
        self.goto_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 重置按钮
        self.reset_btn = ttk.Button(
            page_frame,
            text="🔄 重置",
            command=self.reset_search,
            width=8
        )
        self.reset_btn.pack(side=tk.LEFT)
        
        # 创建Notebook（标签页）- 修复空隙问题
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # 搜索结果标签页
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="搜索结果")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 歌曲列表树状视图
        columns = ("序号", "歌曲ID", "歌曲名", "歌手", "专辑", "时长", "专辑ID", "歌手ID")
        self.tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # 设置列
        column_widths = {
            "序号": 50,
            "歌曲ID": 80,
            "歌曲名": 200,
            "歌手": 150,
            "专辑": 150,
            "时长": 70,
            "专辑ID": 80,
            "歌手ID": 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col])
        
        # 滚动条
        tree_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 歌曲详情标签页
        detail_frame = ttk.Frame(notebook)
        notebook.add(detail_frame, text="歌曲详情")
        detail_frame.columnconfigure(1, weight=1)
        detail_frame.columnconfigure(3, weight=1)
        
        # 歌曲详情显示
        ttk.Label(detail_frame, text="歌曲名:", font=('微软雅黑', 11)).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.detail_name = ttk.Label(detail_frame, text="", font=('微软雅黑', 11, 'bold'))
        self.detail_name.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="歌曲ID:", font=('微软雅黑', 11)).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.detail_song_id = ttk.Label(detail_frame, text="", font=('微软雅黑', 11))
        self.detail_song_id.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="歌手:", font=('微软雅黑', 11)).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.detail_artists = ttk.Label(detail_frame, text="")
        self.detail_artists.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="专辑:", font=('微软雅黑', 11)).grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.detail_album = ttk.Label(detail_frame, text="")
        self.detail_album.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 右侧信息
        ttk.Label(detail_frame, text="专辑ID:", font=('微软雅黑', 11)).grid(
            row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5)
        )
        self.detail_album_id = ttk.Label(detail_frame, text="")
        self.detail_album_id.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="歌手ID:", font=('微软雅黑', 11)).grid(
            row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5)
        )
        self.detail_artist_ids = ttk.Label(detail_frame, text="")
        self.detail_artist_ids.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="时长:", font=('微软雅黑', 11)).grid(
            row=2, column=2, sticky=tk.W, pady=5, padx=(20, 5)
        )
        self.detail_duration = ttk.Label(detail_frame, text="")
        self.detail_duration.grid(row=2, column=3, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(detail_frame, text="发布时间:", font=('微软雅黑', 11)).grid(
            row=3, column=2, sticky=tk.W, pady=5, padx=(20, 5)
        )
        self.detail_publish = ttk.Label(detail_frame, text="")
        self.detail_publish.grid(row=3, column=3, sticky=tk.W, pady=5, padx=5)
        
        # 下载信息
        ttk.Label(detail_frame, text="下载链接:", font=('微软雅黑', 11)).grid(
            row=4, column=0, sticky=tk.W, pady=10, padx=5
        )
        self.detail_download_link = tk.Text(
            detail_frame,
            height=2,
            width=60,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.detail_download_link.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=10, padx=5)
        
        # 下载测试结果
        ttk.Label(detail_frame, text="下载状态:", font=('微软雅黑', 11)).grid(
            row=5, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.detail_download_status = ttk.Label(detail_frame, text="", font=('微软雅黑', 10))
        self.detail_download_status.grid(row=5, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
        
        # 原始数据标签页
        raw_frame = ttk.Frame(notebook)
        notebook.add(raw_frame, text="原始数据")
        raw_frame.columnconfigure(0, weight=1)
        raw_frame.rowconfigure(0, weight=1)
        
        # 原始数据文本框
        self.raw_text = scrolledtext.ScrolledText(
            raw_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            width=80,
            height=20
        )
        self.raw_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 下载记录标签页
        download_log_frame = ttk.Frame(notebook)
        notebook.add(download_log_frame, text="下载记录")
        download_log_frame.columnconfigure(0, weight=1)
        download_log_frame.rowconfigure(0, weight=1)
        
        # 下载记录文本框
        self.download_log_text = scrolledtext.ScrolledText(
            download_log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            width=80,
            height=20
        )
        self.download_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="操作日志")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            width=80,
            height=20
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
    
    def bind_events(self):
        """绑定事件"""
        self.root.bind('<Return>', lambda e: self.on_search())
        self.tree.bind('<<TreeviewSelect>>', self.on_song_selected)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        if self.log_text:
            self.log_text.insert(tk.END, log_entry + "\n")
            self.log_text.see(tk.END)
        
        if level == "DEBUG":
            logger.debug(message)
        elif level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        
        # 更新状态栏
        if level == "INFO":
            self.status_label.config(text=message)
    
    def add_download_log(self, message: str):
        """添加下载记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if self.download_log_text:
            self.download_log_text.insert(tk.END, log_entry + "\n")
            self.download_log_text.see(tk.END)
    
    def search_music(self, keywords: str, offset: str = "0", limit: str = "20") -> Dict:
        """搜索音乐"""
        try:
            url = f"{self.base_url}?keywords={keywords}&offset={offset}&limit={limit}&type=1"
            
            self.log(f"开始搜索: '{keywords}' (offset={offset}, limit={limit})")
            self.log(f"请求URL: {url}", "DEBUG")
            
            response = requests.get(url, timeout=30)
            self.log(f"响应状态: {response.status_code}", "DEBUG")
            
            response.raise_for_status()
            
            data = response.json()
            
            # 显示原始数据
            raw_json = json.dumps(data, ensure_ascii=False, indent=2)
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(tk.END, raw_json)
            
            return data
            
        except Exception as e:
            self.log(f"搜索失败: {e}", "ERROR")
            messagebox.showerror("搜索失败", f"搜索过程中发生错误:\n{str(e)}")
            return None
    
    def extract_song_info(self, song: Dict) -> Dict:
        """从歌曲数据中提取信息"""
        # 获取歌曲ID
        song_id = song.get('id', 0)
        
        # 获取专辑信息
        album_data = song.get('album', {})
        album_id = album_data.get('id', 0)
        album_name = album_data.get('name', '未知专辑')
        
        # 获取歌手信息
        artists_data = song.get('artists', [])
        artist_names = []
        artist_ids = []
        
        for artist in artists_data:
            name = artist.get('name', '未知歌手')
            artist_id = artist.get('id', 0)
            artist_names.append(name)
            artist_ids.append(str(artist_id))
        
        # 获取其他信息
        name = song.get('name', '未知歌曲')
        duration_ms = song.get('duration', 0)
        
        # 格式化时长
        if duration_ms:
            total_seconds = duration_ms // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "0:00"
        
        # 发布时间
        publish_time = album_data.get('publishTime', 0)
        if publish_time:
            try:
                publish_str = datetime.fromtimestamp(publish_time/1000).strftime('%Y-%m-%d')
            except:
                publish_str = str(publish_time)
        else:
            publish_str = "未知"
        
        # 生成下载链接
        download_link = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"
        
        return {
            'song_id': song_id,
            'name': name,
            'artists': artist_names,
            'artist_ids': artist_ids,
            'artist_str': '/'.join(artist_names) if artist_names else '未知歌手',
            'album_id': album_id,
            'album_name': album_name,
            'duration': duration_str,
            'duration_ms': duration_ms,
            'publish_time': publish_str,
            'download_link': download_link,
            'raw_data': song
        }
    
    def generate_filename(self, song_name, artist):
        """根据命名设置生成文件名"""
        # 清理文件名中的非法字符
        def clean_filename(text):
            # 替换Windows文件名中不允许的字符
            illegal_chars = r'<>:"/\\|?*'
            for char in illegal_chars:
                text = text.replace(char, '_')
            return text.strip()
        
        clean_song_name = clean_filename(song_name)
        clean_artist = clean_filename(artist)
        
        if self.naming_format == "歌曲名":
            return f"{clean_song_name}.mp3"
        else:  # 歌曲名-歌手
            return f"{clean_song_name} - {clean_artist}.mp3"
    
    def display_results(self, data: Dict):
        """显示搜索结果"""
        if not data:
            return
        
        # 清空树状视图和缓存
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.song_details = []
        
        # 获取结果
        result = data.get('result', {})
        songs = result.get('songs', [])
        
        if not songs:
            self.log("未找到歌曲", "INFO")
            messagebox.showinfo("无结果", "未找到相关歌曲")
            
            # 禁用下载按钮
            self.download_btn.config(state="disabled")
            self.batch_download_btn.config(state="disabled")
            self.test_download_btn.config(state="disabled")
            self.download_status_label.config(text="未找到歌曲")
            return
        
        # 提取并显示歌曲信息
        for i, song in enumerate(songs):
            song_info = self.extract_song_info(song)
            self.song_details.append(song_info)
            
            # 显示在树状视图中
            self.tree.insert('', 'end', values=(
                i + 1,
                song_info['song_id'],
                song_info['name'],
                song_info['artist_str'],
                song_info['album_name'],
                song_info['duration'],
                song_info['album_id'],
                ','.join(song_info['artist_ids'])
            ))
        
        # 更新状态
        song_count = result.get('songCount', len(songs))
        self.page_label.config(text=f"偏移量: {self.current_offset} | 总数: {song_count}")
        
        # 更新按钮状态
        self.prev_btn.config(state="normal" if self.current_offset > 0 else "disabled")
        self.next_btn.config(state="normal" if len(songs) >= self.current_limit else "disabled")
        
        # 启用批量下载按钮
        self.batch_download_btn.config(state="normal")
        
        self.log(f"显示 {len(songs)} 首歌曲")
        self.current_result = data
        
        # 默认选中第一首歌
        if self.song_details:
            self.tree.selection_set(self.tree.get_children()[0])
            self.update_song_detail(0)
    
    def update_song_detail(self, index: int):
        """更新歌曲详情显示"""
        if index < 0 or index >= len(self.song_details):
            return
        
        song_info = self.song_details[index]
        
        # 更新显示
        self.detail_name.config(text=song_info['name'])
        self.detail_song_id.config(text=str(song_info['song_id']))
        self.detail_artists.config(text=song_info['artist_str'])
        self.detail_album.config(text=song_info['album_name'])
        self.detail_album_id.config(text=str(song_info['album_id']))
        self.detail_artist_ids.config(text=','.join(song_info['artist_ids']))
        self.detail_duration.config(text=song_info['duration'])
        self.detail_publish.config(text=song_info['publish_time'])
        
        # 显示下载链接
        self.detail_download_link.delete(1.0, tk.END)
        self.detail_download_link.insert(tk.END, song_info['download_link'])
        
        # 重置下载状态
        self.detail_download_status.config(text="")
        
        # 存储选中的歌曲信息
        self.selected_song = {
            'id': song_info['song_id'],
            'name': song_info['name'],
            'artist': song_info['artist_str'],
            'download_link': song_info['download_link']
        }
        
        # 启用下载和测试按钮
        self.download_btn.config(state="normal")
        self.test_download_btn.config(state="normal")
        self.download_status_label.config(text=f"准备下载: {song_info['name']}")
    
    def on_song_selected(self, event):
        """歌曲选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        children = self.tree.get_children()
        if item in children:
            index = children.index(item)
            self.update_song_detail(index)
            
            # 在状态栏显示选中信息
            song_info = self.song_details[index]
            self.status_label.config(
                text=f"选中: {song_info['name']} - ID: {song_info['song_id']}"
            )
    
    def fetch_and_download_song(self, song_id, song_name=None, artist=None, download_link=None):
        """下载歌曲"""
        try:
            # 使用提供的下载链接或生成链接
            if not download_link:
                download_link = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"
            
            self.log(f"下载链接: {download_link}", "DEBUG")
            
            response = requests.get(download_link, allow_redirects=True, timeout=30)
            
            # 检查重定向后的最终URL是否为404页面
            if response.url == "https://music.163.com/#/404":
                return False, "无法下载歌曲，请检查ID是否正确"
            
            if response.status_code != 200:
                return False, f"下载失败，状态码: {response.status_code}"
            
            # 创建下载目录
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)
            
            # 生成文件名
            if song_name and artist:
                filename = self.generate_filename(song_name, artist)
            else:
                filename = f"歌曲_{song_id}.mp3"
            
            # 保存文件
            full_path = os.path.join(self.download_dir, filename)
            
            # 避免文件名重复
            counter = 1
            while os.path.exists(full_path):
                base_name, ext = os.path.splitext(filename)
                new_filename = f"{base_name} ({counter}){ext}"
                full_path = os.path.join(self.download_dir, new_filename)
                counter += 1
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            return True, full_path
            
        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {str(e)}"
        except Exception as e:
            return False, f"下载失败: {str(e)}"
    
    def download_selected_song(self):
        """下载选中的歌曲"""
        if not self.selected_song:
            messagebox.showwarning("下载错误", "请先选择一首歌曲")
            return
        
        song_id = self.selected_song['id']
        song_name = self.selected_song['name']
        artist = self.selected_song['artist']
        download_link = self.selected_song['download_link']
        
        # 在新线程中执行下载
        thread = threading.Thread(
            target=self._do_download,
            args=(song_id, song_name, artist, download_link)
        )
        thread.daemon = True
        thread.start()
    
    def batch_download(self):
        """批量下载本页所有歌曲"""
        if not self.song_details:
            messagebox.showwarning("下载错误", "没有可下载的歌曲")
            return
        
        # 询问确认
        if not messagebox.askyesno("批量下载", f"确定要下载本页所有 {len(self.song_details)} 首歌曲吗？"):
            return
        
        # 在新线程中执行批量下载
        thread = threading.Thread(
            target=self._do_batch_download,
            args=(self.song_details,)
        )
        thread.daemon = True
        thread.start()
    
    def test_download_link(self):
        """测试下载链接"""
        if not self.selected_song:
            messagebox.showwarning("测试错误", "请先选择一首歌曲")
            return
        
        download_link = self.selected_song['download_link']
        
        try:
            self.detail_download_status.config(text="正在测试链接...", foreground="blue")
            
            response = requests.head(download_link, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                content_length = response.headers.get('content-length', '未知')
                content_type = response.headers.get('content-type', '未知')
                
                self.detail_download_status.config(
                    text=f"✅ 链接有效 | 大小: {content_length} bytes | 类型: {content_type}",
                    foreground="green"
                )
                self.log(f"链接测试成功: {download_link}")
            elif response.url == "https://music.163.com/#/404":
                self.detail_download_status.config(
                    text="❌ 链接指向404页面（可能没有下载权限）",
                    foreground="red"
                )
                self.log(f"链接测试失败: 指向404页面", "WARNING")
            else:
                self.detail_download_status.config(
                    text=f"❌ 链接测试失败: HTTP {response.status_code}",
                    foreground="red"
                )
                self.log(f"链接测试失败: HTTP {response.status_code}", "WARNING")
                
        except Exception as e:
            self.detail_download_status.config(
                text=f"❌ 链接测试异常: {str(e)}",
                foreground="red"
            )
            self.log(f"链接测试异常: {e}", "ERROR")
    
    def _do_download(self, song_id, song_name, artist, download_link):
        """执行下载（在线程中）"""
        self.root.after(0, lambda: self.status_label.config(text=f"正在下载: {song_name}"))
        self.root.after(0, lambda: self.detail_download_status.config(
            text="下载中...", foreground="blue"
        ))
        
        success, result = self.fetch_and_download_song(song_id, song_name, artist, download_link)
        
        if success:
            self.root.after(0, lambda: self.log(f"下载成功: {song_name} - {artist}"))
            self.root.after(0, lambda: self.add_download_log(f"✅ 下载成功: {song_name} - {artist}"))
            self.root.after(0, lambda: self.detail_download_status.config(
                text=f"✅ 下载完成: {os.path.basename(result)}", foreground="green"
            ))
            self.root.after(0, lambda: messagebox.showinfo("下载成功", f"歌曲已下载到:\n{result}"))
        else:
            self.root.after(0, lambda: self.log(f"下载失败: {result}", "ERROR"))
            self.root.after(0, lambda: self.add_download_log(f"❌ 下载失败: {song_name} - {result}"))
            self.root.after(0, lambda: self.detail_download_status.config(
                text=f"❌ 下载失败: {result}", foreground="red"
            ))
            self.root.after(0, lambda: messagebox.showerror("下载失败", f"下载失败:\n{result}"))
    
    def _do_batch_download(self, songs_info):
        """执行批量下载（在线程中）"""
        total = len(songs_info)
        success_count = 0
        fail_count = 0
        
        self.root.after(0, lambda: self.status_label.config(text=f"批量下载中... 0/{total}"))
        
        for i, song_info in enumerate(songs_info):
            song_id = song_info['song_id']
            song_name = song_info['name']
            artist = song_info['artist_str']
            download_link = song_info['download_link']
            
            # 更新状态
            self.root.after(0, lambda idx=i: self.status_label.config(
                text=f"批量下载中... {idx+1}/{total}"
            ))
            
            # 下载歌曲
            success, result = self.fetch_and_download_song(song_id, song_name, artist, download_link)
            
            if success:
                success_count += 1
                self.root.after(0, lambda name=song_name, artist=artist: self.add_download_log(
                    f"✅ 下载成功: {name} - {artist}"
                ))
            else:
                fail_count += 1
                self.root.after(0, lambda name=song_name, artist=artist, err=result: self.add_download_log(
                    f"❌ 下载失败: {name} - {artist} ({err})"
                ))
        
        # 显示结果
        self.root.after(0, lambda: self.status_label.config(
            text=f"批量下载完成: 成功 {success_count} 首，失败 {fail_count} 首"
        ))
        self.root.after(0, lambda: self.add_download_log(
            f"批量下载完成: 共 {total} 首，成功 {success_count} 首，失败 {fail_count} 首"
        ))
        
        if fail_count == 0:
            self.root.after(0, lambda: messagebox.showinfo(
                "批量下载完成",
                f"批量下载完成！\n成功下载 {success_count} 首歌曲到 {self.download_dir} 文件夹。"
            ))
        else:
            self.root.after(0, lambda: messagebox.showwarning(
                "批量下载完成",
                f"批量下载完成！\n成功下载 {success_count} 首，失败 {fail_count} 首。\n请查看下载记录获取详细信息。"
            ))
    
    def open_download_folder(self):
        """打开下载文件夹"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        try:
            # Windows
            if os.name == 'nt':
                os.startfile(self.download_dir)
            # MacOS
            elif os.name == 'posix':
                import subprocess
                subprocess.call(['open', self.download_dir])
            # Linux
            else:
                import subprocess
                subprocess.call(['xdg-open', self.download_dir])
            
            self.log(f"打开下载文件夹: {os.path.abspath(self.download_dir)}")
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件夹:\n{str(e)}")
    
    def show_naming_settings(self):
        """显示歌曲命名设置窗口"""
        naming_win = tk.Toplevel(self.root)
        naming_win.title("歌曲命名设置")
        naming_win.geometry("400x250")
        naming_win.resizable(False, False)
        naming_win.configure(bg='white')
        
        # 居中显示
        naming_win.transient(self.root)
        naming_win.grab_set()
        
        # 标题
        tk.Label(naming_win, 
                 text="歌曲命名设置", 
                 font=("Microsoft YaHei", 14, "bold"), 
                 bg='white').pack(pady=20)
        
        # 命名格式选项
        tk.Label(naming_win, 
                 text="选择文件命名格式:", 
                 font=("Microsoft YaHei", 11), 
                 bg='white').pack(pady=10)
        
        # 单选按钮
        naming_var = tk.StringVar(value=self.naming_format)
        
        format_frame = tk.Frame(naming_win, bg='white')
        format_frame.pack(pady=10)
        
        tk.Radiobutton(format_frame, 
                      text="歌曲名 (如: 一路生花.mp3)", 
                      variable=naming_var, 
                      value="歌曲名",
                      font=("Microsoft YaHei", 10),
                      bg='white').pack(anchor='w', pady=5)
        
        tk.Radiobutton(format_frame, 
                      text="歌曲名-歌手 (如: 一路生花 - 刘宇宁.mp3)", 
                      variable=naming_var, 
                      value="歌曲名-歌手",
                      font=("Microsoft YaHei", 10),
                      bg='white').pack(anchor='w', pady=5)
        
        # 示例显示
        example_label = tk.Label(naming_win, 
                                text="示例: 一路生花 - 刘宇宁.mp3", 
                                font=("Microsoft YaHei", 10), 
                                fg='gray',
                                bg='white')
        example_label.pack(pady=10)
        
        def update_example():
            if naming_var.get() == "歌曲名":
                example_label.config(text="示例: 一路生花.mp3")
            else:
                example_label.config(text="示例: 一路生花 - 刘宇宁.mp3")
        
        naming_var.trace('w', lambda *args: update_example())
        
        # 按钮区域
        button_frame = tk.Frame(naming_win, bg='white')
        button_frame.pack(pady=20)
        
        def save_naming_settings():
            self.naming_format = naming_var.get()
            self.save_settings()
            self.log(f"歌曲命名格式已设置为: {self.naming_format}")
            naming_win.destroy()
        
        tk.Button(button_frame, 
                  text="保存", 
                  command=save_naming_settings,
                  width=10,
                  bg='#0078D7',
                  fg='white',
                  relief='flat').pack(side='left', padx=10)
        
        tk.Button(button_frame, 
                  text="取消", 
                  command=naming_win.destroy,
                  width=10,
                  bg='#E1E1E1',
                  relief='flat').pack(side='left', padx=10)
    
    def show_download_location(self):
        """显示下载位置设置窗口"""
        location_win = tk.Toplevel(self.root)
        location_win.title("下载位置设置")
        location_win.geometry("500x300")
        location_win.resizable(False, False)
        location_win.configure(bg='white')
        
        # 居中显示
        location_win.transient(self.root)
        location_win.grab_set()
        
        # 标题
        tk.Label(location_win, 
                 text="下载位置设置", 
                 font=("Microsoft YaHei", 14, "bold"), 
                 bg='white').pack(pady=20)
        
        # 当前位置显示
        tk.Label(location_win, 
                 text="当前下载位置:", 
                 font=("Microsoft YaHei", 11), 
                 bg='white').pack(pady=5)
        
        current_location = tk.Label(location_win, 
                                   text=os.path.abspath(self.download_dir),
                                   font=("Microsoft YaHei", 10),
                                   fg='blue',
                                   bg='white',
                                   wraplength=400)
        current_location.pack(pady=5)
        
        # 设置新位置
        tk.Label(location_win, 
                 text="设置新位置:", 
                 font=("Microsoft YaHei", 11), 
                 bg='white').pack(pady=15)
        
        # 输入框和浏览按钮
        location_frame = tk.Frame(location_win, bg='white')
        location_frame.pack(pady=10)
        
        location_var = tk.StringVar(value=self.download_dir)
        
        location_entry = tk.Entry(location_frame, 
                                 textvariable=location_var,
                                 width=40,
                                 font=("Microsoft YaHei", 10))
        location_entry.pack(side='left', padx=(0, 10))
        
        def browse_folder():
            folder = filedialog.askdirectory(
                initialdir=self.download_dir,
                title="选择下载文件夹"
            )
            if folder:
                location_var.set(folder)
        
        tk.Button(location_frame, 
                  text="浏览...", 
                  command=browse_folder,
                  width=8).pack(side='left')
        
        # 按钮区域
        button_frame = tk.Frame(location_win, bg='white')
        button_frame.pack(pady=20)
        
        def save_location_settings():
            new_location = location_var.get().strip()
            
            if not new_location:
                messagebox.showwarning("输入错误", "请输入下载位置")
                return
            
            # 检查路径是否有效
            try:
                # 尝试创建目录
                if not os.path.exists(new_location):
                    try:
                        os.makedirs(new_location)
                    except:
                        messagebox.showerror("路径错误", "无法创建指定的目录，请检查路径是否有写权限。")
                        return
                
                # 检查目录是否可写
                test_file = os.path.join(new_location, "test_write.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                except:
                    messagebox.showerror("权限错误", "无法写入到指定目录，请检查目录权限。")
                    return
                
                # 保存设置
                self.download_dir = new_location
                self.save_settings()
                
                # 更新界面显示
                self.download_location_label.config(
                    text=f"下载位置: {self.download_dir}"
                )
                
                self.log(f"下载位置已设置为: {os.path.abspath(self.download_dir)}")
                location_win.destroy()
                
            except Exception as e:
                messagebox.showerror("设置错误", f"设置下载位置失败:\n{str(e)}")
        
        tk.Button(button_frame, 
                  text="保存", 
                  command=save_location_settings,
                  width=10,
                  bg='#0078D7',
                  fg='white',
                  relief='flat').pack(side='left', padx=10)
        
        tk.Button(button_frame, 
                  text="恢复默认", 
                  command=lambda: location_var.set("downloads"),
                  width=10,
                  bg='#E1E1E1',
                  relief='flat').pack(side='left', padx=10)
        
        tk.Button(button_frame, 
                  text="取消", 
                  command=location_win.destroy,
                  width=10,
                  bg='#E1E1E1',
                  relief='flat').pack(side='left', padx=10)
    
    def on_search(self):
        """搜索按钮点击事件"""
        keywords = self.keyword_var.get().strip()
        if not keywords:
            messagebox.showwarning("输入错误", "请输入搜索关键词")
            self.keyword_entry.focus()
            return
        
        offset = self.offset_var.get().strip() or "0"
        limit = self.limit_var.get().strip() or "20"
        
        try:
            offset_int = int(offset)
            limit_int = int(limit)
            
            self.current_keywords = keywords
            self.current_offset = offset_int
            self.current_limit = limit_int
            
            # 在新线程中执行搜索
            thread = threading.Thread(
                target=self._do_search,
                args=(keywords, offset, limit)
            )
            thread.daemon = True
            thread.start()
            
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字")
    
    def _do_search(self, keywords: str, offset: str, limit: str):
        """执行搜索"""
        data = self.search_music(keywords, offset, limit)
        if data:
            self.root.after(0, lambda: self.display_results(data))
    
    def prev_page(self):
        """上一页"""
        if self.current_offset <= 0:
            return
        
        new_offset = max(0, self.current_offset - self.current_limit)
        self.offset_var.set(str(new_offset))
        self.current_offset = new_offset
        self._do_search(self.current_keywords, str(new_offset), str(self.current_limit))
    
    def next_page(self):
        """下一页"""
        new_offset = self.current_offset + self.current_limit
        self.offset_var.set(str(new_offset))
        self.current_offset = new_offset
        self._do_search(self.current_keywords, str(new_offset), str(self.current_limit))
    
    def goto_offset(self):
        """跳转到指定偏移量"""
        offset_str = self.goto_var.get().strip()
        if not offset_str:
            return
        
        try:
            offset = int(offset_str)
            if offset < 0:
                raise ValueError("偏移量不能为负数")
            
            self.offset_var.set(str(offset))
            self.current_offset = offset
            self._do_search(self.current_keywords, str(offset), str(self.current_limit))
            
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字偏移量")
    
    def reset_search(self):
        """重置搜索"""
        self.keyword_var.set("")
        self.offset_var.set("0")
        self.goto_var.set("")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.raw_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        self.download_log_text.delete(1.0, tk.END)
        
        self.detail_name.config(text="")
        self.detail_song_id.config(text="")
        self.detail_artists.config(text="")
        self.detail_album.config(text="")
        self.detail_album_id.config(text="")
        self.detail_artist_ids.config(text="")
        self.detail_duration.config(text="")
        self.detail_publish.config(text="")
        self.detail_download_link.delete(1.0, tk.END)
        self.detail_download_status.config(text="")
        
        self.page_label.config(text="偏移量: 0 | 总数: 0")
        self.prev_btn.config(state="disabled")
        self.next_btn.config(state="disabled")
        self.download_btn.config(state="disabled")
        self.batch_download_btn.config(state="disabled")
        self.test_download_btn.config(state="disabled")
        self.download_status_label.config(text="未选择歌曲")
        
        self.current_keywords = ""
        self.current_offset = 0
        self.current_result = None
        self.song_details = []
        self.selected_song = None
        
        self.log("搜索状态已重置")
        self.status_label.config(text="就绪")
        self.keyword_entry.focus()
    
    def show_about_window(self):
        """显示关于窗口"""
        about_win = tk.Toplevel(self.root)
        about_win.title("关于 网易云音乐搜索下载工具")
        about_win.geometry("400x300")
        about_win.resizable(False, False)
        about_win.configure(bg='white')
        
        # 居中显示
        about_win.transient(self.root)
        about_win.grab_set()
        
        # 标题栏
        title_frame = tk.Frame(about_win, bg='#0078D7', height=60)
        title_frame.pack(fill='x')
        
        tk.Label(title_frame, 
                 text="网易云音乐搜索下载工具", 
                 font=("Microsoft YaHei", 14, "bold"), 
                 bg='#0078D7', 
                 fg='white').pack(pady=15)
        
        # 内容区域
        content_frame = tk.Frame(about_win, bg='white')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # 版本信息
        tk.Label(content_frame, 
                 text="版本 4.0", 
                 font=("Microsoft YaHei", 12), 
                 bg='white').pack(pady=(0, 10))
        
        # 功能说明
        tk.Label(content_frame, 
                 text="功能：搜索 + 下载 一体化", 
                 font=("Microsoft YaHei", 10), 
                 bg='white').pack(pady=5)
        
        # 版权信息
        tk.Label(content_frame, 
                 text="© 2025 文宇香香工作室 版权所有", 
                 font=("Microsoft YaHei", 9), 
                 bg='white').pack(pady=5)
        
        # 作者信息
        tk.Label(content_frame, 
                 text="开发者：文宇香香", 
                 font=("Microsoft YaHei", 10), 
                 bg='white').pack(pady=5)
        
        # 网站链接（可点击）
        link_frame = tk.Frame(content_frame, bg='white')
        link_frame.pack(pady=10)
        
        tk.Label(link_frame, 
                 text="B站主页：", 
                 font=("Microsoft YaHei", 9), 
                 bg='white').pack(side='left')
        
        link_label = tk.Label(link_frame, 
                             text="https://space.bilibili.com/3461564273265329", 
                             font=("Microsoft YaHei", 9), 
                             fg='blue', 
                             bg='white',
                             cursor="hand2")
        link_label.pack(side='left')
        
        def open_bilibili(event):
            webbrowser.open("https://space.bilibili.com/3461564273265329")
        
        link_label.bind("<Button-1>", open_bilibili)
        
        # 确定按钮
        tk.Button(content_frame, 
                  text="确定", 
                  command=about_win.destroy,
                  width=10,
                  bg='#E1E1E1',
                  relief='flat').pack(pady=20)
    
    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            print("如果觉得这个脚本好用的话就给作者个关注吧！求求啦！！！")
            print("作者B站主页：https://space.bilibili.com/3461564273265329")
            self.log("程序关闭")
            self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()


# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("网易云音乐搜索下载工具")
    print("功能：搜索歌曲 -> 直接下载")
    print("=" * 60)
    
    try:
        app = NeteaseSearchDownload()
        app.run()
    except Exception as e:
        logger.error(f"程序启动失败: {e}", exc_info=True)
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")
