#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D可视化模块 - 处理机械臂的3D显示和交互
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import tkinter as tk
from tkinter import ttk
from config import VISUALIZATION_LIMITS, TaskState

# 设置matplotlib支持中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class Visualization3D:
    """3D可视化器"""
    
    def __init__(self, parent_frame, kinematics_calc):
        self.parent_frame = parent_frame
        self.kinematics = kinematics_calc
        
        # 创建图形
        self.fig = plt.Figure(figsize=(10, 8), dpi=100, facecolor='#f8f9fa')
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#ffffff')
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.fig, parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        self.toolbar_frame = ttk.Frame(parent_frame)
        self.toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 自定义工具栏
        self.create_custom_toolbar()
        
        # 显示选项
        self.show_target = True
        self.show_trajectory = False
        self.show_workspace = False
        
        # 数据存储
        self.current_angles = [190, 130, 130, 130, 130, 130]
        self.target_position = [0.15, 0.0, 0.2]
        self.pickup_points = []
        self.place_points = []
        self.current_task_index = 0
        self.task_state = TaskState.IDLE
        
        # 初始化显示
        self.update_display()
        
    def create_custom_toolbar(self):
        """创建自定义工具栏"""
        # 视图控制按钮
        view_frame = ttk.LabelFrame(self.toolbar_frame, text="视图控制", padding=5)
        view_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        views = [
            ("正视图", 0, 0),
            ("左视图", -90, 0),
            ("俯视图", 0, 90),
            ("等轴测", -60, 30)
        ]
        
        for i, (name, azim, elev) in enumerate(views):
            btn = ttk.Button(view_frame, text=name, width=8,
                           command=lambda a=azim, e=elev: self.set_view(a, e))
            btn.grid(row=0, column=i, padx=2)
            
        # 显示选项
        display_frame = ttk.LabelFrame(self.toolbar_frame, text="显示选项", padding=5)
        display_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.show_target_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="目标点", variable=self.show_target_var,
                       command=self.toggle_target_display).grid(row=0, column=0, padx=5)
        
        self.show_trajectory_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="轨迹", variable=self.show_trajectory_var,
                       command=self.toggle_trajectory_display).grid(row=0, column=1, padx=5)
        
        self.show_workspace_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="工作空间", variable=self.show_workspace_var,
                       command=self.toggle_workspace_display).grid(row=0, column=2, padx=5)
        
        # 操作按钮
        action_frame = ttk.LabelFrame(self.toolbar_frame, text="操作", padding=5)
        action_frame.pack(side=tk.RIGHT)
        
        ttk.Button(action_frame, text="重置视图", 
                  command=self.reset_view).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="保存图片", 
                  command=self.save_image).grid(row=0, column=1, padx=2)
        
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
            filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg"), ("All files", "*.*")],
            initialfile=f"robot_view_{int(time.time())}.png"
        )
        
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            
    def toggle_target_display(self):
        """切换目标点显示"""
        self.show_target = self.show_target_var.get()
        self.update_display()
        
    def toggle_trajectory_display(self):
        """切换轨迹显示"""
        self.show_trajectory = self.show_trajectory_var.get()
        self.update_display()
        
    def toggle_workspace_display(self):
        """切换工作空间显示"""
        self.show_workspace = self.show_workspace_var.get()
        self.update_display()
        
    def update_robot_state(self, angles):
        """更新机械臂状态"""
        self.current_angles = angles.copy()
        self.update_display()
        
    def update_target_position(self, position):
        """更新目标位置"""
        self.target_position = position.copy()
        if self.show_target:
            self.update_display()
            
    def update_task_points(self, pickup_points, place_points):
        """更新任务点"""
        self.pickup_points = pickup_points.copy()
        self.place_points = place_points.copy()
        self.update_display()
        
    def update_task_status(self, task_state, current_index=0):
        """更新任务状态"""
        self.task_state = task_state
        self.current_task_index = current_index
        self.update_display()
        
    def update_display(self):
        """更新3D显示"""
        self.ax.clear()
        
        # 绘制机械臂
        self._draw_robot()
        
        # 绘制目标点
        if self.show_target:
            self._draw_target_point()
            
        # 绘制任务点
        self._draw_task_points()
        
        # 绘制工作空间
        if self.show_workspace:
            self._draw_workspace()
            
        # 设置坐标轴
        self._setup_axes()
        
        # 添加信息文本
        self._add_info_text()
        
        # 刷新画布
        self.canvas.draw()
        
    def _draw_robot(self):
        """绘制机械臂"""
        try:
            chain_angles = self.kinematics.servo_angle_to_chain_angle(self.current_angles)
            
            # 使用ikpy绘制机械臂
            self.kinematics.chain.plot(chain_angles, ax=self.ax, target=None)
            
        except Exception as e:
            print(f"绘制机械臂错误: {e}")
            
    def _draw_target_point(self):
        """绘制目标点"""
        try:
            target_pos = np.array(self.target_position)
            
            # 如果目标位置单位是mm，转换为m
            if np.max(np.abs(target_pos)) > 10:
                target_pos = target_pos / 1000
                
            # 绘制红色目标点
            self.ax.scatter(target_pos[0], target_pos[1], target_pos[2], 
                          c='red', s=120, marker='o', alpha=0.8, 
                          label='目标点', edgecolors='darkred', linewidth=2)
            
            # 添加标注
            self.ax.text(target_pos[0], target_pos[1], target_pos[2] + 0.02, 
                       f'目标点\n({target_pos[0]*1000:.1f}, {target_pos[1]*1000:.1f}, {target_pos[2]*1000:.1f})', 
                       fontsize=8, ha='center', va='bottom',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="red", alpha=0.3))
            
            # 计算并显示误差
            chain_angles = self.kinematics.servo_angle_to_chain_angle(self.current_angles)
            ee_pos = self.kinematics.chain.forward_kinematics(chain_angles)[:3, 3]
            error = np.linalg.norm(ee_pos - target_pos) * 1000
            
            # 绘制误差连线
            if error > 1.0:  # 如果误差大于1mm
                self.ax.plot([ee_pos[0], target_pos[0]], 
                           [ee_pos[1], target_pos[1]], 
                           [ee_pos[2], target_pos[2]], 
                           'r--', alpha=0.6, linewidth=2, label=f'误差: {error:.1f}mm')
                
        except Exception as e:
            print(f"绘制目标点错误: {e}")
            
    def _draw_task_points(self):
        """绘制任务点"""
        # 绘制抓取点
        if self.pickup_points:
            pickup_x = [p[0]/1000 for p in self.pickup_points]
            pickup_y = [p[1]/1000 for p in self.pickup_points]
            pickup_z = [p[2]/1000 for p in self.pickup_points]
            
            self.ax.scatter(pickup_x, pickup_y, pickup_z, 
                          c='#27AE60', s=100, marker='^', alpha=0.8, 
                          label='抓取点', edgecolors='#1E8449', linewidth=1.5)
            
            # 添加编号
            for i, (x, y, z) in enumerate(zip(pickup_x, pickup_y, pickup_z)):
                self.ax.text(x, y, z + 0.015, f'P{i+1}', fontsize=8, ha='center', va='bottom',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="#27AE60", alpha=0.7))
        
        # 绘制放置点
        if self.place_points:
            place_x = [p[0]/1000 for p in self.place_points]
            place_y = [p[1]/1000 for p in self.place_points]
            place_z = [p[2]/1000 for p in self.place_points]
            
            self.ax.scatter(place_x, place_y, place_z, 
                          c='#3498DB', s=100, marker='s', alpha=0.8, 
                          label='放置点', edgecolors='#2E86C1', linewidth=1.5)
            
            # 添加编号
            for i, (x, y, z) in enumerate(zip(place_x, place_y, place_z)):
                self.ax.text(x, y, z + 0.015, f'D{i+1}', fontsize=8, ha='center', va='bottom',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="#3498DB", alpha=0.7))
        
        # 绘制任务连线
        if self.pickup_points and self.place_points:
            min_len = min(len(self.pickup_points), len(self.place_points))
            for i in range(min_len):
                pickup = self.pickup_points[i]
                place = self.place_points[i]
                
                # 普通连线
                line_style = ':'
                line_width = 2
                line_color = '#F39C12'
                line_alpha = 0.6
                
                # 高亮当前任务连线
                if (self.task_state in [TaskState.RUNNING, TaskState.PAUSED] and 
                    i == self.current_task_index):
                    line_style = '-'
                    line_width = 3
                    line_color = '#E74C3C'
                    line_alpha = 1.0
                
                self.ax.plot([pickup[0]/1000, place[0]/1000], 
                           [pickup[1]/1000, place[1]/1000], 
                           [pickup[2]/1000, place[2]/1000], 
                           color=line_color, linestyle=line_style, 
                           alpha=line_alpha, linewidth=line_width)
        
        # 高亮当前执行的任务点
        if (self.task_state in [TaskState.RUNNING, TaskState.PAUSED] and 
            self.current_task_index < len(self.pickup_points) and 
            self.current_task_index < len(self.place_points)):
            
            curr_pickup = self.pickup_points[self.current_task_index]
            curr_place = self.place_points[self.current_task_index]
            
            # 高亮当前抓取点
            self.ax.scatter(curr_pickup[0]/1000, curr_pickup[1]/1000, curr_pickup[2]/1000, 
                          c='#00FF00', s=150, marker='^', alpha=1.0, 
                          edgecolors='black', linewidth=2, zorder=10)
            
            # 高亮当前放置点
            self.ax.scatter(curr_place[0]/1000, curr_place[1]/1000, curr_place[2]/1000, 
                          c='#00FFFF', s=150, marker='s', alpha=1.0, 
                          edgecolors='black', linewidth=2, zorder=10)
                          
    def _draw_workspace(self):
        """绘制工作空间（简化版）"""
        try:
            # 绘制一个简单的工作空间边界
            theta = np.linspace(0, 2*np.pi, 50)
            
            # 最大工作半径（近似）
            max_radius = 0.25  # 250mm
            min_radius = 0.05   # 50mm
            
            # 绘制外圆
            x_outer = max_radius * np.cos(theta)
            y_outer = max_radius * np.sin(theta)
            z_outer = np.full_like(x_outer, 0.1)  # 工作平面高度
            
            # 绘制内圆
            x_inner = min_radius * np.cos(theta)
            y_inner = min_radius * np.sin(theta)
            z_inner = np.full_like(x_inner, 0.1)
            
            self.ax.plot(x_outer, y_outer, z_outer, 'gray', alpha=0.5, linewidth=1, label='工作空间边界')
            self.ax.plot(x_inner, y_inner, z_inner, 'gray', alpha=0.5, linewidth=1)
            
        except Exception as e:
            print(f"绘制工作空间错误: {e}")
            
    def _setup_axes(self):
        """设置坐标轴"""
        # 设置显示范围
        limits = VISUALIZATION_LIMITS
        self.ax.set_xlim(limits['x'])
        self.ax.set_ylim(limits['y'])
        self.ax.set_zlim(limits['z'])
        
        # 设置长宽比
        self.ax.set_box_aspect([1, 1, 1])
        
        # 设置标签
        self.ax.set_xlabel("X (m)", fontsize=10, fontweight='bold')
        self.ax.set_ylabel("Y (m)", fontsize=10, fontweight='bold')
        self.ax.set_zlabel("Z (m)", fontsize=10, fontweight='bold')
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
        
        # 添加图例
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            self.ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
            
    def _add_info_text(self):
        """添加信息文本"""
        try:
            # 计算末端位置
            chain_angles = self.kinematics.servo_angle_to_chain_angle(self.current_angles)
            ee_pos = self.kinematics.chain.forward_kinematics(chain_angles)[:3, 3] * 1000  # 转为mm
            
            # 基本信息
            info_text = f"末端位置: X={ee_pos[0]:.1f} Y={ee_pos[1]:.1f} Z={ee_pos[2]:.1f} mm"
            
            # 目标点误差信息
            if self.show_target:
                target_pos_mm = np.array(self.target_position)
                if np.max(np.abs(target_pos_mm)) <= 10:  # 如果是米单位
                    target_pos_mm *= 1000
                error = np.linalg.norm(ee_pos - target_pos_mm)
                info_text += f"\n误差: {error:.1f} mm"
            
            # 任务点统计
            if self.pickup_points or self.place_points:
                info_text += f"\n抓取点: {len(self.pickup_points)}, 放置点: {len(self.place_points)}"
            
            # 任务状态
            if self.task_state != TaskState.IDLE:
                info_text += f"\n任务状态: {self.task_state.value}"
                if self.task_state in [TaskState.RUNNING, TaskState.PAUSED]:
                    info_text += f"\n当前任务: {self.current_task_index + 1}/{len(self.pickup_points)}"
            
            # 添加文本框
            self.ax.text2D(0.02, 0.02, info_text,
                           transform=self.ax.transAxes, fontsize=9,
                           bbox=dict(boxstyle="round,pad=0.5", facecolor="#ECF0F1", alpha=0.9, edgecolor="#BDC3C7"),
                           verticalalignment='bottom')
                           
        except Exception as e:
            print(f"添加信息文本错误: {e}")