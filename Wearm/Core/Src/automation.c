#include "automation.h"
#include "servo.h"
#include <stdio.h>
#include <string.h>

// �ڲ���������
void move_to_pose(const uint16_t pose[6], uint16_t speed);

// ======================================================================
// �����ﶨ����¼�ƵĶ�������
// ��ʽ: {���0�Ƕ�, ���1�Ƕ�, ���2�Ƕ�, ���3�Ƕ�, ���4�Ƕ�, ��צ���5�Ƕ�}
// ======================================================================

// --- ����1����ȡ����� ---
// ��ʼ��̬
const uint16_t POSE_HOME[6]           = {190, 130, 130, 130, 130, 130}; // ��צ�ſ�(100��)
// ץȡ����
const uint16_t POSE_READY_TO_PICK[6]  = {190, 110, 180, 150, 130, 100}; // �ƶ��������Ϸ�����צ�ſ�
const uint16_t POSE_PICK[6]           = {190, 85,  175, 190, 130, 100}; // �½�������߶ȣ���צ�ſ�
const uint16_t POSE_GRASP[6]          = {190, 85,  175, 190, 130, 140}; // �պϼ�צ(150��)
const uint16_t POSE_LIFT_UP[6]        = {190, 110, 180, 150, 130, 140}; // ������������
// ��������
const uint16_t POSE_READY_TO_PLACE[6] = {230, 110, 180, 150, 130, 140}; // �ƶ������õ��Ϸ�
const uint16_t POSE_PLACE[6]          = {230, 85, 175, 190, 130, 140}; // �½������õ�߶�
const uint16_t POSE_RELEASE[6]        = {230, 85, 175, 190, 130, 100}; // �ſ���צ
const uint16_t POSE_RETREAT[6]        = {190, 130, 130, 130, 130, 130}; // ̧�𲢳���

// ��������̬��ϳ�һ������
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
 * @brief ִ���Զ��������������
 * @param task Ҫִ�е�����
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
                // ʹ��ͳһ���ٶ���ִ��ÿһ��
                move_to_pose(pick_and_place_sequence[i], 2);
                LL_mDelay(2); // ��ÿһ��֮������ͣ�٣��ö���������
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
 * @brief (���ĸ�������) �û�е���ƶ���һ��ָ����̬
 * @param pose Ŀ����̬������6������Ƕȵ����飩
 * @param speed ���ж��ͳһ���˶��ٶ�
 */
void move_to_pose(const uint16_t pose[6], uint16_t speed)
{
    // ����һ���㹻��Ļ����������������ָ���ַ���
    char command_string[128] = {0}; 
    char part_buffer[20];

    // ѭ��ƴ�����ж����ָ��
    for (int id = 0; id < 6; id++)
    {
        // ��ʽ�����������ָ��֣����� "0:135:20"
        sprintf(part_buffer, "%d:%d:%d", id, pose[id], speed);
        strcat(command_string, part_buffer);
        
        // ����������һ����������ں�����Ӷ���
        if (id < 5)
        {
            strcat(command_string, ",");
        }
    }
    
    // ���ö��ָ�����������������ָ���ַ���
    // ����: "0:135:20,1:150:20,2:100:20,3:130:20,4:130:20,5:100:20"
    servo_cmd_angle(command_string);
}

