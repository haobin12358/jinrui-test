#ifndef _SHEET_MANAGER_H_
#define _SHEET_MANAGER_H_

#include <stdint.h>

typedef void HuManager;


/***********************************
 * 返回值
 ***********************************/
#define HU_SHEET_RET_OK 0
#define HU_SHEET_RET_LOAD_MODEL_ERROR         0x00000010
#define HU_SHEET_RET_RELEASE_ERROR            0x00000020
#define HU_SHEET_RET_PROCESS_ERROR            0x00000030
#define HU_SHEET_RET_PROCESS_LOAD_IMAGE_ERROR 0x00000031
#define HU_SHEET_RET_PROCESS_PARAMS_ERROR     0x00000032
#define HU_SHEET_RET_PROCESS_TYPE_ERROR       0x00000033


/***********************************
 * 图片类型
 ***********************************/
#define HU_SHEET_TYPE_SINGLE_CHOICE 0
#define HU_SHEET_TYPE_MULTI_CHOICE  1
#define HU_SHEET_TYPE_CARD_NUM      2
#define HU_SHEET_TYPE_STATE         3
#define HU_SHEET_TYPE_SCORE         4
#define HU_SHEET_TYPE_UUID          5

/*****************************************************
 * 加载识别器
 *
 * 参数:
 *     modelDir    模型目录
 *     prefix      前缀,固定设置为sheet
 *     rmanager    识别器指针存放地址
 *****************************************************/
int sheet_manager_load(const char *modelDir, const char *prefix, HuManager **rmanager);


/*****************************************************
 * 识别
 *
 * 参数:
 *     manager     识别器,由sheet_load_manager创建
 *     imgPath     图片文件路径
 *     type        图片类型,值从HU_SHEET_TYPE_*中选择
 *
 *****************************************************/
int sheet_manager_process(HuManager *manager, const char *imgPath, int type, char *result);

/*****************************************************
 * 释放识别器
 *****************************************************/
void sheet_manager_release(HuManager **rmanager);

#endif
