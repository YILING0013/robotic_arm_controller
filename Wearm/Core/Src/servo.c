#include "servo.h"
#include "stm32f1xx_ll_utils.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>


// 定义6个舵机实例
struct servo servos[6] =
{
	[0] = { .timer = TIM2, .channel = LL_TIM_CHANNEL_CH2, },
	[1] = { .timer = TIM4, .channel = LL_TIM_CHANNEL_CH3, },
	[2] = { .timer = TIM4, .channel = LL_TIM_CHANNEL_CH4, },
	[3] = { .timer = TIM4, .channel = LL_TIM_CHANNEL_CH1, },
	[4] = { .timer = TIM4, .channel = LL_TIM_CHANNEL_CH2, },
	[5] = { .timer = TIM3, .channel = LL_TIM_CHANNEL_CH1, },
};

// 这行代码为 g_movement_should_stop 分配了实际的内存空间
volatile uint8_t g_movement_should_stop = 0;


// 内部函数声明
static uint16_t angle_to_pulse(uint8_t id, uint16_t angle);
void servo_init(uint8_t id, uint16_t initial_angle, uint16_t min_angle, uint16_t max_angle, uint16_t min_pulse, uint16_t max_pulse);
void servo_write(uint8_t id, uint16_t target_pulse, uint16_t delay);
void servo_write_angle(uint8_t id, uint16_t angle, uint16_t delay);
void servo_pulse(uint8_t id, uint16_t pulse);
void servo_step(uint8_t id);


int servo_num(void)
{
	return ARRAY_SIZE(servos);
}

void servo_init(uint8_t id, uint16_t initial_angle, uint16_t min_angle, uint16_t max_angle, uint16_t min_pulse, uint16_t max_pulse)
{
	if (id >= servo_num()) return;

	servos[id].angle_min = min_angle;
	servos[id].angle_max = max_angle;
	servos[id].min = min_pulse;
	servos[id].max = max_pulse;
	servos[id].adjust = 0;
	servos[id].delay = 1;

	uint16_t initial_pulse = angle_to_pulse(id, initial_angle);
	servos[id].pulse = servos[id].begin = servos[id].end = initial_pulse;
	
	servo_pulse(id, initial_pulse);
    
	LL_TIM_CC_EnableChannel(servos[id].timer, servos[id].channel);
}

void servos_init_all(void)
{
    const int base_pulse_min = 500;
    const int base_pulse_max = 2500;
    const int base_angle_max = 270;

    uint16_t servo_params[6][3] = {
        {0,   270, 190},
        {50,  210, 130},
        {20,  250, 130},
        {40,  210, 130},
        {40,  210, 130},
        {100, 175, 130}
    };

    for(int id = 0; id < servo_num(); id++)
    {
        uint16_t min_a = servo_params[id][0];
        uint16_t max_a = servo_params[id][1];
        uint16_t init_a = servo_params[id][2];

        uint16_t min_p = base_pulse_min + (uint32_t)min_a * (base_pulse_max - base_pulse_min) / base_angle_max;
        uint16_t max_p = base_pulse_min + (uint32_t)max_a * (base_pulse_max - base_pulse_min) / base_angle_max;
        
        servo_init(id, init_a, min_a, max_a, min_p, max_p);
    }
}

static uint16_t angle_to_pulse(uint8_t id, uint16_t angle)
{
    if (angle < servos[id].angle_min) angle = servos[id].angle_min;
    if (angle > servos[id].angle_max) angle = servos[id].angle_max;
    
    uint32_t pulse_range = servos[id].max - servos[id].min;
    uint32_t angle_range = servos[id].angle_max - servos[id].angle_min;
    
    if (angle_range == 0) return servos[id].min;
    
    return servos[id].min + (uint16_t)(((uint32_t)(angle - servos[id].angle_min) * pulse_range) / angle_range);
}

void servo_write_angle(uint8_t id, uint16_t angle, uint16_t delay)
{
    if (id >= servo_num()) return;
    
    uint16_t target_pulse = angle_to_pulse(id, angle);
    servo_write(id, target_pulse, delay);
}

void servo_write(uint8_t id, uint16_t target_pulse, uint16_t delay)
{
	if (id >= servo_num()) return;

	if (target_pulse < servos[id].min) target_pulse = servos[id].min;
	if (target_pulse > servos[id].max) target_pulse = servos[id].max;

	if (delay < 1) delay = 1;

	servos[id].begin = servos[id].pulse;
	servos[id].end = target_pulse;
	servos[id].delay = delay;
}

uint16_t servo_read(uint8_t id)
{
	if (id >= servo_num()) return 0;
	return servos[id].pulse;
}

void servo_pulse(uint8_t id, uint16_t pulse)
{
	if (id >= servo_num()) return;

	if (pulse < 500) pulse = 500;
	if (pulse > 2500) pulse = 2500;

	switch (servos[id].channel)
	{
	case LL_TIM_CHANNEL_CH1: LL_TIM_OC_SetCompareCH1(servos[id].timer, pulse); break;
	case LL_TIM_CHANNEL_CH2: LL_TIM_OC_SetCompareCH2(servos[id].timer, pulse); break;
	case LL_TIM_CHANNEL_CH3: LL_TIM_OC_SetCompareCH3(servos[id].timer, pulse); break;
	case LL_TIM_CHANNEL_CH4: LL_TIM_OC_SetCompareCH4(servos[id].timer, pulse); break;
	}
}

void servo_step(uint8_t id)
{
	if (id >= servo_num()) return;
	if (servos[id].pulse == servos[id].end) return;

	if (servos[id].pulse > servos[id].end) servos[id].pulse--;
	else if (servos[id].pulse < servos[id].end) servos[id].pulse++;

	servo_pulse(id, servos[id].pulse + servos[id].adjust);
}

void servo_adjust(uint8_t id, int16_t adjust)
{
	if (id >= servo_num()) return;
	int pulse = servos[id].pulse;
	servo_pulse(id, servos[id].pulse + adjust);
	servos[id].adjust = adjust;
	servos[id].pulse = servos[id].end = pulse;
}

int servo_run(void)
{
	int running;
	int time = 0;
	
	g_movement_should_stop = 0; 
	
	do
	{
		if (g_movement_should_stop)
		{
			for (int id = 0; id < servo_num(); id++)
			{
				servos[id].end = servos[id].pulse; 
			}
			g_movement_should_stop = 0;
			printf("Movement stopped by command.\n");
			break;
		}

		running = 0;
		for (int id = 0; id < servo_num(); id++)
		{
			if (servos[id].pulse != servos[id].end)
			{
				running = 1;
				if (!(time % servos[id].delay))
				{
					servo_step(id);
				}
			}
		}
		if(running)
		{
			LL_mDelay(1); 
			time++;
		}
	} while (running); 

	return time;
}

void servo_cmd_angle(char *arg)
{
	if (arg[0])
	{
		for (char *param = strtok(arg, ","); param; param = strtok(NULL, ","))
		{
			int id, delay, angle;
			sscanf(param, "%d:%d:%d", &id, &angle, &delay);
			servo_write_angle(id, angle, delay);
		}
		servo_run();
	}

	for (int id = 0; id < servo_num(); id++)
	{
		if (id) printf(",");
		printf("%d:%d:1", id, servo_read(id));
	}
	printf("\n");
	puts("OK");
}
