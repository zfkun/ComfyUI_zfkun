//
// Created by zfkun on 2023/12/26.
//

#include <ApplicationServices/ApplicationServices.h>

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

const CFIndex kBufferSize = 256;

int get_window_list(WindowInfo *list, unsigned int option, unsigned int relativeToWindow, long layer, int max)
{
    CFArrayRef windowList = CGWindowListCopyWindowInfo(option, relativeToWindow);

    int total = 0;

    CFIndex count = CFArrayGetCount(windowList);
    CFIndex i = 0;
    for (; i < count; i++)
    {
        CFDictionaryRef window = CFArrayGetValueAtIndex(windowList, i);

        CFNumberRef windowId = CFDictionaryGetValue(window, kCGWindowNumber);
        if (windowId == NULL)
            continue;
        long c_id;
        CFNumberGetValue(windowId, kCFNumberLongType, &c_id);

        CFNumberRef windowLayer = CFDictionaryGetValue(window, kCGWindowLayer);
        if (windowLayer == NULL)
            continue;
        long c_layer;
        CFNumberGetValue(windowLayer, kCFNumberLongType, &c_layer);

        if (c_layer != layer)
            continue;

        // layer
        list[total].layer = c_layer;

        // id
        list[total].id = c_id;

        // name
        CFStringRef windowName = CFDictionaryGetValue(window, kCGWindowName);
        if (windowName)
        {
            char c_name[kBufferSize];
            if (CFStringGetCString(windowName, c_name, kBufferSize, kCFStringEncodingUTF8))
            {
                strncpy(list[total].name, c_name, kBufferSize);
            }
        }

        // rect
        CGRect c_bounds;
        CGRectMakeWithDictionaryRepresentation(CFDictionaryGetValue(window, kCGWindowBounds), &c_bounds);
        list[total].rect[0] = (float)c_bounds.origin.x;
        list[total].rect[1] = (float)c_bounds.origin.y;
        list[total].rect[2] = (float)c_bounds.size.width;
        list[total].rect[3] = (float)c_bounds.size.height;

        // pid
        CFNumberGetValue(CFDictionaryGetValue(window, kCGWindowOwnerPID), kCFNumberIntType, &(list[total].pid));

        // ownerName
        CFStringRef ownerName = CFDictionaryGetValue(window, kCGWindowOwnerName);
        if (ownerName)
        {
            char c_owner_name[kBufferSize];
            if (CFStringGetCString(ownerName, c_owner_name, kBufferSize, kCFStringEncodingUTF8))
            {
                strncpy(list[total].ownerName, c_owner_name, kBufferSize);
            }
        }

        total++;
        if (total >= max)
            break;
    }

    CFRelease(windowList);
    return total;
}

bool get_window_screenshot(long id, float rect[4], const char *filename)
{
    bool ok = false;

    CGRect bounds = CGRectMake((CGFloat)rect[0], (CGFloat)rect[1], (CGFloat)rect[2], (CGFloat)rect[3]);

    CGImageRef screenshot = CGWindowListCreateImage(bounds, kCGWindowListOptionIncludingWindow, (CGWindowID)id, kCGWindowImageBoundsIgnoreFraming);
    if (screenshot)
    {
        CFURLRef url = CFURLCreateWithFileSystemPath(kCFAllocatorDefault, CFStringCreateWithCString(NULL, filename, kCFStringEncodingUTF8), kCFURLPOSIXPathStyle, false);
        if (url)
        {
            CGImageDestinationRef destination = CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, NULL);
            if (destination)
            {
                CGImageDestinationAddImage(destination, screenshot, NULL);
                ok = CGImageDestinationFinalize(destination);
                CFRelease(destination);
            }
            CFRelease(url);
        }
        CGImageRelease(screenshot);
    }

    return ok;
}