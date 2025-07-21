// gcc -finput-charset=UTF-8 main.c src/window_win.c -o libwindow.exe -lgdi32 -luser32
// gcc -finput-charset=UTF-8 main.c src/window_osx.c -shared -o libwindow.dll -lgdi32 -luser32

// gcc -Wno-deprecated-declarations -framework "ApplicationServices" main.c src/window_osx.c -o libwindow
// gcc -Wno-deprecated-declarations -framework "ApplicationServices" main.c src/window_osx.c -shared -o libwindow.dylib

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(WIN32) || defined(_WIN32)
    #include "include/window_win.h"
#else
    #include <ApplicationServices/ApplicationServices.h>
    #include "include/window_osx.h"
#endif

#include "include/window.h"
int main()
{
    WindowInfo list[100];

#if defined(WIN32) || defined(_WIN32)
    int total = get_window_list(list, WINDOW_LIST_OPTION_ON_SCREEN_ONLY, NULL_WINDOW_ID, 0, 100);
#else
    int total = get_window_list(list, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, 0, 100);
#endif

    int i;
    for (i = 0; i < total; i++)
    {
        printf("Window %d: layer = %ld, id = %ld, name = %s, pid = %d, ownerName = %s, bounds = (%f, %f, %f, %f)\n",
               i,
               list[i].layer,
               list[i].id,
               list[i].name,
               list[i].pid,
               list[i].ownerName,
               list[i].rect[0],
               list[i].rect[1],
               list[i].rect[2],
               list[i].rect[3]);
    }

    // single window screenshot
    for (i = 0; i < total; i++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "./screenshot-%02d-%02ld.png", i, list[i].id);

        if (get_window_screenshot(list[i].id, list[i].rect, filename)) {
            printf("Screenshot Success: %ld, %s\n", list[i].id, filename);
        } else {
            printf("Screenshot Fail: %ld, %s\n", list[i].id, filename);
        }
    }

    #if defined(__APPLE__)
        printf("CGRectNull: origin=(%f, %f), size=(%f, %f)\n", CGRectNull.origin.x, CGRectNull.origin.y, CGRectNull.size.width, CGRectNull.size.height);
    #endif

    // multi window combine screenshot
    long *ids = (long *)malloc(total * sizeof(long));
    if (ids == NULL) {
        fprintf(stderr, "malloc fail\n");
        return 1;
    }

    for (i = 0; i < total; i++)
    {
        ids[i] = list[i].id;
    }
    const char *filename = "./screenshot-all.png";
    float bounds[4] = {0, 0, 0,0}; // CGRectNull
    int res = get_window_screenshots(ids, total, bounds, filename);
    if (res == 0) {
        printf("Screenshot All Success: %d, %d, %s\n", res, total, filename);
    }
    else {
        printf("Screenshot All Fail: %d, %d, %s\n", res, total, filename);
    }

    // multi window combine screenshot
    const char *filename512 = "./screenshot-all-512.png";
    float bounds512[4] = {0, 0, 512, 512};
    int res2 = get_window_screenshots(ids, total, bounds512, filename512);
    if (res2 == 0) {
        printf("Screenshot All 512 Success: %d, %d, %s\n", res, total, filename512);
    }
    else {
        printf("Screenshot All 512 Fail: %d, %d, %s\n", res, total, filename512);
    }

    free(ids);

    return 0;
}
