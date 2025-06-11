#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化任务执行模块 - 处理机械臂的自动化抓取放置任务
"""

import threading
import time
import json
from config import TaskState, AutoTaskStep, AUTO_TASK_DEFAULTS, GRIPPER_OPEN, GRIPPER_CLOSE, DEFAULT_ANGLES

class AutomationController:
    """自动化任务控制器"""
    
    def __init__(self, kinematics_calc, communicator, status_callback=None, progress_callback=None):
        self.kinematics = kinematics_calc
        self.communicator = communicator
        self.status_callback = status_callback      # 状态更新回调
        self.progress_callback = progress_callback  # 进度更新回调
        
        # 任务点
        self.pickup_points = []
        self.place_points = []
        
        # 任务状态
        self.task_state = TaskState.IDLE
        self.current_task_index = 0
        self.current_step = AutoTaskStep.MOVE_TO_SAFE_HEIGHT
        self.auto_task_thread = None
        
        # 控制标志
        self.task_stop_flag = False
        self.task_pause_flag = False
        
        # 任务参数
        self.safe_height = AUTO_TASK_DEFAULTS['safe_height']
        self.pickup_height_offset = AUTO_TASK_DEFAULTS['height_offset']
        self.place_height_offset = AUTO_TASK_DEFAULTS['height_offset']
        self.grip_delay = AUTO_TASK_DEFAULTS['grip_delay']
        self.move_delay = AUTO_TASK_DEFAULTS['move_delay']
        self.auto_speed = AUTO_TASK_DEFAULTS['auto_speed']
        self.return_home = AUTO_TASK_DEFAULTS['return_home']
        
        # 当前角度
        self.current_angles = DEFAULT_ANGLES.copy()
        
    def add_pickup_point(self, point):
        """添加抓取点"""
        self.pickup_points.append(tuple(point))
        
    def add_place_point(self, point):
        """添加放置点"""
        self.place_points.append(tuple(point))
        
    def remove_pickup_point(self, index):
        """删除抓取点"""
        if 0 <= index < len(self.pickup_points):
            del self.pickup_points[index]
            
    def remove_place_point(self, index):
        """删除放置点"""
        if 0 <= index < len(self.place_points):
            del self.place_points[index]
            
    def update_pickup_point(self, index, point):
        """更新抓取点"""
        if 0 <= index < len(self.pickup_points):
            self.pickup_points[index] = tuple(point)
            
    def update_place_point(self, index, point):
        """更新放置点"""
        if 0 <= index < len(self.place_points):
            self.place_points[index] = tuple(point)
            
    def clear_all_points(self):
        """清除所有点"""
        self.pickup_points.clear()
        self.place_points.clear()
        
    def update_parameters(self, params):
        """更新任务参数"""
        self.safe_height = params.get('safe_height', self.safe_height)
        self.pickup_height_offset = params.get('height_offset', self.pickup_height_offset)
        self.place_height_offset = params.get('height_offset', self.place_height_offset)
        self.grip_delay = params.get('grip_delay', self.grip_delay)
        self.move_delay = params.get('move_delay', self.move_delay)
        self.auto_speed = params.get('auto_speed', self.auto_speed)
        self.return_home = params.get('return_home', self.return_home)
        
    def start_task(self):
        """开始自动化任务"""
        if not self.pickup_points or not self.place_points:
            return False, "请至少添加一个抓取点和一个放置点!"
            
        if len(self.pickup_points) != len(self.place_points):
            return False, "抓取点和放置点数量必须相等!"
            
        if not self.communicator.is_connected:
            return False, "请先连接串口!"
            
        # 重置任务状态
        self.task_state = TaskState.RUNNING
        self.current_task_index = 0
        self.current_step = AutoTaskStep.MOVE_TO_SAFE_HEIGHT
        self.task_stop_flag = False
        self.task_pause_flag = False
        
        # 启动任务线程
        self.auto_task_thread = threading.Thread(target=self._execute_auto_task, daemon=True)
        self.auto_task_thread.start()
        
        self._update_status()
        return True, f"开始执行 {len(self.pickup_points)} 个抓取-放置任务"
        
    def pause_task(self):
        """暂停任务"""
        if self.task_state == TaskState.RUNNING:
            self.task_pause_flag = True
            self.task_state = TaskState.PAUSED
        elif self.task_state == TaskState.PAUSED:
            self.task_pause_flag = False
            self.task_state = TaskState.RUNNING
            
        self._update_status()
        return self.task_state == TaskState.PAUSED
        
    def stop_task(self):
        """停止任务"""
        self.task_stop_flag = True
        self.task_state = TaskState.IDLE
        self._update_status()
        
    def _execute_auto_task(self):
        """执行自动化任务主循环"""
        try:
            total_tasks = len(self.pickup_points)
            
            for task_index in range(total_tasks):
                if self.task_stop_flag:
                    break
                    
                self.current_task_index = task_index
                pickup_point = self.pickup_points[task_index]
                place_point = self.place_points[task_index]
                
                print(f"开始执行任务 {task_index + 1}/{total_tasks}")
                print(f"抓取点: {pickup_point}, 放置点: {place_point}")
                
                # 执行单个抓取-放置任务
                success = self._execute_single_task(pickup_point, place_point)
                
                if not success or self.task_stop_flag:
                    break
                    
            # 任务完成后返回复位点（如果启用）
            if not self.task_stop_flag and self.return_home:
                print("所有任务完成，正在返回复位点...")
                self.current_step = AutoTaskStep.RETURN_HOME
                self._update_status()
                
                success = self._return_to_home_position()
                
                if success:
                    self.current_step = AutoTaskStep.TASK_COMPLETE
                    self.task_state = TaskState.COMPLETED
                else:
                    self.task_state = TaskState.ERROR
            elif not self.task_stop_flag:
                self.current_step = AutoTaskStep.TASK_COMPLETE
                self.task_state = TaskState.COMPLETED
            else:
                self.task_state = TaskState.IDLE
                
        except Exception as e:
            print(f"任务执行错误: {e}")
            self.task_state = TaskState.ERROR
            
        finally:
            self._update_status()
            
    def _execute_single_task(self, pickup_point, place_point):
        """执行单个抓取-放置任务"""
        steps = [
            (AutoTaskStep.MOVE_TO_SAFE_HEIGHT, lambda: self._move_to_safe_height()),
            (AutoTaskStep.MOVE_TO_PICKUP_ABOVE, lambda: self._move_to_point_above(pickup_point)),
            (AutoTaskStep.MOVE_TO_PICKUP, lambda: self._move_to_point(pickup_point)),
            (AutoTaskStep.GRIP_CLOSE, lambda: self._control_gripper_auto(GRIPPER_CLOSE)),
            (AutoTaskStep.MOVE_UP_FROM_PICKUP, lambda: self._move_to_point_above(pickup_point)),
            (AutoTaskStep.MOVE_TO_PLACE_ABOVE, lambda: self._move_to_point_above(place_point)),
            (AutoTaskStep.MOVE_TO_PLACE, lambda: self._move_to_point(place_point)),
            (AutoTaskStep.GRIP_OPEN, lambda: self._control_gripper_auto(GRIPPER_OPEN)),
            (AutoTaskStep.MOVE_UP_FROM_PLACE, lambda: self._move_to_point_above(place_point)),
        ]
        
        for step, action in steps:
            if self.task_stop_flag:
                return False
                
            # 等待暂停结束
            while self.task_pause_flag and not self.task_stop_flag:
                time.sleep(0.1)
                
            if self.task_stop_flag:
                return False
                
            self.current_step = step
            self._update_status()
            
            print(f"执行步骤: {step.value}")
            
            try:
                success = action()
                if not success:
                    return False
            except Exception as e:
                print(f"步骤执行失败: {e}")
                return False
                
        return True
        
    def _move_to_safe_height(self):
        """移动到安全高度"""
        current_pos = self.kinematics.forward_kinematics(self.current_angles)
        safe_pos = [current_pos[0], current_pos[1], self.safe_height / 1000]
        return self._move_to_position_auto(safe_pos)
        
    def _move_to_point_above(self, point):
        """移动到指定点的上方"""
        above_pos = [point[0] / 1000, point[1] / 1000, (point[2] + self.pickup_height_offset) / 1000]
        return self._move_to_position_auto(above_pos)
        
    def _move_to_point(self, point):
        """移动到指定点"""
        target_pos = [point[0] / 1000, point[1] / 1000, point[2] / 1000]
        return self._move_to_position_auto(target_pos)
        
    def _move_to_position_auto(self, target_pos):
        """自动模式下移动到指定位置"""
        try:
            servo_angles, error = self.kinematics.inverse_kinematics(target_pos, self.current_angles)
            command = self.communicator.create_position_command(servo_angles, self.auto_speed, exclude_gripper=True)
            
            success, message = self.communicator.send_command(command)
            if success:
                # 更新当前角度
                for i in range(5):
                    self.current_angles[i] = servo_angles[i]
                time.sleep(self.move_delay)
                return True
            else:
                print(f"移动失败: {message}")
                return False
                
        except Exception as e:
            print(f"移动失败: {e}")
            return False
            
    def _control_gripper_auto(self, angle):
        """自动模式下控制夹爪"""
        try:
            command = self.communicator.create_gripper_command(angle, self.auto_speed)
            success, message = self.communicator.send_command(command)
            
            if success:
                self.current_angles[5] = angle
                time.sleep(self.grip_delay)
                return True
            else:
                print(f"夹爪控制失败: {message}")
                return False
                
        except Exception as e:
            print(f"夹爪控制失败: {e}")
            return False
            
    def _return_to_home_position(self):
        """返回复位点"""
        try:
            command = self.communicator.create_servo_command(DEFAULT_ANGLES, self.auto_speed)
            
            success, message = self.communicator.send_command(command)
            if success:
                self.current_angles = DEFAULT_ANGLES.copy()
                time.sleep(self.move_delay * 1.5)
                return True
            else:
                print(f"返回复位点失败: {message}")
                return False
                
        except Exception as e:
            print(f"返回复位点失败: {e}")
            return False
            
    def _update_status(self):
        """更新状态"""
        if self.status_callback:
            self.status_callback(self.task_state, self.current_step)
            
        if self.progress_callback:
            total_tasks = len(self.pickup_points)
            current = self.current_task_index + 1 if self.task_state in [TaskState.RUNNING, TaskState.PAUSED] else 0
            self.progress_callback(current, total_tasks)
            
    def save_task_points(self, filename=None):
        """保存任务点到文件"""
        if not filename:
            filename = f"task_points_{int(time.time())}.json"
            
        task_data = {
            'pickup_points': self.pickup_points,
            'place_points': self.place_points,
            'parameters': {
                'safe_height': self.safe_height,
                'height_offset': self.pickup_height_offset,
                'grip_delay': self.grip_delay,
                'move_delay': self.move_delay,
                'auto_speed': self.auto_speed,
                'return_home': self.return_home
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(task_data, f, indent=2)
            return True, f"任务点已保存到: {filename}"
        except Exception as e:
            return False, f"保存任务点失败: {str(e)}"
            
    def load_task_points(self, filename):
        """从文件加载任务点"""
        try:
            with open(filename, 'r') as f:
                task_data = json.load(f)
                
            self.pickup_points = task_data.get('pickup_points', [])
            self.place_points = task_data.get('place_points', [])
            
            # 加载参数
            params = task_data.get('parameters', {})
            self.update_parameters(params)
            
            return True, f"已加载 {len(self.pickup_points)} 个抓取点和 {len(self.place_points)} 个放置点"
            
        except Exception as e:
            return False, f"加载任务点失败: {str(e)}"