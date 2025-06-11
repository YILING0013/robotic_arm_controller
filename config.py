#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 存储所有常量和配置参数
"""

import numpy as np
from enum import Enum

# 机械臂结构参数
LINK_LENGTHS = [
    0.090,    # 底座旋转关节，高度90mm
    0.100,    # 大臂关节，长度100mm  
    0.100,    # 小臂关节，长度100mm
    0.065,    # 手腕俯仰关节，长度50mm
    0.001,    # 手腕旋转关节，长度10mm
    0.090,    # 夹爪关节，长度80mm
]

# 默认舵机角度
DEFAULT_ANGLES = [190, 130, 130, 130, 130, 130]

# 舵机角度范围
SERVO_LIMITS = [
    (0, 270),    # 舵机0: 底座旋转
    (50, 210),   # 舵机1: 大臂
    (20, 250),   # 舵机2: 小臂  
    (40, 210),   # 舵机3: 手腕俯仰
    (40, 210),   # 舵机4: 手腕旋转
    (100, 175)   # 舵机5: 夹爪
]

# 串口配置
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

# 默认目标位置 (mm)
DEFAULT_TARGET_POSITION = [150.0, 0.0, 200.0]

# 自动化任务默认参数
AUTO_TASK_DEFAULTS = {
    'safe_height': 250.0,       # 安全高度(mm)
    'height_offset': 30.0,      # 上方偏移(mm)
    'grip_delay': 2.0,          # 夹爪延迟(秒)
    'move_delay': 3.0,          # 移动延迟(秒)
    'auto_speed': 2,            # 自动执行速度
    'return_home': True         # 任务结束后返回复位点
}

# 夹爪位置
GRIPPER_OPEN = 100
GRIPPER_CLOSE = 175

# 3D可视化范围
VISUALIZATION_LIMITS = {
    'x': [-0.6, 0.6],
    'y': [-0.6, 0.6],
    'z': [0.0, 0.6]
}

# 字体配置 - 支持中文显示
FONT_CONFIG = {
    'windows': {
        'primary': 'Microsoft YaHei UI',
        'secondary': ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS'],
        'fallback': 'Arial'
    },
    'linux': {
        'primary': 'Noto Sans CJK SC',
        'secondary': ['WenQuanYi Micro Hei', 'Noto Sans SC', 'DejaVu Sans'],
        'fallback': 'DejaVu Sans'
    },
    'darwin': {  # macOS
        'primary': 'PingFang SC',
        'secondary': ['Hiragino Sans GB', 'Arial Unicode MS', 'STHeiti'],
        'fallback': 'Arial'
    }
}

# UI主题配置
UI_THEME = {
    'primary_color': '#2C3E50',
    'secondary_color': '#3498DB', 
    'success_color': "#506056",
    'warning_color': "#704500",
    'danger_color': '#E74C3C',
    'background_color': "#FFFFFF",
    'text_color': '#2C3E50',
    'button_padding': (10, 5),
    'frame_padding': 15,
    'font_family': 'Microsoft YaHei UI',  # 改为支持中文的字体
    'font_size': 10,  # 稍微增大字体
    'font_size_large': 12,
    'font_size_small': 8
}

# 状态枚举
class TaskState(Enum):
    """任务执行状态"""
    IDLE = "空闲"
    RUNNING = "执行中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    ERROR = "错误"

class AutoTaskStep(Enum):
    """自动任务步骤"""
    MOVE_TO_SAFE_HEIGHT = "移动到安全高度"
    MOVE_TO_PICKUP_ABOVE = "移动到抓取点上方"
    MOVE_TO_PICKUP = "移动到抓取点"
    GRIP_CLOSE = "夹爪闭合"
    MOVE_UP_FROM_PICKUP = "从抓取点上移"
    MOVE_TO_PLACE_ABOVE = "移动到放置点上方"
    MOVE_TO_PLACE = "移动到放置点"
    GRIP_OPEN = "夹爪张开"
    MOVE_UP_FROM_PLACE = "从放置点上移"
    RETURN_HOME = "返回复位点"
    TASK_COMPLETE = "任务完成"

# 文件设置
SETTINGS_FILE = 'robot_settings.json'
TASK_POINTS_PREFIX = 'task_points_'