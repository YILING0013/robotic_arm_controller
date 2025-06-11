#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块 - 包含设置管理、文件操作等通用功能
"""

import json
import os
import time
from tkinter import messagebox
from config import SETTINGS_FILE, DEFAULT_ANGLES, DEFAULT_TARGET_POSITION, AUTO_TASK_DEFAULTS

class SettingsManager:
    """设置管理器"""
    
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        
    def save_settings(self, **kwargs):
        """保存设置到文件"""
        settings = {
            'port': kwargs.get('port', ''),
            'current_angles': kwargs.get('current_angles', DEFAULT_ANGLES),
            'target_position': kwargs.get('target_position', DEFAULT_TARGET_POSITION),
            'speed': kwargs.get('speed', 2),
            'show_target': kwargs.get('show_target', True),
            'pickup_points': kwargs.get('pickup_points', []),
            'place_points': kwargs.get('place_points', []),
            'auto_parameters': kwargs.get('auto_parameters', AUTO_TASK_DEFAULTS),
            'window_geometry': kwargs.get('window_geometry', '1216x640'),
            'last_saved': time.time()
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True, "设置保存成功"
        except Exception as e:
            return False, f"保存设置失败: {str(e)}"
    
    def load_settings(self):
        """从文件加载设置"""
        default_settings = {
            'port': '',
            'current_angles': DEFAULT_ANGLES,
            'target_position': DEFAULT_TARGET_POSITION,
            'speed': 2,
            'show_target': True,
            'pickup_points': [],
            'place_points': [],
            'auto_parameters': AUTO_TASK_DEFAULTS,
            'window_geometry': '1216x640',
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 合并默认设置，确保所有必要的键都存在
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                
                return True, settings
            else:
                return True, default_settings
                
        except Exception as e:
            print(f"加载设置失败: {e}")
            return False, default_settings
    
    def backup_settings(self):
        """备份当前设置"""
        if os.path.exists(self.settings_file):
            backup_file = f"{self.settings_file}.backup_{int(time.time())}"
            try:
                import shutil
                shutil.copy2(self.settings_file, backup_file)
                return True, f"设置已备份到: {backup_file}"
            except Exception as e:
                return False, f"备份失败: {str(e)}"
        return False, "没有找到设置文件"

class TaskPointsManager:
    """任务点管理器"""
    
    def __init__(self):
        pass
    
    def save_task_points(self, pickup_points, place_points, parameters, filename=None):
        """保存任务点到文件"""
        if not filename:
            timestamp = int(time.time())
            filename = f"task_points_{timestamp}.json"
        
        task_data = {
            'version': '2.0',
            'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pickup_points': pickup_points,
            'place_points': place_points,
            'parameters': parameters,
            'total_tasks': len(pickup_points)
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            return True, f"任务点已保存到: {filename}"
        except Exception as e:
            return False, f"保存任务点失败: {str(e)}"
    
    def load_task_points(self, filename):
        """从文件加载任务点"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 兼容旧版本格式
            if 'version' not in task_data:
                task_data['version'] = '1.0'
            
            pickup_points = task_data.get('pickup_points', [])
            place_points = task_data.get('place_points', [])
            parameters = task_data.get('parameters', AUTO_TASK_DEFAULTS)
            
            # 确保参数完整性
            for key, value in AUTO_TASK_DEFAULTS.items():
                if key not in parameters:
                    parameters[key] = value
            
            return True, {
                'pickup_points': pickup_points,
                'place_points': place_points,
                'parameters': parameters,
                'version': task_data.get('version', '1.0'),
                'created_time': task_data.get('created_time', '未知')
            }
            
        except Exception as e:
            return False, f"加载任务点失败: {str(e)}"
    
    def export_task_report(self, pickup_points, place_points, parameters, filename=None):
        """导出任务报告"""
        if not filename:
            timestamp = int(time.time())
            filename = f"task_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("5DOF机械臂自动化任务报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"任务总数: {len(pickup_points)}\n\n")
                
                f.write("任务参数:\n")
                f.write("-" * 30 + "\n")
                for key, value in parameters.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                f.write("任务点详情:\n")
                f.write("-" * 30 + "\n")
                for i, (pickup, place) in enumerate(zip(pickup_points, place_points)):
                    f.write(f"任务 {i+1}:\n")
                    f.write(f"  抓取点: X={pickup[0]:.1f}, Y={pickup[1]:.1f}, Z={pickup[2]:.1f} mm\n")
                    f.write(f"  放置点: X={place[0]:.1f}, Y={place[1]:.1f}, Z={place[2]:.1f} mm\n")
                    
                    # 计算距离
                    import math
                    distance = math.sqrt(sum((p-q)**2 for p, q in zip(pickup, place)))
                    f.write(f"  移动距离: {distance:.1f} mm\n\n")
                
                # 统计信息
                f.write("统计信息:\n")
                f.write("-" * 30 + "\n")
                if pickup_points:
                    import numpy as np
                    pickup_array = np.array(pickup_points)
                    place_array = np.array(place_points)
                    
                    f.write(f"抓取点范围: X[{pickup_array[:,0].min():.1f}, {pickup_array[:,0].max():.1f}], ")
                    f.write(f"Y[{pickup_array[:,1].min():.1f}, {pickup_array[:,1].max():.1f}], ")
                    f.write(f"Z[{pickup_array[:,2].min():.1f}, {pickup_array[:,2].max():.1f}]\n")
                    
                    f.write(f"放置点范围: X[{place_array[:,0].min():.1f}, {place_array[:,0].max():.1f}], ")
                    f.write(f"Y[{place_array[:,1].min():.1f}, {place_array[:,1].max():.1f}], ")
                    f.write(f"Z[{place_array[:,2].min():.1f}, {place_array[:,2].max():.1f}]\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            return True, f"任务报告已导出到: {filename}"
            
        except Exception as e:
            return False, f"导出任务报告失败: {str(e)}"

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_file="robot_arm.log"):
        self.log_file = log_file
        self.max_log_size = 10 * 1024 * 1024  # 10MB
    
    def log(self, level, message):
        """写入日志"""
        try:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            
            # 检查日志文件大小
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > self.max_log_size:
                self._rotate_log()
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"写入日志失败: {e}")
    
    def _rotate_log(self):
        """轮转日志文件"""
        try:
            backup_file = f"{self.log_file}.{int(time.time())}"
            os.rename(self.log_file, backup_file)
        except Exception as e:
            print(f"轮转日志失败: {e}")
    
    def info(self, message):
        """信息日志"""
        self.log("INFO", message)
        print(f"[INFO] {message}")
    
    def warning(self, message):
        """警告日志"""
        self.log("WARNING", message)
        print(f"[WARNING] {message}")
    
    def error(self, message):
        """错误日志"""
        self.log("ERROR", message)
        print(f"[ERROR] {message}")
    
    def debug(self, message):
        """调试日志"""
        self.log("DEBUG", message)
        print(f"[DEBUG] {message}")

