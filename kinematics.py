#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运动学计算模块 - 正运动学、逆运动学计算
"""

import numpy as np
import ikpy.chain
import ikpy.link
from config import LINK_LENGTHS, SERVO_LIMITS, DEFAULT_ANGLES

class KinematicsCalculator:
    """运动学计算器"""
    
    def __init__(self):
        self.create_kinematic_chain()
        
    def create_kinematic_chain(self):
        """创建与实体一致的运动学链条（基座 → 夹爪）"""
        deg = np.radians
        self.chain = ikpy.chain.Chain([
            # J0 底座旋转（舵机0），关节位于坐标原点
            ikpy.link.URDFLink(
                name='base_rotate',
                origin_translation=[0, 0, 0],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 1],                   # 绕 Z
                bounds=(deg(-190), deg(80))
            ),
            # 固定立柱，高 60 mm
            ikpy.link.URDFLink(
                name='pillar',
                origin_translation=[0, 0, LINK_LENGTHS[0]],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 0]
            ),
            # J1 大臂俯仰（舵机1）
            ikpy.link.URDFLink(
                name='shoulder',
                origin_translation=[0, 0, 0],
                origin_orientation=[0, 0, 0],
                rotation=[0, 1, 0],                   # 绕 Y
                bounds=(deg(-80), deg(80))
            ),
            # 上臂 100 mm
            ikpy.link.URDFLink(
                name='upper_arm',
                origin_translation=[0, 0, LINK_LENGTHS[1]],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 0]
            ),
            # J2 小臂俯仰（舵机2）
            ikpy.link.URDFLink(
                name='elbow',
                origin_translation=[0, 0, 0],
                origin_orientation=[0, 0, 0],
                rotation=[0, 1, 0],
                bounds=(deg(-110), deg(120))
            ),
            # 小臂 100 mm
            ikpy.link.URDFLink(
                name='forearm',
                origin_translation=[0, 0, LINK_LENGTHS[2]],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 0]
            ),
            # J3 手腕俯仰（舵机3）
            ikpy.link.URDFLink(
                name='wrist_pitch',
                origin_translation=[0, 0, 0],
                origin_orientation=[0, 0, 0],
                rotation=[0, 1, 0],
                bounds=(deg(-90), deg(80))
            ),
            # 手腕连杆 50 mm
            ikpy.link.URDFLink(
                name='wrist_pitch_link',
                origin_translation=[0, 0, LINK_LENGTHS[3]],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 0]
            ),
            # J4 手腕旋转（舵机4）——修正轴向为 Z
            ikpy.link.URDFLink(
                name='wrist_rotate',
                origin_translation=[0, 0, 0],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 1],
                bounds=(deg(-180), deg(180))
            ),
            # 末端执行器：舵机4 到夹爪尖 (10 mm + 80 mm)
            ikpy.link.URDFLink(
                name='tool',
                origin_translation=[0, 0, LINK_LENGTHS[4] + LINK_LENGTHS[5]],
                origin_orientation=[0, 0, 0],
                rotation=[0, 0, 0]
            ),
        ])

    def servo_angle_to_chain_angle(self, servo_angles):
        """
        舵机角度列表(6) → IKPy Chain 角度列表(10)
        固定节的角度恒为 0
        """
        return [
            np.radians(servo_angles[0] - 190),          # J0
            0,                                          # 固定: pillar
            np.radians(-(servo_angles[1] - 130)),       # J1
            0,                                          # 固定: upper_arm
            np.radians(servo_angles[2] - 130),          # J2
            0,                                          # 固定: forearm
            np.radians(servo_angles[3] - 130),          # J3
            0,                                          # 固定: wrist_pitch_link
            np.radians(-(servo_angles[4] - 130)),       # J4
            0                                           # 固定: tool
        ]
        
    def chain_angle_to_servo_angle(self, chain_angles, current_gripper_angle):
        """
        IKPy Chain 角度(10) → 舵机角度(6)
        舵机5 (夹爪) 仍保持原状态，不参与运动学
        """
        servo_angles = [
            np.degrees(chain_angles[0]) + 190,                  # 舵机0
            -np.degrees(chain_angles[2]) + 130,                 # 舵机1
            np.degrees(chain_angles[4]) + 130,                  # 舵机2
            np.degrees(chain_angles[6]) + 130,                  # 舵机3
            -np.degrees(chain_angles[8]) + 130,                 # 舵机4
            current_gripper_angle                               # 舵机5 (夹爪)
        ]
        return servo_angles
        
    def forward_kinematics(self, servo_angles):
        """正运动学:根据舵机角度计算末端位置"""
        chain_angles = self.servo_angle_to_chain_angle(servo_angles)
        transform_matrix = self.chain.forward_kinematics(chain_angles)
        # 确保返回的是位置向量(3,)
        position = np.array(transform_matrix[:3, 3]).flatten()
        return position
        
    def inverse_kinematics(self, target_position, current_angles=DEFAULT_ANGLES.copy()):
        """逆运动学:多次迭代，直到结果收敛或达到最大次数，返回误差最小的舵机角度"""
        initial_position = self.servo_angle_to_chain_angle(current_angles)
            
        target_position = np.array(target_position).flatten()
        if len(target_position) != 3:
            raise ValueError(f"目标位置必须是3D坐标，当前长度: {len(target_position)}")
            
        target_frame = np.eye(4)
        target_frame[:3, 3] = target_position

        min_error = float('inf')
        best_servo_angles = None
        prev_servo_angles = None

        max_iter = 10
        tol = 1e-3  # 角度变化小于1e-3度认为收敛

        current_chain_angles = initial_position

        for i in range(max_iter):
            try:
                chain_angles = self.chain.inverse_kinematics_frame(
                    target_frame,
                    initial_position=current_chain_angles
                )
                servo_angles = self.chain_angle_to_servo_angle(chain_angles, current_angles[5])
                
                # 限制角度范围
                for j in range(5):  # 不包括夹爪
                    min_angle, max_angle = SERVO_LIMITS[j]
                    servo_angles[j] = max(min_angle, min(max_angle, servo_angles[j]))

                # 计算末端误差
                fk_pos = self.forward_kinematics(servo_angles)
                error = np.linalg.norm(fk_pos - target_position)

                if error < min_error:
                    min_error = error
                    best_servo_angles = servo_angles.copy()

                # 判断是否收敛
                if prev_servo_angles is not None:
                    diff = np.max(np.abs(np.array(servo_angles) - np.array(prev_servo_angles)))
                    if diff < tol:
                        break
                prev_servo_angles = servo_angles.copy()
                # 更新下一次迭代的初始值
                current_chain_angles = self.servo_angle_to_chain_angle(servo_angles)
            except Exception as e:
                raise ValueError(f"逆运动学计算失败: {str(e)}")
        
        return best_servo_angles, min_error