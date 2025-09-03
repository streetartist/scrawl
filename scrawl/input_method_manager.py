# input_method_manager.py

import platform
import subprocess
import ctypes
from ctypes import wintypes

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
        self._initialize_platform_specifics()

    def _initialize_platform_specifics(self):
        """根据操作系统初始化特定的 API 或设置。"""
        if self._system == "Windows":
            try:
                self._user32 = ctypes.windll.user32
                self._kernel32 = ctypes.windll.kernel32

                # 定义 Windows API 函数和参数
                self._GetKeyboardLayout = self._user32.GetKeyboardLayout
                self._GetKeyboardLayout.argtypes = [wintypes.DWORD]
                self._GetKeyboardLayout.restype = wintypes.HKL

                self._LoadKeyboardLayout = self._user32.LoadKeyboardLayoutA
                self._LoadKeyboardLayout.argtypes = [wintypes.LPCSTR, wintypes.UINT]
                self._LoadKeyboardLayout.restype = wintypes.HKL

                self._ActivateKeyboardLayout = self._user32.ActivateKeyboardLayout
                self._ActivateKeyboardLayout.argtypes = [wintypes.HKL, wintypes.UINT]
                self._ActivateKeyboardLayout.restype = wintypes.HKL

                self._GetCurrentThreadId = self._kernel32.GetCurrentThreadId
                self._GetCurrentThreadId.argtypes = []
                self._GetCurrentThreadId.restype = wintypes.DWORD

                self._KLF_ACTIVATE = 0x00000001
                self._ENGLISH_LAYOUT_ID = "00000409" # US English

            except Exception as e:
                print(f"[错误] Windows API 初始化失败: {e}")
                self._user32 = None # 标记为不可用

        elif self._system == "Darwin": # macOS
            # macOS 依赖 osascript，无需特殊初始化
            pass
        elif self._system == "Linux":
            # Linux 依赖 setxkbmap 命令，无需特殊初始化
            pass
        else:
            print(f"[警告] 不支持的操作系统: {self._system}")

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
        """获取当前 macOS 活动输入源名称"""
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
        """获取当前 Linux 键盘布局"""
        try:
            result = subprocess.run(
                ["setxkbmap", "-query"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10 # 添加超时
            )
            for line in result.stdout.splitlines():
                if line.startswith("layout:"):
                    layouts = line.split(":", 1)[1].strip()
                    # 为了简化，只取第一个布局
                    return layouts.split(",")[0]
            print("[警告] setxkbmap -query 输出中未找到 layout 信息。")
            return "Unknown"
        except subprocess.TimeoutExpired:
            print("[错误] setxkbmap -query 命令超时。")
            return "Unknown"
        except subprocess.CalledProcessError as e:
           print(f"[错误] setxkbmap -query 执行失败: {e.stderr}")
           return "Unknown"
        except FileNotFoundError:
            print("[错误] setxkbmap 命令未找到。")
            return "Unknown"
        except Exception as e:
            print(f"[错误] 获取 Linux 布局时发生未知错误: {e}")
            return "Unknown"

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
                    return True
                else:
                    return False

            elif self._system == "Darwin": # macOS
                layout = self._get_macos_layout()
                if layout != "Unknown":
                   self._original_state['layout'] = layout
                   print(f"[信息] 已保存 macOS 输入法布局: {layout}")
                   return True
                # 即使是 Unknown 也保存，以便后续处理
                self._original_state['layout'] = layout
                print(f"[信息] 已保存 macOS 输入法布局 (可能未知): {layout}")
                return True # 认为保存操作本身成功

            elif self._system == "Linux":
                layout = self._get_linux_layout()
                if layout != "Unknown":
                    self._original_state['layout'] = layout
                    print(f"[信息] 已保存 Linux 键盘布局: {layout}")
                    return True
                self._original_state['layout'] = layout
                print(f"[信息] 已保存 Linux 键盘布局 (可能未知): {layout}")
                return True # 认为保存操作本身成功

            else:
                print(f"[警告] 不支持的操作系统 '{self._system}'，无法保存输入法状态。")
                return False

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
                hkl = self._LoadKeyboardLayout(self._ENGLISH_LAYOUT_ID.encode('ascii'), self._KLF_ACTIVATE)
                if not hkl:
                    print("[错误] 无法加载英文键盘布局。")
                    return False

                result = self._ActivateKeyboardLayout(hkl, self._KLF_ACTIVATE)
                if not result:
                    print("[错误] 无法激活英文键盘布局。")
                    return False
                print("[信息] 已切换到 Windows 英文输入法。")
                return True


            elif self._system == "Darwin":  # macOS
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
                subprocess.run(
                    ["setxkbmap", "us"],
                    check=True,
                    capture_output=True,
                    timeout=10 # 添加超时
                )
                print("[信息] 已切换到 Linux us 键盘布局。")
                return True


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

    def restore_original_state(self):
        """
        跨平台恢复到之前保存的输入法状态。
        :return: True if successful, False otherwise.
        """
        if not self._original_state:
            print("[警告] 没有找到已保存的输入法状态，无法恢复。")
            return False

        layout = self._original_state.get('layout')

        if layout is None or layout == "Unknown":
             print(f"[警告] 保存的状态中没有有效的布局信息 ('{layout}')，无法恢复。")
             # 清空状态
             self._original_state = {}
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
                    subprocess.run(
                        ["setxkbmap", layout],
                        check=True,
                        capture_output=True,
                        timeout=10 # 添加超时
                    )
                    print(f"[信息] 已恢复到 Linux 键盘布局: {layout}")
                    success = True
                else:
                     print(f"[警告] Linux 状态无效或未知: {layout}")
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
            # 无论恢复成功与否，都清空状态
            self._original_state = {}

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