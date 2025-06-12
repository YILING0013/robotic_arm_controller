#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D可视化模块
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import numpy as np
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config import VISUALIZATION_LIMITS, TaskState

class Visualization3D:
    """3D可视化器"""
    
    def __init__(self, parent_frame, kinematics_calc, font_manager, ui_instance):
        """初始化可视化器"""
        self.parent_frame = parent_frame
        self.kinematics = kinematics_calc
        self.font_manager = font_manager
        self.style = ttk.Style()
        self.ui = ui_instance
        
        # 获取字体配置
        self.mpl_font_config = font_manager.get_matplotlib_font_config()
        self.font = font_manager.get_font_config

        # 获取主题颜色
        self.bg_color = self.style.colors.get('bg')
        self.fg_color = self.style.colors.get('fg')
        self.primary_color = self.style.colors.get('primary')
        
        # 设置matplotlib样式
        self._setup_matplotlib_style()
        
        # 创建图形
        self.fig = plt.Figure(figsize=(10, 8), dpi=100, facecolor=self.bg_color)
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor=self.style.colors.get('light'))
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.fig, parent_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=YES, pady=5)
        
        # 创建工具栏
        self.toolbar_frame = ttk.Frame(parent_frame)
        self.toolbar_frame.pack(fill=X, pady=(5, 0))
        self.create_custom_toolbar()
        
        # 初始化数据
        self.current_angles = [0] * 6
        self.target_position = [0, 0, 0]
        self.pickup_points = []
        self.place_points = []
        self.current_task_index = -1
        self.task_state = TaskState.IDLE
        
        # 更新显示
        self.update_display()
        
    def _setup_matplotlib_style(self):
        """设置matplotlib样式，避免字体警告"""
        try:
            # 临时设置，仅针对这个Figure实例
            self.mpl_params = {
                'font.family': 'sans-serif',
                'font.sans-serif': [self.font_manager.matplotlib_font, 'DejaVu Sans', 'Arial'],
                'axes.unicode_minus': False,
                'font.size': 9,
                'axes.labelsize': 10,
                'xtick.labelsize': 8,
                'ytick.labelsize': 8,
                'legend.fontsize': 8
            }
            
            # 验证字体是否可用
            try:
                test_font = fm.FontProperties(family=self.font_manager.matplotlib_font)
                fm.fontManager.findfont(test_font, fallback_to_default=True)
            except:
                # 如果字体不可用，使用安全的默认设置
                self.mpl_params['font.sans-serif'] = ['DejaVu Sans', 'Arial']
                print("使用默认字体设置以避免字体警告")
                
        except Exception as e:
            print(f"设置matplotlib样式时出错: {e}")
            # 最安全的设置
            self.mpl_params = {
                'font.family': 'sans-serif',
                'font.sans-serif': ['DejaVu Sans'],
                'axes.unicode_minus': False,
                'font.size': 9
            }

    def create_custom_toolbar(self):
        """使用 ttkbootstrap 控件创建自定义工具栏"""
        # 视图控制
        view_frame = ttk.Labelframe(self.toolbar_frame, text="视图", padding=5, bootstyle=SECONDARY)
        view_frame.pack(side=LEFT, padx=(0, 10))
        
        views = [("正视", 0, 0), ("左视", -90, 0), ("俯视", 0, 90), ("轴测", -60, 30)]
        for name, azim, elev in views:
            btn = ttk.Button(view_frame, text=name, width=4, bootstyle="secondary-outline",
                             command=lambda a=azim, e=elev: self.set_view(a, e))
            btn.pack(side=LEFT, padx=1)

        # 操作
        action_frame = ttk.Labelframe(self.toolbar_frame, text="操作", padding=5, bootstyle=SECONDARY)
        action_frame.pack(side=LEFT)
        
        ttk.Button(action_frame, text="重置", command=self.reset_view, width=4, bootstyle="secondary-outline").pack(side=LEFT, padx=1)
        ttk.Button(action_frame, text="保存", command=self.save_image, width=4, bootstyle="secondary-outline").pack(side=LEFT, padx=1)
        
    def set_view(self, azim, elev):
        """设置3D视图角度"""
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw()
        
    def reset_view(self):
        """重置到默认视图"""
        self.ax.view_init(elev=20, azim=-60)
        self.canvas.draw()
        
    def save_image(self):
        """保存当前视图为图片"""
        from tkinter import filedialog
        import time
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")],
            initialfile=f"robot_view_{int(time.time())}.png")
        if filename:
            try:
                self.fig.savefig(filename, dpi=300, facecolor=self.fig.get_facecolor(), 
                               bbox_inches='tight', pad_inches=0.1)
                print(f"图像已保存到: {filename}")
            except Exception as e:
                print(f"保存图像失败: {e}")
            
    # --- 数据更新方法 ---
    def update_robot_state(self, angles): 
        self.current_angles = angles.copy()
        
    def update_target_position(self, position): 
        self.target_position = position.copy()
        
    def update_task_points(self, pickup, place): 
        self.pickup_points = pickup.copy()
        self.place_points = place.copy()
        
    def update_task_status(self, state, index): 
        self.task_state = state
        self.current_task_index = index
        
    def update_display(self):
        """更新完整的3D显示"""
        # 应用matplotlib参数
        with plt.rc_context(self.mpl_params):
            self.ax.clear()
            
            self._draw_robot()
            self._draw_target_point()
            self._draw_task_points()
            self._setup_axes()
            self._add_info_text()
            
        try:
            self.canvas.draw()
        except Exception as e:
            print(f"绘图时出错: {e}")
        
    def _draw_robot(self):
        """绘制机械臂"""
        try:
            chain_angles = self.kinematics.servo_angle_to_chain_angle(self.current_angles)
            # 使用ikpy绘制，并自定义颜色
            self.kinematics.chain.plot(chain_angles, ax=self.ax, target=None)
            
            # 美化绘图
            for line in self.ax.get_lines():
                if len(line.get_xdata()) == 2:  # 臂连接线
                    line.set_color(self.primary_color)
                    line.set_linewidth(5)
                else:  # 关节点
                    line.set_markerfacecolor(self.style.colors.get('secondary'))
                    line.set_markeredgecolor(self.fg_color)
                    line.set_markersize(8)

        except Exception as e:
            print(f"绘制机械臂时出错: {e}")
            
    def _draw_target_point(self):
        """绘制目标点"""
        try:
            show_target = self.ui.show_target_var.get()
            if not show_target: 
                return
                
            target_m = np.array(self.target_position) / 1000.0  # mm -> m
            self.ax.scatter(target_m[0], target_m[1], target_m[2], 
                          c=self.style.colors.danger, s=150, marker='*', alpha=0.9, 
                          label='目标点', edgecolors=self.fg_color, linewidth=1)
        except Exception as e:
            print(f"绘制目标点时出错: {e}")
            
    def _draw_task_points(self):
        """绘制任务点和路径"""
        try:
            # 抓取点
            if self.pickup_points:
                points_m = np.array(self.pickup_points) / 1000.0
                self.ax.scatter(points_m[:, 0], points_m[:, 1], points_m[:, 2], 
                              c=self.style.colors.success, s=100, marker='o', alpha=0.8, 
                              label='抓取点', edgecolors=self.fg_color)
            
            # 放置点
            if self.place_points:
                points_m = np.array(self.place_points) / 1000.0
                self.ax.scatter(points_m[:, 0], points_m[:, 1], points_m[:, 2], 
                              c=self.style.colors.info, s=100, marker='s', alpha=0.8, 
                              label='放置点', edgecolors=self.fg_color)

            # 任务连线
            if self.pickup_points and self.place_points:
                for i, (p1, p2) in enumerate(zip(self.pickup_points, self.place_points)):
                    p1_m, p2_m = np.array(p1)/1000.0, np.array(p2)/1000.0
                    is_current = (self.task_state in [TaskState.RUNNING, TaskState.PAUSED] and i == self.current_task_index)
                    
                    self.ax.plot([p1_m[0], p2_m[0]], [p1_m[1], p2_m[1]], [p1_m[2], p2_m[2]], 
                               color=self.style.colors.danger if is_current else self.style.colors.warning, 
                               linestyle='-' if is_current else ':', 
                               linewidth=3 if is_current else 1.5, 
                               alpha=1.0 if is_current else 0.7)
        except Exception as e:
            print(f"绘制任务点时出错: {e}")

    def _setup_axes(self):
        """设置坐标轴样式"""
        try:
            limits = VISUALIZATION_LIMITS
            self.ax.set(xlim=limits['x'], ylim=limits['y'], zlim=limits['z'])
            
            # 设置坐标轴比例
            try:
                self.ax.set_box_aspect((
                    np.diff(limits['x'])[0], 
                    np.diff(limits['y'])[0], 
                    np.diff(limits['z'])[0]
                ))
            except:
                pass  # 某些matplotlib版本可能不支持set_box_aspect

            # 设置标签 - 使用英文避免字体问题
            self.ax.set_xlabel("X (m)", color=self.fg_color)
            self.ax.set_ylabel("Y (m)", color=self.fg_color)
            self.ax.set_zlabel("Z (m)", color=self.fg_color)

            # 设置刻度颜色
            self.ax.tick_params(axis='x', colors=self.fg_color)
            self.ax.tick_params(axis='y', colors=self.fg_color)
            self.ax.tick_params(axis='z', colors=self.fg_color)

            # 设置网格
            self.ax.grid(True, which='both', linestyle=':', linewidth=0.5, 
                        color=self.style.colors.get('secondary'))

            # 设置图例
            handles, labels = self.ax.get_legend_handles_labels()
            if handles:
                try:
                    legend = self.ax.legend(handles, labels, loc='upper left')
                    frame = legend.get_frame()
                    frame.set_facecolor(self.style.colors.get('light'))
                    frame.set_edgecolor(self.fg_color)
                    for text in legend.get_texts():
                        text.set_color(self.fg_color)
                except Exception as e:
                    print(f"设置图例时出错: {e}")
                    
        except Exception as e:
            print(f"设置坐标轴时出错: {e}")

    def _add_info_text(self):
        """在左下角添加信息文本"""
        try:
            chain_angles = self.kinematics.servo_angle_to_chain_angle(self.current_angles)
            ee_pos = self.kinematics.chain.forward_kinematics(chain_angles)[:3, 3] * 1000
            
            # 使用英文和数字，避免中文字体问题
            info_text = f"End Effector: X={ee_pos[0]:.1f} Y={ee_pos[1]:.1f} Z={ee_pos[2]:.1f} mm"
            if self.task_state != TaskState.IDLE:
                info_text += f"\nTask State: {self.task_state.name}"
            
            # 安全地添加文本
            try:
                self.ax.text2D(0.02, 0.02, info_text, transform=self.ax.transAxes,
                             fontsize=9, color=self.fg_color, verticalalignment='bottom',
                             bbox=dict(boxstyle="round,pad=0.4", facecolor=self.bg_color, 
                                     alpha=0.8, edgecolor=self.primary_color))
            except Exception as text_error:
                print(f"添加信息文本时出错: {text_error}")
                # 简化的文本，只显示位置
                simple_text = f"X:{ee_pos[0]:.1f} Y:{ee_pos[1]:.1f} Z:{ee_pos[2]:.1f}"
                self.ax.text2D(0.02, 0.02, simple_text, transform=self.ax.transAxes,
                             fontsize=8, color=self.fg_color)
                
        except Exception as e:
            print(f"计算末端位置时出错: {e}")