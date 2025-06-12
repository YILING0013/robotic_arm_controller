#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5DOF+1夹具机械臂上位机控制程序
主程序文件 - 使用 ttkbootstrap 和现代化UI设计
"""

import sys
import os
import time

# 确保模块可以被正确导入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入 ttkbootstrap 和标准库
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

# 导入自定义模块
try:
    from config import (DEFAULT_THEME, DEFAULT_ANGLES, DEFAULT_TARGET_POSITION, TaskState, 
                       AUTO_TASK_DEFAULTS, GRIPPER_OPEN, GRIPPER_CLOSE)
    from kinematics import KinematicsCalculator
    from communication import SerialCommunicator
    from automation import AutomationController
    from visualization import Visualization3D
    from ui_components import ModernUI
    from utils import (settings_manager, task_points_manager, log_manager, 
                      ValidationHelper, MessageHelper, performance_monitor)
    from font_setup import setup_fonts
except ImportError as e:
    print(f"❌ 导入模块失败: {e}\n请确保所有 .py 文件都在同一个目录下。")
    sys.exit(1)

class RobotArmControllerApp:
    """5DOF机械臂控制器主应用程序 """
    
    def __init__(self):
        """初始化应用程序"""
        performance_monitor.start_timer("app_startup")
        
        # 1. 字体和主题初始化
        self.font_manager = setup_fonts()
        self.root = ttk.Window(themename=DEFAULT_THEME)
        self.root.withdraw()

        # 2. 显示启动画面
        self.show_splash_screen()

        # 3. 初始化核心组件
        self.init_core_components()
        
        # 4. 初始化UI和可视化
        self.ui = ModernUI(self.root, callbacks=self.get_ui_callbacks(), font_manager=self.font_manager)
        # 修正: 将 self.ui 实例传递给 Visualization3D
        self.visualization = Visualization3D(self.ui.viz_frame, self.kinematics, self.font_manager, self.ui)
        
        # 5. 连接回调并加载设置
        self.connect_callbacks()
        self.load_application_settings()
        self.setup_event_handlers()
        
        # 6. 完成启动
        self.hide_splash_screen()
        startup_time = performance_monitor.end_timer("app_startup")
        log_manager.info(f"应用程序启动完成，耗时: {startup_time:.2f}秒")
        
    def show_splash_screen(self):
        """显示现代化的启动画面"""
        self.splash = ttk.Toplevel(self.root)
        self.splash.overrideredirect(True) # 无边框窗口
        width, height = 450, 300
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.splash.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

        style = ttk.Style.get_instance()
        bg_color = style.colors.primary
        fg_color = style.colors.get('light')
        self.splash.configure(bg=bg_color)
        
        ttk.Label(self.splash, text="🤖", font=("", 60), background=bg_color, foreground=fg_color).pack(pady=(30, 10))
        ttk.Label(self.splash, text="5DOF机械臂上位机", font=("", 18, 'bold'), background=bg_color, foreground=fg_color).pack()
        ttk.Label(self.splash, text="UI Enhanced ", font=("", 10), background=bg_color, foreground=style.colors.secondary).pack(pady=5)
        
        self.loading_label = ttk.Label(self.splash, text="正在初始化...", font=("", 10), background=bg_color, foreground=fg_color)
        self.loading_label.pack(pady=(30, 5))
        
        self.progress = ttk.Progressbar(self.splash, mode='determinate', length=350, bootstyle="success-striped")
        self.progress.pack(pady=10)
        self.splash.update()
        
    def update_splash(self, text, value):
        """更新启动画面进度"""
        self.loading_label.config(text=text)
        self.progress['value'] = value
        self.splash.update()
        time.sleep(0.1) # 模拟加载
        
    def hide_splash_screen(self):
        """隐藏启动画面并显示主窗口"""
        self.splash.destroy()
        self.root.deiconify()

    def init_core_components(self):
        """初始化核心业务逻辑组件"""
        self.update_splash("初始化运动学计算器...", 20)
        self.kinematics = KinematicsCalculator()
        
        self.update_splash("初始化串口通信...", 40)
        self.communicator = SerialCommunicator(self.on_connection_status_changed)
        
        self.update_splash("初始化自动化控制器...", 60)
        self.automation = AutomationController(self.kinematics, self.communicator, self.on_task_status_changed, self.on_task_progress_changed)
        
        self.current_angles = DEFAULT_ANGLES.copy()

    def get_ui_callbacks(self):
        """返回所有UI回调函数的字典"""
        return {
            'refresh_ports': self.refresh_serial_ports,
            'toggle_connection': self.toggle_serial_connection,
            'target_position_change': self.on_target_position_change,
            'calculate_angles': self.calculate_inverse_kinematics,
            'send_position_command': self.send_position_command,
            'toggle_target_display': self.update_visualization,
            'angle_change': self.on_servo_angle_change,
            'reset_position': self.reset_robot_position,
            'send_manual_command': self.send_manual_command,
            'control_gripper': self.control_gripper,
            'send_custom_command': self.send_custom_command,
            'toggle_keyboard_control': self.toggle_keyboard_control,
            'add_pickup_point': self.add_pickup_point,
            'edit_pickup_point': self.edit_pickup_point,
            'delete_pickup_point': self.delete_pickup_point,
            'add_place_point': self.add_place_point,
            'edit_place_point': self.edit_place_point,
            'delete_place_point': self.delete_place_point,
            'start_auto_task': self.start_automation_task,
            'pause_auto_task': self.pause_automation_task,
            'stop_auto_task': self.stop_automation_task,
            'save_task_points': self.save_task_points,
            'load_task_points': self.load_task_points,
        }
        
    def connect_callbacks(self):
        """连接核心逻辑与UI/可视化"""
        self.update_splash("连接组件...", 80)
        self.automation.current_angles = self.current_angles

    def load_application_settings(self):
        """加载应用设置"""
        self.update_splash("加载设置...", 90)
        success, settings = settings_manager.load_settings()
        if not success:
            MessageHelper.show_warning("加载失败", "无法加载配置文件，将使用默认设置。")
            return

        try:
            self.ui.port_var.set(settings.get('port', ''))
            self.current_angles = settings.get('current_angles', DEFAULT_ANGLES)
            target_pos = settings.get('target_position', DEFAULT_TARGET_POSITION)
            self.ui.x_var.set(target_pos[0])
            self.ui.y_var.set(target_pos[1])
            self.ui.z_var.set(target_pos[2])
            self.ui.speed_var.set(settings.get('speed', 2))
            self.ui.show_target_var.set(settings.get('show_target', True))
            self.ui.step_size_var.set(settings.get('keyboard_step_size', 5.0))
            
            auto_params = settings.get('auto_parameters', AUTO_TASK_DEFAULTS)
            self.ui.safe_height_var.set(auto_params.get('safe_height'))
            self.ui.height_offset_var.set(auto_params.get('height_offset'))
            self.ui.grip_delay_var.set(auto_params.get('grip_delay'))
            self.ui.move_delay_var.set(auto_params.get('move_delay'))
            self.ui.return_home_var.set(auto_params.get('return_home'))
            
            self.automation.pickup_points = settings.get('pickup_points', [])
            self.automation.place_points = settings.get('place_points', [])
            
            self.root.geometry(settings.get('window_geometry', '1400x850'))
            
            self.ui.update_angles_display(self.current_angles)
            self.ui.update_pickup_listbox(self.automation.pickup_points)
            self.ui.update_place_listbox(self.automation.place_points)
            
            self.refresh_serial_ports()
            self.update_visualization()
            log_manager.info("应用设置加载完成。")
        except Exception as e:
            log_manager.error(f"加载设置时出错: {e}")
            MessageHelper.show_error("加载错误", "加载设置失败，部分设置可能不正确。")
            
    def setup_event_handlers(self):
        """设置事件处理器，如窗口关闭"""
        self.update_splash("完成...", 100)
        self.root.protocol("WM_DELETE_WINDOW", self.on_application_closing)
        self.root.after(500, self.periodic_visualization_update)

    def periodic_visualization_update(self):
        """定期更新可视化，避免不必要的重绘"""
        self.update_visualization()
        self.root.after(500, self.periodic_visualization_update)
        
    # ========== 回调方法实现 ==========
    
    def refresh_serial_ports(self):
        ports = self.communicator.get_available_ports()
        self.ui.update_ports_list(ports)
    
    def toggle_serial_connection(self):
        if self.communicator.is_connected:
            self.communicator.disconnect()
        else:
            port = self.ui.port_var.get()
            if not port:
                MessageHelper.show_error("错误", "请选择一个串口。")
                return
            self.communicator.connect(port)
    
    def on_connection_status_changed(self, connected, status_text):
        self.ui.update_connection_status(connected, status_text)
        log_manager.info(f"连接状态: {status_text}")
    
    def on_target_position_change(self):
        self.update_visualization()
        
    def calculate_inverse_kinematics(self):
        try:
            target_pos_mm = [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()]
            if not ValidationHelper.validate_position(target_pos_mm)[0]:
                MessageHelper.show_error("位置错误", ValidationHelper.validate_position(target_pos_mm)[1])
                return
            
            target_pos_m = [p / 1000.0 for p in target_pos_mm]
            servo_angles, error = self.kinematics.inverse_kinematics(target_pos_m, self.current_angles.copy())
            
            if error > 0.05: # 5cm 误差阈值
                MessageHelper.show_warning("计算警告", f"无法精确到达该位置，误差较大 ({error*1000:.1f} mm)。")

            for i in range(5): self.current_angles[i] = servo_angles[i]
            self.ui.update_angles_display(self.current_angles)
            self.update_visualization()
            MessageHelper.show_info("计算完成", f"逆解计算完成，误差: {error*1000:.2f} mm")
        except Exception as e:
            MessageHelper.show_error("计算错误", f"逆运动学计算失败: {e}")

    def send_command(self, create_command_func, *args):
        """通用发送指令方法"""
        if not self.communicator.is_connected:
            MessageHelper.show_error("错误", "请先连接串口。")
            return
        
        command = create_command_func(*args)
        success, msg = self.communicator.send_command(command)
        if not success:
            MessageHelper.show_error("发送失败", msg)
        return success
        
    def send_position_command(self):
        self.send_command(self.communicator.create_position_command, self.current_angles, self.ui.speed_var.get())
        
    def send_manual_command(self):
        angles = [var.get() for var in self.ui.angle_vars]
        self.current_angles = angles
        if self.send_command(self.communicator.create_servo_command, angles, self.ui.speed_var.get()):
            self.update_visualization()

    def on_servo_angle_change(self, servo_id, value):
        self.current_angles[int(servo_id)] = float(value)
        self.update_visualization()
        
    def reset_robot_position(self):
        if MessageHelper.ask_yes_no("确认", "确定要将机械臂复位到初始位置吗?"):
            self.current_angles = DEFAULT_ANGLES.copy()
            self.ui.update_angles_display(self.current_angles)
            self.send_command(self.communicator.create_servo_command, self.current_angles, self.ui.speed_var.get())
            self.update_visualization()

    def control_gripper(self, angle):
        if self.send_command(self.communicator.create_gripper_command, angle, self.ui.speed_var.get()):
            self.current_angles[5] = angle
            self.ui.angle_vars[5].set(angle)

    def send_custom_command(self):
        cmd = self.ui.cmd_var.get().strip()
        if cmd:
            self.send_command(lambda c: c, cmd) # 传递自身
        else:
            MessageHelper.show_warning("警告", "指令不能为空。")
            
    def toggle_keyboard_control(self, is_enabled):
        if is_enabled:
            self.root.bind('<KeyPress>', self.on_key_press)
            MessageHelper.show_info("键盘控制", "键盘控制已启用。\nWASD:水平移动, ↑↓:垂直移动, Q/F:夹爪")
        else:
            self.root.unbind('<KeyPress>')
            
    def on_key_press(self, event):
        key = event.keysym.lower()
        step = self.ui.step_size_var.get()
        dx, dy, dz = 0, 0, 0
        
        actions = {'w': (0, step, 0), 's': (0, -step, 0), 'a': (-step, 0, 0), 'd': (step, 0, 0),
                   'up': (0, 0, step), 'down': (0, 0, -step)}
        
        if key in actions:
            dx, dy, dz = actions[key]
            self.ui.x_var.set(self.ui.x_var.get() + dx)
            self.ui.y_var.set(self.ui.y_var.get() + dy)
            self.ui.z_var.set(self.ui.z_var.get() + dz)
            self.calculate_inverse_kinematics()
            self.send_position_command()
        elif key == 'q': self.control_gripper(GRIPPER_OPEN)
        elif key == 'f': self.control_gripper(GRIPPER_CLOSE)
        elif key == 'escape': self.ui.keyboard_control_var.set(False); self.toggle_keyboard_control(False)
        
    # --- 自动化任务回调 ---
    def _manage_task_point(self, action, point_type):
        """通用任务点管理方法"""
        is_pickup = (point_type == 'pickup')
        tree = self.ui.pickup_tree if is_pickup else self.ui.place_tree
        manager_action = getattr(self.automation, f"{action}_{point_type}_point")
        
        if action in ['edit', 'delete']:
            idx = self.ui.get_selected_task_index(tree)
            if idx == -1:
                MessageHelper.show_warning("提示", f"请先选择一个要{action}的{point_type}点。")
                return
            
            if action == 'edit':
                old_point = self.automation.pickup_points[idx] if is_pickup else self.automation.place_points[idx]
                new_point = self.ui.get_point_from_dialog(f"编辑{point_type}点", old_point)
                if new_point: manager_action(idx, new_point)
            else: # delete
                if MessageHelper.ask_yes_no("确认删除", "确定要删除选中的点吗?"):
                    manager_action(idx)
        else: # add
            point = self.ui.get_point_from_dialog(f"添加{point_type}点")
            if point: manager_action(point)

        self.ui.update_pickup_listbox(self.automation.pickup_points)
        self.ui.update_place_listbox(self.automation.place_points)
        self.update_visualization()

    def add_pickup_point(self): self._manage_task_point('add', 'pickup')
    def edit_pickup_point(self): self._manage_task_point('edit', 'pickup')
    def delete_pickup_point(self): self._manage_task_point('delete', 'pickup')
    def add_place_point(self): self._manage_task_point('add', 'place')
    def edit_place_point(self): self._manage_task_point('edit', 'place')
    def delete_place_point(self): self._manage_task_point('delete', 'place')

    def start_automation_task(self):
        valid, msg = ValidationHelper.validate_task_points(self.automation.pickup_points, self.automation.place_points)
        if not valid:
            MessageHelper.show_error("任务错误", msg)
            return
        
        params = {k: v.get() for k, v in [('safe_height', self.ui.safe_height_var), ('height_offset', self.ui.height_offset_var), ('grip_delay', self.ui.grip_delay_var), ('move_delay', self.ui.move_delay_var), ('return_home', self.ui.return_home_var)]}
        self.automation.update_parameters(params)
        
        success, msg = self.automation.start_task()
        if not success: MessageHelper.show_error("任务失败", msg)

    def pause_automation_task(self): self.automation.pause_task()
    def stop_automation_task(self): self.automation.stop_task()
    
    def on_task_status_changed(self, state, step):
        self.ui.update_task_status(state, step)
        if state == TaskState.COMPLETED: MessageHelper.show_info("任务完成", "自动化任务已全部执行完毕。")
        if state == TaskState.ERROR: MessageHelper.show_error("任务错误", "任务执行中断。")

    def on_task_progress_changed(self, current, total):
        self.ui.update_task_progress(current, total)
        
    def save_task_points(self):
        filename = filedialog.asksaveasfilename(title="保存任务", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not filename: return
        params = {k: v.get() for k, v in [('safe_height', self.ui.safe_height_var), ('height_offset', self.ui.height_offset_var), ('grip_delay', self.ui.grip_delay_var), ('move_delay', self.ui.move_delay_var), ('return_home', self.ui.return_home_var)]}
        success, msg = task_points_manager.save_task_points(self.automation.pickup_points, self.automation.place_points, params, filename)
        MessageHelper.show_info("保存", msg)

    def load_task_points(self):
        filename = filedialog.askopenfilename(title="加载任务", filetypes=[("JSON", "*.json")])
        if not filename: return
        success, data = task_points_manager.load_task_points(filename)
        if not success:
            MessageHelper.show_error("加载失败", data)
            return

        self.automation.clear_all_points()
        self.automation.pickup_points = data.get('pickup_points', [])
        self.automation.place_points = data.get('place_points', [])
        
        params = data.get('parameters', AUTO_TASK_DEFAULTS)
        self.ui.safe_height_var.set(params.get('safe_height'))
        self.ui.height_offset_var.set(params.get('height_offset'))
        self.ui.grip_delay_var.set(params.get('grip_delay'))
        self.ui.move_delay_var.set(params.get('move_delay'))
        self.ui.return_home_var.set(params.get('return_home'))
        
        self.ui.update_pickup_listbox(self.automation.pickup_points)
        self.ui.update_place_listbox(self.automation.place_points)
        self.update_visualization()
        MessageHelper.show_info("加载成功", f"成功加载 {len(self.automation.pickup_points)} 个任务点。")

    # --- 可视化与应用生命周期 ---

    def update_visualization(self):
        self.visualization.update_robot_state(self.current_angles)
        self.visualization.update_target_position([self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()])
        self.visualization.update_task_points(self.automation.pickup_points, self.automation.place_points)
        self.visualization.update_task_status(self.automation.task_state, self.automation.current_task_index)
        self.visualization.update_display()
        
    def on_application_closing(self):
        if self.automation.is_task_running():
            if not MessageHelper.ask_yes_no("任务正在执行", "有任务正在运行，确定要退出吗?"):
                return
            self.automation.stop_task()
        
        settings_to_save = {
            'port': self.ui.port_var.get(), 'current_angles': self.current_angles,
            'target_position': [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()],
            'speed': self.ui.speed_var.get(), 'show_target': self.ui.show_target_var.get(),
            'keyboard_step_size': self.ui.step_size_var.get(),
            'pickup_points': self.automation.pickup_points, 'place_points': self.automation.place_points,
            'auto_parameters': {k: v.get() for k, v in [('safe_height', self.ui.safe_height_var), ('height_offset', self.ui.height_offset_var), ('grip_delay', self.ui.grip_delay_var), ('move_delay', self.ui.move_delay_var), ('return_home', self.ui.return_home_var)]},
            'window_geometry': self.root.geometry()
        }
        settings_manager.save_settings(**settings_to_save)
        
        if self.communicator.is_connected: self.communicator.disconnect()
        log_manager.info("应用程序正常关闭。")
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

def main():
    """主函数入口"""
    try:
        app = RobotArmControllerApp()
        app.run()
    except Exception as e:
        log_manager.error(f"应用程序启动时发生致命错误: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("致命错误", f"应用程序无法启动: {e}")

if __name__ == "__main__":
    main()
