# input_method_manager.py

import platform
import subprocess
import ctypes
from ctypes import wintypes
import os
import json
import tempfile
import multiprocessing
import atexit

def _ime_watchdog_process(parent_pid, state_file_path, system_type):
    """
    守护进程：监视父进程，当父进程退出（包括崩溃）时恢复输入法。
    此函数在独立进程中运行。
    """
    import time
    import psutil
    
    try:
        # 等待父进程退出
        parent = psutil.Process(parent_pid)
        parent.wait()  # 阻塞直到父进程退出
    except psutil.NoSuchProcess:
        # 父进程已经不存在
        pass
    except Exception as e:
        print(f"[守护进程] 监视父进程时出错: {e}")
    
    # 父进程已退出，检查是否需要恢复输入法
    try:
        if os.path.exists(state_file_path):
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            layout = state.get('layout')
            if layout is not None and layout != "Unknown":
                print(f"[守护进程] 检测到程序异常退出，正在恢复输入法...")
                
                # 根据系统类型恢复输入法
                if system_type == "Windows":
                    try:
                        user32 = ctypes.windll.user32
                        KLF_ACTIVATE = 0x00000001
                        hkl_to_restore = int(layout)
                        user32.ActivateKeyboardLayout(hkl_to_restore, KLF_ACTIVATE)
                        print(f"[守护进程] 已恢复 Windows 输入法布局: {layout}")
                    except Exception as e:
                        print(f"[守护进程] 恢复 Windows 输入法失败: {e}")
                
                elif system_type == "Darwin":  # macOS
                    try:
                        script = f'''
                        tell application "System Events"
                            tell process "SystemUIServer"
                                tell (first menu bar item whose description is "text input") of menu bar 1
                                    click
                                    click menu item "{layout}" of menu 1
                                end tell
                            end tell
                        end tell
                        '''
                        subprocess.run(["osascript", "-e", script], timeout=10)
                        print(f"[守护进程] 已恢复 macOS 输入法: {layout}")
                    except Exception as e:
                        print(f"[守护进程] 恢复 macOS 输入法失败: {e}")
                
                elif system_type == "Linux":
                    try:
                        if layout == '1':
                            subprocess.run(["fcitx-remote", "-o"], timeout=2)
                        elif layout == '2':
                            subprocess.run(["fcitx-remote", "-c"], timeout=2)
                        else:
                            subprocess.run(["ibus", "engine", layout], timeout=2)
                        print(f"[守护进程] 已恢复 Linux 输入法: {layout}")
                    except Exception as e:
                        print(f"[守护进程] 恢复 Linux 输入法失败: {e}")
            
            # 删除状态文件
            os.remove(state_file_path)
            print("[守护进程] 已清理状态文件")
    except Exception as e:
        print(f"[守护进程] 恢复输入法时出错: {e}")


