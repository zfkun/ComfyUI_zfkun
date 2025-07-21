//
// Created by zfkun on 2025/07/20.
//

#include <stdbool.h>

typedef struct
{
    // window id
    long id;
    // window name
    char name[256];
    // window bounds
    float rect[4];

    // window owner pid
    int pid;
    // window owner name
    char ownerName[256];

    // window layer
    long layer;
} WindowInfo;

int get_window_list(WindowInfo *list, unsigned int option, unsigned int relativeToWindow, long layer, int max);

bool get_window_screenshot(long id, float rect[4], const char *filename);

bool get_window_screenshots(long *ids, int count, float rect[4], const char *filename);
