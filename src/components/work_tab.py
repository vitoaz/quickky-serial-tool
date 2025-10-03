"""
工作Tab页面

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from datetime import datetime
import threading
from .serial_settings_panel import SerialSettingsPanel
from .receive_settings_panel import ReceiveSettingsPanel
from .send_settings_panel import SendSettingsPanel
from utils.serial_manager import SerialManager
from utils.ttk_paned_window_minisize import ttk_panedwindow_minsize
from utils.hex_utils import HexUtils

class WorkTab(ttk.Frame):
    """工作Tab"""
    
    def __init__(self, parent, config_manager, tab_name='New Tab', is_first_tab=False, on_widget_click=None, on_data_sent=None, panel_type='main'):
        """
        初始化工作Tab
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            tab_name: Tab名称
            is_first_tab: 是否为第一个Tab
            on_widget_click: 控件点击回调函数
            on_data_sent: 数据发送后回调函数
            panel_type: 面板类型 ('main' 或 'secondary')
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.tab_name = tab_name
        self.parent_notebook = parent
        self.is_first_tab = is_first_tab
        self.on_widget_click = on_widget_click
        self.on_data_sent = on_data_sent
        self.panel_type = panel_type
        self.serial_manager = SerialManager()
        self.log_file_path = None  # 日志文件路径，不再持有文件句柄
        self.loop_send_timer = None
        self.theme_manager = None  # 主题管理器将在apply_theme中设置
        
        # 自动重连相关
        self.auto_reconnect_enabled = False  # 是否启用自动重连
        self.reconnect_timer = None  # 重连定时器
        self.reconnect_interval = 5.0  # 重连间隔（秒）
        
        # 延迟创建控件，减少Tab切换时的刷新
        self.after(1, self._init_ui)
    
    def _init_ui(self):
        """初始化UI"""
        self._create_widgets()
        self._setup_callbacks()
    
    def _create_widgets(self):
        """创建控件"""
        # 使用PanedWindow实现可调整的左右分栏
        paned_window = ttk.PanedWindow(self, orient='horizontal')
        paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建最小尺寸管理器
        minsize_manager = ttk_panedwindow_minsize(paned_window, 'horizontal')
        
        # 左侧配置区（参数设置区）
        left_pane = ttk.Frame(paned_window, width=180)
        left_pane.pack_propagate(False)  # 阻止子控件改变Frame大小
        minsize_manager.add_panel(left_pane, min_size=160, weight=0)
        
        # 右侧数据区（可扩展）
        right_pane = ttk.Frame(paned_window)
        minsize_manager.add_panel(right_pane, min_size=300, weight=1)
        
        # 左侧配置区
        # 串口设置
        self.serial_settings = SerialSettingsPanel(left_pane, self.config_manager, 
                                                   on_change_callback=self._on_serial_config_changed,
                                                   panel_type=self.panel_type)
        self.serial_settings.pack(fill='x', pady=(0, 3))
        
        # 连接/断开按钮（放在串口设置下面）
        btn_frame = ttk.Frame(left_pane)
        btn_frame.pack(fill='x', padx=10, pady=3)
        
        self.connect_btn = ttk.Button(btn_frame, text='打开串口', command=self._toggle_connection)
        self.connect_btn.pack(fill='x')
        
        # 接收设置
        self.receive_settings = ReceiveSettingsPanel(left_pane, self.config_manager,
                                                     on_change_callback=self._on_receive_config_changed,
                                                     on_clear_callback=self._clear_receive,
                                                     on_save_log_callback=self._on_save_log_checked)
        self.receive_settings.pack(fill='x', pady=3)
        
        # 发送设置
        self.send_settings = SendSettingsPanel(left_pane, self.config_manager,
                                               on_change_callback=self._on_send_config_changed,
                                               on_mode_change_callback=self._on_send_mode_changed)
        self.send_settings.pack(fill='x', pady=3)
        
        # 右侧数据区
        # 接收区
        receive_frame = ttk.LabelFrame(right_pane, text='数据接收', padding=5)
        receive_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # 使用自定义滚动条的Text控件替代ScrolledText
        text_container = ttk.Frame(receive_frame)
        text_container.pack(fill='both', expand=True)
        
        self.receive_scrollbar = ttk.Scrollbar(text_container, orient='vertical')
        self.receive_scrollbar.pack(side='right', fill='y')
        
        self.receive_text = tk.Text(text_container, height=15, state='disabled',
                                   relief='flat', borderwidth=0, highlightthickness=0,
                                   yscrollcommand=self.receive_scrollbar.set)
        self.receive_text.pack(side='left', fill='both', expand=True)
        self.receive_scrollbar.config(command=self.receive_text.yview)
        
        # 绑定接收区点击事件
        self.receive_text.bind('<Button-1>', self._on_widget_clicked)
        
        # 发送区
        send_frame = ttk.LabelFrame(right_pane, text='数据发送', padding=5)
        send_frame.pack(fill='both')
        
        self.send_text = tk.Text(send_frame, height=5,
                                relief='flat', borderwidth=0, highlightthickness=0)
        self.send_text.pack(fill='both', expand=True)
        
        # 绑定发送区点击事件
        self.send_text.bind('<Button-1>', self._on_widget_clicked)
        
        # 绑定文本改变事件，自动保存
        self.send_text.bind('<<Modified>>', self._on_send_text_modified)
        
        send_btn_frame = ttk.Frame(send_frame)
        send_btn_frame.pack(fill='x', pady=(5, 0))
        
        # 清除发送按钮（Label样式）
        self.clear_send_label = tk.Label(send_btn_frame, text='清除发送', fg='blue', cursor='hand2', font=('', 9))
        self.clear_send_label.pack(side='left')
        self.clear_send_label.bind('<Button-1>', self._clear_send)
        self.clear_send_label.bind('<Enter>', lambda e: self.clear_send_label.config(font=('', 9, 'underline')))
        self.clear_send_label.bind('<Leave>', lambda e: self.clear_send_label.config(font=('', 9)))
        
        # 错误提示Label
        self.send_error_label = tk.Label(send_btn_frame, text='', fg='red', font=('', 9))
        self.send_error_label.pack(side='left', padx=(10, 0))
        
        self.send_btn = ttk.Button(send_btn_frame, text='发送', command=self._toggle_send, state='disabled')
        self.send_btn.pack(side='right')
        
        # 循环发送状态
        self.is_loop_sending = False
    
    def _setup_callbacks(self):
        """设置回调函数"""
        self.serial_manager.set_receive_callback(self._on_data_received)
        self.serial_manager.set_disconnect_callback(self._on_disconnected)
        
        # 只有第一个Tab才默认选择串口
        if self.is_first_tab:
            # 加载上次使用的串口配置或默认选择第一个
            last_port = self.config_manager.get_last_port(self.panel_type)
            if last_port:
                self.serial_settings.set_current_port(last_port)
            else:
                # 默认选择第一个串口
                self.serial_settings._refresh_ports()
                if self.serial_settings.port_combo['values']:
                    first_port = self.serial_settings.port_combo['values'][0]
                    self.serial_settings.set_current_port(first_port)
    
    def _on_serial_config_changed(self, key, value):
        """串口配置变化"""
        if key == 'port':
            # 保存当前串口的发送文本（如果有的话）
            current_port = self.serial_settings.get_current_port()
            if current_port and current_port != value:
                current_text = self.send_text.get('1.0', 'end-1c')
                self.config_manager.set_send_text(current_port, current_text)
            
            # 保存当前面板的最后使用串口
            self.config_manager.set_last_port(value, self.panel_type)
            
            # 加载该串口的接收和发送配置
            config = self.config_manager.get_port_config(value)
            self.receive_settings.load_config(value, config['receive_settings'])
            self.send_settings.load_config(value, config['send_settings'])
            
            # 加载发送文本
            send_text = self.config_manager.get_send_text(value)
            self.send_text.delete('1.0', 'end')
            self.send_text.insert('1.0', send_text)
            
            # 更新Tab标题为串口号
            self._update_tab_title(value)
    
    def _update_tab_title(self, port):
        """更新Tab标题"""
        try:
            # 保存tab名称
            self.tab_name = port
            # 获取当前Tab的索引
            tab_index = self.parent_notebook.index(self)
            # 更新Tab文本为串口号
            self.parent_notebook.tab(tab_index, text=port)
        except:
            pass
    
    def _on_receive_config_changed(self, settings):
        """接收配置变化"""
        # 更新串口自动重连设置
        old_auto_reconnect = self.auto_reconnect_enabled
        self.auto_reconnect_enabled = settings['auto_reconnect']
        
        # 如果从启用变为禁用，停止自动重连
        if old_auto_reconnect and not self.auto_reconnect_enabled:
            self._stop_auto_reconnect()
    
    def _on_save_log_checked(self):
        """保存日志文件勾选时的回调"""
        # 弹出文件选择对话框
        return self._select_log_file()
    
    def _on_send_mode_changed(self, old_mode, new_mode):
        """发送模式切换"""
        # 获取当前发送文本
        text = self.send_text.get('1.0', 'end-1c').strip()
        if not text:
            return
        
        try:
            if old_mode == 'TEXT' and new_mode == 'HEX':
                # TEXT -> HEX: 将文本转为HEX格式
                hex_str = ' '.join([f'{ord(c):02X}' for c in text])
                self.send_text.delete('1.0', 'end')
                self.send_text.insert('1.0', hex_str)
            elif old_mode == 'HEX' and new_mode == 'TEXT':
                # HEX -> TEXT: 将HEX转为文本
                # 移除空格和换行
                hex_str = text.replace(' ', '').replace('\n', '').replace('\r', '')
                # 转换为字节
                if hex_str:
                    bytes_data = bytes.fromhex(hex_str)
                    # 尝试解码为文本
                    text_str = bytes_data.decode('utf-8', errors='ignore')
                    self.send_text.delete('1.0', 'end')
                    self.send_text.insert('1.0', text_str)
        except Exception as e:
            # 转换失败时不做处理
            pass
    
    def _on_send_config_changed(self, settings):
        """发送配置变化"""
        # 检查是否需要停止循环发送
        if settings.get('stop_loop') and self.is_loop_sending:
            self._stop_loop_send()
            self.is_loop_sending = False
            self.send_btn.config(text='发送')
    
    def _on_send_text_modified(self, event=None):
        """发送文本修改事件"""
        # 只在修改标志为True时处理（避免重复触发）
        if self.send_text.edit_modified():
            # 重置修改标志
            self.send_text.edit_modified(False)
            
            # 保存当前串口的发送文本
            port = self.serial_settings.get_current_port()
            if port:
                text = self.send_text.get('1.0', 'end-1c')
                self.config_manager.set_send_text(port, text)
    
    def _toggle_connection(self):
        """切换连接状态"""
        if self.serial_manager.is_open():
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """连接串口"""
        port = self.serial_settings.get_current_port()
        if not port:
            self._append_receive('[错误] 请选择串口\n', 'error')
            return
        
        settings = self.serial_settings.get_settings()
        
        if self.serial_manager.open(
            port=port,
            baudrate=settings['baudrate'],
            parity=settings['parity'],
            bytesize=settings['bytesize'],
            stopbits=settings['stopbits'],
            flow_control=settings['flow_control']
        ):
            self.connect_btn.config(text='关闭串口')
            self.send_btn.config(state='normal')
            self._append_receive(f'[信息] 串口已打开: {port}\n', 'success')
            
            # 禁用串口设置
            self.serial_settings.set_enabled(False)
        else:
            self._append_receive(f'[错误] 打开串口失败: {port}\n', 'error')
            
            # 如果启用了自动重连，开始自动重连
            if self.auto_reconnect_enabled:
                self._start_auto_reconnect()
    
    def _disconnect(self):
        """断开串口"""
        self._stop_loop_send()
        self._stop_auto_reconnect()  # 停止自动重连
        self.serial_manager.close()
        self.connect_btn.config(text='打开串口')
        self.send_btn.config(state='disabled')
        
        # 显示关闭信息（日志会自动写入）
        self._append_receive('[信息] 串口已关闭\n', 'info')
        
        # 启用串口设置
        self.serial_settings.set_enabled(True)
    
    def _on_data_received(self, data):
        """接收到数据"""
        # 使用after确保在主线程中更新UI
        def update_ui():
            settings = self.receive_settings.get_settings()
            
            # 格式化数据
            if settings['mode'] == 'HEX':
                formatted_data = ' '.join([f'{b:02X}' for b in data]) + ' '
            else:
                try:
                    formatted_data = data.decode(settings['encoding'].lower().replace('-', ''))
                except:
                    formatted_data = str(data)
            
            # 显示数据（时间戳由_append_receive统一处理）
            self._append_receive(formatted_data, level='normal')
        
        self.after(0, update_ui)
    
    def _on_disconnected(self):
        """串口断开"""
        def handle_disconnect():
            self._append_receive('[警告] 串口已断开\n', 'warning')
            self.connect_btn.config(text='打开串口')
            self.send_btn.config(state='disabled')
            self.serial_settings.set_enabled(True)
            
            # 如果启用了自动重连，开始重连
            if self.auto_reconnect_enabled:
                self._start_auto_reconnect()
        
        self.after(0, handle_disconnect)
    
    def _toggle_send(self):
        """切换发送/取消循环发送"""
        if self.is_loop_sending:
            # 停止循环发送
            self._stop_loop_send()
            self.is_loop_sending = False
            self.send_btn.config(text='发送')
        else:
            # 正常发送
            self._send_data()
    
    def _send_data(self, override_mode=None):
        """
        发送数据
        
        Args:
            override_mode: 覆盖的发送模式(TEXT/HEX)，如果指定则使用该模式，否则使用当前设置的模式
        """
        data = self.send_text.get('1.0', 'end-1c')
        if not data:
            return
        
        settings = self.send_settings.get_settings()
        
        # 使用覆盖的模式或当前设置的模式
        send_mode = override_mode if override_mode else settings['mode']
        
        # HEX模式下检查格式
        if send_mode == 'HEX':
            if not HexUtils.validate_hex_format(data):
                self.send_error_label.config(text=HexUtils.get_format_error_message())
                # 3秒后清除错误提示
                self.after(3000, lambda: self.send_error_label.config(text=''))
                return
        
        # 清除错误提示
        self.send_error_label.config(text='')
        
        if self.serial_manager.send(data, send_mode, 
                                    self.receive_settings.get_settings()['encoding']):
            # 添加到发送历史（带模式和时间）
            self.config_manager.add_send_history(data, send_mode)
            
            # 通知数据已发送
            if self.on_data_sent:
                self.on_data_sent()
            
            # 循环发送（只在非覆盖模式时生效）
            if not override_mode and settings['loop_send']:
                self.is_loop_sending = True
                self.send_btn.config(text='取消发送')
                self._start_loop_send()
        else:
            self._append_receive('[错误] 发送失败\n', 'error')
    
    
    def _start_loop_send(self):
        """启动循环发送"""
        settings = self.send_settings.get_settings()
        if settings['loop_send'] and self.serial_manager.is_open():
            period = settings['loop_period_ms']
            self.loop_send_timer = threading.Timer(period / 1000.0, self._loop_send_callback)
            self.loop_send_timer.daemon = True
            self.loop_send_timer.start()
    
    def _loop_send_callback(self):
        """循环发送回调"""
        self.after(0, self._send_data)
    
    def _stop_loop_send(self):
        """停止循环发送"""
        if self.loop_send_timer:
            self.loop_send_timer.cancel()
            self.loop_send_timer = None
    
    def _clear_receive(self):
        """清除接收区"""
        self.receive_text.config(state='normal')
        self.receive_text.delete('1.0', 'end')
        self.receive_text.config(state='disabled')
    
    def _clear_send(self, event=None):
        """清除发送区"""
        self.send_text.delete('1.0', 'end')
    
    def _append_receive(self, text, level='normal'):
        """
        追加接收数据（统一处理显示和日志保存）
        
        Args:
            text: 文本内容
            level: 日志级别 ('normal', 'info', 'error', 'success', 'warning')
        """
        # 获取接收设置
        settings = self.receive_settings.get_settings()
        
        # 统一处理时间戳
        display_text = text
        
        # 如果开启了日志模式，则添加时间戳
        if settings['log_mode']:
            # 检查文本是否已经包含时间戳
            if not text.startswith('[') or ']:' not in text[:15]:
                timestamp = datetime.now().strftime('[%H:%M:%S.%f')[:-3] + '] '
                display_text = timestamp + text
                
                # 确保有换行符
                if not display_text.endswith('\n'):
                    display_text += '\n'
        
        # 显示文本
        self.receive_text.config(state='normal')
        
        # 根据主题和级别获取对应的颜色
        if self.theme_manager and level != 'normal':
            colors = self.theme_manager.get_theme_colors()
            # 映射日志级别到主题颜色
            level_color_map = {
                'info': colors.get('log_info_color', '#0066CC'),
                'error': colors.get('log_error_color', '#D32F2F'),
                'success': colors.get('log_success_color', '#388E3C'),
                'warning': colors.get('log_error_color', '#D32F2F'),  # 警告用错误色
            }
            actual_color = level_color_map.get(level, colors.get('text_fg', '#000000'))
        else:
            # 普通文本使用当前主题的文本颜色
            if self.theme_manager:
                colors = self.theme_manager.get_theme_colors()
                actual_color = colors.get('text_fg', '#000000')
            else:
                actual_color = 'black'
        
        # 创建tag
        tag_name = f'level_{level}'
        self.receive_text.tag_config(tag_name, foreground=actual_color)
        
        self.receive_text.insert('end', display_text, tag_name)
        
        # 保存日志文件（不区分串口是否打开，只要勾选了保存日志文件就写入）
        if settings['save_log'] and self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(display_text)
            except Exception as e:
                print(f"写入日志文件失败: {e}")
        
        # 检查buffer大小限制
        global_settings = self.config_manager.get_global_settings()
        max_lines = global_settings.get('receive_buffer_size', 10000)
        
        # 获取当前行数
        current_lines = int(self.receive_text.index('end-1c').split('.')[0])
        
        # 如果超过限制，删除前面的行
        if current_lines > max_lines:
            lines_to_delete = current_lines - max_lines
            self.receive_text.delete('1.0', f'{lines_to_delete + 1}.0')
        
        # 根据接收自动滚屏设置决定是否滚动
        if settings.get('auto_scroll', True):
            self.receive_text.see('end')
        
        self.receive_text.config(state='disabled')
    
    def _select_log_file(self):
        """选择日志文件"""
        port = self.serial_settings.get_current_port()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        default_filename = f'{port}-{timestamp}.log'
        
        file_path = filedialog.asksaveasfilename(
            title='保存日志文件',
            defaultextension='.log',
            initialfile=default_filename,
            filetypes=[('日志文件', '*.log'), ('文本文件', '*.txt'), ('所有文件', '*.*')]
        )
        
        if file_path:
            try:
                # 创建日志文件（如果不存在）
                with open(file_path, 'a', encoding='utf-8') as f:
                    pass  # 仅创建文件
                
                self.log_file_path = file_path
                self._append_receive(f'[信息] 日志文件: {file_path}\n', 'info')
                return True
            except Exception as e:
                self._append_receive(f'[错误] 创建日志文件失败: {e}\n', 'error')
                return False
        return False
    
    def _on_widget_clicked(self, event=None):
        """控件点击事件"""
        if self.on_widget_click:
            self.on_widget_click(self)
    
    def _start_auto_reconnect(self):
        """开始自动重连"""
        # 停止之前的定时器
        self._stop_auto_reconnect()
        
        # 5秒后开始第一次重连尝试（不立即尝试，避免重复日志）
        self.reconnect_timer = self.after(int(self.reconnect_interval * 1000), self._try_reconnect)
    
    def _stop_auto_reconnect(self):
        """停止自动重连"""
        if self.reconnect_timer:
            self.after_cancel(self.reconnect_timer)
            self.reconnect_timer = None
    
    def _try_reconnect(self):
        """尝试重连"""
        # 如果自动重连未启用，停止
        if not self.auto_reconnect_enabled:
            self._stop_auto_reconnect()
            return
        
        # 如果已经连接，停止重连
        if self.serial_manager.is_open():
            self._stop_auto_reconnect()
            return
        
        # 尝试连接
        port = self.serial_settings.get_current_port()
        if not port:
            self._append_receive('[错误] 自动重连失败: 未选择串口\n', 'error')
            # 继续定时重试
            self.reconnect_timer = self.after(int(self.reconnect_interval * 1000), self._try_reconnect)
            return
        
        settings = self.serial_settings.get_settings()
        
        if self.serial_manager.open(
            port=port,
            baudrate=settings['baudrate'],
            parity=settings['parity'],
            bytesize=settings['bytesize'],
            stopbits=settings['stopbits'],
            flow_control=settings['flow_control']
        ):
            # 连接成功
            self.connect_btn.config(text='关闭串口')
            self.send_btn.config(state='normal')
            self._append_receive(f'[信息] 自动重连成功: {port}\n', 'success')
            self.serial_settings.set_enabled(False)
            # 停止重连定时器
            self._stop_auto_reconnect()
        else:
            # 连接失败，继续定时重试
            self._append_receive(f'[错误] 自动重连失败: {port}，{int(self.reconnect_interval)}秒后重试\n', 'error')
            # 继续定时重试
            self.reconnect_timer = self.after(int(self.reconnect_interval * 1000), self._try_reconnect)
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止循环发送
            self._stop_loop_send()
            
            # 停止自动重连
            self._stop_auto_reconnect()
            
            # 关闭串口连接
            if self.serial_manager:
                self.serial_manager.close()
            
            # 日志文件不需要关闭，因为使用即开即关的方式
        except Exception as e:
            print(f"清理Tab资源时出错: {e}")
    
    def apply_theme(self, theme_manager, font_size=9):
        """
        应用主题到工作Tab
        
        Args:
            theme_manager: 主题管理器
            font_size: 字体大小
        """
        self.theme_manager = theme_manager
        colors = theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用到主Frame
            self.configure(style='WorkTab.TFrame')
            
            # 应用到接收区
            if hasattr(self, 'receive_text'):
                self.receive_text.configure(
                    bg=colors.get('text_bg', '#FFFFFF'),
                    fg=colors.get('text_fg', '#000000'),
                    selectbackground=colors.get('selectbackground', '#0078D7'),
                    selectforeground=colors.get('selectforeground', '#FFFFFF'),
                    insertbackground=colors.get('text_fg', '#000000'),
                    font=('Consolas', font_size)
                )
            
            # 应用到发送区
            if hasattr(self, 'send_text'):
                self.send_text.configure(
                    bg=colors.get('text_bg', '#FFFFFF'),
                    fg=colors.get('text_fg', '#000000'),
                    selectbackground=colors.get('selectbackground', '#0078D7'),
                    selectforeground=colors.get('selectforeground', '#FFFFFF'),
                    insertbackground=colors.get('text_fg', '#000000'),
                    font=('Consolas', font_size)
                )
            
            # 应用到设置面板
            if hasattr(self, 'serial_settings') and hasattr(self.serial_settings, 'apply_theme'):
                self.serial_settings.apply_theme(theme_manager)
            
            if hasattr(self, 'receive_settings') and hasattr(self.receive_settings, 'apply_theme'):
                self.receive_settings.apply_theme(theme_manager)
            
            if hasattr(self, 'send_settings') and hasattr(self.send_settings, 'apply_theme'):
                self.send_settings.apply_theme(theme_manager)
            
            # 应用到其他tk控件
            if hasattr(self, 'clear_send_label'):
                self.clear_send_label.configure(
                    bg=colors.get('frame_bg', '#F5F5F5'),
                    fg=colors.get('link_color', '#0066CC')
                )
            
            if hasattr(self, 'send_error_label'):
                self.send_error_label.configure(
                    bg=colors.get('frame_bg', '#F5F5F5'),
                    fg=colors.get('log_error_color', '#D32F2F')
                )
        
        except Exception as e:
            print(f"应用主题到WorkTab失败: {e}")

