#include "automation.h"
#include "servo.h"
#include <stdio.h>
#include <string.h>

// 内部函数声明
void move_to_pose(const uint16_t pose[6], uint16_t speed);

// ======================================================================
// 在这里定义您录制的动作序列
// 格式: {舵机0角度, 舵机1角度, 舵机2角度, 舵机3角度, 舵机4角度, 夹爪舵机5角度}
// ======================================================================

// --- 任务1：夹取与放置 ---
// 初始姿态
const uint16_t POSE_HOME[6]           = {190, 130, 130, 130, 130, 130}; // 夹爪张开(100度)
// 抓取序列
const uint16_t POSE_READY_TO_PICK[6]  = {190, 110, 180, 150, 130, 100}; // 移动到物体上方，夹爪张开
const uint16_t POSE_PICK[6]           = {190, 85,  175, 190, 130, 100}; // 下降到物体高度，夹爪张开
const uint16_t POSE_GRASP[6]          = {190, 85,  175, 190, 130, 140}; // 闭合夹爪(150度)
const uint16_t POSE_LIFT_UP[6]        = {190, 110, 180, 150, 130, 140}; // 向上提起物体
// 放置序列
const uint16_t POSE_READY_TO_PLACE[6] = {230, 110, 180, 150, 130, 140}; // 移动到放置点上方
const uint16_t POSE_PLACE[6]          = {230, 85, 175, 190, 130, 140}; // 下降到放置点高度
const uint16_t POSE_RELEASE[6]        = {230, 85, 175, 190, 130, 100}; // 张开夹爪
const uint16_t POSE_RETREAT[6]        = {190, 130, 130, 130, 130, 130}; // 抬起并撤退

// 将所有姿态组合成一个序列
const uint16_t* pick_and_place_sequence[] = {
    POSE_HOME,
    POSE_READY_TO_PICK,
    POSE_PICK,
    POSE_GRASP,
    POSE_LIFT_UP,
    POSE_READY_TO_PLACE,
    POSE_PLACE,
    POSE_RELEASE,
    POSE_RETREAT,
    POSE_HOME
};


/**
 * @brief 执行自动化任务的主函数
 * @param task 要执行的任务
 */
void execute_automation_task(AutomationTask task)
{
    printf("Executing task: %d\n", task);
    
    switch(task)
    {
        case TASK_PICK_AND_PLACE_1:
        {
            int step_count = sizeof(pick_and_place_sequence) / sizeof(pick_and_place_sequence[0]);
            for(int i = 0; i < step_count; i++)
            {
                printf("Step %d...\n", i);
                // 使用统一的速度来执行每一步
                move_to_pose(pick_and_place_sequence[i], 2);
                LL_mDelay(2); // 在每一步之间稍作停顿，让动作更清晰
            }
            break;
        }
        default:
            printf("Unknown task.\n");
            break;
    }
    
    puts("Task finished.");
}


/**
 * @brief (核心辅助函数) 让机械臂移动到一个指定姿态
 * @param pose 目标姿态（包含6个舵机角度的数组）
 * @param speed 所有舵机统一的运动速度
 */
void move_to_pose(const uint16_t pose[6], uint16_t speed)
{
    // 创建一个足够大的缓冲区来存放完整的指令字符串
    char command_string[128] = {0}; 
    char part_buffer[20];

    // 循环拼接所有舵机的指令
    for (int id = 0; id < 6; id++)
    {
        // 格式化单个舵机的指令部分，例如 "0:135:20"
        sprintf(part_buffer, "%d:%d:%d", id, pose[id], speed);
        strcat(command_string, part_buffer);
        
        // 如果不是最后一个舵机，则在后面添加逗号
        if (id < 5)
        {
            strcat(command_string, ",");
        }
    }
    
    // 调用舵机指令处理函数，传入完整的指令字符串
    // 例如: "0:135:20,1:150:20,2:100:20,3:130:20,4:130:20,5:100:20"
    servo_cmd_angle(command_string);
}

