//
// Created by zfkun on 2023/12/26.
//

#ifndef WINDOW_OSX_H_
#define WINDOW_OSX_H_

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

#endif // WINDOW_OSX_H_