class InputMethodManager:
    """
    一个跨平台的输入法管理器，用于切换到英文输入法和恢复原始输入法状态。
    """

    def __init__(self):
        """
        初始化 InputMethodManager 实例。
        """
        self._original_state = {}
        self._system = platform.system()
        self._watchdog_process = None
        self._state_file_path = os.path.join(tempfile.gettempdir(), 'scrawl_ime_state.json')
        self._initialize_platform_specifics()
        
        # 注册 atexit 处理器，用于正常退出时清理
        atexit.register(self._cleanup_on_exit)

    def _initialize_platform_specifics(self):
        """根据操作系统初始化特定的 API 或设置。"""
        if self._system == "Windows":
            try:
                self._user32 = ctypes.windll.user32
                self._kernel32 = ctypes.windll.kernel32
                self._imm32 = ctypes.windll.imm32 # 加载 imm32.dll

                # 定义 Windows API 函数和参数
                self._GetKeyboardLayout = self._user32.GetKeyboardLayout
                self._GetKeyboardLayout.argtypes = [wintypes.DWORD]
                self._GetKeyboardLayout.restype = wintypes.HKL

                self._LoadKeyboardLayout = self._user32.LoadKeyboardLayoutW # 使用 Unicode 版本
                self._LoadKeyboardLayout.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
                self._LoadKeyboardLayout.restype = wintypes.HKL

                self._ActivateKeyboardLayout = self._user32.ActivateKeyboardLayout
                self._ActivateKeyboardLayout.argtypes = [wintypes.HKL, wintypes.UINT]
                self._ActivateKeyboardLayout.restype = wintypes.HKL

                self._GetCurrentThreadId = self._kernel32.GetCurrentThreadId
                self._GetCurrentThreadId.argtypes = []
                self._GetCurrentThreadId.restype = wintypes.DWORD
                
                # Imm32 API
                self._ImmGetContext = self._imm32.ImmGetContext
                self._ImmGetContext.argtypes = [wintypes.HWND]
                self._ImmGetContext.restype = wintypes.HANDLE
                
                self._ImmSetOpenStatus = self._imm32.ImmSetOpenStatus
                self._ImmSetOpenStatus.argtypes = [wintypes.HANDLE, wintypes.BOOL]
                self._ImmSetOpenStatus.restype = wintypes.BOOL
                
                self._ImmReleaseContext = self._imm32.ImmReleaseContext
                self._ImmReleaseContext.argtypes = [wintypes.HWND, wintypes.HANDLE]
                self._ImmReleaseContext.restype = wintypes.BOOL

                self._GetForegroundWindow = self._user32.GetForegroundWindow
                self._GetForegroundWindow.restype = wintypes.HWND

                self._KLF_ACTIVATE = 0x00000001
                self._ENGLISH_LAYOUT_ID = "00000409" # US English
                self._english_hkl_cache = None # 缓存 HKL

            except Exception as e:
                print(f"[错误] Windows API 初始化失败: {e}")
                self._user32 = None # 标记为不可用

        elif self._system == "Darwin": # macOS
            # macOS: 尝试使用 Carbon 框架的 TISSelectInputSource
            try:
                self._carbon = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Carbon.framework/Carbon')
                
                # 定义必要的类型和常量
                self._kTISPropertyInputSourceID = ctypes.c_void_p.in_dll(self._carbon, 'kTISPropertyInputSourceID')
                self._kTISPropertyInputSourceType = ctypes.c_void_p.in_dll(self._carbon, 'kTISPropertyInputSourceType')
                self._kTISTypeKeyboardLayout = ctypes.c_void_p.in_dll(self._carbon, 'kTISTypeKeyboardLayout')
                self._kTISPropertyInputSourceIsSelectCapable = ctypes.c_void_p.in_dll(self._carbon, 'kTISPropertyInputSourceIsSelectCapable')
                
                # CFString 相关函数
                self._CFStringCreateWithCString = self._carbon.CFStringCreateWithCString
                self._CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
                self._CFStringCreateWithCString.restype = ctypes.c_void_p
                
                self._CFStringGetLength = self._carbon.CFStringGetLength
                self._CFStringGetLength.argtypes = [ctypes.c_void_p]
                self._CFStringGetLength.restype = ctypes.c_long
                
                self._CFStringGetCString = self._carbon.CFStringGetCString
                self._CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
                self._CFStringGetCString.restype = ctypes.c_bool
                
                self._CFRelease = self._carbon.CFRelease
                self._CFRelease.argtypes = [ctypes.c_void_p]
                
                # TIS 相关函数
                self._TISCopyCurrentKeyboardInputSource = self._carbon.TISCopyCurrentKeyboardInputSource
                self._TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
                
                self._TISSelectInputSource = self._carbon.TISSelectInputSource
                self._TISSelectInputSource.argtypes = [ctypes.c_void_p]
                self._TISSelectInputSource.restype = ctypes.c_int
                
                self._TISCreateInputSourceList = self._carbon.TISCreateInputSourceList
                self._TISCreateInputSourceList.argtypes = [ctypes.c_void_p, ctypes.c_bool]
                self._TISCreateInputSourceList.restype = ctypes.c_void_p
                
                self._TISGetInputSourceProperty = self._carbon.TISGetInputSourceProperty
                self._TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                self._TISGetInputSourceProperty.restype = ctypes.c_void_p
                
                # CFArray 相关
                self._CFArrayGetCount = self._carbon.CFArrayGetCount
                self._CFArrayGetCount.argtypes = [ctypes.c_void_p]
                self._CFArrayGetCount.restype = ctypes.c_long
                
                self._CFArrayGetValueAtIndex = self._carbon.CFArrayGetValueAtIndex
                self._CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
                self._CFArrayGetValueAtIndex.restype = ctypes.c_void_p
                
                self._kCFStringEncodingUTF8 = 0x08000100
                self._use_carbon = True
                
            except Exception as e:
                print(f"[警告] macOS Carbon 框架加载失败，将回退到 AppleScript: {e}")
                self._use_carbon = False
        elif self._system == "Linux":
            # 尝试检测 fcitx 或 ibus
            self._linux_ime_backend = None
            if self._check_command("fcitx-remote"):
                self._linux_ime_backend = "fcitx"
            elif self._check_command("ibus"):
                self._linux_ime_backend = "ibus"
            else:
                print("[信息] Linux 下未检测到 fcitx 或 ibus，输入法切换功能将禁用。")
        else:
            print(f"[警告] 不支持的操作系统: {self._system}")

    def _check_command(self, cmd):
        """检查命令是否存在"""
        from shutil import which
        return which(cmd) is not None

    def _start_watchdog(self):
        """启动守护进程监视主进程"""
        import sys
        try:
            # 如果已有守护进程在运行，先停止它
            self._stop_watchdog()
            
            # 使用 subprocess 启动独立的 Python 进程
            # 这样可以避免 Windows 上 multiprocessing 的 bootstrapping 问题
            watchdog_code = f'''
import os
import sys
import json
import ctypes
import subprocess

try:
    import psutil
    parent = psutil.Process({os.getpid()})
    parent.wait()
except:
    pass

state_file = r"{self._state_file_path}"
system_type = "{self._system}"

try:
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        layout = state.get('layout')
        if layout is not None and layout != "Unknown":
            if system_type == "Windows":
                user32 = ctypes.windll.user32
                user32.ActivateKeyboardLayout(int(layout), 0x00000001)
            elif system_type == "Linux":
                if layout == '1':
                    subprocess.run(["fcitx-remote", "-o"], timeout=2)
                elif layout == '2':
                    subprocess.run(["fcitx-remote", "-c"], timeout=2)
                else:
                    subprocess.run(["ibus", "engine", layout], timeout=2)
        
        os.remove(state_file)
except:
    pass
'''
            
            # 启动子进程
            self._watchdog_process = subprocess.Popen(
                [sys.executable, '-c', watchdog_code],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"[信息] 已启动输入法守护进程 (PID: {self._watchdog_process.pid})")
        except Exception as e:
            print(f"[警告] 启动守护进程失败: {e}")
    
    def _stop_watchdog(self):
        """停止守护进程"""
        if self._watchdog_process is not None:
            try:
                # 检查进程是否还在运行
                if self._watchdog_process.poll() is None:
                    self._watchdog_process.terminate()
                    try:
                        self._watchdog_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self._watchdog_process.kill()
                    print("[信息] 已停止输入法守护进程")
            except Exception as e:
                print(f"[警告] 停止守护进程时出错: {e}")
        self._watchdog_process = None
    
    def _cleanup_on_exit(self):
        """正常退出时的清理工作"""
        # 停止守护进程
        self._stop_watchdog()
        
        # 删除状态文件（如果存在）
        try:
            if os.path.exists(self._state_file_path):
                os.remove(self._state_file_path)
        except Exception as e:
            print(f"[警告] 清理状态文件失败: {e}")
    
    def _save_state_to_file(self):
        """将输入法状态保存到文件"""
        try:
            state_to_save = {
                'layout': self._original_state.get('layout'),
                'system': self._system
            }
            with open(self._state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f)
            return True
        except Exception as e:
            print(f"[警告] 保存状态文件失败: {e}")
            return False
    
    def _delete_state_file(self):
        """删除状态文件"""
        try:
            if os.path.exists(self._state_file_path):
                os.remove(self._state_file_path)
        except Exception:
            pass

    def _get_windows_layout(self):
        """获取当前 Windows 键盘布局 HKL"""
        if not self._user32:
            print("[错误] Windows API 未正确初始化。")
            return None
        try:
            thread_id = self._GetCurrentThreadId()
            hkl = self._GetKeyboardLayout(thread_id)
            return hkl
        except Exception as e:
            print(f"[错误] 获取 Windows 布局失败: {e}")
            return None

    def _get_macos_layout(self):
        """获取当前 macOS 活动输入源 ID"""
        if self._use_carbon:
            try:
                current_source = self._TISCopyCurrentKeyboardInputSource()
                if not current_source:
                    return "Unknown"
                
                source_id_ptr = self._TISGetInputSourceProperty(current_source, self._kTISPropertyInputSourceID)
                if not source_id_ptr:
                    self._CFRelease(current_source)
                    return "Unknown"
                
                # CFString to Python str
                length = self._CFStringGetLength(source_id_ptr)
                buffer_size = length * 4 + 1
                buffer = ctypes.create_string_buffer(buffer_size)
                if self._CFStringGetCString(source_id_ptr, buffer, buffer_size, self._kCFStringEncodingUTF8):
                    result = buffer.value.decode('utf-8')
                else:
                    result = "Unknown"
                
                self._CFRelease(current_source)
                return result
            except Exception as e:
                print(f"[错误] Carbon 获取布局失败: {e}")
                return "Unknown"
        else:
            # 回退到 AppleScript
            try:
                # AppleScript 获取当前活动输入源
                script_get = '''
                tell application "System Events"
                    tell process "SystemUIServer"
                        tell (first menu bar item whose description is "text input") of menu bar 1
                            return name of first menu item of menu 1 whose (value of attribute "AXMenuItemMarkChar" is "✓")
                        end tell
                    end tell
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script_get],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10 # 添加超时
                )
                layout_name = result.stdout.strip()
                if layout_name:
                    return layout_name
                else:
                    print("[警告] 无法通过 AppleScript 获取 macOS 活动输入源。")
                    return "Unknown"
            except subprocess.TimeoutExpired:
                print("[错误] 获取 macOS 输入源超时。")
                return "Unknown"
            except subprocess.CalledProcessError as e:
                print(f"[错误] AppleScript 执行失败: {e.stderr}")
                return "Unknown"
            except FileNotFoundError:
                print("[错误] osascript 命令未找到。")
                return "Unknown"
            except Exception as e:
                print(f"[错误] 获取 macOS 布局时发生未知错误: {e}")
                return "Unknown"

    def _get_linux_layout(self):
        """获取当前 Linux 输入法状态"""
        if self._linux_ime_backend == "fcitx":
            try:
                # 1: 激活, 2: 非激活 (通常 2 是英文)
                result = subprocess.run(
                    ["fcitx-remote"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=2
                )
                return result.stdout.strip()
            except Exception:
                return "Unknown"
        elif self._linux_ime_backend == "ibus":
            try:
                # 获取当前引擎名称
                result = subprocess.run(
                    ["ibus", "engine"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=2
                )
                return result.stdout.strip()
            except Exception:
                return "Unknown"
        else:
            return "Unknown"

    def has_saved_state(self):
        """检查是否有已保存的输入法状态"""
        return bool(self._original_state)

    def save_current_state(self):
        """
        保存当前输入法状态。
        :return: True if successful, False otherwise.
        """
        self._original_state = {} # 重置之前的状态
        try:
            if self._system == "Windows":
                layout = self._get_windows_layout()
                if layout is not None:
                    self._original_state['layout'] = layout
                    print(f"[信息] 已保存 Windows 输入法布局: {layout}")
                else:
                    return False

            elif self._system == "Darwin": # macOS
                layout = self._get_macos_layout()
                if layout != "Unknown":
                   self._original_state['layout'] = layout
                   print(f"[信息] 已保存 macOS 输入法布局: {layout}")
                else:
                    # 即使是 Unknown 也保存，以便后续处理
                    self._original_state['layout'] = layout
                    print(f"[信息] 已保存 macOS 输入法布局 (可能未知): {layout}")

            elif self._system == "Linux":
                layout = self._get_linux_layout()
                self._original_state['layout'] = layout

            else:
                print(f"[警告] 不支持的操作系统 '{self._system}'，无法保存输入法状态。")
                return False
            
            # 保存状态到文件并启动守护进程
            if self._original_state.get('layout'):
                self._save_state_to_file()
                self._start_watchdog()
            
            return True

        except Exception as e:
            print(f"[错误] 保存输入法状态时发生未知错误: {e}")
            self._original_state = {} # 重置状态以防万一
            return False


    def switch_to_english(self):
        """
        跨平台切换输入法到英文状态。
        :return: True if successful, False otherwise.
        """
        try:
            if self._system == "Windows":
                if not self._user32:
                    print("[错误] Windows API 未正确初始化，无法切换。")
                    return False

                # 1. 检查当前布局，避免重复切换
                current_hkl = self._get_windows_layout()
                # 0x0409 (US) 的低 16 位是语言 ID
                if current_hkl and (current_hkl & 0xFFFF) == 0x0409:
                     # 已经是英文布局，无需再次 Load/Activate
                     # print("[信息] 当前已经是英文布局，跳过切换。")
                     pass
                else:
                    # 获取或加载英文 HKL
                    if not self._english_hkl_cache:
                        self._english_hkl_cache = self._LoadKeyboardLayout(self._ENGLISH_LAYOUT_ID, self._KLF_ACTIVATE)
                    
                    if not self._english_hkl_cache:
                        print("[错误] 无法加载英文键盘布局。")
                        return False

                    result = self._ActivateKeyboardLayout(self._english_hkl_cache, self._KLF_ACTIVATE)
                    if not result:
                        print("[错误] 无法激活英文键盘布局。")
                        return False
                    print("[信息] 已切换到 Windows 英文输入法。")
                
                # 2. 双重保险：尝试使用 ImmSetOpenStatus 关闭 IME 窗口
                try:
                    hwnd = self._GetForegroundWindow()
                    if hwnd:
                        himc = self._ImmGetContext(hwnd)
                        if himc:
                            self._ImmSetOpenStatus(himc, False)
                            self._ImmReleaseContext(hwnd, himc)
                except Exception as imm_e:
                    print(f"[警告] 设置 ImmOpenStatus 失败 (非致命): {imm_e}")

                return True


            elif self._system == "Darwin":  # macOS
                if self._use_carbon:
                    try:
                        current_layout = self._get_macos_layout()
                        if "com.apple.keylayout.US" in current_layout or "ABC" in current_layout:
                             # 已经是英文，无需切换
                             return True

                        # 创建属性字典 (这里简化为直接搜索所有可选的键盘布局)
                        # 我们需要找到一个英文输入源，通常是 'com.apple.keylayout.US' 或 'com.apple.keylayout.ABC'
                        
                        # 创建 input source list
                        source_list = self._TISCreateInputSourceList(None, False)
                        if not source_list:
                            return False
                        
                        count = self._CFArrayGetCount(source_list)
                        target_source = None
                        
                        for i in range(count):
                            source = self._CFArrayGetValueAtIndex(source_list, i)
                            
                            # 检查类型是否为键盘布局
                            source_type = self._TISGetInputSourceProperty(source, self._kTISPropertyInputSourceType)
                            if source_type != self._kTISTypeKeyboardLayout:
                                continue
                            
                            # 检查是否可选
                            is_capable = self._TISGetInputSourceProperty(source, self._kTISPropertyInputSourceIsSelectCapable)
                            # is_capable 是 CFBooleanRef，但在 ctypes 中是指针。这里简化判断，如果指针不为空且值大概为真 (kCFBooleanTrue)
                            # 更严谨的做法是加载 kCFBooleanTrue 并比较。这里假设能列出的基本都能选。

                            # 获取 ID
                            source_id_ptr = self._TISGetInputSourceProperty(source, self._kTISPropertyInputSourceID)
                            if not source_id_ptr: continue
                            
                            length = self._CFStringGetLength(source_id_ptr)
                            buffer_size = length * 4 + 1
                            buffer = ctypes.create_string_buffer(buffer_size)
                            if self._CFStringGetCString(source_id_ptr, buffer, buffer_size, self._kCFStringEncodingUTF8):
                                source_id = buffer.value.decode('utf-8')
                                if source_id == "com.apple.keylayout.US" or source_id == "com.apple.keylayout.ABC":
                                    target_source = source
                                    break
                        
                        if target_source:
                            result = self._TISSelectInputSource(target_source)
                            self._CFRelease(source_list)
                            if result == 0:
                                print("[信息] Carbon: 已切换到 macOS 英文输入源。")
                                return True
                            else:
                                print(f"[错误] Carbon: 切换失败，错误码: {result}")
                                return False
                        else:
                            self._CFRelease(source_list)
                            print("[警告] Carbon: 未找到英文输入源 (US/ABC)。")
                            # 没找到，尝试回退到 AppleScript
                    except Exception as e:
                        print(f"[错误] Carbon 切换失败: {e}")
                        # 回退到 AppleScript
                
                # AppleScript Fallback
                # 确保 'U.S.' 在输入源列表中
                script = '''
                tell application "System Events"
                    tell process "SystemUIServer"
                        tell (first menu bar item whose description is "text input") of menu bar 1
                            click
                            click menu item "U.S." of menu 1
                        end tell
                    end tell
                end tell
                '''
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True,
                    capture_output=True,
                    timeout=10 # 添加超时
                )
                print("[信息] 已切换到 macOS U.S. 输入源。")
                return True


            elif self._system == "Linux":
                if self._linux_ime_backend == "fcitx":
                    # 切换到关闭状态 (通常是英文)
                    subprocess.run(["fcitx-remote", "-c"], check=True, timeout=2)
                    return True
                elif self._linux_ime_backend == "ibus":
                    # 切换到英文 (这里假设 xkb:us::eng 是英文，这可能需要更通用的方法，但 ibus 比较复杂)
                    subprocess.run(["ibus", "engine", "xkb:us::eng"], check=True, timeout=2)
                    return True
                else:
                    return False


            else:
                print(f"[警告] 不支持的操作系统 '{self._system}'。")
                return False

        except subprocess.TimeoutExpired:
             print("[错误] 切换输入法命令超时。")
             return False
        except subprocess.CalledProcessError as e:
            print(f"[错误] 切换输入法失败，命令执行出错: {e.stderr}")
            return False
        except OSError as e:
            print(f"[错误] 切换输入法失败。{e}")
            return False
        except Exception as e:
            print(f"[错误] 切换输入法时发生未知错误: {e}")
            return False

    def restore_original_state(self, clear_history=True):
        """
        跨平台恢复到之前保存的输入法状态。
        :param clear_history: 是否在恢复后清空保存的状态，默认为 True。
        :return: True if successful, False otherwise.
        """
        if not self._original_state:
            print("[警告] 没有找到已保存的输入法状态，无法恢复。")
            return False

        layout = self._original_state.get('layout')

        if layout is None or layout == "Unknown":
             print(f"[警告] 保存的状态中没有有效的布局信息 ('{layout}')，无法恢复。")
             return False

        success = False
        try:
            if self._system == "Windows":
                if isinstance(layout, int) or (isinstance(layout, str) and layout.isdigit()):
                    hkl_to_restore = int(layout)
                    if not self._user32:
                         print("[错误] Windows API 未正确初始化，无法恢复。")
                         return False
                    result = self._ActivateKeyboardLayout(hkl_to_restore, self._KLF_ACTIVATE)
                    if not result:
                        print("[错误] 无法激活保存的 Windows 键盘布局。")
                        success = False # 标记失败，但继续执行清理
                    else:
                        print(f"[信息] 已恢复到 Windows 输入法布局: {layout}")
                        success = True
                else:
                     print(f"[警告] Windows 状态格式不正确: {layout}")
                     success = False


            elif self._system == "Darwin": # macOS
                if self._use_carbon:
                     if isinstance(layout, str) and layout != "Unknown":
                         # 尝试查找并切换回 ID
                         try:
                             source_list = self._TISCreateInputSourceList(None, False)
                             if source_list:
                                 count = self._CFArrayGetCount(source_list)
                                 target_source = None
                                 for i in range(count):
                                     source = self._CFArrayGetValueAtIndex(source_list, i)
                                     source_id_ptr = self._TISGetInputSourceProperty(source, self._kTISPropertyInputSourceID)
                                     if not source_id_ptr: continue
                                     
                                     length = self._CFStringGetLength(source_id_ptr)
                                     buffer_size = length * 4 + 1
                                     buffer = ctypes.create_string_buffer(buffer_size)
                                     if self._CFStringGetCString(source_id_ptr, buffer, buffer_size, self._kCFStringEncodingUTF8):
                                         source_id = buffer.value.decode('utf-8')
                                         if source_id == layout:
                                             target_source = source
                                             break
                                 
                                 if target_source:
                                     self._TISSelectInputSource(target_source)
                                     success = True
                                     print(f"[信息] Carbon: 已恢复到 macOS 输入源: {layout}")
                                 
                                 self._CFRelease(source_list)
                         except Exception as e:
                             print(f"[错误] Carbon 恢复失败: {e}")
                             success = False
                     
                     if success:
                         return True
                     # 如果 Carbon 失败，尝试 AppleScript
                
                if isinstance(layout, str) and layout != "Unknown":
                    # 使用 AppleScript 切换回保存的输入源名称
                    script = f'''
                    tell application "System Events"
                        tell process "SystemUIServer"
                            tell (first menu bar item whose description is "text input") of menu bar 1
                                click
                                set menuItems to name of every menu item of menu 1
                                if "{layout}" is in menuItems then
                                    click menu item "{layout}" of menu 1
                                else
                                    log ("输入源 '{layout}' 未在菜单中找到")
                                end if
                            end tell
                        end tell
                    end tell
                    '''
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=10 # 添加超时
                    )
                    if result.returncode != 0:
                         print(f"[警告] 恢复 macOS 输入源失败: {result.stderr.strip()}")
                         # 不将此标记为完全失败，因为可能已经尝试了操作
                         success = True # 认为尝试了恢复
                    else:
                         print(f"[信息] 已尝试恢复到 macOS 输入源: {layout}")
                         success = True
                else:
                     print(f"[警告] macOS 状态无效或未知: {layout}")
                     success = False


            elif self._system == "Linux":
                if isinstance(layout, str) and layout != "Unknown":
                    if self._linux_ime_backend == "fcitx":
                        # fcitx-remote -o 打开输入法，-c 关闭。
                        # 保存的状态如果是 '2' (关闭)，则恢复关闭；如果是 '1' (打开)，则恢复打开
                        if layout == '1':
                             subprocess.run(["fcitx-remote", "-o"], check=True, timeout=2)
                        elif layout == '2':
                             subprocess.run(["fcitx-remote", "-c"], check=True, timeout=2)
                        success = True
                    elif self._linux_ime_backend == "ibus":
                        subprocess.run(["ibus", "engine", layout], check=True, timeout=2)
                        success = True
                else:
                     success = False


            else:
                print(f"[警告] 不支持的操作系统 '{self._system}'，无法恢复输入法状态。")
                success = False

        except subprocess.TimeoutExpired:
             print("[错误] 恢复输入法命令超时。")
             success = False
        except subprocess.CalledProcessError as e:
           print(f"[错误] 恢复输入法失败，命令执行出错: {e.stderr}")
           success = False
        except OSError as e:
            print(f"[错误] 恢复输入法失败。{e}")
            success = False
        except Exception as e:
            print(f"[错误] 恢复输入法时发生未知错误: {e}")
            success = False
        finally:
            # 无论恢复成功与否，都清空状态（如果 clear_history 为 True）
            if clear_history:
                self._original_state = {}
                # 停止守护进程并删除状态文件
                self._stop_watchdog()
                self._delete_state_file()

        return success

# --- 使用示例 (需要在导入此模块的其他 Python 文件中) ---
# import input_method_manager
#
# # 创建管理器实例
# imm = input_method_manager.InputMethodManager()
#
# # 保存当前状态
# print("--- 保存当前输入法状态 ---")
# imm.save_current_state()
#
# # 切换到英文
# print("\n--- 切换到英文输入法 ---")
# success_switch = imm.switch_to_english()
# print(f"切换结果: {'成功' if success_switch else '失败'}")
# input("按 Enter 键恢复原始输入法状态...")
#
# # 恢复原始状态
# print("\n--- 恢复原始输入法状态 ---")
# success_restore = imm.restore_original_state()
# print(f"恢复结果: {'成功' if success_restore else '失败'}")


"""
Pygame Window Utilities

一个用于管理 Pygame 窗口属性（如置顶、获取焦点）的跨平台扩展库。
支持 Windows, macOS (需 pyobjc), Linux (需 wmctrl)。
此版本使用 print 输出信息，而非 logging 模块。
"""

import sys
import platform
import subprocess

# --- 平台特定导入和初始化 ---
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("警告: Pygame 未安装。部分功能需要 Pygame。")

# Windows
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        # Windows API 常量
        _HWND_TOPMOST = -1
        _SWP_NOMOVE = 0x0002
        _SWP_NOSIZE = 0x0001
        _SWP_SHOWWINDOW = 0x0040
        _GWL_EXSTYLE = -20
        _WS_EX_TOPMOST = 0x00000008
        _SW_RESTORE = 9

        # 定义函数原型
        _SetWindowPos = ctypes.windll.user32.SetWindowPos
        _SetWindowPos.argtypes = [
            wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.UINT
        ]
        _SetWindowPos.restype = wintypes.BOOL

        _SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
        _SetForegroundWindow.argtypes = [wintypes.HWND]
        _SetForegroundWindow.restype = wintypes.BOOL

        _ShowWindow = ctypes.windll.user32.ShowWindow
        _ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        _ShowWindow.restype = wintypes.BOOL

        WIN_API_AVAILABLE = True
    except (ImportError, AttributeError, OSError) as e:
        WIN_API_AVAILABLE = False
        print(f"错误: 无法初始化 Windows API: {e}")

# macOS
elif sys.platform == "darwin":
    try:
        from AppKit import NSApp
        NS_APP_AVAILABLE = True
    except ImportError:
        NS_APP_AVAILABLE = False
        print("警告: AppKit (pyobjc) 未安装。macOS 置顶/焦点功能受限。请运行 'pip install pyobjc-framework-Cocoa'。")

# Linux (假设使用 X11/Wayland)
elif sys.platform.startswith("linux"):
    # Linux 功能依赖外部命令 wmctrl
    pass

else:
    print(f"警告: 不支持的平台: {sys.platform}")


def _get_hwnd():
    """安全地获取 Pygame 窗口的 HWND (Windows)"""
    if not PYGAME_AVAILABLE:
        print("错误: Pygame 未安装，无法获取窗口句柄。")
        return None
    try:
        wm_info = pygame.display.get_wm_info()
        hwnd = wm_info.get('window')
        if hwnd:
            return hwnd
        else:
            print("警告: 无法从 pygame.display.get_wm_info() 获取窗口句柄。")
            return None
    except Exception as e:
        print(f"错误: 获取窗口句柄时出错: {e}")
        return None

def set_always_on_top():
    """
    尝试将当前 Pygame 窗口设置为置顶。
    成功时返回 True，否则返回 False。
    """
    system = platform.system()
    if system == "Windows":
        if not WIN_API_AVAILABLE:
            print("错误: Windows API 不可用，无法设置窗口置顶。")
            return False
        hwnd = _get_hwnd()
        if hwnd:
            try:
                # 确保窗口恢复（如果最小化）
                _ShowWindow(hwnd, _SW_RESTORE)
                result = _SetWindowPos(
                    hwnd, _HWND_TOPMOST, 0, 0, 0, 0,
                    _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW
                )
                if result:
                    print("Windows: 窗口已置顶。")
                    return True
                else:
                    print("错误: Windows API 调用 SetWindowPos 失败。")
                    return False
            except Exception as e:
                print(f"错误: Windows: 设置窗口置顶时发生异常: {e}")
                return False
        else:
            return False

    elif system == "Darwin": # macOS
        if not NS_APP_AVAILABLE:
             print("警告: AppKit 不可用，跳过 macOS 置顶。")
             return False
        try:
            # 激活应用通常会使窗口前置并可能置顶
            NSApp().activateIgnoringOtherApps_(True)
            print("macOS: 已尝试激活应用以置顶窗口。")
            return True # 假设调用成功
        except Exception as e:
            print(f"错误: macOS: 设置窗口置顶时发生异常: {e}")
            return False

    elif system.startswith("Linux"):
        # 在 Linux 上，使用 wmctrl 命令
        try:
            # 获取当前活动窗口的标题 (需要 wmctrl)
            caption = pygame.display.get_caption()[0] if PYGAME_AVAILABLE else ""
            if caption:
                 # 使用 wmctrl 根据标题设置置顶
                 subprocess.run(["wmctrl", "-r", caption, "-b", "add,above"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 print(f"Linux: 已尝试使用 wmctrl 将窗口 '{caption}' 置顶。")
                 return True
            else:
                 print("警告: 无法获取窗口标题以用于 wmctrl。")
                 return False
        except subprocess.CalledProcessError:
            print("错误: Linux: wmctrl 命令执行失败。请确保 wmctrl 已安装 (e.g., 'sudo apt install wmctrl')。")
            return False
        except FileNotFoundError:
            print("错误: Linux: 未找到 wmctrl 命令。请安装 wmctrl。")
            return False
        except Exception as e:
             print(f"错误: Linux: 设置窗口置顶时发生异常: {e}")
             return False

    else:
        print(f"警告: 不支持的平台: {system}，无法设置窗口置顶。")
        return False


def bring_to_front():
    """
    尝试将当前 Pygame 窗口带到前台并获取焦点。
    成功时返回 True，否则返回 False。
    """
    system = platform.system()
    if system == "Windows":
        if not WIN_API_AVAILABLE:
            print("错误: Windows API 不可用，无法将窗口前置。")
            return False
        hwnd = _get_hwnd()
        if hwnd:
            try:
                # 确保窗口恢复（如果最小化）
                _ShowWindow(hwnd, _SW_RESTORE)
                result = _SetForegroundWindow(hwnd)
                if result:
                    print("Windows: 窗口已前置并获取焦点。")
                    return True
                else:
                    print("警告: Windows API 调用 SetForegroundWindow 失败。窗口可能未获得焦点。")
                    # 注意：Windows 有安全策略阻止程序随意夺取焦点
                    return False
            except Exception as e:
                print(f"错误: Windows: 将窗口前置时发生异常: {e}")
                return False
        else:
            return False

    elif system == "Darwin": # macOS
        if not NS_APP_AVAILABLE:
             print("警告: AppKit 不可用，跳过 macOS 前置。")
             return False
        try:
            # 激活应用以获取焦点
            # 注意：macOS 有安全限制，程序不能随意夺取焦点，通常需要用户先交互
            NSApp().activateIgnoringOtherApps_(True)
            print("macOS: 已尝试激活应用以获取焦点。")
            return True # 假设调用成功
        except Exception as e:
            print(f"错误: macOS: 将窗口前置时发生异常: {e}")
            return False

    elif system.startswith("Linux"):
        # 在 Linux 上，使用 wmctrl 命令
        try:
            caption = pygame.display.get_caption()[0] if PYGAME_AVAILABLE else ""
            if caption:
                 # 使用 wmctrl 根据标题激活窗口
                 subprocess.run(["wmctrl", "-a", caption], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 print(f"Linux: 已尝试使用 wmctrl 将窗口 '{caption}' 前置。")
                 return True
            else:
                 print("警告: 无法获取窗口标题以用于 wmctrl。")
                 return False
        except subprocess.CalledProcessError:
            print("错误: Linux: wmctrl 命令执行失败。请确保 wmctrl 已安装且窗口标题匹配。")
            return False
        except FileNotFoundError:
            print("错误: Linux: 未找到 wmctrl 命令。请安装 wmctrl。")
            return False
        except Exception as e:
             print(f"错误: Linux: 将窗口前置时发生异常: {e}")
             return False

    else:
        print(f"警告: 不支持的平台: {system}，无法将窗口前置。")
        return False

# 为了方便，也可以提供一个组合函数
def focus_and_raise():
    """
    尝试获取焦点并将窗口前置/置顶。
    在某些系统上，这两个操作可能是同一个。
    成功时返回 True，否则返回 False。
    """
    print("尝试获取焦点并前置/置顶窗口...")
    res1 = bring_to_front()
    res2 = set_always_on_top()
    # 返回部分成功或全部成功
    return res1 or res2