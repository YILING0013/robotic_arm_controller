#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口通信模块 - 处理与机械臂的串口通信
"""

import serial
import serial.tools.list_ports
import threading
import time
from config import SERIAL_BAUDRATE, SERIAL_TIMEOUT

class SerialCommunicator:
    """串口通信器"""
    
    def __init__(self, status_callback=None, data_callback=None):
        self.serial_port = None
        self.is_connected = False
        self.receive_thread = None
        self.status_callback = status_callback  # 状态变化回调
        self.data_callback = data_callback      # 数据接收回调
        
    def get_available_ports(self):
        """获取可用串口列表"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports
        
    def connect(self, port):
        """连接串口"""
        try:
            self.serial_port = serial.Serial(port, SERIAL_BAUDRATE, timeout=SERIAL_TIMEOUT)
            self.is_connected = True
            
            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_data, daemon=True)
            self.receive_thread.start()
            
            if self.status_callback:
                self.status_callback(True, f"已连接到 {port}")
            
            return True
            
        except Exception as e:
            if self.status_callback:
                self.status_callback(False, f"连接失败: {str(e)}")
            return False
            
    def disconnect(self):
        """断开串口连接"""
        try:
            self.is_connected = False
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
                
            if self.status_callback:
                self.status_callback(False, "未连接")
                
        except Exception as e:
            print(f"断开连接错误: {e}")
            
    def send_command(self, command):
        """发送指令到机械臂"""
        if not self.is_connected or not self.serial_port:
            return False, "串口未连接"
            
        try:
            print(f"发送指令: {command}")
            self.serial_port.write((command + '\r\n').encode('utf-8'))
            return True, "指令发送成功"
        except Exception as e:
            return False, f"发送指令失败: {str(e)}"
            
    def _receive_data(self):
        """接收串口数据线程"""
        while self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        print(f"接收: {data}")
                        if self.data_callback:
                            self.data_callback(data)
            except Exception as e:
                print(f"接收数据错误: {e}")
                break
            time.sleep(0.1)
            
    def create_servo_command(self, servo_angles, speed):
        """创建舵机控制指令"""
        command_parts = []
        for i, angle in enumerate(servo_angles):
            if i < len(servo_angles):
                command_parts.append(f"{i}:{round(angle)}:{speed}")
        return ",".join(command_parts)
        
    def create_position_command(self, servo_angles, speed, exclude_gripper=False):
        """创建位置控制指令"""
        command_parts = []
        end_index = 5 if exclude_gripper else 6
        
        for i in range(end_index):
            angle = round(servo_angles[i])
            command_parts.append(f"{i}:{angle}:{speed}")
            
        return ",".join(command_parts)
        
    def create_gripper_command(self, angle, speed):
        """创建夹爪控制指令"""
        return f"5:{round(angle)}:{speed}"