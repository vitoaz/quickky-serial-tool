"""
工作Tab页面 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.stc as stc
import wx.adv
from datetime import datetime
import threading
from .serial_settings_panel_wx import SerialSettingsPanel
from .receive_settings_panel_wx import ReceiveSettingsPanel
from .send_settings_panel_wx import SendSettingsPanel
from utils.serial_manager import SerialManager
from utils.hex_utils import HexUtils
from utils.custom_controls_wx import ThemedButton


class WorkTab(wx.Panel):
    """工作Tab"""
    
    def __init__(self, parent, config_manager, tab_name='New Tab', is_first_tab=False, 
                 on_data_sent=None, panel_type='main', parent_notebook=None):
        """
        初始化工作Tab
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            tab_name: Tab名称
            is_first_tab: 是否为第一个Tab
            on_data_sent: 数据发送后回调函数
            panel_type: 面板类型 ('main' 或 'secondary')
            parent_notebook: 父Notebook控件（用于更新Tab标题）
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.tab_name = tab_name
        self.parent_notebook = parent_notebook if parent_notebook else parent
        self.is_first_tab = is_first_tab
        self.on_data_sent = on_data_sent
        self.panel_type = panel_type
        self.serial_manager = SerialManager()
        self.log_file_path = None
        self.loop_send_timer = None
        self.theme_manager = None
        
        # 接收区显示缓冲
        self.display_buffer = []
        self.flush_timer = None
        self.flush_interval_ms = 100
        
        # 日志级别样式定义
        self.level_styles = {
            'normal': 0,   # 使用默认样式
            'info': 1,     # 信息（蓝色）
            'error': 2,    # 错误（红色）
            'success': 3,  # 成功（绿色）
            'warning': 4   # 警告（红色）
        }
        
        # 自动重连相关
        self.auto_reconnect_enabled = False
        self.reconnect_timer = None
        
        # 从全局设置中读取重连间隔
        global_settings = self.config_manager.get_global_settings()
        self.reconnect_interval = global_settings.get('reconnect_interval', 5)
        
        # 统计
        self.rx_count = 0
        self.tx_count = 0
        
        # 创建UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 主横向分割器（左右分栏）
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧配置区
        self._create_left_panel()
        main_sizer.Add(self.left_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 右侧数据区
        self._create_right_panel()
        main_sizer.Add(self.right_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
        # 设置回调
        self._setup_callbacks()
    
    def _create_left_panel(self):
        """创建左侧配置面板"""
        self.left_panel = wx.Panel(self)
        self.left_panel.SetMinSize((180, -1))
        
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 串口设置面板
        self.serial_settings = SerialSettingsPanel(
            self.left_panel,
            self.config_manager,
            on_change_callback=self._on_serial_config_changed,
            panel_type=self.panel_type
        )
        left_sizer.Add(self.serial_settings, 0, wx.EXPAND | wx.ALL, 3)
        
        # 连接按钮
        self.connect_btn = ThemedButton(self.left_panel, label='打开串口')
        self.connect_btn.Bind(wx.EVT_BUTTON, self._toggle_connection)
        left_sizer.Add(self.connect_btn, 0, wx.EXPAND | wx.ALL, 10)
        
        # 接收设置面板
        self.receive_settings = ReceiveSettingsPanel(
            self.left_panel,
            self.config_manager,
            on_change_callback=self._on_receive_config_changed,
            on_clear_callback=self._clear_receive,
            on_save_log_callback=self._on_save_log_checked
        )
        left_sizer.Add(self.receive_settings, 0, wx.EXPAND | wx.ALL, 2)
        
        # 发送设置面板
        self.send_settings = SendSettingsPanel(
            self.left_panel,
            self.config_manager,
            on_change_callback=self._on_send_config_changed,
            on_mode_change_callback=self._on_send_mode_changed
        )
        left_sizer.Add(self.send_settings, 0, wx.EXPAND | wx.ALL, 2)
        
        self.left_panel.SetSizer(left_sizer)
    
    def _create_right_panel(self):
        """创建右侧数据面板"""
        self.right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 接收区
        receive_box = wx.StaticBox(self.right_panel, label='数据接收')
        receive_sizer = wx.StaticBoxSizer(receive_box, wx.VERTICAL)
        
        # 使用 StyledTextCtrl 实现高性能文本显示
        self.receive_text = stc.StyledTextCtrl(self.right_panel, style=wx.BORDER_NONE)
        self._setup_stc(self.receive_text)
        self.receive_text.SetReadOnly(True)
        
        receive_sizer.Add(self.receive_text, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(receive_sizer, 1, wx.EXPAND | wx.BOTTOM, 5)
        
        # 发送区
        send_box = wx.StaticBox(self.right_panel, label='数据发送')
        send_sizer = wx.StaticBoxSizer(send_box, wx.VERTICAL)
        
        # 发送文本框
        self.send_text = wx.TextCtrl(
            self.right_panel,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.BORDER_NONE,
            size=(-1, 100)
        )
        # 设置字体 - 从配置中获取字体大小
        font_size = self.config_manager.get_font_size()
        send_font = wx.Font(font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Consolas')
        self.send_text.SetFont(send_font)
        
        self.send_text.Bind(wx.EVT_TEXT, self._on_send_text_modified)
        send_sizer.Add(self.send_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # 发送按钮区
        btn_panel = wx.Panel(self.right_panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 清除发送按钮（使用StaticText模拟超链接）
        self.clear_send_label = wx.StaticText(btn_panel, label='清除发送')
        self.clear_send_label.SetForegroundColour(wx.Colour(0, 102, 204))
        self.clear_send_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        # 设置默认下划线
        font = self.clear_send_label.GetFont()
        font.MakeUnderlined()
        self.clear_send_label.SetFont(font)
        self.clear_send_label.Bind(wx.EVT_LEFT_DOWN, self._clear_send)
        btn_sizer.Add(self.clear_send_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # 错误提示
        self.send_error_label = wx.StaticText(btn_panel, label='')
        btn_sizer.Add(self.send_error_label, 1, wx.ALIGN_CENTER_VERTICAL)
        
        # 发送按钮
        self.send_btn = ThemedButton(btn_panel, label='发送')
        self.send_btn.Enable(False)
        self.send_btn.Bind(wx.EVT_BUTTON, self._toggle_send)
        btn_sizer.Add(self.send_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        btn_panel.SetSizer(btn_sizer)
        send_sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(send_sizer, 0, wx.EXPAND)
        
        # 统计栏
        stats_panel = wx.Panel(self.right_panel)
        stats_panel.SetBackgroundColour(wx.Colour(239, 239, 239))
        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 复位计数（使用StaticText模拟超链接，放在最右侧）
        self.reset_count_label = wx.StaticText(stats_panel, label='复位计数')
        self.reset_count_label.SetForegroundColour(wx.Colour(0, 102, 204))
        self.reset_count_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        # 设置默认下划线
        font = self.reset_count_label.GetFont()
        font.MakeUnderlined()
        self.reset_count_label.SetFont(font)
        self.reset_count_label.Bind(wx.EVT_LEFT_DOWN, self._reset_count)
        stats_sizer.Add(self.reset_count_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        stats_sizer.AddStretchSpacer(1)
        
        # RX/TX计数（合并到一个label，设置最小宽度，右对齐）
        self.count_label = wx.StaticText(stats_panel, label='RX: 0  TX: 0', style=wx.ALIGN_RIGHT)
        self.count_label.SetMinSize((150, -1))  # 设置最小宽度150像素
        stats_sizer.Add(self.count_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        stats_panel.SetSizer(stats_sizer)
        right_sizer.Add(stats_panel, 0, wx.EXPAND | wx.TOP, 2)
        
        self.right_panel.SetSizer(right_sizer)
    
    def _setup_stc(self, stc_ctrl):
        """设置StyledTextCtrl的属性以优化性能"""
        # 启用自动换行（避免横向滚动条）
        stc_ctrl.SetWrapMode(stc.STC_WRAP_WORD)  # 按单词换行
        
        # 设置缓冲区大小
        stc_ctrl.SetBufferedDraw(True)
        
        # 设置滚动条
        stc_ctrl.SetUseHorizontalScrollBar(False)  # 禁用横向滚动条（因为启用了自动换行）
        stc_ctrl.SetUseVerticalScrollBar(True)  # 启用纵向滚动条
        
        # 设置滚动宽度跟踪（确保不会出现不必要的滚动）
        stc_ctrl.SetScrollWidth(1)
        stc_ctrl.SetScrollWidthTracking(True)
        
        # 设置字体 - 从配置中获取字体大小
        font_size = self.config_manager.get_font_size()
        font = wx.Font(font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Consolas')
        stc_ctrl.StyleSetFont(stc.STC_STYLE_DEFAULT, font)
        stc_ctrl.StyleClearAll()
        
        # 初始化日志级别样式颜色
        self._initialize_receive_styles(stc_ctrl, font)
        
        # 设置边距
        stc_ctrl.SetMarginWidth(0, 0)  # 行号边距
        stc_ctrl.SetMarginWidth(1, 0)  # 符号边距
        stc_ctrl.SetMarginWidth(2, 0)  # 折叠边距
    
    def _initialize_receive_styles(self, stc_ctrl, font):
        """初始化接收区日志级别样式"""
        # 定义默认颜色
        default_colors = {
            'normal': '#000000',
            'info': '#0066CC',
            'error': '#D32F2F',
            'success': '#388E3C',
            'warning': '#D32F2F',
        }
        
        # 从主题管理器获取颜色（如果有）
        colors = self.theme_manager.get_theme_colors() if self.theme_manager else {}
        
        # 为每个级别设置样式
        for level, style_id in self.level_styles.items():
            if level == 'normal':
                color = colors.get('text_fg', default_colors['normal'])
            else:
                color_key = f'log_{level}_color'
                color = colors.get(color_key, default_colors.get(level, default_colors['error']))
            
            # 设置样式
            stc_ctrl.StyleSetFont(style_id, font)
            stc_ctrl.StyleSetForeground(style_id, wx.Colour(color))
    
    def _setup_callbacks(self):
        """设置回调函数"""
        self.serial_manager.set_receive_callback(self._on_data_received)
        self.serial_manager.set_disconnect_callback(self._on_disconnected)
        
        # 只有第一个Tab才默认选择串口
        if self.is_first_tab:
            # 延迟执行，确保Tab已经完全加载到Notebook中
            wx.CallAfter(self._init_default_port)
    
    def _init_default_port(self):
        """初始化默认串口（延迟执行）"""
        # 刷新串口列表
        self.serial_settings._refresh_ports()
        
        # 尝试加载上次使用的串口
        last_port = self.config_manager.get_last_port(self.panel_type)
        ports = self.serial_settings.get_available_ports()
        
        if last_port and last_port in ports:
            # 如果上次的串口还存在，选择它
            self.serial_settings.set_current_port(last_port)
        elif ports:
            # 否则选择第一个可用串口
            self.serial_settings.set_current_port(ports[0])
    
    def _on_serial_config_changed(self, key, value):
        """串口配置变化"""
        if key == 'port':
            # 保存当前串口的发送文本
            current_port = self.serial_settings.get_current_port()
            if current_port and current_port != value:
                current_text = self.send_text.GetValue()
                self.config_manager.set_send_text(current_port, current_text)
            
            # 保存当前面板的最后使用串口
            self.config_manager.set_last_port(value, self.panel_type)
            
            # 加载该串口的配置
            config = self.config_manager.get_port_config(value)
            self.receive_settings.load_config(value, config['receive_settings'])
            self.send_settings.load_config(value, config['send_settings'])
            
            # 加载发送文本
            send_text = self.config_manager.get_send_text(value)
            self.send_text.SetValue(send_text)
            
            # 更新Tab标题
            self._update_tab_title(value)
    
    def _update_tab_title(self, port):
        """更新Tab标题"""
        try:
            self.tab_name = port
            # 查找当前Tab在Notebook中的索引并更新标题
            if self.parent_notebook:
                for i in range(self.parent_notebook.GetPageCount()):
                    if self.parent_notebook.GetPage(i) == self:
                        self.parent_notebook.SetPageText(i, port)
                        print(f"Updated tab {i} title to: {port}")
                        break
        except Exception as e:
            print(f"Error updating tab title: {e}")
    
    def _on_receive_config_changed(self, settings):
        """接收配置变化"""
        old_auto_reconnect = self.auto_reconnect_enabled
        self.auto_reconnect_enabled = settings['auto_reconnect']
        
        if old_auto_reconnect and not self.auto_reconnect_enabled:
            self._stop_auto_reconnect()
    
    def _on_save_log_checked(self):
        """保存日志文件勾选时的回调"""
        return self._select_log_file()
    
    def _on_send_mode_changed(self, old_mode, new_mode):
        """发送模式切换"""
        text = self.send_text.GetValue().strip()
        if not text:
            return
        
        try:
            if old_mode == 'TEXT' and new_mode == 'HEX':
                # TEXT -> HEX
                hex_str = ' '.join([f'{ord(c):02X}' for c in text])
                self.send_text.SetValue(hex_str)
            elif old_mode == 'HEX' and new_mode == 'TEXT':
                # HEX -> TEXT
                hex_str = text.replace(' ', '').replace('\n', '').replace('\r', '')
                if hex_str:
                    bytes_data = bytes.fromhex(hex_str)
                    text_str = bytes_data.decode('utf-8', errors='ignore')
                    self.send_text.SetValue(text_str)
        except Exception as e:
            pass
    
    def _on_send_config_changed(self, settings):
        """发送配置变化"""
        if settings.get('stop_loop') and hasattr(self, 'is_loop_sending') and self.is_loop_sending:
            self._stop_loop_send()
            self.is_loop_sending = False
            self.send_btn.SetLabel('发送')
    
    def _on_send_text_modified(self, event):
        """发送文本修改事件"""
        port = self.serial_settings.get_current_port()
        if port:
            text = self.send_text.GetValue()
            self.config_manager.set_send_text(port, text)
    
    def _toggle_connection(self, event):
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
            self.connect_btn.SetLabel('关闭串口')
            self.send_btn.Enable(True)
            self._append_receive(f'[信息] 串口已打开: {port}\n', 'success')
            self.serial_settings.set_enabled(False)
        else:
            self._append_receive(f'[错误] 打开串口失败: {port}\n', 'error')
            if self.auto_reconnect_enabled:
                self._start_auto_reconnect()
    
    def _disconnect(self):
        """断开串口"""
        self._stop_loop_send()
        self._stop_auto_reconnect()
        self.serial_manager.close()
        self.connect_btn.SetLabel('打开串口')
        self.send_btn.Enable(False)
        self._append_receive('[信息] 串口已关闭\n', 'info')
        self.serial_settings.set_enabled(True)
    
    def _on_data_received(self, data):
        """接收到数据"""
        wx.CallAfter(self._update_receive_ui, data)
    
    def _update_receive_ui(self, data):
        """更新接收UI"""
        settings = self.receive_settings.get_settings()
        
        # 更新RX计数
        self.rx_count += len(data)
        self.count_label.SetLabel(f'RX: {self.rx_count}  TX: {self.tx_count}')
        
        # 格式化数据
        if settings['mode'] == 'HEX':
            formatted_data = ' '.join([f'{b:02X}' for b in data]) + ' '
            if settings['log_mode']:
                formatted_data += '\n'
            self._append_receive(formatted_data)
        else:
            try:
                formatted_data = data.decode(settings['encoding'].lower().replace('-', ''))
            except:
                formatted_data = str(data)
            
            if settings['log_mode'] and ('\n' in formatted_data or '\r' in formatted_data):
                lines = formatted_data.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                for i, line in enumerate(lines):
                    if i < len(lines) - 1:
                        self._append_receive(line + '\n', flush=False)
                    elif line:
                        self._append_receive(line, flush=True)
                if lines and not lines[-1]:
                    self._flush_display(force=True)
            else:
                self._append_receive(formatted_data)
    
    def _on_disconnected(self):
        """串口断开"""
        wx.CallAfter(self._handle_disconnect)
    
    def _handle_disconnect(self):
        """处理断开事件"""
        self._append_receive('[警告] 串口已断开\n', 'warning')
        self.connect_btn.SetLabel('打开串口')
        self.send_btn.Enable(False)
        self.serial_settings.set_enabled(True)
        
        if self.auto_reconnect_enabled:
            self._start_auto_reconnect()
    
    def _toggle_send(self, event):
        """切换发送/取消循环发送"""
        if hasattr(self, 'is_loop_sending') and self.is_loop_sending:
            self._stop_loop_send()
            self.is_loop_sending = False
            self.send_btn.SetLabel('发送')
        else:
            self._send_data()
    
    def _send_data(self, override_mode=None):
        """发送数据"""
        data = self.send_text.GetValue()
        if not data:
            return
        
        settings = self.send_settings.get_settings()
        send_mode = override_mode if override_mode else settings['mode']
        
        # HEX模式下检查格式
        if send_mode == 'HEX':
            if not HexUtils.validate_hex_format(data):
                self.send_error_label.SetLabel(HexUtils.get_format_error_message())
                self.send_error_label.SetForegroundColour(wx.Colour(211, 47, 47))
                wx.CallLater(3000, lambda: self.send_error_label.SetLabel(''))
                return
        
        self.send_error_label.SetLabel('')
        
        # 计算发送的字节数
        byte_count = 0
        if send_mode == 'HEX':
            hex_str = data.replace(' ', '').replace('\n', '').replace('\r', '')
            byte_count = len(hex_str) // 2
        else:
            encoding = self.receive_settings.get_settings()['encoding'].lower().replace('-', '')
            byte_count = len(data.encode(encoding))
        
        if self.serial_manager.send(data, send_mode, 
                                    self.receive_settings.get_settings()['encoding']):
            # 更新TX计数
            self.tx_count += byte_count
            self.count_label.SetLabel(f'RX: {self.rx_count}  TX: {self.tx_count}')
            
            # 添加到发送历史
            self.config_manager.add_send_history(data, send_mode)
            
            # 通知数据已发送
            if self.on_data_sent:
                self.on_data_sent()
            
            # 循环发送
            if not override_mode and settings['loop_send']:
                self.is_loop_sending = True
                self.send_btn.SetLabel('取消发送')
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
        wx.CallAfter(self._send_data)
    
    def _stop_loop_send(self):
        """停止循环发送"""
        if self.loop_send_timer:
            self.loop_send_timer.cancel()
            self.loop_send_timer = None
    
    def _clear_receive(self):
        """清除接收区"""
        self.receive_text.SetReadOnly(False)
        self.receive_text.ClearAll()
        self.receive_text.SetReadOnly(True)
    
    def _clear_send(self, event):
        """清除发送区"""
        self.send_text.Clear()
    
    def _append_receive(self, text, level='normal', flush=True):
        """追加接收数据"""
        settings = self.receive_settings.get_settings()
        
        # 添加时间戳
        display_text = text
        if settings['log_mode']:
            timestamp = datetime.now().strftime('[%H:%M:%S.%f')[:-3] + '] '
            display_text = timestamp + text
        
        # 添加到缓冲区
        self.display_buffer.append({
            'text': display_text,
            'level': level
        })
        
        # 保存到日志文件
        if settings['save_log'] and self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(display_text)
            except Exception as e:
                print(f"写入日志文件失败: {e}")
        
        # 刷新显示
        if flush:
            self._schedule_flush()
    
    def _schedule_flush(self):
        """安排延迟刷新"""
        if self.flush_timer is None:
            self.flush_timer = wx.CallLater(self.flush_interval_ms, self._perform_scheduled_flush)
    
    def _perform_scheduled_flush(self):
        """执行延迟刷新"""
        self.flush_timer = None
        self._flush_display_internal()
    
    def _flush_display(self, force=False):
        """强制刷新显示"""
        if force and self.flush_timer:
            self.flush_timer.Stop()
            self.flush_timer = None
        self._flush_display_internal()
    
    def _flush_display_internal(self):
        """刷新显示缓冲区内容"""
        if not self.display_buffer:
            return
        
        settings = self.receive_settings.get_settings()
        
        self.receive_text.SetReadOnly(False)
        
        # 批量插入文本，应用样式
        for item in self.display_buffer:
            text = item['text']
            level = item.get('level', 'normal')
            style_id = self.level_styles.get(level, 0)
            
            # 获取当前文本末尾位置
            pos = self.receive_text.GetLength()
            
            # 插入文本
            self.receive_text.AppendText(text)
            
            # 应用样式到新插入的文本
            end_pos = self.receive_text.GetLength()
            self.receive_text.StartStyling(pos)
            self.receive_text.SetStyling(end_pos - pos, style_id)
        
        # 清空缓冲区
        self.display_buffer.clear()
        
        # 检查buffer大小限制
        global_settings = self.config_manager.get_global_settings()
        max_lines = global_settings.get('receive_buffer_size', 10000)
        
        # 如果超过限制，删除前面的行
        line_count = self.receive_text.GetLineCount()
        if line_count > max_lines:
            lines_to_delete = line_count - max_lines
            pos = self.receive_text.PositionFromLine(lines_to_delete)
            self.receive_text.SetTargetStart(0)
            self.receive_text.SetTargetEnd(pos)
            self.receive_text.ReplaceTarget('')
        
        # 自动滚屏
        if settings.get('auto_scroll', True):
            self.receive_text.ScrollToEnd()
        
        self.receive_text.SetReadOnly(True)
    
    def _select_log_file(self):
        """选择日志文件"""
        port = self.serial_settings.get_current_port()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        default_filename = f'{port}-{timestamp}.log'
        
        dlg = wx.FileDialog(
            self,
            '保存日志文件',
            defaultFile=default_filename,
            wildcard='日志文件 (*.log)|*.log|文本文件 (*.txt)|*.txt|所有文件 (*.*)|*.*',
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    pass
                self.log_file_path = file_path
                self._append_receive(f'[信息] 日志文件: {file_path}\n', 'info')
                dlg.Destroy()
                return True
            except Exception as e:
                self._append_receive(f'[错误] 创建日志文件失败: {e}\n', 'error')
                dlg.Destroy()
                return False
        
        dlg.Destroy()
        return False
    
    def _reset_count(self, event):
        """复位计数"""
        self.rx_count = 0
        self.tx_count = 0
        self.count_label.SetLabel('RX: 0  TX: 0')
    
    def _start_auto_reconnect(self):
        """开始自动重连"""
        self._stop_auto_reconnect()
        
        global_settings = self.config_manager.get_global_settings()
        self.reconnect_interval = global_settings.get('reconnect_interval', 5)
        
        self.reconnect_timer = wx.CallLater(int(self.reconnect_interval * 1000), self._try_reconnect)
    
    def _stop_auto_reconnect(self):
        """停止自动重连"""
        if self.reconnect_timer:
            self.reconnect_timer.Stop()
            self.reconnect_timer = None
    
    def _try_reconnect(self):
        """尝试重连"""
        if not self.auto_reconnect_enabled:
            self._stop_auto_reconnect()
            return
        
        if self.serial_manager.is_open():
            self._stop_auto_reconnect()
            return
        
        port = self.serial_settings.get_current_port()
        if not port:
            self._append_receive('[错误] 自动重连失败: 未选择串口\n', 'error')
            self.reconnect_timer = wx.CallLater(int(self.reconnect_interval * 1000), self._try_reconnect)
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
            self.connect_btn.SetLabel('关闭串口')
            self.send_btn.Enable(True)
            self._append_receive(f'[信息] 自动重连成功: {port}\n', 'success')
            self.serial_settings.set_enabled(False)
            self._stop_auto_reconnect()
        else:
            self._append_receive(f'[错误] 自动重连失败: {port}，{int(self.reconnect_interval)}秒后重试\n', 'error')
            self.reconnect_timer = wx.CallLater(int(self.reconnect_interval * 1000), self._try_reconnect)
    
    def cleanup(self):
        """清理资源"""
        try:
            self._stop_loop_send()
            self._stop_auto_reconnect()
            if self.serial_manager:
                self.serial_manager.close()
        except Exception as e:
            print(f"清理Tab资源时出错: {e}")
    
    def apply_theme(self, theme_manager, font_size=9):
        """应用主题"""
        self.theme_manager = theme_manager
        colors = theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用到按钮
            btn_bg = theme_manager.hex_to_wx_colour(colors.get('button_bg', '#0078D4'))
            btn_fg = theme_manager.hex_to_wx_colour(colors.get('button_fg', '#FFFFFF'))
            self.connect_btn.apply_theme(btn_bg, btn_fg)
            self.send_btn.apply_theme(btn_bg, btn_fg)
            
            # 应用到接收区 (STC)
            bg_color = theme_manager.hex_to_wx_colour(colors.get('text_bg', '#FFFFFF'))
            fg_color = theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
            
            self.receive_text.StyleSetBackground(stc.STC_STYLE_DEFAULT, bg_color)
            self.receive_text.StyleSetForeground(stc.STC_STYLE_DEFAULT, fg_color)
            self.receive_text.StyleClearAll()
            
            # 更新字体
            font = wx.Font(font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, 
                          wx.FONTWEIGHT_NORMAL, False, 'Consolas')
            self.receive_text.StyleSetFont(stc.STC_STYLE_DEFAULT, font)
            
            # 重新初始化日志级别样式（应用新主题颜色）
            self._initialize_receive_styles(self.receive_text, font)
            
            # 应用到发送区
            self.send_text.SetBackgroundColour(bg_color)
            self.send_text.SetForegroundColour(fg_color)
            self.send_text.SetFont(font)
            self.send_text.Refresh()
            
            # 强制更新接收区背景
            self.receive_text.SetCaretForeground(fg_color)
            
            # 设置滚动条颜色（仅对StyledTextCtrl有效）
            try:
                # 尝试设置滚动条背景色
                scrollbar_bg = theme_manager.hex_to_wx_colour(colors.get('scrollbar_bg', bg_color))
                scrollbar_fg = theme_manager.hex_to_wx_colour(colors.get('scrollbar_fg', fg_color))
                # StyledTextCtrl没有直接的滚动条颜色API，但可以设置边框颜色
                # self.receive_text.SetEdgeColour(scrollbar_bg)
            except:
                pass
            
            self.receive_text.Refresh()
            
            # 应用到设置面板
            if hasattr(self.serial_settings, 'apply_theme'):
                self.serial_settings.apply_theme(theme_manager)
            if hasattr(self.receive_settings, 'apply_theme'):
                self.receive_settings.apply_theme(theme_manager)
            if hasattr(self.send_settings, 'apply_theme'):
                self.send_settings.apply_theme(theme_manager)
            
            # 应用链接颜色到"清除发送"和"复位计数"
            link_color = theme_manager.hex_to_wx_colour(colors.get('link_color', '#4FC3F7'))
            self.clear_send_label.SetForegroundColour(link_color)
            self.reset_count_label.SetForegroundColour(link_color)
            
            self.Refresh()
        
        except Exception as e:
            print(f"应用主题到WorkTab失败: {e}")

