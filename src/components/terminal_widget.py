"""
基于Pyte的终端控件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import scrolledtext
import pyte
import threading
import time


class TerminalWidget(tk.Frame):
    """基于Pyte的终端模拟器控件"""
    
    def __init__(self, parent, width=100, height=20, **kwargs):
        """
        初始化终端控件
        
        Args:
            parent: 父控件
            width: 终端宽度（字符数）
            height: 终端高度（行数）
        """
        super().__init__(parent, **kwargs)
        
        self.width = width
        self.height = height
        
        # 创建显示用的Pyte终端和屏幕
        self.screen = pyte.Screen(width, height)
        self.stream = pyte.Stream(self.screen)
        
        # 创建输入处理用的Pyte终端（用于标准化键盘输入）
        self.input_buffer = []  # 存储要发送的数据
        
        # 创建文本控件
        self.text_widget = scrolledtext.ScrolledText(
            self,
            width=width,
            height=height,
            font=('Consolas', 10),
            bg='black',
            fg='white',
            state='normal',
            wrap='none',
            highlightthickness=0,  # 移除焦点边框
            selectbackground='#404040'  # 选择背景色
        )
        self.text_widget.pack(fill='both', expand=True)
        
        # 禁用文本编辑器的光标，我们用自定义光标
        self.text_widget.config(insertwidth=0)
        
        # 配置颜色标签
        self._setup_color_tags()
        
        # 绑定键盘事件
        self.text_widget.bind('<Key>', self._on_key_press)
        self.text_widget.bind('<Button-1>', self._on_click)
        self.text_widget.bind('<FocusIn>', self._on_focus_in)
        self.text_widget.bind('<FocusOut>', self._on_focus_out)
        
        # 回调函数
        self.on_input = None  # 用户输入回调
        
        # 更新线程控制
        self._update_running = True
        self._update_thread = threading.Thread(target=self._update_display, daemon=True)
        self._update_thread.start()
    
    def _setup_color_tags(self):
        """设置颜色标签"""
        # 定义颜色映射
        colors = {
            'black': '#000000',
            'red': '#FF0000',
            'green': '#00FF00',
            'yellow': '#FFFF00',
            'blue': '#0000FF',
            'magenta': '#FF00FF',
            'cyan': '#00FFFF',
            'white': '#FFFFFF',
            'orange': '#FFA500',
            'gray': '#808080',
            'lightred': '#FF6666',
            'lightgreen': '#66FF66',
            'lightblue': '#6666FF'
        }
        
        # 为每种颜色创建标签
        for color_name, color_value in colors.items():
            self.text_widget.tag_config(f'color_{color_name}', foreground=color_value)
    
    def write(self, data, color=None):
        """
        向终端写入数据
        
        Args:
            data: 要写入的数据（字符串或字节）
            color: 文本颜色（可选）
        """
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8', errors='replace')
            except:
                data = str(data)
        
        if color:
            # 如果指定了颜色，直接插入带颜色的文本
            self._write_colored_text(data, color)
        else:
            # 将数据传递给Pyte流处理
            self.stream.feed(data)
    
    
    def _write_colored_text(self, text, color):
        """写入带颜色的文本"""
        try:
            # 获取当前内容
            current_content = self.text_widget.get('1.0', 'end-1c')
            
            # 插入带颜色的文本
            self.text_widget.config(state='normal')
            self.text_widget.insert('end', text, f'color_{color}')
            
            # 设置光标位置到末尾
            self.text_widget.mark_set(tk.INSERT, 'end')
            self.text_widget.see('end')
            
        except Exception as e:
            print(f"写入彩色文本错误: {e}")
            # 回退到普通写入
            self.stream.feed(text)
    
    def _update_display(self):
        """更新显示线程"""
        last_display = None
        
        while self._update_running:
            try:
                # 获取当前屏幕内容和光标位置
                current_display = self._get_screen_content()
                
                # 只有内容变化时才更新
                if current_display != last_display:
                    self.after(0, self._refresh_display, current_display)
                    last_display = current_display
                
                time.sleep(0.01)  # 100Hz更新频率
            except Exception as e:
                print(f"终端更新错误: {e}")
                time.sleep(0.1)
    
    def _get_screen_content(self):
        """获取屏幕内容和光标位置"""
        lines = []
        for y in range(self.screen.lines):
            line = ""
            for x in range(self.screen.columns):
                char = self.screen.buffer[y][x]
                line += char.data
            lines.append(line.rstrip())  # 移除行尾空格
        
        # 移除末尾的空行
        while lines and not lines[-1]:
            lines.pop()
        
        # 获取光标位置
        cursor_row = self.screen.cursor.y
        cursor_col = self.screen.cursor.x
        
        return {
            'content': '\n'.join(lines),
            'cursor_row': cursor_row,
            'cursor_col': cursor_col
        }
    
    def _refresh_display(self, display_data):
        """刷新显示内容"""
        try:
            content = display_data['content']
            cursor_row = display_data['cursor_row']
            cursor_col = display_data['cursor_col']
            
            # 更新内容
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', 'end')
            self.text_widget.insert('1.0', content)
            
            # 设置光标位置（基于Pyte的光标位置）
            cursor_line = cursor_row + 1  # Tkinter行号从1开始
            
            try:
                self.text_widget.mark_set(tk.INSERT, f'{cursor_line}.{cursor_col}')
            except:
                self.text_widget.mark_set(tk.INSERT, 'end')
            
            # 自动滚动到光标位置
            self.text_widget.see(tk.INSERT)
            
            # 绘制自定义光标块
            self._draw_cursor_block(cursor_row, cursor_col)
            
        except Exception as e:
            print(f"刷新显示错误: {e}")
    
    def _draw_cursor_block(self, cursor_row, cursor_col):
        """绘制终端风格的光标块"""
        try:
            # 清除之前的光标标记
            self.text_widget.tag_delete('cursor_block')
            
            # 确保文本控件有足够的行数
            current_content = self.text_widget.get('1.0', 'end-1c')
            lines = current_content.split('\n')
            
            # 如果需要，添加空行到指定的光标行
            while len(lines) <= cursor_row:
                lines.append('')
            
            # 确保当前行有足够的字符
            if len(lines[cursor_row]) <= cursor_col:
                # 用空格填充到光标位置
                lines[cursor_row] = lines[cursor_row].ljust(cursor_col + 1)
            
            # 更新文本控件内容
            updated_content = '\n'.join(lines)
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', 'end')
            self.text_widget.insert('1.0', updated_content)
            
            # 计算光标位置
            cursor_line = cursor_row + 1  # Tkinter行号从1开始
            start_pos = f'{cursor_line}.{cursor_col}'
            end_pos = f'{cursor_line}.{cursor_col + 1}'
            
            # 创建光标块标记
            self.text_widget.tag_add('cursor_block', start_pos, end_pos)
            self.text_widget.tag_config('cursor_block', 
                                      background='white', 
                                      foreground='black')
            
        except Exception as e:
            print(f"绘制光标错误: {e}")
    
    
    def _on_key_press(self, event):
        """处理按键事件"""
        if not self.on_input:
            return 'break'
        
        # 获取按键信息
        keysym = event.keysym
        char = event.char
        
        # 直接转换为终端序列并发送
        key_data = self._convert_key_to_sequence(keysym, char, event.state)
        
        if key_data:
            self.on_input(key_data)
        
        return 'break'
    
    def _convert_key_to_sequence(self, keysym, char, state):
        """将按键转换为标准终端序列"""
        # 使用标准的键盘到终端序列映射表
        key_map = {
            'Return': '\r\n',
            'BackSpace': '\x08 \x08',  # 退格+空格+退格（标准删除序列）
            'Tab': '\t',
            'Escape': '\x1b',
            'Delete': ' \x08',  # Delete键：空格+退格（删除当前字符）
            'Up': '\x1b[A',
            'Down': '\x1b[B',
            'Right': '\x1b[C',
            'Left': '\x1b[D',
            'Home': '\x1b[H',
            'End': '\x1b[F',
            'Prior': '\x1b[5~',  # Page Up
            'Next': '\x1b[6~',   # Page Down
        }
        
        # 检查是否是映射表中的特殊键
        if keysym in key_map:
            return key_map[keysym]
        
        # 功能键 F1-F12
        if keysym.startswith('F') and keysym[1:].isdigit():
            fkey_num = int(keysym[1:])
            if 1 <= fkey_num <= 12:
                if fkey_num <= 4:
                    return f'\x1b[{10 + fkey_num}~'
                else:
                    return f'\x1b[{15 + fkey_num}~'
        
        # Ctrl组合键
        ctrl = (state & 0x4) != 0
        if ctrl and char and len(char) == 1:
            if 'a' <= char.lower() <= 'z':
                return chr(ord(char.lower()) - ord('a') + 1)
            elif ord(char) < 32:
                return char
        
        # 普通可打印字符
        if char and len(char) == 1 and ord(char) >= 32:
            return char
        
        return None
    
    def _on_click(self, event):
        """处理鼠标点击"""
        # 不强制设置焦点，允许正常的鼠标选择行为
        # 光标位置由Pyte管理，不受鼠标点击影响
        return None
    
    def _on_focus_in(self, event):
        """获得焦点时"""
        # 可以在这里添加获得焦点时的处理
        pass
    
    def _on_focus_out(self, event):
        """失去焦点时"""
        # 可以在这里添加失去焦点时的处理
        pass
    
    
    def clear(self):
        """清屏"""
        self.screen.reset()
    
    def resize(self, width, height):
        """调整终端大小"""
        self.width = width
        self.height = height
        self.screen.resize(height, width)
        self.text_widget.config(width=width, height=height)
    
    def set_input_callback(self, callback):
        """设置输入回调函数"""
        self.on_input = callback
    
    def destroy(self):
        """销毁控件"""
        self._update_running = False
        if hasattr(self, '_update_thread'):
            self._update_thread.join(timeout=1.0)
        super().destroy()


# 使用示例
if __name__ == "__main__":
    def on_terminal_input(data):
        """终端输入回调"""
        print(f"输入: {repr(data)}")
        # 回显输入
        terminal.write(data)
    
    root = tk.Tk()
    root.title("终端测试")
    
    terminal = TerminalWidget(root, width=80, height=24)
    terminal.pack(fill='both', expand=True)
    terminal.set_input_callback(on_terminal_input)
    
    # 测试写入一些数据
    terminal.write("欢迎使用终端模拟器!\n")
    terminal.write("支持完整的xterm控制序列\n")
    terminal.write("请输入命令: ")
    
    root.mainloop()
