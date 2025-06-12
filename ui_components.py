#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块 - 使用 ttkbootstrap
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config import (DEFAULT_ANGLES, SERVO_LIMITS, DEFAULT_TARGET_POSITION, 
                   AUTO_TASK_DEFAULTS, TaskState, GRIPPER_OPEN, GRIPPER_CLOSE)

class ModernUI:
    """现代化UI界面 - 基于 ttkbootstrap 和卡片式布局"""
    
    def __init__(self, root, callbacks=None, font_manager=None):
        """初始化UI"""
        self.root = root
        self.callbacks = callbacks or {}
        self.font = font_manager.get_font_config if font_manager else lambda size=10, weight='normal': ('Helvetica', size, weight)
        
        # 初始化变量
        self.init_variables()
        
        # 创建主界面
        self.create_main_interface()
        
    def init_variables(self):
        """初始化所有Tkinter变量"""
        # 连接
        self.port_var = ttk.StringVar()
        self.status_var = ttk.StringVar(value="未连接")
        
        # 位置控制
        self.x_var = ttk.DoubleVar(value=DEFAULT_TARGET_POSITION[0])
        self.y_var = ttk.DoubleVar(value=DEFAULT_TARGET_POSITION[1])
        self.z_var = ttk.DoubleVar(value=DEFAULT_TARGET_POSITION[2])
        self.speed_var = ttk.IntVar(value=2)
        
        # 手动控制
        self.angle_vars = [ttk.DoubleVar(value=angle) for angle in DEFAULT_ANGLES]
        
        # 可视化
        self.show_target_var = ttk.BooleanVar(value=True)
        
        # 自动化
        self.safe_height_var = ttk.DoubleVar(value=AUTO_TASK_DEFAULTS['safe_height'])
        self.height_offset_var = ttk.DoubleVar(value=AUTO_TASK_DEFAULTS['height_offset'])
        self.grip_delay_var = ttk.DoubleVar(value=AUTO_TASK_DEFAULTS['grip_delay'])
        self.move_delay_var = ttk.DoubleVar(value=AUTO_TASK_DEFAULTS['move_delay'])
        self.return_home_var = ttk.BooleanVar(value=AUTO_TASK_DEFAULTS['return_home'])
        
        # 状态
        self.task_status_var = ttk.StringVar(value=TaskState.IDLE.value)
        self.task_progress_var = ttk.StringVar(value="0/0")
        self.task_step_var = ttk.StringVar(value="无")
        
        # 自定义指令
        self.cmd_var = ttk.StringVar()
        
        # 键盘控制
        self.keyboard_control_var = ttk.BooleanVar(value=False)
        self.step_size_var = ttk.DoubleVar(value=5.0)

    def create_main_interface(self):
        """创建主界面，分为左右两个面板"""
        self.root.title("🤖 5DOF机械臂上位机")
        self.root.geometry("1400x850")

        # 创建主容器
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=BOTH, expand=YES)

        # 左侧控制面板
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=LEFT, fill=Y, padx=(0, 10))

        # 右侧可视化面板
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # 创建标签页
        self.create_tabbed_interface(left_panel)
        
        # 创建可视化面板
        self.create_visualization_panel(right_panel)
        
    def create_tabbed_interface(self, parent):
        """在左侧面板创建标签页"""
        self.notebook = ttk.Notebook(parent, bootstyle="primary", width=500)
        self.notebook.pack(fill=BOTH, expand=YES)

        # 创建标签页
        tab1 = ttk.Frame(self.notebook, padding=10)
        tab2 = ttk.Frame(self.notebook, padding=10)
        tab3 = ttk.Frame(self.notebook, padding=10)
        tab4 = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(tab1, text="🔌 主要控制")
        self.notebook.add(tab2, text="🎮 手动微调")
        self.notebook.add(tab3, text="🤖 自动化")
        self.notebook.add(tab4, text="⚙️ 设置")
        
        # 填充内容
        self.create_main_control_tab(tab1)
        self.create_manual_finetune_tab(tab2)
        self.create_automation_tab(tab3)
        self.create_settings_tab(tab4)

    # ========================================================================
    # 标签页1: 主要控制
    # ========================================================================
    def create_main_control_tab(self, parent):
        """创建主要控制标签页的内容"""
        self.create_connection_panel(parent)
        self.create_position_panel(parent)
        self.create_quick_control_panel(parent)
        self.create_keyboard_control_panel(parent)
        self.create_custom_command_panel(parent)

    def create_connection_panel(self, parent):
        """创建串口连接面板"""
        frame = ttk.Labelframe(parent, text="🔌 串口连接", padding=15, bootstyle=INFO)
        frame.pack(fill=X, pady=10)

        # 端口选择
        port_frame = ttk.Frame(frame)
        port_frame.pack(fill=X, pady=5)
        ttk.Label(port_frame, text="串口:", width=5).pack(side=LEFT)
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, state="readonly", bootstyle=INFO)
        self.port_combo.pack(side=LEFT, fill=X, expand=YES, padx=5)
        ttk.Button(port_frame, text="🔄", command=self._refresh_ports, bootstyle="info-outline", width=3).pack(side=LEFT)
        
        # 连接按钮和状态
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=X, pady=5)
        self.connect_btn = ttk.Button(action_frame, text="🔗 连接", bootstyle="success", command=self._toggle_connection)
        self.connect_btn.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        
        status_frame = ttk.Frame(action_frame)
        status_frame.pack(side=LEFT, fill=X, expand=YES)
        ttk.Label(status_frame, text="状态:").pack(side=LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, bootstyle="info")
        self.status_label.pack(side=LEFT, padx=5)

    def create_position_panel(self, parent):
        """创建位置控制面板"""
        frame = ttk.Labelframe(parent, text="🎯 目标位置控制 (mm)", padding=15, bootstyle=PRIMARY)
        frame.pack(fill=X, pady=10)

        coords = [("X:", self.x_var), ("Y:", self.y_var), ("Z:", self.z_var)]
        for label, var in coords:
            row = ttk.Frame(frame)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, width=3).pack(side=LEFT)
            entry = ttk.Entry(row, textvariable=var, bootstyle=PRIMARY)
            entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
            entry.bind('<KeyRelease>', self._on_target_position_change)
        
        # 速度
        row = ttk.Frame(frame)
        row.pack(fill=X, pady=(10, 5))
        ttk.Label(row, text="速度:", width=5).pack(side=LEFT)
        ttk.Entry(row, textvariable=self.speed_var, width=5).pack(side=LEFT, padx=5)
        
        # 控制按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, pady=10)
        ttk.Button(btn_frame, text="🧮 计算角度", command=self._calculate_angles, bootstyle="primary-outline").pack(fill=X, pady=3)
        ttk.Button(btn_frame, text="📤 发送位置", command=self._send_position_command, bootstyle="success").pack(fill=X, pady=3)
        
    def create_quick_control_panel(self, parent):
        """创建快速控制面板（复位、夹爪）"""
        frame = ttk.Labelframe(parent, text="⚡ 快速操作", padding=15, bootstyle=SECONDARY)
        frame.pack(fill=X, pady=10)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="🏠 复位", command=self._reset_position, bootstyle="warning").pack(side=LEFT, expand=YES, fill=X, padx=2)
        ttk.Button(btn_frame, text="✋ 张开", command=lambda: self._control_gripper(GRIPPER_OPEN), bootstyle="success-outline").pack(side=LEFT, expand=YES, fill=X, padx=2)
        ttk.Button(btn_frame, text="✊ 合上", command=lambda: self._control_gripper(GRIPPER_CLOSE), bootstyle="danger-outline").pack(side=LEFT, expand=YES, fill=X, padx=2)

    def create_keyboard_control_panel(self, parent):
        """创建键盘控制面板"""
        frame = ttk.Labelframe(parent, text="⌨️ 键盘控制", padding=15, bootstyle=DARK)
        frame.pack(fill=X, pady=10)

        toggle_frame = ttk.Frame(frame)
        toggle_frame.pack(fill=X, pady=5)
        self.keyboard_control_btn = ttk.Checkbutton(
            toggle_frame, text="启用键盘控制", variable=self.keyboard_control_var,
            command=self._toggle_keyboard_control, bootstyle="success-round-toggle")
        self.keyboard_control_btn.pack(side=LEFT)

        step_frame = ttk.Frame(frame)
        step_frame.pack(fill=X, pady=5)
        ttk.Label(step_frame, text="步长 (mm):").pack(side=LEFT, padx=(0,5))
        ttk.Entry(step_frame, textvariable=self.step_size_var, width=6).pack(side=LEFT)
        
        help_text = "WASD:水平移动 | ↑↓:垂直移动 | Q/F:夹爪"
        ttk.Label(frame, text=help_text, font=self.font(8), bootstyle="secondary").pack(fill=X, pady=(5,0))

    def create_custom_command_panel(self, parent):
        """创建自定义指令面板"""
        frame = ttk.Labelframe(parent, text="✍️ 自定义指令", padding=15, bootstyle=INFO)
        frame.pack(fill=X, pady=10)
        
        entry = ttk.Entry(frame, textvariable=self.cmd_var, bootstyle=INFO)
        entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        ttk.Button(frame, text="发送", command=self._send_custom_command, bootstyle="info").pack(side=LEFT)

    # ========================================================================
    # 标签页2: 手动微调
    # ========================================================================
    def create_manual_finetune_tab(self, parent):
        """创建手动微调标签页的内容"""
        frame = ttk.Labelframe(parent, text="🕹️ 舵机角度微调", padding=15)
        frame.pack(fill=BOTH, expand=YES)
        
        servo_names = ["底座旋转", "大臂俯仰", "小臂俯仰", "手腕俯仰", "手腕旋转", "夹爪开合"]
        
        for i in range(6):
            servo_frame = ttk.Frame(frame, padding=(0,10))
            servo_frame.pack(fill=X)
            
            min_angle, max_angle = SERVO_LIMITS[i]
            
            ttk.Label(servo_frame, text=f"S{i} {servo_names[i]}", font=self.font(10, 'bold')).pack(fill=X)
            
            scale_frame = ttk.Frame(servo_frame)
            scale_frame.pack(fill=X, pady=5)

            scale = ttk.Scale(scale_frame, from_=min_angle, to=max_angle,
                              orient=HORIZONTAL, variable=self.angle_vars[i],
                              command=lambda val, idx=i: self._on_angle_change(idx, val),
                              bootstyle=SECONDARY)
            scale.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
            
            entry = ttk.Entry(scale_frame, textvariable=self.angle_vars[i], width=5)
            entry.pack(side=LEFT)
            entry.bind('<Return>', lambda e, idx=i: self._on_angle_change(idx, self.angle_vars[idx].get()))

        # 发送按钮
        ttk.Button(frame, text="📤 发送所有角度", command=self._send_manual_command, bootstyle="success").pack(fill=X, pady=15)

    # ========================================================================
    # 标签页3: 自动化
    # ========================================================================
    def create_automation_tab(self, parent):
        """创建自动化任务标签页的内容"""
        self.create_task_points_panel(parent)
        self.create_automation_params_panel(parent)
        self.create_automation_control_panel(parent)
        self.create_task_status_panel(parent)

    def create_task_points_panel(self, parent):
        """创建任务点管理面板"""
        frame = ttk.Labelframe(parent, text="📍 任务点管理", padding=15, bootstyle=PRIMARY)
        frame.pack(fill=X, pady=10)

        lists_frame = ttk.Frame(frame)
        lists_frame.pack(fill=X, expand=YES)
        
        # 抓取点
        pickup_frame = ttk.Frame(lists_frame)
        pickup_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5))
        ttk.Label(pickup_frame, text="抓取点", font=self.font(10, 'bold')).pack()
        
        self.pickup_tree = ttk.Treeview(pickup_frame, columns=("coords"), show="headings", height=6, bootstyle=PRIMARY)
        self.pickup_tree.heading("coords", text="坐标 (X, Y, Z)")
        self.pickup_tree.column("coords", width=180)
        self.pickup_tree.pack(fill=BOTH, expand=YES, pady=(5,0))
        
        pickup_btns = ttk.Frame(pickup_frame)
        pickup_btns.pack(fill=X, pady=5)
        ttk.Button(pickup_btns, text="➕", command=self._add_pickup_point, bootstyle="success-outline", width=3).pack(side=LEFT, expand=YES)
        ttk.Button(pickup_btns, text="✏️", command=self._edit_pickup_point, bootstyle="info-outline", width=3).pack(side=LEFT, expand=YES)
        ttk.Button(pickup_btns, text="🗑️", command=self._delete_pickup_point, bootstyle="danger-outline", width=3).pack(side=LEFT, expand=YES)

        # 放置点
        place_frame = ttk.Frame(lists_frame)
        place_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0))
        ttk.Label(place_frame, text="放置点", font=self.font(10, 'bold')).pack()

        self.place_tree = ttk.Treeview(place_frame, columns=("coords"), show="headings", height=6, bootstyle=INFO)
        self.place_tree.heading("coords", text="坐标 (X, Y, Z)")
        self.place_tree.column("coords", width=180)
        self.place_tree.pack(fill=BOTH, expand=YES, pady=(5,0))

        place_btns = ttk.Frame(place_frame)
        place_btns.pack(fill=X, pady=5)
        ttk.Button(place_btns, text="➕", command=self._add_place_point, bootstyle="success-outline", width=3).pack(side=LEFT, expand=YES)
        ttk.Button(place_btns, text="✏️", command=self._edit_place_point, bootstyle="info-outline", width=3).pack(side=LEFT, expand=YES)
        ttk.Button(place_btns, text="🗑️", command=self._delete_place_point, bootstyle="danger-outline", width=3).pack(side=LEFT, expand=YES)

    def create_automation_params_panel(self, parent):
        """创建自动化参数设置面板"""
        frame = ttk.Labelframe(parent, text="⚙️ 任务参数", padding=15, bootstyle=SECONDARY)
        frame.pack(fill=X, pady=10)
        
        params = [
            ("安全高度 (mm):", self.safe_height_var),
            ("上方偏移 (mm):", self.height_offset_var),
            ("夹爪延迟 (s):", self.grip_delay_var),
            ("移动延迟 (s):", self.move_delay_var)
        ]
        
        for label, var in params:
            row = ttk.Frame(frame)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, width=15).pack(side=LEFT)
            ttk.Entry(row, textvariable=var, width=8).pack(side=LEFT, padx=5)
        
        ttk.Checkbutton(frame, text="任务结束后返回复位点", variable=self.return_home_var, bootstyle="primary-round-toggle").pack(pady=(10,0))
    
    def create_automation_control_panel(self, parent):
        """创建自动化任务控制面板"""
        frame = ttk.Labelframe(parent, text="🚀 任务控制", padding=15, bootstyle=SUCCESS)
        frame.pack(fill=X, pady=10)
        
        # 任务启停
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=X, pady=5)
        self.start_task_btn = ttk.Button(action_frame, text="开始任务", command=self._start_auto_task, bootstyle="success")
        self.start_task_btn.pack(side=LEFT, expand=YES, fill=X, padx=2)
        self.pause_task_btn = ttk.Button(action_frame, text="暂停", command=self._pause_auto_task, bootstyle="warning", state=DISABLED)
        self.pause_task_btn.pack(side=LEFT, expand=YES, fill=X, padx=2)
        self.stop_task_btn = ttk.Button(action_frame, text="停止", command=self._stop_auto_task, bootstyle="danger", state=DISABLED)
        self.stop_task_btn.pack(side=LEFT, expand=YES, fill=X, padx=2)
        
        # 文件操作
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=X, pady=10)
        ttk.Button(file_frame, text="📂 加载任务", command=self._load_task_points, bootstyle="info-outline").pack(side=LEFT, expand=YES, fill=X, padx=2)
        ttk.Button(file_frame, text="💾 保存任务", command=self._save_task_points, bootstyle="primary-outline").pack(side=LEFT, expand=YES, fill=X, padx=2)
        
    def create_task_status_panel(self, parent):
        """创建任务状态显示面板"""
        frame = ttk.Labelframe(parent, text="📊 任务状态", padding=15, bootstyle=INFO)
        frame.pack(fill=X, pady=10)
        
        row1 = ttk.Frame(frame)
        row1.pack(fill=X, pady=2)
        ttk.Label(row1, text="状态:", width=8).pack(side=LEFT)
        self.task_status_label = ttk.Label(row1, textvariable=self.task_status_var, bootstyle="info")
        self.task_status_label.pack(side=LEFT)
        
        row2 = ttk.Frame(frame)
        row2.pack(fill=X, pady=2)
        ttk.Label(row2, text="进度:", width=8).pack(side=LEFT)
        self.task_progress_label = ttk.Label(row2, textvariable=self.task_progress_var, bootstyle="info")
        self.task_progress_label.pack(side=LEFT)
        
        row3 = ttk.Frame(frame)
        row3.pack(fill=X, pady=2)
        ttk.Label(row3, text="当前步骤:", width=8).pack(side=LEFT)
        self.task_step_label = ttk.Label(row3, textvariable=self.task_step_var, bootstyle="info")
        self.task_step_label.pack(side=LEFT)

    # ========================================================================
    # 标签页4: 设置
    # ========================================================================
    def create_settings_tab(self, parent):
        """创建设置标签页的内容"""
        frame = ttk.Labelframe(parent, text="ℹ️ 关于本程序", padding=20)
        frame.pack(fill=X, pady=10)
        
        about_text = """5DOF机械臂上位机

主要特性:
- ttkbootstrap 现代化界面
- 实时3D可视化与交互
- 自动化任务编程与管理
- 键盘实时增量控制
- 串口通信与指令生成

© 2025 Robot Control System
"""
        ttk.Label(frame, text=about_text, justify=LEFT).pack(fill=X)
        
        # 添加可视化显示选项
        viz_frame = ttk.Labelframe(parent, text="👓 可视化选项", padding=15)
        viz_frame.pack(fill=X, pady=10)
        ttk.Checkbutton(viz_frame, text="显示目标点", variable=self.show_target_var, command=self._toggle_target_display, bootstyle="primary-square-toggle").pack(anchor=W)

    def create_visualization_panel(self, parent):
        """创建右侧的可视化面板"""
        frame = ttk.Labelframe(parent, text="🎬 3D 可视化", padding=15, bootstyle=PRIMARY)
        frame.pack(fill=BOTH, expand=YES)
        self.viz_frame = frame

    # ========================================================================
    # UI 更新与交互方法
    # ========================================================================
    def _call_callback(self, name, *args):
        """安全地调用回调函数"""
        if name in self.callbacks:
            self.callbacks[name](*args)
            
    # --- 回调代理 ---
    def _refresh_ports(self): self._call_callback('refresh_ports')
    def _toggle_connection(self): self._call_callback('toggle_connection')
    def _on_target_position_change(self, e=None): self._call_callback('target_position_change')
    def _calculate_angles(self): self._call_callback('calculate_angles')
    def _send_position_command(self): self._call_callback('send_position_command')
    def _toggle_target_display(self): self._call_callback('toggle_target_display')
    def _reset_position(self): self._call_callback('reset_position')
    def _control_gripper(self, angle): self._call_callback('control_gripper', angle)
    def _toggle_keyboard_control(self): self._call_callback('toggle_keyboard_control', self.keyboard_control_var.get())
    def _send_custom_command(self): self._call_callback('send_custom_command')
    def _on_angle_change(self, servo_id, value): self._call_callback('angle_change', servo_id, value)
    def _send_manual_command(self): self._call_callback('send_manual_command')
    def _add_pickup_point(self): self._call_callback('add_pickup_point')
    def _edit_pickup_point(self): self._call_callback('edit_pickup_point')
    def _delete_pickup_point(self): self._call_callback('delete_pickup_point')
    def _add_place_point(self): self._call_callback('add_place_point')
    def _edit_place_point(self): self._call_callback('edit_place_point')
    def _delete_place_point(self): self._call_callback('delete_place_point')
    def _start_auto_task(self): self._call_callback('start_auto_task')
    def _pause_auto_task(self): self._call_callback('pause_auto_task')
    def _stop_auto_task(self): self._call_callback('stop_auto_task')
    def _save_task_points(self): self._call_callback('save_task_points')
    def _load_task_points(self): self._call_callback('load_task_points')

    # --- UI 更新方法 ---
    def update_ports_list(self, ports):
        """更新端口列表"""
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_combo.current(0)
    
    def update_connection_status(self, connected, status_text):
        """更新连接状态及按钮样式"""
        self.status_var.set(status_text)
        if connected:
            self.connect_btn.config(text="🔌 断开", bootstyle="danger")
        else:
            self.connect_btn.config(text="🔗 连接", bootstyle="success")
    
    def update_angles_display(self, angles):
        """更新所有角度变量"""
        for i, angle in enumerate(angles):
            if i < len(self.angle_vars):
                self.angle_vars[i].set(round(angle, 1))
    
    def update_task_list(self, tree, points):
        """通用方法，更新Treeview中的任务点"""
        # 清空现有内容
        for item in tree.get_children():
            tree.delete(item)
        # 插入新内容
        for i, point in enumerate(points):
            coord_str = f"({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})"
            tree.insert("", END, iid=i, values=(coord_str,))

    def update_pickup_listbox(self, points):
        """更新抓取点列表"""
        self.update_task_list(self.pickup_tree, points)
    
    def update_place_listbox(self, points):
        """更新放置点列表"""
        self.update_task_list(self.place_tree, points)

    def get_selected_task_index(self, tree):
        """获取Treeview中选中项的索引"""
        selection = tree.focus()
        return int(selection) if selection else -1

    def update_task_status(self, state, step):
        """更新任务状态显示和按钮可用性"""
        self.task_status_var.set(state.value)
        self.task_step_var.set(step.value if hasattr(step, 'value') else str(step))
        
        is_running = (state == TaskState.RUNNING)
        is_paused = (state == TaskState.PAUSED)
        is_idle = (state == TaskState.IDLE or state == TaskState.COMPLETED or state == TaskState.ERROR)
        
        self.start_task_btn.config(state=DISABLED if (is_running or is_paused) else NORMAL)
        self.pause_task_btn.config(state=NORMAL if (is_running or is_paused) else DISABLED)
        self.stop_task_btn.config(state=NORMAL if (is_running or is_paused) else DISABLED)
        
        if is_paused:
            self.pause_task_btn.config(text="▶️ 恢复")
        else:
            self.pause_task_btn.config(text="⏸️ 暂停")
            
    def update_task_progress(self, current, total):
        """更新任务进度"""
        self.task_progress_var.set(f"{current}/{total}")
        
    def get_point_from_dialog(self, title, initial_values=None):
        """显示一个对话框来获取或编辑坐标点"""
        if initial_values is None:
            initial_values = [self.x_var.get(), self.y_var.get(), self.z_var.get()]
        
        # 使用 ttkbootstrap 的 Dialog
        dialog = ttk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        ttk.Label(main_frame, text=title, font=self.font(14, 'bold'), bootstyle=PRIMARY).pack(pady=(0, 20))
        
        result = {} # 用于存储结果

        # 输入字段
        x_var = ttk.DoubleVar(value=initial_values[0])
        y_var = ttk.DoubleVar(value=initial_values[1])
        z_var = ttk.DoubleVar(value=initial_values[2])
        
        coords = [("X 坐标 (mm):", x_var), ("Y 坐标 (mm):", y_var), ("Z 坐标 (mm):", z_var)]
        for label, var in coords:
            row = ttk.Frame(main_frame)
            row.pack(fill=X, pady=5)
            ttk.Label(row, text=label, width=12).pack(side=LEFT)
            ttk.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=YES, padx=5)

        # 按钮
        btn_frame = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        btn_frame.pack(fill=X)

        def on_ok():
            result['point'] = (x_var.get(), y_var.get(), z_var.get())
            dialog.destroy()

        ttk.Button(btn_frame, text="✅ 确定", command=on_ok, bootstyle="success").pack(side=LEFT, expand=YES, padx=5)
        ttk.Button(btn_frame, text="❌ 取消", command=dialog.destroy, bootstyle="danger-outline").pack(side=LEFT, expand=YES, padx=5)

        dialog.wait_window()
        return result.get('point')
