#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化任务执行模块 - 处理机械臂的自动化抓取放置任务 (已优化路径规划)
"""

import threading
import time
import json
import numpy as np  # 导入NumPy库
from config import TaskState, AutoTaskStep, AUTO_TASK_DEFAULTS, GRIPPER_OPEN, GRIPPER_CLOSE, DEFAULT_ANGLES
from utils import log_manager

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

    def is_task_running(self):
        """检查任务是否正在运行"""
        return self.task_state in [TaskState.RUNNING, TaskState.PAUSED]
        
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
        """
        自动模式下移动到指定位置。
        此方法包含智能路径规划，以决定是直接移动、沿球面轨迹移动还是沿侧边圆弧轨迹移动。
        """
        try:
            start_pos = self.kinematics.forward_kinematics(self.current_angles)
            end_pos = np.array(target_pos)
            
            # 1. 如果距离小于阈值，则直接移动
            if np.linalg.norm(end_pos - start_pos) < 0.01:
                return self._move_to_target_directly(end_pos)

            # 2. 分析XY平面上的角度，决定是否需要侧方绕行
            start_xy = start_pos[:2]
            end_xy = end_pos[:2]
            norm_start_xy = np.linalg.norm(start_xy)
            norm_end_xy = np.linalg.norm(end_xy)
            
            # 仅当两点都在原点之外时才计算夹角
            if norm_start_xy > 1e-6 and norm_end_xy > 1e-6:
                u_start = start_xy / norm_start_xy
                u_end = end_xy / norm_end_xy
                dot_product = np.dot(u_start, u_end)
                angle_deg = np.degrees(np.arccos(np.clip(dot_product, -1.0, 1.0)))

                # 如果角度大于150度，则采用侧方绕行策略
                if angle_deg > 120:
                    log_manager.info(f"检测到大角度转向 ({angle_deg:.1f}°)，启用侧方路径规划。")
                    return self._move_along_horizontal_arc_path(start_pos, end_pos)

            # 3. 对于其他情况，使用球面路径规划
            return self._move_along_spherical_path(start_pos, end_pos)

        except Exception as e:
            log_manager.error(f"移动到位置失败 (路径规划): {e}")
            return False

    def _execute_path(self, path, total_duration):
        """
        通用路径执行函数。
        :param path: 一系列要经过的坐标点 (list of np.array)。
        :param total_duration: 完成整个路径的总时间。
        """
        num_segments = len(path) - 1
        if num_segments <= 0:
            return True
        
        segment_duration = total_duration / num_segments

        for i in range(num_segments):
            # 检查任务是否被暂停或停止
            if self.task_stop_flag: return False
            while self.task_pause_flag and not self.task_stop_flag: time.sleep(0.1)
            if self.task_stop_flag: return False

            waypoint = path[i+1]
            # print(f"  移动到路径点 {i+1}/{num_segments}: {np.round(waypoint*1000, 2)} mm")

            servo_angles, error = self.kinematics.inverse_kinematics(waypoint, self.current_angles)
            if servo_angles is None:
                log_manager.warning(f"  [!] 路径规划警告：无法为中间点 {waypoint} 找到解。跳过此点。")
                continue

            command = self.communicator.create_position_command(servo_angles, self.auto_speed, exclude_gripper=True)
            success, message = self.communicator.send_command(command)
            
            if success:
                for j in range(5):
                    self.current_angles[j] = servo_angles[j]
                time.sleep(segment_duration)
            else:
                log_manager.error(f"  [!] 移动到中间点失败: {message}。终止轨迹移动。")
                return False
        return True

    def _move_to_target_directly(self, target_pos):
        """直接移动到目标点，不进行路径插值"""
        path = [target_pos]
        return self._execute_path(path, self.move_delay)

    def _move_along_horizontal_arc_path(self, start_pos, end_pos):
        """
        为避免穿越中心，生成一个在安全高度的侧边水平圆弧路径。
        路径组成为: 起点 -> 圆弧入口 -> [圆弧路径] -> 圆弧出口 -> 终点
        """
        log_manager.info("生成侧方水平圆弧路径...")
        # 1. 确定圆弧参数
        safe_z = self.safe_height / 1000
        start_xy = start_pos[:2]
        end_xy = end_pos[:2]
        dist_start_xy = np.linalg.norm(start_xy)
        dist_end_xy = np.linalg.norm(end_xy)
        
        # 使用较小半径确保能达到
        arc_radius = min(dist_start_xy, dist_end_xy)
        if arc_radius < 0.01: # 半径太小没有意义
            log_manager.info("绕行半径过小，切换为球面路径。")
            return self._move_along_spherical_path(start_pos, end_pos)

        # 2. 定义路径关键点
        # 圆弧入口点
        u_start_xy = start_xy / dist_start_xy
        arc_entry_pos = np.array([u_start_xy[0] * arc_radius, u_start_xy[1] * arc_radius, safe_z])
        # 圆弧出口点
        u_end_xy = end_xy / dist_end_xy
        arc_exit_pos = np.array([u_end_xy[0] * arc_radius, u_end_xy[1] * arc_radius, safe_z])
        
        # 3. 生成圆弧上的点
        start_angle = np.arctan2(u_start_xy[1], u_start_xy[0])
        end_angle = np.arctan2(u_end_xy[1], u_end_xy[0])
        
        # 选择最短的绕行方向
        angle_diff = end_angle - start_angle
        if angle_diff > np.pi: angle_diff -= 2 * np.pi
        if angle_diff < -np.pi: angle_diff += 2 * np.pi
        
        num_arc_steps = 5
        arc_points = []
        for i in range(1, num_arc_steps + 1):
            t = i / num_arc_steps
            current_angle = start_angle + t * angle_diff
            x = arc_radius * np.cos(current_angle)
            y = arc_radius * np.sin(current_angle)
            arc_points.append(np.array([x, y, safe_z]))
        
        # 4. 组合完整路径
        # 为了让每段运动更平滑，也用Slerp连接到圆弧
        path1 = self._get_slerp_path(start_pos, arc_entry_pos, 3)
        path2 = arc_points
        path3 = self._get_slerp_path(arc_exit_pos, end_pos, 3)
        
        full_path = path1 + path2 + path3
        
        log_manager.info(f"侧方路径生成完毕，共 {len(full_path)} 个路径点。")
        return self._execute_path(full_path, self.move_delay)

    def _get_slerp_path(self, p1, p2, num_steps):
        """辅助函数: 根据Slerp生成一段路径点列表 (不包含起点)"""
        path = []
        r1 = np.linalg.norm(p1)
        r2 = np.linalg.norm(p2)

        if r1 < 1e-6 or r2 < 1e-6: # 线性插值
            for i in range(1, num_steps + 1):
                t = i / num_steps
                path.append(p1 * (1 - t) + p2 * t)
            return path
            
        u1 = p1 / r1
        u2 = p2 / r2
        dot_product = np.dot(u1, u2)
        omega = np.arccos(np.clip(dot_product, -1.0, 1.0))

        if omega < np.radians(1.0): # 线性插值
            for i in range(1, num_steps + 1):
                t = i / num_steps
                path.append(p1 * (1 - t) + p2 * t)
            return path

        sin_omega = np.sin(omega)
        for i in range(1, num_steps + 1):
            t = i / num_steps
            slerp_factor1 = np.sin((1 - t) * omega) / sin_omega
            slerp_factor2 = np.sin(t * omega) / sin_omega
            u_t = slerp_factor1 * u1 + slerp_factor2 * u2
            r_t = (1 - t) * r1 + t * r2
            path.append(r_t * u_t)
        return path
        
    def _move_along_spherical_path(self, start_pos, end_pos):
        """
        使用球面线性插值(Slerp)在起点和终点之间生成平滑的球形轨迹。
        """
        log_manager.info("生成球面路径...")
        path_points = self._get_slerp_path(start_pos, end_pos, num_steps=6)
        return self._execute_path(path_points, self.move_delay)
            
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
                log_manager.warning(f"夹爪控制失败: {message}")
                return False
                
        except Exception as e:
            log_manager.error(f"夹爪控制失败: {e}")
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
                log_manager.warning(f"返回复位点失败: {message}")
                return False
                
        except Exception as e:
            log_manager.error(f"返回复位点失败: {e}")
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
