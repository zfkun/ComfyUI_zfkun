//
// Created by zfkun on 2025/07/12.
//

#ifndef WINDOW_WIN_H_
#define WINDOW_WIN_H_

#include <windows.h>

typedef enum {
    WINDOW_LIST_OPTION_ALL = 0,
    WINDOW_LIST_OPTION_ON_SCREEN_ONLY = 1 << 0,
    WINDOW_LIST_OPTION_ON_SCREEN_ABOVE_WINDOW = 1 << 1,
    WINDOW_LIST_OPTION_ON_SCREEN_BELOW_WINDOW = 1 << 2,
    WINDOW_LIST_OPTION_INCLUDING_WINDOW = 1 << 3,
    WINDOW_LIST_EXCLUDE_DESKTOP_ELEMENTS = 1 << 4
} WindowListOption;

#ifndef NULL_WINDOW_ID
#define NULL_WINDOW_ID 0
#endif

#endif // WINDOW_WIN_H_