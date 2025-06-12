#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 存储所有常量和配置参数 (字体修复版)
"""

import numpy as np
from enum import Enum

# =============================================================================
# 应用主题配置
# =============================================================================
# 可选主题: ['cosmo', 'flatly', 'journal', 'litera', 'lumen', 'minty', 'pulse', 
# 'sandstone', 'united', 'yeti', 'cyborg', 'darkly', 'solar', 'superhero']
DEFAULT_THEME = 'flatly'

# 串口配置
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

# =============================================================================
# 机械臂与物理参数
# =============================================================================
# 机械臂结构参数 (单位: m)
LINK_LENGTHS = [
    0.090,    # 底座旋转关节，高度90mm
    0.100,    # 大臂关节，长度100mm  
    0.100,    # 小臂关节，长度100mm
    0.065,    # 手腕俯仰关节，长度65mm
    0.001,    # 手腕旋转关节，长度1mm
    0.090,    # 夹爪关节，长度90mm
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

# 夹爪位置
GRIPPER_OPEN = 100
GRIPPER_CLOSE = 175

# 默认目标位置 (mm)
DEFAULT_TARGET_POSITION = [150.0, 0.0, 200.0]


# =============================================================================
# 自动化与控制参数
# =============================================================================
# 自动化任务默认参数
AUTO_TASK_DEFAULTS = {
    'safe_height': 250.0,       # 安全高度(mm)
    'height_offset': 30.0,      # 上方偏移(mm)
    'grip_delay': 2.0,          # 夹爪延迟(秒)
    'move_delay': 3.0,          # 移动延迟(秒)
    'auto_speed': 2,            # 自动执行速度
    'return_home': True         # 任务结束后返回复位点
}

# 键盘控制默认参数
KEYBOARD_CONTROL_DEFAULTS = {
    'step_size': 5.0,           # 默认步长(mm)
    'command_interval': 0.1,    # 指令间隔(秒)
}

# =============================================================================
# UI 与可视化配置
# =============================================================================
# 3D可视化范围 (单位: m)
VISUALIZATION_LIMITS = {
    'x': [-0.4, 0.4],
    'y': [-0.4, 0.4],
    'z': [0.0, 0.5]
}

# 字体配置 (按系统优先级) - 修复版
FONT_CONFIG = {
    'windows': [
        'Microsoft YaHei',      # 微软雅黑
        'Microsoft YaHei UI',   # 微软雅黑UI
        'SimHei',               # 黑体
        'SimSun',               # 宋体
        'Arial Unicode MS'      # Arial Unicode
    ],
    'linux': [
        'Noto Sans CJK SC',     # 思源黑体
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
        'WenQuanYi Zen Hei',    # 文泉驿正黑
        'DejaVu Sans',          # DejaVu Sans
        'Liberation Sans'       # Liberation Sans
    ],
    'darwin': [
        'PingFang SC',          # 苹方
        'Hiragino Sans GB',     # 冬青黑体
        'STHeiti',              # 华文黑体
        'Arial Unicode MS'      # Arial Unicode
    ],
    'fallback': 'Arial'         # 最终后备字体
}

# 为matplotlib准备的字体映射
MATPLOTLIB_FONT_MAPPING = {
    'Microsoft YaHei': ['Microsoft YaHei', 'Microsoft YaHei UI'],
    'SimHei': ['SimHei'],
    'SimSun': ['SimSun'],
    'PingFang SC': ['PingFang SC'],
    'Hiragino Sans GB': ['Hiragino Sans GB'],
    'Noto Sans CJK SC': ['Noto Sans CJK SC', 'Noto Sans CJK'],
    'WenQuanYi Micro Hei': ['WenQuanYi Micro Hei'],
    'DejaVu Sans': ['DejaVu Sans'],
    'Arial': ['Arial']
}

# =============================================================================
# 系统状态与枚举
# =============================================================================
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

# =============================================================================
# 文件与版本信息
# =============================================================================
# 文件设置
SETTINGS_FILE = 'robot_settings.json'
LOG_FILE = 'robot_arm.log'

# 版本信息
VERSION_INFO = {
    'version': '2.1.1',
    'build_date': '2024-06-12',
    'author': 'Robot Control System',
    'description': '5DOF机械臂上位机控制程序 (字体修复版)',
}