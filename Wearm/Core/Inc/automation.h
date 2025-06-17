#ifndef __AUTOMATION_H
#define __AUTOMATION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

// 定义自动化任务的枚举
typedef enum {
    TASK_PICK_AND_PLACE_1, // 任务1：夹取并放置
    TASK_DANCE,            // 任务2：跳舞（示例）
    TASK_COUNT             // 任务总数
} AutomationTask;


/**
 * @brief 执行一个预设的自动化任务
 * @param task 要执行的任务，来自 AutomationTask 枚举
 */
void execute_automation_task(AutomationTask task);


#ifdef __cplusplus
}
#endif

#endif /* __AUTOMATION_H */
