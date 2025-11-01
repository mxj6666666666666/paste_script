import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import time
from pynput import mouse, keyboard
import sys
import os

class AutoTyper:
    def __init__(self):
        self.is_typing = False
        self.stop_requested = False
        self.typing_thread = None
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # 创建主窗口（隐藏）
        self.root = tk.Tk()
        self.root.title("自动输入器")
        self.root.geometry("300x250")  # 增加高度以容纳新说明
        
        # 创建界面组件
        self.setup_ui()
        
        print("程序已启动!")
        print("- 点击'选择文件'按钮选择TXT文件并开始输入")
        print("- 按数字键1停止输入")
        print("- 按数字键2重新选择文件")
        print("- 按数字键3关闭程序")
    
    def setup_ui(self):
        """设置用户界面"""
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        self.select_btn = tk.Button(
            frame, 
            text="选择TXT文件", 
            command=self.select_file_and_type,
            font=("Arial", 12),
            width=15,
            height=2
        )
        self.select_btn.pack(pady=10)
        
        self.stop_btn = tk.Button(
            frame,
            text="停止输入",
            command=self.stop_typing,
            font=("Arial", 12),
            width=15,
            height=2,
            state="disabled"
        )
        self.stop_btn.pack(pady=10)
        
        self.status_label = tk.Label(
            frame,
            text="等待选择文件...",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=10)
        
        # 添加键盘快捷键说明
        shortcut_frame = tk.Frame(frame)
        shortcut_frame.pack(pady=5)
        
        shortcuts = [
            "快捷键说明:",
            "1 - 停止输入",
            "2 - 重新选择文件", 
            "3 - 关闭程序"
        ]
        
        for shortcut in shortcuts:
            label = tk.Label(shortcut_frame, text=shortcut, font=("Arial", 9))
            label.pack(anchor="w")
    
    def select_file_and_type(self):
        """选择文件并开始输入内容"""
        if self.is_typing:
            messagebox.showwarning("警告", "已经在输入中，请等待完成或停止当前输入")
            return
            
        file_path = filedialog.askopenfilename(
            title="选择TXT文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            self.status_label.config(text="未选择文件")
            return
            
        if not file_path.lower().endswith('.txt'):
            messagebox.showerror("错误", "请选择TXT文件！")
            self.status_label.config(text="错误：请选择TXT文件")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            self.status_label.config(text=f"已选择文件: {file_path.split('/')[-1]}")
            print(f"已选择文件: {file_path}")
            print(f"文件大小: {len(content)} 字符")
            print("3秒后开始输入...")
            
            # 更新按钮状态
            self.select_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # 在新线程中开始输入
            self.is_typing = True
            self.typing_thread = threading.Thread(target=self._start_typing, args=(content,))
            self.typing_thread.daemon = True
            self.typing_thread.start()
            
        except Exception as e:
            error_msg = f"读取文件时出错: {e}"
            messagebox.showerror("错误", error_msg)
            self.status_label.config(text="文件读取失败")
            print(error_msg)
    
    def _start_typing(self, content):
        """开始倒计时并输入"""
        for i in range(3, 0, -1):
            if self.stop_requested:
                self._reset_ui()
                return
            status_text = f"{i}秒后开始输入..."
            self.root.after(0, lambda: self.status_label.config(text=status_text))
            print(f"{i}...")
            time.sleep(1)
            
        print("开始输入!")
        self.root.after(0, lambda: self.status_label.config(text="正在输入中..."))
        self.type_content(content)
    
    def type_content(self, content):
        """在后台线程中输入内容"""
        try:
            for char in content:
                if self.stop_requested:
                    break
                # 使用 xdotool 输入字符，支持中文
                self.type_char_with_xdotool(char)
                time.sleep(0.01)  # 每个字符间隔0.01秒
        except Exception as e:
            error_msg = f"输入过程中出错: {e}"
            print(error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            self.is_typing = False
            self.root.after(0, self._reset_ui)
            
            if self.stop_requested:
                print("输入已停止")
                self.stop_requested = False
            else:
                print("输入完成!")
                self.root.after(0, lambda: self.status_label.config(text="输入完成!"))
    
    def type_char_with_xdotool(self, char):
        """使用 xdotool 输入单个字符"""
        try:
            if char == '\n':
                # 对于换行符，使用 key 命令模拟回车键
                subprocess.run(['xdotool', 'key', 'Return'], 
                             check=True, capture_output=True, text=True)
            else:
                # 转义特殊字符
                escaped_char = char.replace('"', '\\"').replace("'", "\\'")
                # 使用 xdotool type 命令输入字符
                subprocess.run(['xdotool', 'type', '--delay', '100', escaped_char], 
                             check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"xdotool 输入失败: {e}")
            raise
    
    def _reset_ui(self):
        """重置UI状态"""
        self.select_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if not self.is_typing and not self.stop_requested:
            self.status_label.config(text="等待选择文件...")
    
    def stop_typing(self):
        """停止所有输入行为"""
        if self.is_typing:
            print("正在停止输入...")
            self.stop_requested = True
            self.status_label.config(text="正在停止...")
            if self.typing_thread and self.typing_thread.is_alive():
                self.typing_thread.join(timeout=1)
            self.is_typing = False
            self._reset_ui()
        else:
            print("当前没有正在进行的输入")
    
    def restart_typing(self):
        """重新选择文件并开始输入"""
        if self.is_typing:
            self.stop_typing()
            # 等待停止完成
            time.sleep(0.5)
        print("重新选择文件...")
        self.select_file_and_type()
    
    def exit_program(self):
        """关闭整个程序"""
        print("正在关闭程序...")
        self.cleanup()
        self.root.quit()
        sys.exit(0)
    
    def on_key_press(self, key):
        """键盘按键事件处理"""
        try:
            if hasattr(key, 'char'):
                if key.char == '1':
                    self.stop_typing()
                elif key.char == '2':
                    self.restart_typing()
                elif key.char == '3':
                    self.exit_program()
        except AttributeError:
            pass
    
    def start_listeners(self):
        """启动键盘监听"""
        # 启动键盘监听
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.daemon = True
        self.keyboard_listener.start()
        
        print("键盘监听器已启动")
    
    def cleanup(self):
        """清理资源"""
        self.stop_typing()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("程序已退出")
    
    def run(self):
        """运行主程序"""
        self.start_listeners()
        
        print("\n使用说明:")
        print("1. 将光标放在你想要输入文本的位置")
        print("2. 点击'选择TXT文件'按钮")
        print("3. 程序会在3秒后开始自动输入文件内容")
        print("4. 按数字键1可以随时停止输入")
        print("5. 按数字键2可以重新选择文件")
        print("6. 按数字键3可以关闭程序")
        print("7. 也可以点击'停止输入'按钮停止")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行出错: {e}")
        finally:
            self.cleanup()

def main():
    try:
        from pynput import keyboard
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请运行: pip install pynput")
        return
    
    typer = AutoTyper()
    typer.run()

if __name__ == "__main__":
    main()
