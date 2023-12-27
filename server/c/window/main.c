#include <ApplicationServices/ApplicationServices.h>
#include "include/window_osx.h"

int main()
{
    WindowInfo list[100];
    int total = get_window_list(list, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, 0, 10);

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

        //            char filename[256];
        //            snprintf(filename, sizeof(filename), "./screenshot-%02d-%02ld.png", i, list[i].id);
        //
        //            if (get_window_screenshot(list[i].id, list[i].rect, filename)) {
        //                printf("Screenshot Success: %ld, %s\n", list[i].id, filename);
        //            }
        //            else {
        //                printf("Screenshot Fail: %ld, %s\n", list[i].id, filename);
        //            }
    }

    return 0;
}
