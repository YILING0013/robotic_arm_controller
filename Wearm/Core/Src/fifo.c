#include "fifo.h"
#include <stdio.h>

// 初始化队列
void fifo_init(struct fifo* q) {
    q->front = 0;
    q->rear = 0;
}

// 检查队列是否为空
int fifo_is_empty(struct fifo* q) {
    return q->front == q->rear;
}

// 计算下一个位置
static inline int next_pos(int pos) {
    return (pos + 1) % FIFO_SIZE;
}

// 检查队列是否已满
int fifo_is_full(struct fifo* q) {
    return next_pos(q->rear) == q->front;
}

// 入队操作
int fifo_enqueue(struct fifo* q, char v) {
    if (fifo_is_full(q)) {
        return 0;
    }
    q->array[q->rear] = v;
    q->rear = next_pos(q->rear);
    return 1;
}

// 出队操作
int fifo_dequeue(struct fifo* q, char* v) {
    if (fifo_is_empty(q)) {
        return 0;
    }
    *v = q->array[q->front];
    q->front = next_pos(q->front);
    return 1;
}

// 打印队列中的内容
void fifo_print(struct fifo* q) {
    for (int i = q->front; i != q->rear; i = next_pos(i)) {
        printf("%x ", q->array[i]);
    }
    printf("\n");
}
