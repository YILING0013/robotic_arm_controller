#ifndef __AUTOMATION_H
#define __AUTOMATION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

// �����Զ��������ö��
typedef enum {
    TASK_PICK_AND_PLACE_1, // ����1����ȡ������
    TASK_DANCE,            // ����2�����裨ʾ����
    TASK_COUNT             // ��������
} AutomationTask;


/**
 * @brief ִ��һ��Ԥ����Զ�������
 * @param task Ҫִ�е��������� AutomationTask ö��
 */
void execute_automation_task(AutomationTask task);


#ifdef __cplusplus
}
#endif

#endif /* __AUTOMATION_H */
