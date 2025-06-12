#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5DOF+1夹具机械臂上位机控制程序 v2.0
主程序文件 - 集成所有模块，提供完整的机械臂控制功能

Author: Robot Arm Control System
Version: 2.0
Date: 2024
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os
import threading
import time

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入自定义模块
try:
    from config import (DEFAULT_ANGLES, DEFAULT_TARGET_POSITION, TaskState, 
                       AUTO_TASK_DEFAULTS, UI_THEME, GRIPPER_OPEN, GRIPPER_CLOSE)
    from kinematics import KinematicsCalculator
    from communication import SerialCommunicator
    from automation import AutomationController
    from visualization import Visualization3D
    from ui_components import ModernUI
    from utils import (settings_manager, task_points_manager, log_manager, 
                      ValidationHelper, MessageHelper, performance_monitor)
    from font_setup import setup_fonts
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有模块文件都在同一目录下")
    sys.exit(1)

class RobotArmControllerApp:
    """5DOF机械臂控制器主应用程序"""
    
    def __init__(self):
        """初始化应用程序"""
        # 记录启动时间
        performance_monitor.start_timer("app_startup")
        
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.withdraw()  # 先隐藏窗口
        
        # 显示启动画面
        self.show_splash_screen()
        
        # 初始化核心组件
        self.init_core_components()
        
        # 初始化UI组件
        self.init_ui_components()
        
        # 初始化可视化组件
        self.init_visualization()
        
        # 连接回调函数
        self.connect_callbacks()
        
        # 加载设置
        self.load_application_settings()
        
        # 设置应用程序事件处理
        self.setup_event_handlers()
        
        # 隐藏启动画面并显示主窗口
        self.hide_splash_screen()
        
        # 记录启动完成时间
        startup_time = performance_monitor.end_timer("app_startup")
        log_manager.info(f"应用程序启动完成，耗时: {startup_time:.2f}秒")
        
    def show_splash_screen(self):
        """显示启动画面"""
        self.splash = tk.Toplevel()
        self.splash.title("加载中...")
        self.splash.geometry("400x300")
        self.splash.configure(bg=UI_THEME['primary_color'])
        self.splash.resizable(False, False)
        
        # 居中显示
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (self.splash.winfo_width() // 2)
        y = (self.splash.winfo_screenheight() // 2) - (self.splash.winfo_height() // 2)
        self.splash.geometry(f"+{x}+{y}")
        
        # 添加启动内容
        tk.Label(self.splash, text="🤖", font=("Arial", 48), 
                bg=UI_THEME['primary_color'], fg="white").pack(pady=20)
        
        tk.Label(self.splash, text="5DOF机械臂上位机", 
                font=(UI_THEME['font_family'], 16, 'bold'),
                bg=UI_THEME['primary_color'], fg="white").pack(pady=10)
        
        tk.Label(self.splash, text="版本 2.0", 
                font=(UI_THEME['font_family'], 12),
                bg=UI_THEME['primary_color'], fg="white").pack()
        
        self.loading_label = tk.Label(self.splash, text="正在初始化组件...", 
                                     font=(UI_THEME['font_family'], 10),
                                     bg=UI_THEME['primary_color'], fg="white")
        self.loading_label.pack(pady=20)
        
        # 进度条
        progress_frame = tk.Frame(self.splash, bg=UI_THEME['primary_color'])
        progress_frame.pack(pady=10)
        
        self.progress_canvas = tk.Canvas(progress_frame, width=300, height=20, 
                                        bg="white", highlightthickness=0)
        self.progress_canvas.pack()
        
        self.splash.update()
        
    def update_splash_progress(self, text, progress):
        """更新启动画面进度"""
        self.loading_label.config(text=text)
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, progress * 3, 20, 
                                            fill=UI_THEME['success_color'], outline="")
        self.splash.update()
        
    def hide_splash_screen(self):
        """隐藏启动画面"""
        self.splash.destroy()
        self.root.deiconify()
        
    def init_core_components(self):
        """初始化核心组件"""
        self.update_splash_progress("初始化运动学计算器...", 20)
        
        # 运动学计算器
        self.kinematics = KinematicsCalculator()
        log_manager.info("运动学计算器初始化完成")
        
        self.update_splash_progress("初始化串口通信...", 40)
        
        # 串口通信器
        self.communicator = SerialCommunicator(
            status_callback=self.on_connection_status_changed,
            data_callback=self.on_serial_data_received
        )
        log_manager.info("串口通信器初始化完成")
        
        self.update_splash_progress("初始化自动化控制器...", 60)
        
        # 自动化控制器
        self.automation = AutomationController(
            kinematics_calc=self.kinematics,
            communicator=self.communicator,
            status_callback=self.on_task_status_changed,
            progress_callback=self.on_task_progress_changed
        )
        log_manager.info("自动化控制器初始化完成")
        
        # 当前状态
        self.current_angles = DEFAULT_ANGLES.copy()
        
    def init_ui_components(self):
        """初始化UI组件"""
        self.update_splash_progress("初始化字体配置...", 70)
        
        # 设置字体
        self.font_manager = setup_fonts()
        
        self.update_splash_progress("初始化用户界面...", 80)
        
        # 创建UI组件
        self.ui = ModernUI(self.root, callbacks=self.get_ui_callbacks(), font_manager=self.font_manager)
        log_manager.info("用户界面初始化完成")
        
    def init_visualization(self):
        """初始化可视化组件"""
        self.update_splash_progress("初始化3D可视化...", 90)
        
        # 创建3D可视化
        self.visualization = Visualization3D(self.ui.viz_frame, self.kinematics)
        log_manager.info("3D可视化初始化完成")
        
    def get_ui_callbacks(self):
        """获取UI回调函数字典"""
        return {
            # 串口连接相关
            'refresh_ports': self.refresh_serial_ports,
            'toggle_connection': self.toggle_serial_connection,
            
            # 位置控制相关
            'target_position_change': self.on_target_position_change,
            'calculate_angles': self.calculate_inverse_kinematics,
            'send_position_command': self.send_position_command,
            'toggle_target_display': self.toggle_target_display,
            
            # 手动控制相关
            'angle_change': self.on_servo_angle_change,
            'reset_position': self.reset_robot_position,
            'send_manual_command': self.send_manual_command,
            'control_gripper': self.control_gripper,
            'send_custom_command': self.send_custom_command,
            
            # 自动化任务相关
            'add_current_as_pickup': self.add_current_position_as_pickup,
            'add_current_as_place': self.add_current_position_as_place,
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
        """连接回调函数"""
        self.update_splash_progress("连接回调函数...", 95)
        
        # 设置自动化控制器的当前角度引用
        self.automation.current_angles = self.current_angles
        
    def load_application_settings(self):
        """加载应用程序设置"""
        self.update_splash_progress("加载设置...", 98)
        
        success, settings = settings_manager.load_settings()
        if success:
            try:
                # 恢复串口设置
                self.ui.port_var.set(settings.get('port', ''))
                
                # 恢复当前角度
                saved_angles = settings.get('current_angles')
                if saved_angles is not None:
                    self.current_angles = list(saved_angles)  # 创建新列表
                else:
                    self.current_angles = DEFAULT_ANGLES.copy()  # 使用副本
                
                self.ui.update_angles_display(self.current_angles)
                
                # 恢复目标位置
                target_pos = settings.get('target_position', DEFAULT_TARGET_POSITION)
                self.ui.x_var.set(target_pos[0])
                self.ui.y_var.set(target_pos[1])
                self.ui.z_var.set(target_pos[2])
                
                # 恢复其他设置
                self.ui.speed_var.set(settings.get('speed', 2))
                self.ui.show_target_var.set(settings.get('show_target', True))
                
                # 恢复自动化任务设置
                auto_params = settings.get('auto_parameters', AUTO_TASK_DEFAULTS)
                self.ui.safe_height_var.set(auto_params.get('safe_height', 250.0))
                self.ui.height_offset_var.set(auto_params.get('height_offset', 30.0))
                self.ui.grip_delay_var.set(auto_params.get('grip_delay', 2.0))
                self.ui.move_delay_var.set(auto_params.get('move_delay', 3.0))
                self.ui.return_home_var.set(auto_params.get('return_home', True))
                
                # 恢复任务点
                pickup_points = settings.get('pickup_points', [])
                place_points = settings.get('place_points', [])
                for point in pickup_points:
                    self.automation.add_pickup_point(point)
                for point in place_points:
                    self.automation.add_place_point(point)
                
                self.ui.update_pickup_listbox(self.automation.pickup_points)
                self.ui.update_place_listbox(self.automation.place_points)
                
                # 恢复窗口几何信息
                geometry = settings.get('window_geometry', '1216x640')
                self.root.geometry(geometry)
                
                log_manager.info("设置加载完成")
                
            except Exception as e:
                log_manager.error(f"加载设置时发生错误: {e}")
                MessageHelper.show_warning("设置加载", "部分设置加载失败，将使用默认设置")
        
        # 刷新端口列表
        self.refresh_serial_ports()
        
        # 更新可视化
        self.update_visualization()
        
    def setup_event_handlers(self):
        """设置事件处理器"""
        self.update_splash_progress("设置事件处理器...", 100)
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_application_closing)
        
        # 定时更新任务
        self.root.after(1000, self.periodic_update)
        
    def periodic_update(self):
        """定期更新任务"""
        try:
            # 更新可视化
            if hasattr(self, 'visualization'):
                self.visualization.update_robot_state(self.current_angles)
                self.visualization.update_task_status(
                    self.automation.task_state, 
                    self.automation.current_task_index
                )
            
        except Exception as e:
            log_manager.error(f"定期更新时发生错误: {e}")
        
        # 设置下次更新
        self.root.after(1000, self.periodic_update)
        
    # ========== 串口通信相关方法 ==========
    
    def refresh_serial_ports(self):
        """刷新串口列表"""
        try:
            ports = self.communicator.get_available_ports()
            self.ui.update_ports_list(ports)
            log_manager.info(f"发现 {len(ports)} 个串口: {ports}")
        except Exception as e:
            log_manager.error(f"刷新串口列表失败: {e}")
            MessageHelper.show_error("错误", f"刷新串口列表失败: {str(e)}")
    
    def toggle_serial_connection(self):
        """切换串口连接状态"""
        try:
            if self.communicator.is_connected:
                self.communicator.disconnect()
                log_manager.info("串口已断开")
            else:
                port = self.ui.port_var.get()
                if not port:
                    MessageHelper.show_error("错误", "请选择串口")
                    return
                
                success = self.communicator.connect(port)
                if success:
                    log_manager.info(f"串口已连接: {port}")
                else:
                    log_manager.error(f"串口连接失败: {port}")
                    
        except Exception as e:
            log_manager.error(f"切换串口连接状态失败: {e}")
            MessageHelper.show_error("连接错误", f"串口操作失败: {str(e)}")
    
    def on_connection_status_changed(self, connected, status_text):
        """串口连接状态变化回调"""
        self.ui.update_connection_status(connected, status_text)
        
    def on_serial_data_received(self, data):
        """串口数据接收回调"""
        log_manager.debug(f"收到串口数据: {data}")
        
    # ========== 位置控制相关方法 ==========
    
    def on_target_position_change(self, event=None):
        """目标位置变化回调"""
        try:
            target_pos = [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()]
            
            # 验证位置
            valid, message = ValidationHelper.validate_position(target_pos)
            if valid:
                self.visualization.update_target_position(target_pos)
            
        except Exception as e:
            log_manager.error(f"更新目标位置失败: {e}")
    
    def calculate_inverse_kinematics(self):
        """计算逆运动学"""
        try:
            performance_monitor.start_timer("ik_calculation")
            
            # 获取目标位置并转换为米
            target_pos = [
                self.ui.x_var.get() / 1000,
                self.ui.y_var.get() / 1000,
                self.ui.z_var.get() / 1000
            ]
            
            # 验证目标位置
            valid, message = ValidationHelper.validate_position([p * 1000 for p in target_pos])
            if not valid:
                MessageHelper.show_error("位置错误", message)
                return
            
            # 计算逆运动学
            servo_angles, error = self.kinematics.inverse_kinematics(target_pos, DEFAULT_ANGLES.copy())
            
            # 更新界面显示
            for i in range(5):  # 不包括夹爪
                self.current_angles[i] = servo_angles[i]
            
            self.ui.update_angles_display(self.current_angles)
            
            # 更新可视化
            self.update_visualization()
            
            # 记录性能
            calc_time = performance_monitor.end_timer("ik_calculation")
            performance_monitor.log_performance("逆运动学计算", calc_time)
            
            MessageHelper.show_info("计算完成", 
                                   f"逆运动学计算完成!\n"
                                   f"目标位置: X={target_pos[0]*1000:.1f}, Y={target_pos[1]*1000:.1f}, Z={target_pos[2]*1000:.1f} mm\n"
                                   f"计算误差: {error*1000:.2f} mm\n"
                                   f"计算时间: {calc_time:.3f}s")
            
            log_manager.info(f"逆运动学计算完成，误差: {error*1000:.2f}mm")
            
        except Exception as e:
            log_manager.error(f"逆运动学计算失败: {e}")
            MessageHelper.show_error("计算错误", f"逆运动学计算失败: {str(e)}")
    
    def send_position_command(self):
        """发送位置控制指令"""
        try:
            if not self.communicator.is_connected:
                MessageHelper.show_error("错误", "请先连接串口")
                return
            
            speed = self.ui.speed_var.get()
            command = self.communicator.create_position_command(self.current_angles, speed)
            
            if MessageHelper.ask_yes_no("确认发送", f"即将发送位置指令:\n{command}\n\n确认发送吗?"):
                success, message = self.communicator.send_command(command)
                if success:
                    MessageHelper.show_info("发送成功", "位置指令发送成功!")
                    log_manager.info(f"位置指令发送成功: {command}")
                else:
                    MessageHelper.show_error("发送失败", message)
                    log_manager.error(f"位置指令发送失败: {message}")
                    
        except Exception as e:
            log_manager.error(f"发送位置指令失败: {e}")
            MessageHelper.show_error("发送错误", f"发送位置指令失败: {str(e)}")
    
    def toggle_target_display(self):
        """切换目标点显示"""
        self.update_visualization()
    
    # ========== 手动控制相关方法 ==========
    
    def on_servo_angle_change(self, servo_id, value):
        """舵机角度变化回调"""
        try:
            if isinstance(value, str):
                value = float(value)
            
            # 验证角度
            valid, message = ValidationHelper.validate_servo_angle(servo_id, value)
            if not valid:
                log_manager.warning(f"舵机{servo_id}角度无效: {message}")
                return
            
            self.current_angles[servo_id] = value
            self.ui.angle_vars[servo_id].set(value)
            
            # 更新可视化
            self.update_visualization()
            
        except Exception as e:
            log_manager.error(f"更新舵机{servo_id}角度失败: {e}")
    
    def reset_robot_position(self):
        """复位机器人位置"""
        try:
            if MessageHelper.ask_yes_no("确认复位", "确认将机械臂复位到初始位置吗?"):
                # 设置为默认角度
                self.current_angles = DEFAULT_ANGLES.copy()
                
                # 更新UI显示（确保同步）
                self.ui.update_angles_display(self.current_angles)
                self.update_visualization()
                
                # 如果连接了串口，发送复位指令
                if self.communicator.is_connected:
                    speed = self.ui.speed_var.get()
                    # ✅ 直接使用 DEFAULT_ANGLES 而不是 self.current_angles
                    print(DEFAULT_ANGLES)
                    command = self.communicator.create_servo_command(DEFAULT_ANGLES, speed)
                    success, message = self.communicator.send_command(command)
                    
                    if success:
                        MessageHelper.show_info("复位成功", "机械臂已复位到初始位置!")
                        log_manager.info("机械臂复位成功")
                    else:
                        MessageHelper.show_error("复位失败", message)
                        log_manager.error(f"机械臂复位失败: {message}")
                        
        except Exception as e:
            log_manager.error(f"复位机械臂失败: {e}")
            MessageHelper.show_error("复位错误", f"复位机械臂失败: {str(e)}")
    
    def send_manual_command(self):
        """发送手动控制指令"""
        try:
            if not self.communicator.is_connected:
                MessageHelper.show_error("错误", "请先连接串口")
                return
            
            # ✅ 修改：先同步UI到current_angles，然后使用current_angles
            # 从UI获取最新角度值
            temp_angles = []
            for i in range(6):
                temp_angles.append(self.ui.angle_vars[i].get())
            
            # 验证角度是否有效
            for i, angle in enumerate(temp_angles):
                valid, message = ValidationHelper.validate_servo_angle(i, angle)
                if not valid:
                    MessageHelper.show_error("角度错误", f"舵机{i}角度无效: {message}")
                    return
            
            # 更新current_angles
            self.current_angles = temp_angles.copy()
            
            speed = self.ui.speed_var.get()
            command = self.communicator.create_servo_command(self.current_angles, speed)
            
            if MessageHelper.ask_yes_no("确认发送", f"即将发送手动指令:\n{command}\n\n确认发送吗?"):
                success, message = self.communicator.send_command(command)
                if success:
                    MessageHelper.show_info("发送成功", "手动指令发送成功!")
                    log_manager.info(f"手动指令发送成功: {command}")
                else:
                    MessageHelper.show_error("发送失败", message)
                    log_manager.error(f"手动指令发送失败: {message}")
                    
        except Exception as e:
            log_manager.error(f"发送手动指令失败: {e}")
            MessageHelper.show_error("发送错误", f"发送手动指令失败: {str(e)}")
    
    def control_gripper(self, angle):
        """控制夹爪"""
        try:
            if not self.communicator.is_connected:
                MessageHelper.show_error("错误", "请先连接串口")
                return
            
            speed = self.ui.speed_var.get()
            command = self.communicator.create_gripper_command(angle, speed)
            
            action = "张开" if angle == GRIPPER_OPEN else "合上"
            if MessageHelper.ask_yes_no("确认操作", f"确认{action}夹爪吗?"):
                success, message = self.communicator.send_command(command)
                if success:
                    self.current_angles[5] = angle
                    self.ui.angle_vars[5].set(angle)
                    MessageHelper.show_info("夹爪控制", f"夹爪{action}指令发送成功!")
                    log_manager.info(f"夹爪{action}成功: {command}")
                else:
                    MessageHelper.show_error("夹爪控制失败", message)
                    log_manager.error(f"夹爪控制失败: {message}")
                    
        except Exception as e:
            log_manager.error(f"控制夹爪失败: {e}")
            MessageHelper.show_error("夹爪错误", f"控制夹爪失败: {str(e)}")
    
    def send_custom_command(self):
        """发送自定义指令"""
        try:
            if not self.communicator.is_connected:
                MessageHelper.show_error("错误", "请先连接串口")
                return
            
            command = self.ui.cmd_var.get().strip()
            if not command:
                MessageHelper.show_warning("警告", "请输入指令")
                return
            
            if MessageHelper.ask_yes_no("确认发送", f"即将发送自定义指令:\n{command}\n\n确认发送吗?"):
                success, message = self.communicator.send_command(command)
                if success:
                    self.ui.cmd_var.set("")  # 清空输入框
                    MessageHelper.show_info("发送成功", "自定义指令发送成功!")
                    log_manager.info(f"自定义指令发送成功: {command}")
                else:
                    MessageHelper.show_error("发送失败", message)
                    log_manager.error(f"自定义指令发送失败: {message}")
                    
        except Exception as e:
            log_manager.error(f"发送自定义指令失败: {e}")
            MessageHelper.show_error("发送错误", f"发送自定义指令失败: {str(e)}")
    
    # ========== 自动化任务相关方法 ==========
    
    def add_current_position_as_pickup(self):
        """将当前目标位置添加为抓取点"""
        try:
            point = [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()]
            
            # 验证位置
            valid, message = ValidationHelper.validate_position(point)
            if not valid:
                MessageHelper.show_error("位置错误", message)
                return
            
            self.automation.add_pickup_point(point)
            self.ui.update_pickup_listbox(self.automation.pickup_points)
            self.update_visualization()
            
            log_manager.info(f"添加抓取点: {point}")
            
        except Exception as e:
            log_manager.error(f"添加抓取点失败: {e}")
            MessageHelper.show_error("添加错误", f"添加抓取点失败: {str(e)}")
    
    def add_current_position_as_place(self):
        """将当前目标位置添加为放置点"""
        try:
            point = [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()]
            
            # 验证位置
            valid, message = ValidationHelper.validate_position(point)
            if not valid:
                MessageHelper.show_error("位置错误", message)
                return
            
            self.automation.add_place_point(point)
            self.ui.update_place_listbox(self.automation.place_points)
            self.update_visualization()
            
            log_manager.info(f"添加放置点: {point}")
            
        except Exception as e:
            log_manager.error(f"添加放置点失败: {e}")
            MessageHelper.show_error("添加错误", f"添加放置点失败: {str(e)}")
    
    def add_pickup_point(self):
        """添加抓取点"""
        try:
            point = self.ui.get_point_from_dialog("添加抓取点")
            if point:
                # 验证位置
                valid, message = ValidationHelper.validate_position(point)
                if not valid:
                    MessageHelper.show_error("位置错误", message)
                    return
                
                self.automation.add_pickup_point(point)
                self.ui.update_pickup_listbox(self.automation.pickup_points)
                self.update_visualization()
                
                log_manager.info(f"添加抓取点: {point}")
                
        except Exception as e:
            log_manager.error(f"添加抓取点失败: {e}")
            MessageHelper.show_error("添加错误", f"添加抓取点失败: {str(e)}")
    
    def edit_pickup_point(self):
        """编辑抓取点"""
        try:
            selection = self.ui.pickup_listbox.curselection()
            if not selection:
                MessageHelper.show_warning("提示", "请选择要编辑的抓取点")
                return
            
            index = selection[0]
            if index >= len(self.automation.pickup_points):
                return
            
            old_point = self.automation.pickup_points[index]
            point = self.ui.get_point_from_dialog("编辑抓取点", old_point)
            
            if point:
                # 验证位置
                valid, message = ValidationHelper.validate_position(point)
                if not valid:
                    MessageHelper.show_error("位置错误", message)
                    return
                
                self.automation.update_pickup_point(index, point)
                self.ui.update_pickup_listbox(self.automation.pickup_points)
                self.update_visualization()
                
                log_manager.info(f"编辑抓取点 {index}: {old_point} -> {point}")
                
        except Exception as e:
            log_manager.error(f"编辑抓取点失败: {e}")
            MessageHelper.show_error("编辑错误", f"编辑抓取点失败: {str(e)}")
    
    def delete_pickup_point(self):
        """删除抓取点"""
        try:
            selection = self.ui.pickup_listbox.curselection()
            if not selection:
                MessageHelper.show_warning("提示", "请选择要删除的抓取点")
                return
            
            index = selection[0]
            if index >= len(self.automation.pickup_points):
                return
            
            point = self.automation.pickup_points[index]
            if MessageHelper.ask_yes_no("确认删除", f"确认删除抓取点 {index+1}?\n坐标: {point}"):
                self.automation.remove_pickup_point(index)
                self.ui.update_pickup_listbox(self.automation.pickup_points)
                self.update_visualization()
                
                log_manager.info(f"删除抓取点 {index}: {point}")
                
        except Exception as e:
            log_manager.error(f"删除抓取点失败: {e}")
            MessageHelper.show_error("删除错误", f"删除抓取点失败: {str(e)}")
    
    def add_place_point(self):
        """添加放置点"""
        try:
            point = self.ui.get_point_from_dialog("添加放置点")
            if point:
                # 验证位置
                valid, message = ValidationHelper.validate_position(point)
                if not valid:
                    MessageHelper.show_error("位置错误", message)
                    return
                
                self.automation.add_place_point(point)
                self.ui.update_place_listbox(self.automation.place_points)
                self.update_visualization()
                
                log_manager.info(f"添加放置点: {point}")
                
        except Exception as e:
            log_manager.error(f"添加放置点失败: {e}")
            MessageHelper.show_error("添加错误", f"添加放置点失败: {str(e)}")
    
    def edit_place_point(self):
        """编辑放置点"""
        try:
            selection = self.ui.place_listbox.curselection()
            if not selection:
                MessageHelper.show_warning("提示", "请选择要编辑的放置点")
                return
            
            index = selection[0]
            if index >= len(self.automation.place_points):
                return
            
            old_point = self.automation.place_points[index]
            point = self.ui.get_point_from_dialog("编辑放置点", old_point)
            
            if point:
                # 验证位置
                valid, message = ValidationHelper.validate_position(point)
                if not valid:
                    MessageHelper.show_error("位置错误", message)
                    return
                
                self.automation.update_place_point(index, point)
                self.ui.update_place_listbox(self.automation.place_points)
                self.update_visualization()
                
                log_manager.info(f"编辑放置点 {index}: {old_point} -> {point}")
                
        except Exception as e:
            log_manager.error(f"编辑放置点失败: {e}")
            MessageHelper.show_error("编辑错误", f"编辑放置点失败: {str(e)}")
    
    def delete_place_point(self):
        """删除放置点"""
        try:
            selection = self.ui.place_listbox.curselection()
            if not selection:
                MessageHelper.show_warning("提示", "请选择要删除的放置点")
                return
            
            index = selection[0]
            if index >= len(self.automation.place_points):
                return
            
            point = self.automation.place_points[index]
            if MessageHelper.ask_yes_no("确认删除", f"确认删除放置点 {index+1}?\n坐标: {point}"):
                self.automation.remove_place_point(index)
                self.ui.update_place_listbox(self.automation.place_points)
                self.update_visualization()
                
                log_manager.info(f"删除放置点 {index}: {point}")
                
        except Exception as e:
            log_manager.error(f"删除放置点失败: {e}")
            MessageHelper.show_error("删除错误", f"删除放置点失败: {str(e)}")
    
    def start_automation_task(self):
        """开始自动化任务"""
        try:
            # 验证任务点
            valid, message = ValidationHelper.validate_task_points(
                self.automation.pickup_points, 
                self.automation.place_points
            )
            if not valid:
                MessageHelper.show_error("任务验证失败", message)
                return
            
            # 更新自动化参数
            params = {
                'safe_height': self.ui.safe_height_var.get(),
                'height_offset': self.ui.height_offset_var.get(),
                'grip_delay': self.ui.grip_delay_var.get(),
                'move_delay': self.ui.move_delay_var.get(),
                'return_home': self.ui.return_home_var.get()
            }
            self.automation.update_parameters(params)
            
            # 开始任务
            success, message = self.automation.start_task()
            if success:
                MessageHelper.show_info("任务开始", message)
                log_manager.info(f"自动化任务开始: {len(self.automation.pickup_points)} 个任务")
            else:
                MessageHelper.show_error("任务开始失败", message)
                log_manager.error(f"自动化任务开始失败: {message}")
                
        except Exception as e:
            log_manager.error(f"开始自动化任务失败: {e}")
            MessageHelper.show_error("任务错误", f"开始自动化任务失败: {str(e)}")
    
    def pause_automation_task(self):
        """暂停/恢复自动化任务"""
        try:
            is_paused = self.automation.pause_task()
            action = "暂停" if is_paused else "恢复"
            log_manager.info(f"自动化任务已{action}")
            
        except Exception as e:
            log_manager.error(f"暂停/恢复自动化任务失败: {e}")
            MessageHelper.show_error("任务控制错误", f"暂停/恢复任务失败: {str(e)}")
    
    def stop_automation_task(self):
        """停止自动化任务"""
        try:
            if MessageHelper.ask_yes_no("确认停止", "确认停止当前自动化任务吗?"):
                self.automation.stop_task()
                log_manager.info("自动化任务已停止")
                
        except Exception as e:
            log_manager.error(f"停止自动化任务失败: {e}")
            MessageHelper.show_error("任务控制错误", f"停止任务失败: {str(e)}")
    
    def save_task_points(self):
        """保存任务点"""
        try:
            if not self.automation.pickup_points and not self.automation.place_points:
                MessageHelper.show_warning("提示", "没有任务点可保存")
                return
            
            filename = filedialog.asksaveasfilename(
                title="保存任务点",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"task_points_{int(time.time())}.json"
            )
            
            if filename:
                # 获取当前参数
                params = {
                    'safe_height': self.ui.safe_height_var.get(),
                    'height_offset': self.ui.height_offset_var.get(),
                    'grip_delay': self.ui.grip_delay_var.get(),
                    'move_delay': self.ui.move_delay_var.get(),
                    'return_home': self.ui.return_home_var.get()
                }
                
                success, message = task_points_manager.save_task_points(
                    self.automation.pickup_points,
                    self.automation.place_points,
                    params,
                    filename
                )
                
                if success:
                    MessageHelper.show_info("保存成功", message)
                    log_manager.info(f"任务点保存成功: {filename}")
                else:
                    MessageHelper.show_error("保存失败", message)
                    log_manager.error(f"任务点保存失败: {message}")
                    
        except Exception as e:
            log_manager.error(f"保存任务点失败: {e}")
            MessageHelper.show_error("保存错误", f"保存任务点失败: {str(e)}")
    
    def load_task_points(self):
        """加载任务点"""
        try:
            filename = filedialog.askopenfilename(
                title="加载任务点",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                success, data = task_points_manager.load_task_points(filename)
                
                if success:
                    # 清除现有任务点
                    self.automation.clear_all_points()
                    
                    # 加载新任务点
                    for point in data['pickup_points']:
                        self.automation.add_pickup_point(point)
                    for point in data['place_points']:
                        self.automation.add_place_point(point)
                    
                    # 更新界面
                    self.ui.update_pickup_listbox(self.automation.pickup_points)
                    self.ui.update_place_listbox(self.automation.place_points)
                    
                    # 更新参数
                    params = data['parameters']
                    self.ui.safe_height_var.set(params.get('safe_height', 250.0))
                    self.ui.height_offset_var.set(params.get('height_offset', 30.0))
                    self.ui.grip_delay_var.set(params.get('grip_delay', 2.0))
                    self.ui.move_delay_var.set(params.get('move_delay', 3.0))
                    self.ui.return_home_var.set(params.get('return_home', True))
                    
                    # 更新可视化
                    self.update_visualization()
                    
                    count_pickup = len(self.automation.pickup_points)
                    count_place = len(self.automation.place_points)
                    version = data.get('version', '1.0')
                    created_time = data.get('created_time', '未知')
                    
                    MessageHelper.show_info("加载成功", 
                                           f"任务点加载成功!\n"
                                           f"版本: {version}\n"
                                           f"创建时间: {created_time}\n"
                                           f"抓取点: {count_pickup} 个\n"
                                           f"放置点: {count_place} 个")
                    
                    log_manager.info(f"任务点加载成功: {filename}, 抓取点: {count_pickup}, 放置点: {count_place}")
                    
                else:
                    MessageHelper.show_error("加载失败", data)
                    log_manager.error(f"任务点加载失败: {data}")
                    
        except Exception as e:
            log_manager.error(f"加载任务点失败: {e}")
            MessageHelper.show_error("加载错误", f"加载任务点失败: {str(e)}")
    
    def on_task_status_changed(self, state, step):
        """任务状态变化回调"""
        self.ui.update_task_status(state, step)
        log_manager.info(f"任务状态变化: {state.value}, 步骤: {step.value}")
        
        # 根据状态显示不同的消息
        if state == TaskState.COMPLETED:
            MessageHelper.show_info("任务完成", "所有自动化任务已成功完成!")
        elif state == TaskState.ERROR:
            MessageHelper.show_error("任务错误", "自动化任务执行过程中发生错误!")
    
    def on_task_progress_changed(self, current, total):
        """任务进度变化回调"""
        self.ui.update_task_progress(current, total)
    
    # ========== 可视化相关方法 ==========
    
    def update_visualization(self):
        """更新3D可视化"""
        try:
            # 更新机械臂状态
            self.visualization.update_robot_state(self.current_angles)
            
            # 更新目标位置
            target_pos = [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()]
            self.visualization.update_target_position(target_pos)
            
            # 更新任务点
            self.visualization.update_task_points(
                self.automation.pickup_points,
                self.automation.place_points
            )
            
            # 更新任务状态
            self.visualization.update_task_status(
                self.automation.task_state,
                self.automation.current_task_index
            )
            
        except Exception as e:
            log_manager.error(f"更新可视化失败: {e}")
    
    # ========== 应用程序生命周期方法 ==========
    
    def save_application_settings(self):
        """保存应用程序设置"""
        try:
            # 收集所有设置
            settings = {
                'port': self.ui.port_var.get(),
                'current_angles': self.current_angles,
                'target_position': [self.ui.x_var.get(), self.ui.y_var.get(), self.ui.z_var.get()],
                'speed': self.ui.speed_var.get(),
                'show_target': self.ui.show_target_var.get(),
                'pickup_points': self.automation.pickup_points,
                'place_points': self.automation.place_points,
                'auto_parameters': {
                    'safe_height': self.ui.safe_height_var.get(),
                    'height_offset': self.ui.height_offset_var.get(),
                    'grip_delay': self.ui.grip_delay_var.get(),
                    'move_delay': self.ui.move_delay_var.get(),
                    'return_home': self.ui.return_home_var.get()
                },
                'window_geometry': self.root.geometry()
            }
            
            success, message = settings_manager.save_settings(**settings)
            if success:
                log_manager.info("应用程序设置保存成功")
            else:
                log_manager.error(f"应用程序设置保存失败: {message}")
                
        except Exception as e:
            log_manager.error(f"保存应用程序设置失败: {e}")
    
    def on_application_closing(self):
        """应用程序关闭时的处理"""
        try:
            # 停止自动化任务
            if self.automation.task_state in [TaskState.RUNNING, TaskState.PAUSED]:
                if MessageHelper.ask_yes_no("任务正在执行", "有自动化任务正在执行，确认退出吗?"):
                    self.automation.stop_task()
                else:
                    return
            
            # 保存设置
            self.save_application_settings()
            
            # 断开串口连接
            if self.communicator.is_connected:
                self.communicator.disconnect()
                log_manager.info("串口连接已断开")
            
            log_manager.info("应用程序正常退出")
            
            # 关闭窗口
            self.root.destroy()
            
        except Exception as e:
            log_manager.error(f"应用程序关闭时发生错误: {e}")
            self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        try:
            log_manager.info("应用程序开始运行")
            self.root.mainloop()
        except Exception as e:
            log_manager.error(f"应用程序运行时发生错误: {e}")
            MessageHelper.show_error("应用程序错误", f"应用程序运行时发生错误: {str(e)}")

def main():
    """主函数"""
    print("=" * 60)
    print("5DOF机械臂上位机")
    print("=" * 60)
    print("正在启动应用程序...")
    
    # 检查依赖
    try:
        import numpy
        import matplotlib
        import ikpy
        import serial
        print("✅ 所有依赖包检查通过")
    except ImportError as e:
        print(f"❌ 依赖包检查失败: {e}")
        print("\n请安装以下依赖包:")
        print("pip install pyserial numpy matplotlib ikpy")
        input("按任意键退出...")
        return
    
    try:
        # 创建应用程序实例
        app = RobotArmControllerApp()
        
        # 运行应用程序
        app.run()
        
    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        log_manager.error(f"应用程序启动失败: {e}")
        
        # 显示错误信息
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", f"应用程序启动失败:\n{str(e)}\n\n请检查依赖包是否正确安装。")
        except:
            pass
        
        input("按任意键退出...")

if __name__ == "__main__":
    main()