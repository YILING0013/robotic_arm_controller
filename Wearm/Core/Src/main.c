/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "servo.h"
#include "automation.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define RX_BUFFER_SIZE 128 // 定义接收缓冲区大小
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */
// --- 新增：用于中断接收的全局变量 ---
char rx_buffer[RX_BUFFER_SIZE];                     // 原始中断接收缓冲区
volatile uint16_t rx_buffer_index = 0;              // 缓冲区写入索引
volatile uint8_t g_new_command_received = 0;        // 新指令接收完成标志
char line_buffer[RX_BUFFER_SIZE];                   // 存储一行完整指令供主循环处理
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void process_command(char* cmd); // 指令处理函数
void clear_rx_buffer(void);      // 清空接收缓冲区函数
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/**
  * @brief 清空软件接收缓冲区
  */
void clear_rx_buffer(void) {
    rx_buffer_index = 0;
    // (可选) 如果需要，可以加入代码清空硬件FIFO，但通常清空软件缓冲区即可
}

/**
  * @brief USART1中断服务程序
  * @note  这是实现即时响应的关键
  */
void USART1_IRQHandler(void)
{
    // 检查是否是接收非空中断
    if(LL_USART_IsActiveFlag_RXNE(USART1) && LL_USART_IsEnabledIT_RXNE(USART1))
    {
        char received_char = LL_USART_ReceiveData8(USART1); // 读取接收到的字符

        // 判断是否是行尾字符
        if (received_char == '\n' || received_char == '\r')
        {
            if (rx_buffer_index > 0) // 确保不是空行
            {
                rx_buffer[rx_buffer_index] = '\0'; // 添加字符串结束符

                // --- 关键：立即处理 stop 指令 ---
                if (strcmp((const char*)rx_buffer, "stop") == 0) {
                    g_movement_should_stop = 1; // 设置全局停止标志
                    clear_rx_buffer();          // 清空缓冲区，丢弃后续指令
                    puts("STOP CMD RECV");      // 向上位机发送确认信息
                } else {
                    // 对于其他指令，复制到处理缓冲区，并设置标志位通知主循环
                    strcpy(line_buffer, (const char*)rx_buffer);
                    g_new_command_received = 1;
                    rx_buffer_index = 0; // 重置缓冲区索引，准备接收下一条指令
                }
            }
        }
        else // 如果不是行尾字符
        {
            // 将字符存入缓冲区
            if (rx_buffer_index < RX_BUFFER_SIZE - 1)
            {
                rx_buffer[rx_buffer_index++] = received_char;
            }
        }
    }
}

/**
  * @brief 指令处理函数
  * @param cmd 指向指令字符串的指针
  */
void process_command(char* cmd)
{
    if(strlen(cmd) == 0) return;

    if (strcmp(cmd, "beep") == 0)
    {
        printf("BEEP CMD\n");
        LL_GPIO_SetOutputPin(BEEP_GPIO_Port, BEEP_Pin);
        LL_mDelay(200);
        LL_GPIO_ResetOutputPin(BEEP_GPIO_Port, BEEP_Pin);
        puts("OK");
    }
    else if (strncmp(cmd, "run ", 4) == 0)
    {
        int task_id;
        sscanf(cmd + 4, "%d", &task_id); 
        if(task_id >= 0 && task_id < TASK_COUNT)
        {
            execute_automation_task((AutomationTask)task_id);
        }
        else
        {
            printf("Invalid task ID.\n");
        }
    }
    else
    {
        // 手动控制指令
        printf("MANUAL CMD: %s\n", cmd);
        servo_cmd_angle(cmd); // 这个函数会调用可中断的 servo_run()
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_AFIO);
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);

  /* System interrupt init*/
  NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);

  /* SysTick_IRQn interrupt configuration */
  NVIC_SetPriority(SysTick_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),15, 0));

  /** DISABLE: JTAG-DP Disabled and SW-DP Disabled
  */
  LL_GPIO_AF_DisableRemap_SWJ();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_TIM3_Init();
  MX_TIM2_Init();
  MX_TIM4_Init();
  /* USER CODE BEGIN 2 */
	
    // --- 新增：使能串口接收中断 ---
    LL_USART_EnableIT_RXNE(USART1);
    NVIC_SetPriority(USART1_IRQn, 0); // 设置中断优先级
    NVIC_EnableIRQ(USART1_IRQn);      // 在NVIC中使能中断

    servos_init_all();
    LL_mDelay(500);
    servo_run();
    LL_mDelay(500);
    
    // 更新使用说明
    puts("Servo control system ready.");
    puts("MANUAL: id:angle:delay,id:angle:delay...");
    puts("STOP: stop"); // <-- 新增
    puts("AUTO: run <task_id>");
    puts("BEEP: beep");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
    // --- 修改后的主循环 ---
    while (1)
    { 
        // 检查是否有新指令需要处理
        if (g_new_command_received)
        {
            g_new_command_received = 0; // 清除标志位
            process_command(line_buffer); // 处理指令
        }
        
        // 主循环现在是非阻塞的，可以在这里添加其他后台任务
        // LL_mDelay(10); // 可以加入短暂延时降低CPU占用率
    }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  LL_FLASH_SetLatency(LL_FLASH_LATENCY_2);
  while(LL_FLASH_GetLatency()!= LL_FLASH_LATENCY_2)
  {
  }
  LL_RCC_HSE_Enable();

   /* Wait till HSE is ready */
  while(LL_RCC_HSE_IsReady() != 1)
  {

  }
  LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE_DIV_1, LL_RCC_PLL_MUL_9);
  LL_RCC_PLL_Enable();

   /* Wait till PLL is ready */
  while(LL_RCC_PLL_IsReady() != 1)
  {

  }
  LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
  LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_2);
  LL_RCC_SetAPB2Prescaler(LL_RCC_APB2_DIV_1);
  LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);

   /* Wait till System clock is ready */
  while(LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL)
  {

  }
  LL_Init1msTick(72000000);
  LL_SetSystemCoreClock(72000000);
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  * where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