class ValidationHelper:
    """验证辅助类"""
    
    @staticmethod
    def validate_position(position):
        """验证位置坐标"""
        try:
            if len(position) != 3:
                return False, "位置坐标必须包含X、Y、Z三个值"
            
            x, y, z = position
            
            # 检查数值范围（mm）
            if not (-500 <= x <= 500):
                return False, "X坐标超出范围 [-500, 500]mm"
            if not (-500 <= y <= 500):
                return False, "Y坐标超出范围 [-500, 500]mm"
            if not (0 <= z <= 500):
                return False, "Z坐标超出范围 [0, 500]mm"
            
            return True, "位置坐标有效"
            
        except Exception as e:
            return False, f"位置验证失败: {str(e)}"
    
    @staticmethod
    def validate_servo_angle(servo_id, angle):
        """验证舵机角度"""
        try:
            from config import SERVO_LIMITS
            
            if not (0 <= servo_id < len(SERVO_LIMITS)):
                return False, f"舵机编号超出范围 [0, {len(SERVO_LIMITS)-1}]"
            
            min_angle, max_angle = SERVO_LIMITS[servo_id]
            if not (min_angle <= angle <= max_angle):
                return False, f"舵机{servo_id}角度超出范围 [{min_angle}, {max_angle}]度"
            
            return True, "舵机角度有效"
            
        except Exception as e:
            return False, f"角度验证失败: {str(e)}"
    
    @staticmethod
    def validate_task_points(pickup_points, place_points):
        """验证任务点"""
        try:
            if not pickup_points:
                return False, "至少需要一个抓取点"
            if not place_points:
                return False, "至少需要一个放置点"
            if len(pickup_points) != len(place_points):
                return False, "抓取点和放置点数量必须相等"
            
            # 验证每个点的坐标
            for i, point in enumerate(pickup_points):
                valid, msg = ValidationHelper.validate_position(point)
                if not valid:
                    return False, f"抓取点{i+1}: {msg}"
            
            for i, point in enumerate(place_points):
                valid, msg = ValidationHelper.validate_position(point)
                if not valid:
                    return False, f"放置点{i+1}: {msg}"
            
            return True, "任务点验证通过"
            
        except Exception as e:
            return False, f"任务点验证失败: {str(e)}"

class MessageHelper:
    """消息提示辅助类"""
    
    @staticmethod
    def show_info(title, message):
        """显示信息消息"""
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_warning(title, message):
        """显示警告消息"""
        messagebox.showwarning(title, message)
    
    @staticmethod
    def show_error(title, message):
        """显示错误消息"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def ask_yes_no(title, message):
        """询问是/否"""
        return messagebox.askyesno(title, message)
    
    @staticmethod
    def ask_ok_cancel(title, message):
        """询问确定/取消"""
        return messagebox.askokcancel(title, message)

class FileHelper:
    """文件操作辅助类"""
    
    @staticmethod
    def ensure_directory(path):
        """确保目录存在"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(filepath):
        """获取文件大小（MB）"""
        try:
            if os.path.exists(filepath):
                size_bytes = os.path.getsize(filepath)
                return size_bytes / (1024 * 1024)
            return 0
        except Exception:
            return 0
    
    @staticmethod
    def cleanup_old_files(directory, pattern, max_files=10):
        """清理旧文件，保留最新的几个"""
        try:
            import glob
            files = glob.glob(os.path.join(directory, pattern))
            files.sort(key=os.path.getmtime, reverse=True)
            
            # 删除超过数量限制的文件
            for file_to_delete in files[max_files:]:
                try:
                    os.remove(file_to_delete)
                    print(f"删除旧文件: {file_to_delete}")
                except Exception as e:
                    print(f"删除文件失败: {e}")
        except Exception as e:
            print(f"清理文件失败: {e}")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.timers = {}
    
    def start_timer(self, name):
        """开始计时"""
        self.timers[name] = time.time()
    
    def end_timer(self, name):
        """结束计时并返回耗时"""
        if name in self.timers:
            elapsed = time.time() - self.timers[name]
            del self.timers[name]
            return elapsed
        return 0
    
    def log_performance(self, name, elapsed_time):
        """记录性能信息"""
        if elapsed_time > 1.0:  # 超过1秒的操作记录日志
            print(f"[PERFORMANCE] {name}: {elapsed_time:.3f}s")

# 全局实例
settings_manager = SettingsManager()
task_points_manager = TaskPointsManager()
log_manager = LogManager()
performance_monitor = PerformanceMonitor()