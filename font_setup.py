#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体设置模块 - 自动检测系统并配置合适的中文字体
"""

import platform
import tkinter as tk
import tkinter.font as tkFont
import matplotlib
import matplotlib.pyplot as plt
from config import FONT_CONFIG, UI_THEME

class FontManager:
    """字体管理器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.available_fonts = None
        self.selected_font = None
        
    def detect_available_fonts(self):
        """检测系统可用字体"""
        try:
            # 创建临时窗口来获取字体列表
            temp_root = tk.Tk()
            temp_root.withdraw()
            
            # 获取系统字体列表
            font_families = tkFont.families()
            self.available_fonts = set(font_families)
            
            temp_root.destroy()
            
            print(f"检测到 {len(self.available_fonts)} 个系统字体")
            return self.available_fonts
            
        except Exception as e:
            print(f"检测系统字体失败: {e}")
            return set()
    
    def find_best_font(self):
        """根据系统找到最佳中文字体"""
        if self.available_fonts is None:
            self.detect_available_fonts()
        
        # 获取当前系统的字体配置
        system_fonts = FONT_CONFIG.get(self.system, FONT_CONFIG['windows'])
        
        # 优先选择主字体
        if system_fonts['primary'] in self.available_fonts:
            self.selected_font = system_fonts['primary']
            print(f"使用主字体: {self.selected_font}")
            return self.selected_font
        
        # 尝试备选字体
        for font in system_fonts['secondary']:
            if font in self.available_fonts:
                self.selected_font = font
                print(f"使用备选字体: {self.selected_font}")
                return self.selected_font
        
        # 使用后备字体
        self.selected_font = system_fonts['fallback']
        print(f"使用后备字体: {self.selected_font}")
        return self.selected_font
    
    def setup_matplotlib_fonts(self):
        """设置matplotlib中文字体"""
        try:
            # 设置matplotlib支持中文
            if self.system == 'windows':
                # Windows系统
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
            elif self.system == 'darwin':  # macOS
                chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Arial Unicode MS']
            else:  # Linux
                chinese_fonts = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback']
            
            # 设置字体
            for font in chinese_fonts:
                try:
                    plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                    break
                except:
                    continue
            
            # 解决负号显示问题
            plt.rcParams['axes.unicode_minus'] = False
            
            print("matplotlib中文字体设置完成")
            
        except Exception as e:
            print(f"设置matplotlib字体失败: {e}")
    
    def get_font_config(self, size=None, weight='normal'):
        """获取字体配置元组"""
        if self.selected_font is None:
            self.find_best_font()
        
        if size is None:
            size = UI_THEME['font_size']
        
        return (self.selected_font, size, weight)
    
    def test_font_display(self):
        """测试字体显示效果"""
        try:
            # 创建测试窗口
            test_window = tk.Toplevel()
            test_window.title("字体测试")
            test_window.geometry("400x300")
            
            font_config = self.get_font_config(12)
            
            # 测试文本
            test_texts = [
                "🤖 5DOF机械臂控制系统",
                "串口连接状态：已连接",
                "当前位置：X=150.0, Y=0.0, Z=200.0",
                "任务状态：执行中",
                "抓取点、放置点、夹爪控制",
                "自动化任务、位置控制、手动控制"
            ]
            
            tk.Label(test_window, text=f"当前字体: {self.selected_font}", 
                    font=font_config, fg='blue').pack(pady=10)
            
            for text in test_texts:
                tk.Label(test_window, text=text, font=font_config).pack(pady=2)
            
            # 关闭按钮
            tk.Button(test_window, text="关闭", font=font_config,
                     command=test_window.destroy).pack(pady=10)
            
        except Exception as e:
            print(f"字体测试失败: {e}")
    
    def print_font_info(self):
        """打印字体信息"""
        print("\n" + "="*50)
        print("字体配置信息")
        print("="*50)
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"当前选择字体: {self.selected_font}")
        
        if self.available_fonts:
            # 显示可用的中文字体
            chinese_fonts = []
            chinese_keywords = ['Microsoft', 'YaHei', 'SimHei', 'SimSun', 'KaiTi', 
                              'PingFang', 'Hiragino', 'STHeiti', 'Noto', 'WenQuanYi']
            
            for font in self.available_fonts:
                if any(keyword in font for keyword in chinese_keywords):
                    chinese_fonts.append(font)
            
            print(f"检测到的中文字体 ({len(chinese_fonts)} 个):")
            for font in sorted(chinese_fonts)[:10]:  # 显示前10个
                print(f"  - {font}")
            
            if len(chinese_fonts) > 10:
                print(f"  ... 还有 {len(chinese_fonts) - 10} 个字体")
        
        print("="*50)

def setup_fonts():
    """设置字体的主函数"""
    print("正在配置字体...")
    
    font_manager = FontManager()
    
    # 检测并设置最佳字体
    font_manager.find_best_font()
    
    # 设置matplotlib字体
    font_manager.setup_matplotlib_fonts()
    
    # 更新UI主题字体
    UI_THEME['font_family'] = font_manager.selected_font
    
    # 打印字体信息
    font_manager.print_font_info()
    
    return font_manager

def manual_font_selection():
    """手动选择字体"""
    print("\n可选字体配置:")
    print("1. Microsoft YaHei UI (推荐-Windows)")
    print("2. Microsoft YaHei")
    print("3. SimHei (黑体)")
    print("4. PingFang SC (推荐-macOS)")
    print("5. Noto Sans CJK SC (推荐-Linux)")
    print("6. 自动检测")
    print("7. 测试当前字体")
    
    try:
        choice = input("\n请选择字体 (1-7): ").strip()
        
        font_options = {
            '1': 'Microsoft YaHei UI',
            '2': 'Microsoft YaHei', 
            '3': 'SimHei',
            '4': 'PingFang SC',
            '5': 'Noto Sans CJK SC'
        }
        
        if choice in font_options:
            selected_font = font_options[choice]
            print(f"已选择字体: {selected_font}")
            
            # 更新配置
            UI_THEME['font_family'] = selected_font
            
            # 测试字体
            font_manager = FontManager()
            font_manager.selected_font = selected_font
            font_manager.setup_matplotlib_fonts()
            
            return font_manager
            
        elif choice == '6':
            return setup_fonts()
            
        elif choice == '7':
            font_manager = FontManager()
            font_manager.test_font_display()
            return font_manager
            
        else:
            print("无效选择，使用自动检测")
            return setup_fonts()
            
    except KeyboardInterrupt:
        print("\n操作取消，使用默认字体配置")
        return setup_fonts()

if __name__ == "__main__":
    # 直接运行此文件来测试字体
    font_manager = setup_fonts()
    
    # 提供手动选择选项
    try:
        user_input = input("\n是否需要手动选择字体? (y/n): ").strip().lower()
        if user_input == 'y':
            font_manager = manual_font_selection()
            
        # 显示字体测试窗口
        test_input = input("是否显示字体测试窗口? (y/n): ").strip().lower()
        if test_input == 'y':
            root = tk.Tk()
            root.withdraw()
            font_manager.test_font_display()
            root.mainloop()
            
    except KeyboardInterrupt:
        print("\n程序退出")