#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块 - 包含所有用户界面组件 (修复版)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
import json
import time
from config import (UI_THEME, DEFAULT_ANGLES, SERVO_LIMITS, DEFAULT_TARGET_POSITION, 
                   AUTO_TASK_DEFAULTS, TaskState, GRIPPER_OPEN, GRIPPER_CLOSE)

class ModernUI:
    """现代化UI界面"""
    
    def __init__(self, root, callbacks=None, font_manager=None):
        self.root = root
        self.callbacks = callbacks or {}
        self.font_manager = font_manager
        
        # 配置主题和字体
        self.setup_theme()
        
        # 初始化变量
        self.init_variables()
        
        # 创建主界面
        self.create_main_interface()
        
    def setup_theme(self):
        """设置UI主题和字体"""
        style = ttk.Style()
        
        # 配置样式
        style.theme_use('clam')
        
        # 获取字体配置
        if self.font_manager:
            font_family = self.font_manager.selected_font
        else:
            font_family = UI_THEME['font_family']
        
        # 更新字体配置
        self.font_config = {
            'default': (font_family, UI_THEME['font_size']),
            'bold': (font_family, UI_THEME['font_size'], 'bold'),
            'large': (font_family, UI_THEME.get('font_size_large', UI_THEME['font_size'] + 2)),
            'large_bold': (font_family, UI_THEME.get('font_size_large', UI_THEME['font_size'] + 2), 'bold'),
            'small': (font_family, UI_THEME.get('font_size_small', UI_THEME['font_size'] - 1))
        }
        
        # 自定义颜色
        theme = UI_THEME
        
        # 配置ttk控件的默认字体
        try:
            default_font = tkFont.nametofont("TkDefaultFont")
            default_font.configure(family=font_family, size=UI_THEME['font_size'])
            
            text_font = tkFont.nametofont("TkTextFont")
            text_font.configure(family=font_family, size=UI_THEME['font_size'])
        except:
            pass
        
        # 配置按钮样式
        style.configure('Primary.TButton',
                       background=theme['primary_color'],
                       foreground='white',
                       padding=theme['button_padding'])
        
        style.configure('Success.TButton',
                       background=theme['success_color'],
                       foreground='white',
                       padding=theme['button_padding'])
        
        style.configure('Warning.TButton',
                       background=theme['warning_color'],
                       foreground='white',
                       padding=theme['button_padding'])
        
        style.configure('Danger.TButton',
                       background=theme['danger_color'],
                       foreground='white',
                       padding=theme['button_padding'])
        
        # 配置标签框样式
        style.configure('Card.TLabelframe',
                       background=theme['background_color'],
                       borderwidth=2,
                       relief='solid')
        
    def init_variables(self):
        """初始化变量"""
        # 串口变量
        self.port_var = tk.StringVar()
        self.status_var = tk.StringVar(value="未连接")
        
        # 位置变量
        self.x_var = tk.DoubleVar(value=DEFAULT_TARGET_POSITION[0])
        self.y_var = tk.DoubleVar(value=DEFAULT_TARGET_POSITION[1])
        self.z_var = tk.DoubleVar(value=DEFAULT_TARGET_POSITION[2])
        self.speed_var = tk.IntVar(value=2)
        
        # 角度变量
        self.angle_vars = [tk.DoubleVar(value=angle) for angle in DEFAULT_ANGLES]
        
        # 显示选项
        self.show_target_var = tk.BooleanVar(value=True)
        
        # 自动化任务变量
        self.safe_height_var = tk.DoubleVar(value=AUTO_TASK_DEFAULTS['safe_height'])
        self.height_offset_var = tk.DoubleVar(value=AUTO_TASK_DEFAULTS['height_offset'])
        self.grip_delay_var = tk.DoubleVar(value=AUTO_TASK_DEFAULTS['grip_delay'])
        self.move_delay_var = tk.DoubleVar(value=AUTO_TASK_DEFAULTS['move_delay'])
        self.return_home_var = tk.BooleanVar(value=AUTO_TASK_DEFAULTS['return_home'])
        
        # 任务状态变量
        self.task_status_var = tk.StringVar(value=TaskState.IDLE.value)
        self.task_progress_var = tk.StringVar(value="0/0")
        self.task_step_var = tk.StringVar(value="")
        
        # 自定义指令变量
        self.cmd_var = tk.StringVar()
        
    def create_main_interface(self):
        """创建主界面"""
        # 配置根窗口
        self.root.title("5DOF机械臂上位机")
        self.root.geometry("1216x640")
        self.root.configure(bg=UI_THEME['background_color'])
        
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 创建左右分栏
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建滚动控制面板
        self.create_scrollable_control_panel(left_panel)
        
        # 创建可视化面板
        self.create_visualization_panel(right_panel)
        
    def create_scrollable_control_panel(self, parent):
        """创建可滚动的控制面板"""
        # 创建画布和滚动条
        canvas = tk.Canvas(parent, width=650, bg=UI_THEME['background_color'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建控制面板内容
        self.create_control_panels()
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def create_control_panels(self):
        """创建所有控制面板"""
        # 串口连接面板
        self.create_connection_panel()
        
        # 状态监控面板
        self.create_status_panel()
        
        # 自动化任务面板
        self.create_automation_panel()
        
        # 位置控制面板
        self.create_position_panel()
        
        # 手动控制面板
        self.create_manual_panel()
        
        # 夹爪控制面板
        self.create_gripper_panel()
        
        # 自定义指令面板
        self.create_custom_command_panel()
        
    def create_connection_panel(self):
        """创建串口连接面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="🔌 串口连接", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 端口选择行
        port_frame = ttk.Frame(frame)
        port_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(port_frame, text="端口:").pack(side=tk.LEFT)
        
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, width=20, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(port_frame, text="🔄 刷新", command=self._refresh_ports).pack(side=tk.LEFT, padx=(5, 0))
        
        # 连接按钮和状态
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X)
        
        self.connect_btn = ttk.Button(control_frame, text="🔗 连接", style='Success.TButton',
                                     command=self._toggle_connection)
        self.connect_btn.pack(side=tk.LEFT)
        
        # 状态标签
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT, padx=(10, 5))
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
    def create_status_panel(self):
        """创建状态监控面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="📊 系统状态", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建状态网格
        status_grid = ttk.Frame(frame)
        status_grid.pack(fill=tk.X)
        
        # 任务状态
        ttk.Label(status_grid, text="任务状态:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.task_status_label = ttk.Label(status_grid, textvariable=self.task_status_var)
        self.task_status_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 任务进度
        ttk.Label(status_grid, text="进度:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.task_progress_label = ttk.Label(status_grid, textvariable=self.task_progress_var)
        self.task_progress_label.grid(row=0, column=3, sticky=tk.W)
        
        # 当前步骤
        ttk.Label(status_grid, text="当前步骤:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.task_step_label = ttk.Label(status_grid, textvariable=self.task_step_var)
        self.task_step_label.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))
        
    def create_automation_panel(self):
        """创建自动化任务面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="🤖 自动化任务", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 任务点管理
        points_frame = ttk.Frame(frame)
        points_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 抓取点管理
        pickup_frame = ttk.LabelFrame(points_frame, text="📦 抓取点", padding=10)
        pickup_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.pickup_listbox = tk.Listbox(pickup_frame, height=5)
        self.pickup_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        pickup_btn_frame = ttk.Frame(pickup_frame)
        pickup_btn_frame.pack(fill=tk.X)
        
        ttk.Button(pickup_btn_frame, text="➕", command=self._add_pickup_point, width=4).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pickup_btn_frame, text="✏️", command=self._edit_pickup_point, width=4).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(pickup_btn_frame, text="🗑️", command=self._delete_pickup_point, width=4).pack(side=tk.LEFT)
        
        # 放置点管理
        place_frame = ttk.LabelFrame(points_frame, text="📍 放置点", padding=10)
        place_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.place_listbox = tk.Listbox(place_frame, height=5)
        self.place_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        place_btn_frame = ttk.Frame(place_frame)
        place_btn_frame.pack(fill=tk.X)
        
        ttk.Button(place_btn_frame, text="➕", command=self._add_place_point, width=4).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(place_btn_frame, text="✏️", command=self._edit_place_point, width=4).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(place_btn_frame, text="🗑️", command=self._delete_place_point, width=4).pack(side=tk.LEFT)
        
        # 任务参数设置
        params_frame = ttk.LabelFrame(frame, text="⚙️ 任务参数", padding=10)
        params_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 参数网格
        param_grid = ttk.Frame(params_frame)
        param_grid.pack(fill=tk.X)
        
        # 第一行
        ttk.Label(param_grid, text="安全高度(mm):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(param_grid, textvariable=self.safe_height_var, width=10).grid(row=0, column=1, padx=(0, 15))
        
        ttk.Label(param_grid, text="上方偏移(mm):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(param_grid, textvariable=self.height_offset_var, width=10).grid(row=0, column=3, padx=(0, 15))
        
        # 第二行
        ttk.Label(param_grid, text="夹爪延迟(s):").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(param_grid, textvariable=self.grip_delay_var, width=10).grid(row=1, column=1, padx=(0, 15), pady=(10, 0))
        
        ttk.Label(param_grid, text="移动延迟(s):").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(param_grid, textvariable=self.move_delay_var, width=10).grid(row=1, column=3, padx=(0, 15), pady=(10, 0))
        
        # 选项
        options_frame = ttk.Frame(params_frame)
        options_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Checkbutton(options_frame, text="任务结束后返回复位点", 
                       variable=self.return_home_var).pack(side=tk.LEFT)
        
        # 任务控制按钮
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_task_btn = ttk.Button(control_frame, text="🚀 开始任务", style='Success.TButton',
                                        command=self._start_auto_task)
        self.start_task_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pause_task_btn = ttk.Button(control_frame, text="⏸️ 暂停", style='Warning.TButton',
                                        command=self._pause_auto_task, state=tk.DISABLED)
        self.pause_task_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_task_btn = ttk.Button(control_frame, text="⏹️ 停止", style='Danger.TButton',
                                       command=self._stop_auto_task, state=tk.DISABLED)
        self.stop_task_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(control_frame, text="💾 保存任务", command=self._save_task_points).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(control_frame, text="📂 加载任务", command=self._load_task_points).pack(side=tk.RIGHT)
        
    def create_position_panel(self):
        """创建位置控制面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="🎯 位置控制", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 目标位置输入
        pos_frame = ttk.Frame(frame)
        pos_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(pos_frame, text="目标位置 (mm):").pack(anchor=tk.W, pady=(0, 10))
        
        # 坐标输入网格
        coord_frame = ttk.Frame(pos_frame)
        coord_frame.pack(fill=tk.X)
        
        # X坐标
        ttk.Label(coord_frame, text="X:").grid(row=0, column=0, padx=(0, 5))
        x_entry = ttk.Entry(coord_frame, textvariable=self.x_var, width=12)
        x_entry.grid(row=0, column=1, padx=(0, 20))
        x_entry.bind('<KeyRelease>', self._on_target_position_change)
        
        # Y坐标
        ttk.Label(coord_frame, text="Y:").grid(row=0, column=2, padx=(0, 5))
        y_entry = ttk.Entry(coord_frame, textvariable=self.y_var, width=12)
        y_entry.grid(row=0, column=3, padx=(0, 20))
        y_entry.bind('<KeyRelease>', self._on_target_position_change)
        
        # Z坐标
        ttk.Label(coord_frame, text="Z:").grid(row=0, column=4, padx=(0, 5))
        z_entry = ttk.Entry(coord_frame, textvariable=self.z_var, width=12)
        z_entry.grid(row=0, column=5, padx=(0, 20))
        z_entry.bind('<KeyRelease>', self._on_target_position_change)
        
        # 速度控制
        ttk.Label(coord_frame, text="速度:").grid(row=0, column=6, padx=(0, 5))
        ttk.Entry(coord_frame, textvariable=self.speed_var, width=8).grid(row=0, column=7)
        
        # 控制按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(btn_frame, text="🧮 计算角度", style='Primary.TButton',
                  command=self._calculate_angles).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📤 发送指令", style='Success.TButton',
                  command=self._send_position_command).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(btn_frame, text="📍 添加为抓取点", 
                  command=self._add_current_as_pickup).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="🎯 添加为放置点", 
                  command=self._add_current_as_place).pack(side=tk.RIGHT)
        
        # 目标点显示控制
        display_frame = ttk.Frame(frame)
        display_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(display_frame, text="显示目标点", 
                       variable=self.show_target_var, 
                       command=self._toggle_target_display).pack(side=tk.LEFT)
        
    def create_manual_panel(self):
        """创建手动控制面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="🎮 手动控制", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 舵机控制网格
        servo_frame = ttk.Frame(frame)
        servo_frame.pack(fill=tk.X, pady=(0, 15))
        
        servo_names = ["底座旋转", "大臂俯仰", "小臂俯仰", "手腕俯仰", "手腕旋转", "夹爪开合"]
        
        for i in range(6):
            # 标签
            ttk.Label(servo_frame, text=f"舵机{i}({servo_names[i]}):").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            # 滑块
            min_angle, max_angle = SERVO_LIMITS[i]
            scale = ttk.Scale(servo_frame, from_=min_angle, to=max_angle, 
                            orient=tk.HORIZONTAL, variable=self.angle_vars[i],
                            command=lambda val, idx=i: self._on_angle_change(idx, val))
            scale.grid(row=i, column=1, sticky=tk.EW, padx=(10, 10), pady=5)
            
            # 数值输入
            entry = ttk.Entry(servo_frame, textvariable=self.angle_vars[i], width=10)
            entry.grid(row=i, column=2, padx=(0, 5), pady=5)
            entry.bind('<Return>', lambda e, idx=i: self._on_angle_change(idx, self.angle_vars[idx].get()))
            
            # 当前角度显示
            ttk.Label(servo_frame, text=f"[{min_angle}°-{max_angle}°]").grid(row=i, column=3, padx=(5, 0), pady=5)
        
        servo_frame.columnconfigure(1, weight=1)
        
        # 控制按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🏠 复位", style='Warning.TButton',
                  command=self._reset_position).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📤 发送角度", style='Success.TButton',
                  command=self._send_manual_command).pack(side=tk.LEFT)
        
    def create_gripper_panel(self):
        """创建夹爪控制面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="🤏 夹爪控制", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✋ 张开", style='Success.TButton',
                  command=lambda: self._control_gripper(GRIPPER_OPEN)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(btn_frame, text="✊ 合上", style='Warning.TButton',
                  command=lambda: self._control_gripper(GRIPPER_CLOSE)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
    def create_custom_command_panel(self):
        """创建自定义指令面板"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="⌨️ 自定义指令", style='Card.TLabelframe', padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # 指令输入
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(cmd_frame, textvariable=self.cmd_var).pack(fill=tk.X, pady=(0, 10))
        ttk.Button(cmd_frame, text="📤 发送指令", style='Primary.TButton',
                  command=self._send_custom_command).pack(fill=tk.X)
        
    def create_visualization_panel(self, parent):
        """创建可视化面板"""
        # 这里只创建容器，实际的3D可视化将由visualization.py模块处理
        self.viz_frame = ttk.LabelFrame(parent, text="🎬 3D可视化", style='Card.TLabelframe', padding=15)
        self.viz_frame.pack(fill=tk.BOTH, expand=True)
        
    # 回调方法（需要在主程序中连接到实际的处理函数）
    def _refresh_ports(self):
        if 'refresh_ports' in self.callbacks:
            self.callbacks['refresh_ports']()
            
    def _toggle_connection(self):
        if 'toggle_connection' in self.callbacks:
            self.callbacks['toggle_connection']()
            
    def _on_target_position_change(self, event=None):
        if 'target_position_change' in self.callbacks:
            self.callbacks['target_position_change']()
            
    def _calculate_angles(self):
        if 'calculate_angles' in self.callbacks:
            self.callbacks['calculate_angles']()
            
    def _send_position_command(self):
        if 'send_position_command' in self.callbacks:
            self.callbacks['send_position_command']()
            
    def _add_current_as_pickup(self):
        if 'add_current_as_pickup' in self.callbacks:
            self.callbacks['add_current_as_pickup']()
            
    def _add_current_as_place(self):
        if 'add_current_as_place' in self.callbacks:
            self.callbacks['add_current_as_place']()
            
    def _toggle_target_display(self):
        if 'toggle_target_display' in self.callbacks:
            self.callbacks['toggle_target_display']()
            
    def _on_angle_change(self, servo_id, value):
        # ✅ 如果正在更新角度显示，则跳过回调
        if hasattr(self, '_updating_angles') and self._updating_angles:
            return
            
        if 'angle_change' in self.callbacks:
            self.callbacks['angle_change'](servo_id, value)
            
    def _reset_position(self):
        if 'reset_position' in self.callbacks:
            self.callbacks['reset_position']()
            
    def _send_manual_command(self):
        if 'send_manual_command' in self.callbacks:
            self.callbacks['send_manual_command']()
            
    def _control_gripper(self, angle):
        if 'control_gripper' in self.callbacks:
            self.callbacks['control_gripper'](angle)
            
    def _send_custom_command(self):
        if 'send_custom_command' in self.callbacks:
            self.callbacks['send_custom_command']()
            
    def _add_pickup_point(self):
        if 'add_pickup_point' in self.callbacks:
            self.callbacks['add_pickup_point']()
            
    def _edit_pickup_point(self):
        if 'edit_pickup_point' in self.callbacks:
            self.callbacks['edit_pickup_point']()
            
    def _delete_pickup_point(self):
        if 'delete_pickup_point' in self.callbacks:
            self.callbacks['delete_pickup_point']()
            
    def _add_place_point(self):
        if 'add_place_point' in self.callbacks:
            self.callbacks['add_place_point']()
            
    def _edit_place_point(self):
        if 'edit_place_point' in self.callbacks:
            self.callbacks['edit_place_point']()
            
    def _delete_place_point(self):
        if 'delete_place_point' in self.callbacks:
            self.callbacks['delete_place_point']()
            
    def _start_auto_task(self):
        if 'start_auto_task' in self.callbacks:
            self.callbacks['start_auto_task']()
            
    def _pause_auto_task(self):
        if 'pause_auto_task' in self.callbacks:
            self.callbacks['pause_auto_task']()
            
    def _stop_auto_task(self):
        if 'stop_auto_task' in self.callbacks:
            self.callbacks['stop_auto_task']()
            
    def _save_task_points(self):
        if 'save_task_points' in self.callbacks:
            self.callbacks['save_task_points']()
            
    def _load_task_points(self):
        if 'load_task_points' in self.callbacks:
            self.callbacks['load_task_points']()
    
    # UI更新方法
    def update_ports_list(self, ports):
        """更新端口列表"""
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_combo.current(0)
    
    def update_connection_status(self, connected, status_text):
        """更新连接状态"""
        if connected:
            self.connect_btn.config(text="🔌 断开", style='Danger.TButton')
        else:
            self.connect_btn.config(text="🔗 连接", style='Success.TButton')
        self.status_var.set(status_text)
    
    def update_angles_display(self, angles):
        """更新角度显示"""
        # ✅ 增加标志位防止触发回调
        self._updating_angles = True
        try:
            for i, angle in enumerate(angles):
                if i < len(self.angle_vars):
                    self.angle_vars[i].set(round(angle, 1))
        finally:
            self._updating_angles = False
    
    def update_pickup_listbox(self, points):
        """更新抓取点列表"""
        self.pickup_listbox.delete(0, tk.END)
        for i, point in enumerate(points):
            self.pickup_listbox.insert(tk.END, f"{i+1}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
    
    def update_place_listbox(self, points):
        """更新放置点列表"""
        self.place_listbox.delete(0, tk.END)
        for i, point in enumerate(points):
            self.place_listbox.insert(tk.END, f"{i+1}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
    
    def update_task_status(self, state, step=""):
        """更新任务状态"""
        self.task_status_var.set(state.value if hasattr(state, 'value') else str(state))
        self.task_step_var.set(step.value if hasattr(step, 'value') else str(step))
        
        # 更新按钮状态
        if state == TaskState.IDLE:
            self.start_task_btn.config(state=tk.NORMAL)
            self.pause_task_btn.config(state=tk.DISABLED, text="⏸️ 暂停")
            self.stop_task_btn.config(state=tk.DISABLED)
        elif state == TaskState.RUNNING:
            self.start_task_btn.config(state=tk.DISABLED)
            self.pause_task_btn.config(state=tk.NORMAL, text="⏸️ 暂停")
            self.stop_task_btn.config(state=tk.NORMAL)
        elif state == TaskState.PAUSED:
            self.start_task_btn.config(state=tk.DISABLED)
            self.pause_task_btn.config(state=tk.NORMAL, text="▶️ 恢复")
            self.stop_task_btn.config(state=tk.NORMAL)
        else:  # COMPLETED, ERROR
            self.start_task_btn.config(state=tk.NORMAL)
            self.pause_task_btn.config(state=tk.DISABLED, text="⏸️ 暂停")
            self.stop_task_btn.config(state=tk.DISABLED)
    
    def update_task_progress(self, current, total):
        """更新任务进度"""
        self.task_progress_var.set(f"{current}/{total}")
    
    def get_point_from_dialog(self, title, initial_values=None):
        """获取点坐标的对话框"""
        if initial_values is None:
            initial_values = [self.x_var.get(), self.y_var.get(), self.z_var.get()]
            
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=UI_THEME['background_color'])
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        result = [None]
        
        # 创建主框架
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入框
        ttk.Label(main_frame, text="X坐标 (mm):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=10)
        x_var = tk.DoubleVar(value=initial_values[0])
        ttk.Entry(main_frame, textvariable=x_var, width=15).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Y坐标 (mm):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=10)
        y_var = tk.DoubleVar(value=initial_values[1])
        ttk.Entry(main_frame, textvariable=y_var, width=15).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Z坐标 (mm):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=10)
        z_var = tk.DoubleVar(value=initial_values[2])
        ttk.Entry(main_frame, textvariable=z_var, width=15).grid(row=2, column=1, padx=10, pady=10)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def on_ok():
            result[0] = (x_var.get(), y_var.get(), z_var.get())
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
            
        ttk.Button(btn_frame, text="✅ 确定", style='Success.TButton', command=on_ok).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="❌ 取消", style='Danger.TButton', command=on_cancel).pack(side=tk.LEFT)
        
        dialog.wait_window()
        return result[0]