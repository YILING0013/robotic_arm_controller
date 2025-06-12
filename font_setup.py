#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体设置模块
"""

import platform
import tkinter as tk
import tkinter.font as tkFont
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from config import FONT_CONFIG

class FontManager:
    """字体管理器"""

    def __init__(self):
        """初始化字体管理器"""
        self.system = platform.system().lower()
        print(f"检测到操作系统: {platform.system()} {platform.release()}")
        
        # 先检测matplotlib可用字体
        self.matplotlib_fonts = self._get_matplotlib_fonts()
        
        # 检测tkinter可用字体
        self.tkinter_fonts = self._get_tkinter_fonts()
        
        # 选择最佳字体
        self.selected_font = self._find_best_font()
        self.matplotlib_font = self._find_matplotlib_font()
        
        # 设置字体
        self.setup_matplotlib_fonts()
        self.print_font_info()

    def _get_matplotlib_fonts(self):
        """获取matplotlib可用的字体列表"""
        try:
            font_list = [f.name for f in fm.fontManager.ttflist]
            # 过滤出可能的中文字体
            chinese_fonts = []
            chinese_keywords = ['微软雅黑', 'Microsoft YaHei', 'SimHei', 'SimSun', 'NotoSans', 'PingFang', 'Hiragino', 'WenQuanYi']
            
            for font in font_list:
                for keyword in chinese_keywords:
                    if keyword.lower() in font.lower():
                        chinese_fonts.append(font)
                        break
            
            print(f"Matplotlib检测到 {len(font_list)} 个字体，其中 {len(chinese_fonts)} 个中文字体")
            return chinese_fonts if chinese_fonts else font_list
        except Exception as e:
            print(f"警告: 检测matplotlib字体失败: {e}")
            return []

    def _get_tkinter_fonts(self):
        """检测并返回tkinter可用字体集合"""
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            fonts = set(tkFont.families())
            temp_root.destroy()
            print(f"Tkinter检测到 {len(fonts)} 个可用字体")
            return fonts
        except Exception as e:
            print(f"警告: 检测tkinter字体失败: {e}")
            return set()

    def _find_best_font(self):
        """为tkinter找到最合适的中文字体"""
        # 获取当前系统的推荐字体列表
        font_candidates = FONT_CONFIG.get(self.system, [])
        
        # 依次检查推荐字体是否可用
        for font in font_candidates:
            if font in self.tkinter_fonts:
                print(f"Tkinter成功匹配到推荐字体: {font}")
                return font
        
        # 如果推荐字体都不可用，尝试一些通用的中文字体
        fallback_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS', 'DejaVu Sans']
        for font in fallback_fonts:
            if font in self.tkinter_fonts:
                print(f"Tkinter使用备选字体: {font}")
                return font
        
        # 最后的后备字体
        fallback_font = FONT_CONFIG.get('fallback', 'Arial')
        print(f"警告: 未找到合适的中文字体，Tkinter将使用后备字体: {fallback_font}")
        return fallback_font

    def _find_matplotlib_font(self):
        """为matplotlib找到最合适的中文字体"""
        # 尝试系统推荐的字体
        font_candidates = FONT_CONFIG.get(self.system, [])
        
        for font in font_candidates:
            # 检查matplotlib是否有这个字体
            if any(font.lower() in mpl_font.lower() for mpl_font in self.matplotlib_fonts):
                matching_font = next((mpl_font for mpl_font in self.matplotlib_fonts if font.lower() in mpl_font.lower()), None)
                if matching_font:
                    print(f"Matplotlib匹配到字体: {matching_font}")
                    return matching_font
        
        # 尝试一些常见的中文字体名称
        common_fonts = [
            'Microsoft YaHei', 'Microsoft YaHei UI',
            'SimHei', 'SimSun', 'KaiTi',
            'PingFang SC', 'Hiragino Sans GB',
            'Noto Sans CJK SC', 'WenQuanYi Micro Hei',
            'DejaVu Sans'
        ]
        
        for font in common_fonts:
            if any(font.lower() in mpl_font.lower() for mpl_font in self.matplotlib_fonts):
                matching_font = next((mpl_font for mpl_font in self.matplotlib_fonts if font.lower() in mpl_font.lower()), None)
                if matching_font:
                    print(f"Matplotlib使用通用字体: {matching_font}")
                    return matching_font
        
        # 如果都找不到，使用matplotlib的默认字体并禁用中文
        print("警告: Matplotlib未找到合适的中文字体，使用默认字体")
        return 'DejaVu Sans'

    def setup_matplotlib_fonts(self):
        """设置matplotlib以支持中文字体和负号显示"""
        try:
            # 设置字体
            plt.rcParams['font.sans-serif'] = [self.matplotlib_font, 'DejaVu Sans', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 设置默认字体大小
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.titlesize'] = 12
            plt.rcParams['axes.labelsize'] = 10
            plt.rcParams['xtick.labelsize'] = 9
            plt.rcParams['ytick.labelsize'] = 9
            plt.rcParams['legend.fontsize'] = 9
            
            # 测试字体是否工作
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.text(0.5, 0.5, '测试中文', fontsize=12, ha='center')
            plt.close(fig)
            
            print("Matplotlib 字体设置完成")
            
        except Exception as e:
            print(f"警告: 设置matplotlib字体失败: {e}")
            # 使用最安全的设置
            try:
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                print("已切换到安全的matplotlib字体设置")
            except:
                pass

    def get_font_config(self, size=10, weight='normal'):
        """获取tkinter字体配置元组"""
        return (self.selected_font, size, weight)

    def get_matplotlib_font_config(self):
        """获取matplotlib字体配置"""
        return {
            'fontname': self.matplotlib_font,
            'fontsize': 10
        }

    def print_font_info(self):
        """打印最终的字体配置信息"""
        print("\n" + "="*60)
        print("字体配置信息")
        print("="*60)
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"Tkinter字体: {self.selected_font}")
        print(f"Matplotlib字体: {self.matplotlib_font}")
        print(f"可用中文字体数量: {len(self.matplotlib_fonts)}")
        if self.matplotlib_fonts:
            print(f"部分可用字体: {', '.join(self.matplotlib_fonts[:3])}...")
        print("="*60)

def setup_fonts():
    """
    执行字体设置的主函数
    返回一个配置好的FontManager实例
    """
    print("正在初始化字体配置...")
    return FontManager()

if __name__ == "__main__":
    # 直接运行此文件以测试字体配置
    manager = setup_fonts()
    
    # 创建一个测试窗口来展示字体效果
    root = tk.Tk()
    root.title("字体测试")
    root.geometry("500x400")
    
    tk.Label(root, text=f"Tkinter字体: {manager.selected_font}", 
             font=manager.get_font_config(14, 'bold'), fg='blue').pack(pady=10)
    
    tk.Label(root, text=f"Matplotlib字体: {manager.matplotlib_font}", 
             font=manager.get_font_config(12), fg='green').pack(pady=5)
    
    test_texts = [
        "🤖 5DOF机械臂控制系统 v2.1",
        "你好，世界！ Hello, World!",
        "串口: COM3, 状态: 已连接",
        "X:150.0, Y:0.0, Z:200.0",
        "目标位置控制、手动微调、自动化任务",
        "1234567890 ABCDEFGHIJK"
    ]
    
    for text in test_texts:
        tk.Label(root, text=text, font=manager.get_font_config(11)).pack(pady=3)
    
    # 测试matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.text(0.5, 0.7, '这是matplotlib中文测试', ha='center', fontsize=14)
    ax.text(0.5, 0.3, f'使用字体: {manager.matplotlib_font}', ha='center', fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Matplotlib中文字体测试')
    
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.get_tk_widget().pack(pady=10)
    
    root.mainloop()