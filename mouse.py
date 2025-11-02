import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import time
import sys
import os
import tempfile

# 尝试导入 pynput 来处理全局快捷键
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告: pynput 未安装，快捷键功能将不可用")
    print("可以运行 'pip install pynput' 来安装并启用快捷键功能")

class AutoTyper:
    def __init__(self):
        self.is_typing = False
        self.stop_requested = False
        self.typing_thread = None
        self.keyboard_listener = None
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("自动输入器 - 中文增强版")
        self.root.geometry("350x400")
        
        # 创建界面组件
        self.setup_ui()
        
        # 启动键盘监听器
        if PYNPUT_AVAILABLE:
            self.setup_keyboard_listener()
        
        print("程序已启动!")
        print("- 点击'选择文件'按钮选择TXT文件并开始输入")
        print("- 完全支持中文和换行")
        print("- 按数字键1停止输入")
        print("- 按数字键2重新选择文件")
        print("- 按数字键3关闭程序")
    
    def setup_ui(self):
        """设置用户界面"""
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        # 标题
        title_label = tk.Label(frame, text="自动输入器 - 中文增强版", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        self.select_btn = tk.Button(
            frame, 
            text="选择TXT文件", 
            command=self.select_file_and_type,
            font=("Arial", 12),
            width=18,
            height=2,
            bg="#4CAF50",
            fg="white"
        )
        self.select_btn.pack(pady=10)
        
        self.stop_btn = tk.Button(
            frame,
            text="停止输入",
            command=self.stop_typing,
            font=("Arial", 12),
            width=18,
            height=2,
            state="disabled",
            bg="#f44336",
            fg="white"
        )
        self.stop_btn.pack(pady=10)
        
        self.status_label = tk.Label(
            frame,
            text="等待选择文件...",
            font=("Arial", 10),
            wraplength=300
        )
        self.status_label.pack(pady=10)
        
        # 添加输入方法选择
        method_frame = tk.Frame(frame)
        method_frame.pack(pady=10)
        
        tk.Label(method_frame, text="输入方法:", font=("Arial", 10, "bold")).pack()
        
        self.method_var = tk.StringVar(value="auto")
        methods = [
            ("自动选择（推荐）", "auto"),
            ("剪贴板方法", "clipboard"),
            ("xdotool方法", "xdotool"),
            ("逐字符输入", "char_by_char")
        ]
        
        for text, value in methods:
            tk.Radiobutton(method_frame, text=text, variable=self.method_var, 
                          value=value, font=("Arial", 9)).pack(anchor="w")
        
        # 添加键盘快捷键说明
        shortcut_frame = tk.Frame(frame)
        shortcut_frame.pack(pady=10)
        
        shortcuts = [
            "快捷键说明:",
            "1 - 停止输入",
            "2 - 重新选择文件", 
            "3 - 关闭程序",
            "",
            "支持功能:",
            "✓ 中文字符完美支持",
            "✓ 换行符正确处理",
            "✓ 多种输入方法",
            "✓ 进度显示"
        ]
        
        for shortcut in shortcuts:
            label = tk.Label(shortcut_frame, text=shortcut, font=("Arial", 9))
            label.pack(anchor="w")
    
    def setup_keyboard_listener(self):
        """设置全局键盘监听器"""
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char:
                    if key.char == '1':
                        self.stop_typing()
                    elif key.char == '2':
                        self.restart_typing()
                    elif key.char == '3':
                        self.exit_program()
            except AttributeError:
                pass
        
        if PYNPUT_AVAILABLE:
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
    
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
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # 预处理内容
            processed_content = self.preprocess_content(content)
            
            self.status_label.config(text=f"已选择: {os.path.basename(file_path)}")
            print(f"已选择文件: {file_path}")
            print(f"文件大小: {len(processed_content)} 字符")
            print(f"包含换行符: {processed_content.count(chr(10))} 个")
            print("3秒后开始输入...")
            
            # 更新按钮状态
            self.select_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # 在新线程中开始输入
            self.is_typing = True
            self.typing_thread = threading.Thread(target=self._start_typing, args=(processed_content,))
            self.typing_thread.daemon = True
            self.typing_thread.start()
            
        except Exception as e:
            error_msg = f"读取文件时出错: {e}"
            messagebox.showerror("错误", error_msg)
            self.status_label.config(text="文件读取失败")
            print(error_msg)
    
    def preprocess_content(self, content):
        """预处理内容，确保格式正确"""
        # 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # 移除文件末尾的多余空白
        content = content.rstrip()
        return content
    
    def _start_typing(self, content):
        """开始倒计时并输入"""
        # 首先检测目标窗口
        target_window = self.detect_target_window()
        
        for i in range(5, 0, -1):  # 增加到5秒给用户更多时间切换窗口
            if self.stop_requested:
                self._reset_ui()
                return
            status_text = f"{i}秒后开始输入...请切换到目标应用"
            self.root.after(0, lambda t=status_text: self.status_label.config(text=t))
            print(f"{i}秒后开始输入...请将光标放到目标文本编辑器中")
            time.sleep(1)
            
        print("开始输入!")
        self.root.after(0, lambda: self.status_label.config(text="正在输入中..."))
        
        # 确保目标窗口获得焦点
        self.ensure_target_focus()
        
        self.type_content(content)
    
    def type_content(self, content):
        """在后台线程中输入内容"""
        try:
            method = self.method_var.get()
            success = False
            
            if method == "auto":
                # 自动选择最佳方法
                success = self.smart_type_content(content)
            elif method == "clipboard":
                success = self.try_clipboard_method(content)
            elif method == "xdotool":
                success = self.try_xdotool_method(content)
            elif method == "char_by_char":
                success = self.type_char_by_char_enhanced(content)
            
            if not success and method != "auto":
                print("选择的方法失败，尝试自动选择...")
                success = self.smart_type_content(content)
                
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
    
    def smart_type_content(self, content):
        """智能选择输入方法"""
        methods = [
            ("剪贴板方法", self.try_clipboard_method),
            ("xdotool方法", self.try_xdotool_method),
            ("增强逐字符方法", self.type_char_by_char_enhanced),
            ("基础ydotool方法", self.try_basic_ydotool)
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"尝试 {method_name}...")
                if method_func(content):
                    print(f"{method_name} 成功!")
                    return True
            except Exception as e:
                print(f"{method_name} 失败: {e}")
                continue
        
        print("所有方法都失败了")
        return False
    
    def try_clipboard_method(self, content):
        """剪贴板方法 - 对中文和换行支持最好"""
        try:
            clipboard_cmd = None
            paste_cmd = None
            
            # 检查可用的剪贴板工具
            for tool, cmd in [("xclip", ["xclip", "-selection", "clipboard"]), 
                             ("wl-copy", ["wl-copy"]),
                             ("xsel", ["xsel", "--clipboard", "--input"])]:
                try:
                    subprocess.run(["which", tool], check=True, capture_output=True)
                    clipboard_cmd = cmd
                    print(f"检测到 {tool}，使用剪贴板方法...")
                    break
                except subprocess.CalledProcessError:
                    continue
            
            if not clipboard_cmd:
                print("未找到剪贴板工具")
                return False
            
            print(f"使用剪贴板输入 {len(content)} 字符，{content.count(chr(10))} 个换行符")
            
            # 备份当前剪贴板内容
            original_clipboard = self.get_clipboard_content()
            
            # 将内容复制到剪贴板
            process = subprocess.Popen(clipboard_cmd, stdin=subprocess.PIPE, text=True, encoding='utf-8')
            process.communicate(input=content)
            
            if process.returncode != 0:
                return False
                
            # 等待剪贴板设置完成
            time.sleep(0.5)
            
            # 确保目标窗口激活
            self.ensure_target_focus()
            
            # 尝试多种粘贴方法
            paste_methods = [
                # ydotool Ctrl+V
                (["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], "ydotool Ctrl+V"),
                # xdotool Ctrl+V (如果可用)
                (["xdotool", "key", "ctrl+v"], "xdotool Ctrl+V"),
                # wtype (Wayland)
                (["wtype", "-M", "ctrl", "-P", "v", "-m", "ctrl", "-p", "v"], "wtype Ctrl+V")
            ]
            
            success = False
            for paste_cmd, method_name in paste_methods:
                try:
                    # 检查工具是否可用
                    tool_name = paste_cmd[0]
                    subprocess.run(["which", tool_name], check=True, capture_output=True)
                    
                    # 执行粘贴前再次确保焦点
                    time.sleep(0.2)
                    
                    # 执行粘贴
                    result = subprocess.run(paste_cmd, check=True, capture_output=True, timeout=10)
                    print(f"剪贴板粘贴成功 (使用 {method_name})")
                    success = True
                    break
                    
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                    print(f"{method_name} 失败: {e}")
                    continue
            
            # 恢复原始剪贴板内容
            if original_clipboard and success:
                time.sleep(0.5)  # 等待粘贴完成
                try:
                    self.restore_clipboard_content(original_clipboard)
                except:
                    pass
            
            if not success:
                print("所有粘贴方法都失败了")
                
            return success
            
        except Exception as e:
            print(f"剪贴板方法失败: {e}")
            return False
    
    def get_clipboard_content(self):
        """获取当前剪贴板内容"""
        try:
            # 尝试不同的剪贴板读取工具
            for tool, cmd in [("xclip", ["xclip", "-selection", "clipboard", "-o"]),
                             ("wl-paste", ["wl-paste"]),
                             ("xsel", ["xsel", "--clipboard", "--output"])]:
                try:
                    subprocess.run(["which", tool], check=True, capture_output=True)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        return result.stdout
                except:
                    continue
        except:
            pass
        return None
    
    def restore_clipboard_content(self, content):
        """恢复剪贴板内容"""
        try:
            for tool, cmd in [("xclip", ["xclip", "-selection", "clipboard"]),
                             ("wl-copy", ["wl-copy"]),
                             ("xsel", ["xsel", "--clipboard", "--input"])]:
                try:
                    subprocess.run(["which", tool], check=True, capture_output=True)
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True, encoding='utf-8')
                    process.communicate(input=content)
                    if process.returncode == 0:
                        break
                except:
                    continue
        except:
            pass
    
    def try_xdotool_method(self, content):
        """xdotool方法"""
        try:
            subprocess.run(["which", "xdotool"], check=True, capture_output=True)
            print("使用 xdotool 直接输入...")
            
            # 确保目标窗口激活
            self.ensure_target_focus()
            
            # 分段输入以提高稳定性
            lines = content.split('\n')
            total_lines = len(lines)
            
            for i, line in enumerate(lines):
                if self.stop_requested:
                    break
                    
                # 更新进度
                progress = f"xdotool输入进度: {i+1}/{total_lines} 行"
                self.root.after(0, lambda p=progress: self.status_label.config(text=p))
                
                # 在每行输入前短暂延迟，确保应用响应
                time.sleep(0.1)
                
                if line.strip() or i == 0:  # 非空行或第一行（即使为空也要处理）
                    try:
                        # 使用 xdotool 输入文本，增加延迟以提高兼容性
                        subprocess.run(["xdotool", "type", "--delay", "80", "--clearmodifiers", line], 
                                     check=True, capture_output=True, text=True, timeout=60)
                    except subprocess.TimeoutExpired:
                        print(f"第 {i+1} 行输入超时，跳过")
                        continue
                    except subprocess.CalledProcessError as e:
                        print(f"第 {i+1} 行输入失败: {e}")
                        # 尝试逐字符输入这一行
                        self.xdotool_type_char_by_char(line)
                
                # 如果不是最后一行，添加换行
                if i < total_lines - 1:
                    try:
                        subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], 
                                     check=True, capture_output=True, timeout=5)
                    except:
                        # 如果按键失败，尝试输入换行字符
                        try:
                            subprocess.run(["xdotool", "type", "\n"], 
                                         check=True, capture_output=True, timeout=5)
                        except:
                            print(f"第 {i+1} 行换行失败")
                    
                    time.sleep(0.1)
            
            print("xdotool 输入成功")
            return True
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"xdotool 方法失败: {e}")
            return False
    
    def xdotool_type_char_by_char(self, text):
        """使用xdotool逐字符输入"""
        for char in text:
            if self.stop_requested:
                break
            try:
                subprocess.run(["xdotool", "type", "--delay", "100", char], 
                             check=True, capture_output=True, timeout=5)
            except:
                print(f"字符输入失败: {repr(char)}")
            time.sleep(0.05)
    
    def type_char_by_char_enhanced(self, content):
        """增强的逐字符输入方法"""
        try:
            print(f"使用增强逐字符方法输入 {len(content)} 字符...")
            
            for i, char in enumerate(content):
                if self.stop_requested:
                    break
                
                # 每20个字符更新进度
                if i % 20 == 0:
                    progress = f"逐字符输入: {i+1}/{len(content)}"
                    self.root.after(0, lambda p=progress: self.status_label.config(text=p))
                
                success = False
                
                if char == '\n':
                    # 换行符处理
                    for method in [
                        ["ydotool", "key", "28:1", "28:0"],
                        ["xdotool", "key", "Return"],
                        ["wtype", "-k", "Return"]
                    ]:
                        try:
                            subprocess.run(method, check=True, capture_output=True, timeout=2)
                            success = True
                            break
                        except:
                            continue
                    
                    if success:
                        time.sleep(0.15)  # 换行后稍作停顿
                else:
                    # 普通字符处理
                    # 方法1: 尝试直接输入
                    for tool_cmd in [
                        ["ydotool", "type", char],
                        ["xdotool", "type", "--delay", "80", char],
                        ["wtype", char]
                    ]:
                        try:
                            result = subprocess.run(tool_cmd, check=True, capture_output=True, timeout=3)
                            success = True
                            break
                        except:
                            continue
                    
                    # 方法2: 如果直接输入失败，尝试临时文件方法
                    if not success and ord(char) > 127:  # 中文字符
                        try:
                            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                                           suffix='.txt', delete=False) as temp_file:
                                temp_file.write(char)
                                temp_path = temp_file.name
                            
                            subprocess.run(["ydotool", "type", "--file", temp_path, "--key-delay", "100"], 
                                         check=True, capture_output=True, timeout=5)
                            os.unlink(temp_path)
                            success = True
                        except:
                            pass
                
                if not success:
                    print(f"跳过字符: {repr(char)}")
                
                time.sleep(0.08)  # 字符间延迟
            
            return True
            
        except Exception as e:
            print(f"增强逐字符方法失败: {e}")
            return False
    
    def try_basic_ydotool(self, content):
        """基础ydotool方法"""
        try:
            print("使用基础 ydotool 方法...")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            # 使用 ydotool 输入
            subprocess.run(["ydotool", "type", "--file", temp_path, "--key-delay", "100"], 
                         check=True, capture_output=True, text=True, timeout=60)
            
            os.unlink(temp_path)
            print("基础 ydotool 方法成功")
            return True
            
        except Exception as e:
            print(f"基础 ydotool 方法失败: {e}")
            return False
    
    def _reset_ui(self):
        """重置UI状态"""
        self.select_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if not self.is_typing and not self.stop_requested:
            self.status_label.config(text="等待选择文件...")
    
    def stop_typing(self):
        """停止输入"""
        if self.is_typing:
            print("正在停止输入...")
            self.stop_requested = True
            self.status_label.config(text="正在停止...")
        else:
            print("当前没有正在进行的输入")

    def restart_typing(self):
        """重新选择文件"""
        if self.is_typing:
            self.stop_typing()
            time.sleep(0.5)
        print("重新选择文件...")
        self.select_file_and_type()
    
    def exit_program(self):
        """关闭程序"""
        print("正在关闭程序...")
        self.cleanup()
        self.root.quit()

    def cleanup(self):
        """清理资源"""
        self.stop_requested = True
        self.is_typing = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("程序已退出")
    
    def run(self):
        """运行主程序"""
        print("\n=== 自动输入器 - 中文增强版 ===")
        print("使用说明:")
        print("1. 启动程序后，点击'选择TXT文件'按钮")
        print("2. 选择输入方法（推荐自动选择）")
        print("3. 在倒计时期间，切换到目标应用程序")
        print("4. 将光标放在想要输入文本的位置")
        print("5. 程序会自动在目标应用中输入内容")
        print("\n支持的应用程序:")
        print("✓ 文本编辑器: VS Code, gedit, nano, vim")
        print("✓ 办公软件: LibreOffice Writer, WPS")
        print("✓ 浏览器: Chrome, Firefox (文本框)")
        print("✓ 终端: GNOME Terminal, Konsole")
        print("✓ 其他: Telegram, QQ, 微信等")
        print("\n快捷键:")
        print("- 按数字键1: 停止输入")
        print("- 按数字键2: 重新选择文件")
        print("- 按数字键3: 关闭程序")
        print("\n中文输入增强:")
        print("- 自动检测最佳输入方法")
        print("- 完美支持中文字符")
        print("- 正确处理换行符")
        print("- 智能窗口焦点管理")
        print("- 跨应用程序支持")
        print("- 实时进度显示")
        
        # 检测可用工具
        print("\n检测可用工具:")
        tools = ["ydotool", "xdotool", "xclip", "wl-copy", "wtype"]
        available_count = 0
        for tool in tools:
            try:
                subprocess.run(["which", tool], check=True, capture_output=True)
                print(f"✓ {tool} - 可用")
                available_count += 1
            except subprocess.CalledProcessError:
                print(f"✗ {tool} - 不可用")
        
        if available_count == 0:
            print("\n⚠️  警告: 未检测到任何输入工具!")
            print("请安装以下工具之一:")
            print("- sudo apt install xdotool xclip (推荐)")
            print("- sudo apt install ydotool")
            print("- sudo apt install wtype wl-clipboard (Wayland)")
        elif available_count < 2:
            print(f"\n💡 建议: 安装更多工具以获得更好的兼容性")
            print("推荐命令: sudo apt install xdotool xclip")
        else:
            print(f"\n✅ 检测到 {available_count} 个工具，兼容性良好!")
        
        print("\n重要提示:")
        print("- 程序启动后有5秒时间切换到目标应用")
        print("- 确保目标应用窗口处于活动状态")
        print("- 对于某些应用，可能需要先点击文本输入区域")
        print("- 如果输入异常，请尝试不同的输入方法")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行出错: {e}")
        finally:
            self.cleanup()

    def detect_target_window(self):
        """检测目标窗口"""
        try:
            # 尝试使用 xdotool 获取当前活动窗口
            result = subprocess.run(["xdotool", "getactivewindow"], 
                                  capture_output=True, text=True, check=True)
            window_id = result.stdout.strip()
            print(f"检测到活动窗口ID: {window_id}")
            
            # 获取窗口信息
            result = subprocess.run(["xdotool", "getwindowname", window_id], 
                                  capture_output=True, text=True, check=True)
            window_name = result.stdout.strip()
            print(f"当前活动窗口: {window_name}")
            
            return {"id": window_id, "name": window_name}
        except:
            print("无法检测活动窗口，将使用通用方法")
            return None
    
    def ensure_target_focus(self):
        """确保目标窗口获得焦点"""
        try:
            # 方法1: 使用鼠标点击来激活窗口
            print("尝试激活目标窗口...")
            
            # 获取鼠标当前位置附近的窗口
            mouse_result = subprocess.run(["xdotool", "getmouselocation", "--shell"], 
                                        capture_output=True, text=True, check=True)
            
            # 轻微移动鼠标以确保窗口激活
            subprocess.run(["xdotool", "mousemove_relative", "1", "1"], 
                         capture_output=True, check=True)
            subprocess.run(["xdotool", "mousemove_relative", "-1", "-1"], 
                         capture_output=True, check=True)
            
            # 点击当前位置来激活窗口
            subprocess.run(["xdotool", "click", "1"], 
                         capture_output=True, check=True)
            
            time.sleep(0.2)  # 等待窗口激活
            print("窗口激活完成")
            
        except Exception as e:
            print(f"窗口激活失败: {e}")
            print("请手动确保目标应用处于活动状态")
    
def main():
    typer = AutoTyper()
    typer.run()

if __name__ == "__main__":
    main()
