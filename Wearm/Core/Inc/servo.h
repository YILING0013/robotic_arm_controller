#ifndef __SERVO_H
#define __SERVO_H

#include "main.h"
#include <stdint.h>

// 宏定义，用于计算数组元素个数
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

// 舵机结构体定义
struct servo
{
    TIM_TypeDef *timer;
    uint32_t channel;
    uint16_t pulse;     // 当前脉宽
    uint16_t min;       // 最小脉宽
    uint16_t max;       // 最大脉宽
    uint16_t angle_min; // 最小角度
    uint16_t angle_max; // 最大角度
    uint16_t begin;     // 运动起始脉宽
    uint16_t end;       // 运动目标脉宽
    uint16_t delay;     // 运动速度（延迟）
    int16_t adjust;     // 脉宽微调值
};

/**
 * @brief 全局标志位，用于从中断中通知 servo_run() 停止运动
 * @note volatile 关键字防止编译器优化
 */
extern volatile uint8_t g_movement_should_stop;

// 函数原型声明
int servo_num(void);
void servos_init_all(void);
void servo_write_angle(uint8_t id, uint16_t angle, uint16_t delay);
uint16_t servo_read(uint8_t id);
int servo_run(void);
void servo_cmd_angle(char *arg);

#endif /* __SERVO_H */
