#ifndef FIFO_H
#define FIFO_H

#define FIFO_SIZE 1024 // 定义队列的最大长度

/**
 * @struct fifo
 * @brief 队列结构体
 */
struct fifo {
    int front;            ///< 队列头部索引
    int rear;             ///< 队列尾部索引
    char array[FIFO_SIZE]; ///< 存储队列元素的数组
};

/**
 * @brief 初始化队列
 * @param q 指向队列结构体的指针
 */
void fifo_init(struct fifo* q);

/**
 * @brief 检查队列是否为空
 * @param q 指向队列结构体的指针
 * @return 如果队列为空返回1，否则返回0
 */
int fifo_is_empty(struct fifo* q);

/**
 * @brief 检查队列是否已满
 * @param q 指向队列结构体的指针
 * @return 如果队列已满返回1，否则返回0
 */
int fifo_is_full(struct fifo* q);

/**
 * @brief 将元素入队
 * @param q 指向队列结构体的指针
 * @param v 要入队的元素
 * @return 如果成功入队返回1，如果队列已满返回0
 */
int fifo_enqueue(struct fifo* q, char v);

/**
 * @brief 将元素出队
 * @param q 指向队列结构体的指针
 * @param v 指向存储出队元素的变量
 * @return 如果成功出队返回1，如果队列为空返回0
 */
int fifo_dequeue(struct fifo* q, char* v);

/**
 * @brief 打印队列中的内容
 * @param q 指向队列结构体的指针
 */
void fifo_print(struct fifo* q);

#endif // FIFO_H
