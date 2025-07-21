#if defined(WIN32) || defined(_WIN32)

#include <stdbool.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef WINDOW_WIN_H_

#ifndef NULL_WINDOW_ID
#define NULL_WINDOW_ID 0
#endif

typedef struct {
    long id;
    char name[256];
    float rect[4]; // left, top, right, bottom

    int pid;
    char ownerName[256];

    long layer;
} WindowInfo;

typedef enum {
    WINDOW_LIST_OPTION_ALL = 0,
    WINDOW_LIST_OPTION_ON_SCREEN_ONLY = 1 << 0,
    WINDOW_LIST_OPTION_ON_SCREEN_ABOVE_WINDOW = 1 << 1,
    WINDOW_LIST_OPTION_ON_SCREEN_BELOW_WINDOW = 1 << 2,
    WINDOW_LIST_OPTION_INCLUDING_WINDOW = 1 << 3,
    WINDOW_LIST_EXCLUDE_DESKTOP_ELEMENTS = 1 << 4
} WindowListOption;

#endif

typedef struct {
    WindowListOption option; // 窗口过滤选项
    HWND relativeToWindow; // 相对窗口（如果有）;
    WindowInfo* list;  // 必须指向长度为 max 的数组
    int count;         // 实际有效元素数
    int max;           // 数组总容量
    int index;
} EnumWindowsContext;

BOOL IsSystemWindow(HWND hwnd) {
    char className[256];
    GetClassNameA(hwnd, className, sizeof(className));
    
    // 常见系统窗口类名
    const char* systemClasses[] = {
        "Windows.UI.Core.CoreWindow",   // UWP窗口
        "IME",                          // 输入法
        "MSCTFIME UI",                  // 文本服务框架
        "SysShadow",                    // 阴影窗口
        NULL
    };
    
    for(int i = 0; systemClasses[i]; i++) {
        if(strcmp(className, systemClasses[i]) == 0) {
            return TRUE;
        }
    }
    return FALSE;
}


// 窗口枚举回调函数
BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam) {
    // 跳过无效窗口句柄
    if (hwnd == NULL) {
        return TRUE;
    }

    // 跳过不可见窗口
    if (!IsWindowVisible(hwnd) || !IsWindowEnabled(hwnd)) {
        return TRUE;
    }

    // 跳过最小化窗口
    if (IsIconic(hwnd)) {
        return TRUE;
    }

    // 跳过系统窗口
    if (IsSystemWindow(hwnd)) {
        return TRUE;
    }

    // 跳过子窗口
    HWND root = GetAncestor(hwnd, GA_ROOTOWNER);
    if (root != hwnd) {
        return TRUE;
    }

    // 检查窗口样式 (排除工具窗口、隐藏窗口等)
    LONG_PTR styles = GetWindowLongPtr(hwnd, GWL_STYLE);
    if (styles & WS_DISABLED || !(styles & WS_VISIBLE)) {
        return TRUE;
    }

    // 检查窗口扩展样式 (排除ComboBox下拉列表等)
    LONG_PTR exStyles = GetWindowLongPtr(hwnd, GWL_EXSTYLE);
    if (exStyles & WS_EX_TOOLWINDOW || exStyles & WS_EX_NOACTIVATE) {
        return TRUE;
    }
    // 过滤透明输入法窗口
    if ((exStyles & WS_EX_TRANSPARENT) && 
        (exStyles & WS_EX_LAYERED) && 
        (exStyles & WS_EX_NOACTIVATE)) {
        return TRUE;
    }

    // 过滤透明窗口 (alpha通道全透明)
    if (GetLayeredWindowAttributes(hwnd, NULL, NULL, NULL) && 
        (exStyles & WS_EX_LAYERED)) {
        return TRUE;
    }


    EnumWindowsContext* ctx = (EnumWindowsContext*)lParam;

    if (ctx->option & WINDOW_LIST_OPTION_ALL) {
        // 包含所有窗口
        // 这里不做任何过滤
    } else {
        // 跳过非指定窗口
        if (ctx->option & WINDOW_LIST_OPTION_INCLUDING_WINDOW) {
            if (ctx->relativeToWindow == NULL || hwnd != ctx->relativeToWindow) return TRUE;
        }

        // 跳过非屏幕上的窗口
        if (ctx->option & WINDOW_LIST_OPTION_ON_SCREEN_ONLY) {
            RECT rect;
            if (!GetWindowRect(hwnd, &rect) || 
                (rect.right <= 0 || rect.bottom <= 0 || rect.left >= GetSystemMetrics(SM_CXSCREEN) || rect.top >= GetSystemMetrics(SM_CYSCREEN))) {
                return TRUE;
            }
        }

        // 跳过桌面元素
        if (ctx->option & WINDOW_LIST_EXCLUDE_DESKTOP_ELEMENTS) {
            if (hwnd == GetDesktopWindow() || hwnd == GetShellWindow()) {
                return TRUE;
            }
        }

        // 查找指定窗口的上/下窗口
        if (ctx->relativeToWindow != NULL) {
            if ((ctx->option & WINDOW_LIST_OPTION_ON_SCREEN_ABOVE_WINDOW) || ctx->option & WINDOW_LIST_OPTION_ON_SCREEN_BELOW_WINDOW) {
                if (hwnd == ctx->relativeToWindow) return TRUE;

                RECT relativeRect;
                GetWindowRect(ctx->relativeToWindow, &relativeRect);
                
                RECT currentRect;
                GetWindowRect(hwnd, &currentRect);

                // 查找指定窗口上方的窗口
                if (ctx->option & WINDOW_LIST_OPTION_ON_SCREEN_ABOVE_WINDOW) {
                    if (currentRect.top > relativeRect.top) {
                        return TRUE;
                    }
                }
                
                // 查找指定窗口下方的窗口
                if (ctx->option & WINDOW_LIST_OPTION_ON_SCREEN_BELOW_WINDOW) {
                    if (currentRect.bottom < relativeRect.bottom) {
                        return TRUE;
                    }
                }
            }
        }
    }

    WindowInfo* info = &ctx->list[ctx->index];
    info->id = (long)(LONG_PTR)hwnd;

    // 获取窗口PID
    GetWindowThreadProcessId(hwnd, (LPDWORD)&info->pid);
    
    // 获取窗口标题
    GetWindowTextA(hwnd, info->name, sizeof(info->name));
    
    // 跳过标题为空的窗口
    if (strlen(info->name) == 0) {
      return TRUE;
    }

    // 获取窗口位置尺寸
    RECT rect;
    GetWindowRect(hwnd, &rect);
    info->rect[0] = (float)rect.left;
    info->rect[1] = (float)rect.top;
    info->rect[2] = (float)rect.right;
    info->rect[3] = (float)rect.bottom;

    // 忽略过小的窗口
    if (rect.right - rect.left <= 10 || rect.bottom - rect.top <= 10) {
        return TRUE;
    }
    
    // 确保不超过最大数量
    if (ctx->count > ctx->max) {
        return TRUE;
    }

    ctx->count++;
    ctx->index++;
    
    return TRUE;
}


// 获取所有可见窗口信息
// __declspec(dllexport) int GetAllWindows(WindowInfo* windows, int max) {
__declspec(dllexport) int get_window_list(WindowInfo *list, unsigned int option, unsigned int relativeToWindow, long layer, int max) {
    EnumWindowsContext context = { 
      .list = list,
      .count = 0,
      .max = max,
      .index = 0,
      .option = (WindowListOption)option,
      .relativeToWindow = (HWND)(LONG_PTR)relativeToWindow,
    };
    EnumWindows(EnumWindowsProc, (LPARAM)&context);
    
    return context.count;
}


// 单窗口截图
__declspec(dllexport) bool get_window_screenshot(long id, float rect[4], const char *filename)
{
    HWND hwnd = (HWND)(LONG_PTR)id;
  
    if (hwnd == NULL) {
        return FALSE;
    }

    if (!IsWindowVisible(hwnd)) {
        return FALSE;
    }

    // 获取窗口位置和大小
    // RECT rect;
    // GetWindowRect(hwnd, &rect);
    // int width = rect.right - rect.left;
    // int height = rect.bottom - rect.top;
    int width = rect[2] - rect[0];
    int height = rect[3] - rect[1];
    
    // 排除过小的窗口
    if (width <= 10 || height <= 10) {
        return FALSE;
    }


    HDC hdcScreen = GetDC(NULL);
    HDC hdcWindow = GetDC(hwnd);
    HDC hdcMemDC = CreateCompatibleDC(hdcWindow);

    // 关键修改1：创建位图时使用负高度
    BITMAPINFO bmi = {0};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height;  // 负值表示从上到下的位图
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    
    void* pBits = NULL;
    HBITMAP hBitmap = CreateDIBSection(hdcMemDC, &bmi, DIB_RGB_COLORS, &pBits, NULL, 0);

    SelectObject(hdcMemDC, hBitmap);

    // 方法1：尝试PrintWindow（支持更多窗口类型）
    BOOL result = PrintWindow(hwnd, hdcMemDC, PW_RENDERFULLCONTENT);
    
    // 方法2：如果失败，尝试带延迟的BitBlt
    if (!result) {
        Sleep(100); // 给窗口渲染时间
        result = BitBlt(hdcMemDC, 0, 0, width, height, hdcScreen, 
                       rect[0], rect[1], SRCCOPY | CAPTUREBLT);
    }

    // 方法3：如果仍失败，尝试获取客户区
    if (!result) {
        RECT clientRect;
        GetClientRect(hwnd, &clientRect);
        POINT pt = {0, 0};
        ClientToScreen(hwnd, &pt);
        result = BitBlt(hdcMemDC, 0, 0, 
                       clientRect.right - clientRect.left,
                       clientRect.bottom - clientRect.top,
                       hdcScreen, pt.x, pt.y, SRCCOPY | CAPTUREBLT);
    }

    if (!result) {
        DeleteObject(hBitmap);
        DeleteDC(hdcMemDC);
        ReleaseDC(NULL, hdcScreen);
        ReleaseDC(hwnd, hdcWindow);
        return FALSE;
    }

    // 检查截图是否全黑
    BITMAP bmpInfo;
    GetObject(hBitmap, sizeof(BITMAP), &bmpInfo);
    if (bmpInfo.bmBitsPixel == 32) {
        DWORD* pixels = (DWORD*)malloc(width * height * 4);
        GetBitmapBits(hBitmap, width * height * 4, pixels);
        
        BOOL isBlack = TRUE;
        for (int i = 0; i < width * height; i++) {
            if (pixels[i] != 0xFF000000) { // 非全黑像素
                isBlack = FALSE;
                break;
            }
        }
        free(pixels);
        
        if (isBlack) {
            DeleteObject(hBitmap);
            DeleteDC(hdcMemDC);
            ReleaseDC(NULL, hdcScreen);
            ReleaseDC(hwnd, hdcWindow);
            return FALSE;
        }
    }

    // 保存BMP文件
    BITMAPFILEHEADER bmfh = {0};
    BITMAPINFOHEADER bmih = {0};

    bmih.biSize = sizeof(BITMAPINFOHEADER);
    bmih.biWidth = width;
    bmih.biHeight = -height;  // 保持负高度
    bmih.biPlanes = 1;
    bmih.biBitCount = 32;
    bmih.biCompression = BI_RGB;
    bmih.biSizeImage = width * height * 4;
    // bmih.biXPelsPerMeter = 0;
    // bmih.biYPelsPerMeter = 0;
    // bmih.biClrUsed = 0;
    // bmih.biClrImportant = 0;

    // 设置文件头
    bmfh.bfType = 0x4D42; // "BM"
    bmfh.bfSize = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER) + bmih.biSizeImage;
    bmfh.bfReserved1 = 0;
    bmfh.bfReserved2 = 0;
    bmfh.bfOffBits = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);
    
    // 创建并写入文件
    FILE* file = fopen(filename, "wb");
    if (!file) {
        DeleteObject(hBitmap);
        DeleteDC(hdcMemDC);
        ReleaseDC(NULL, hdcScreen);
        ReleaseDC(hwnd, hdcWindow);
        return FALSE;
    }
    
    fwrite(&bmfh, sizeof(BITMAPFILEHEADER), 1, file);
    fwrite(&bmih, sizeof(BITMAPINFOHEADER), 1, file);
    fwrite(pBits, bmih.biSizeImage, 1, file);
    
    // 清理资源
    fclose(file);
    DeleteObject(hBitmap);
    DeleteDC(hdcMemDC);
    ReleaseDC(NULL, hdcScreen);
    ReleaseDC(hwnd, hdcWindow);
    
    return TRUE;
}


// 批量窗口截图
__declspec(dllexport) bool get_window_screenshots(long *ids, int count, float rect[4], const char *filename) 
{
    if(!ids || count <= 0 || !rect || !filename) 
        return false;

    // 1. 确定截图区域
    RECT screenRect;
    if(rect[0] == 0 && rect[1] == 0 && rect[2] == 0 && rect[3] == 0) {
        // 获取整个屏幕区域
        screenRect.left = 0;
        screenRect.top = 0;
        screenRect.right = GetSystemMetrics(SM_CXSCREEN);
        screenRect.bottom = GetSystemMetrics(SM_CYSCREEN);
    } else {
        // 使用指定的rect区域
        screenRect.left = (int)rect[0];
        screenRect.top = (int)rect[1];
        screenRect.right = (int)rect[2];
        screenRect.bottom = (int)rect[3];
    }

    int width = screenRect.right - screenRect.left;
    int height = screenRect.bottom - screenRect.top;
    
    if(width <= 0 || height <= 0) 
        return false;

    // 2. 创建内存DC和位图
    HDC hdcScreen = GetDC(NULL);
    HDC hdcMem = CreateCompatibleDC(hdcScreen);
    HBITMAP hBitmap = CreateCompatibleBitmap(hdcScreen, width, height);
    HBITMAP hOldBitmap = (HBITMAP)SelectObject(hdcMem, hBitmap);

    // 3. 先截取整个屏幕区域
    BitBlt(hdcMem, 0, 0, width, height,
          hdcScreen, screenRect.left, screenRect.top, SRCCOPY);

    // 4. 创建掩码区域(只保留目标窗口)
    HRGN hrgnTotal = CreateRectRgn(0, 0, 0, 0);
    for(int i = 0; i < count; i++) {
        HWND hwnd = (HWND)(LONG_PTR)ids[i];
        if(!IsWindowVisible(hwnd)) continue;

        RECT winRect;
        GetWindowRect(hwnd, &winRect);
        
        // 计算窗口与截图区域的交集
        int left = max(winRect.left, screenRect.left) - screenRect.left;
        int top = max(winRect.top, screenRect.top) - screenRect.top;
        int right = min(winRect.right, screenRect.right) - screenRect.left;
        int bottom = min(winRect.bottom, screenRect.bottom) - screenRect.top;

        if(left >= right || top >= bottom) continue;

        // 创建窗口区域并合并
        HRGN hrgnWindow = CreateRectRgn(left, top, right, bottom);
        CombineRgn(hrgnTotal, hrgnTotal, hrgnWindow, RGN_OR);
        DeleteObject(hrgnWindow);
    }

    // 5. 应用区域掩码(只保留目标窗口区域)
    HBITMAP hMask = CreateBitmap(width, height, 1, 1, NULL);
    HDC hdcMask = CreateCompatibleDC(NULL);
    SelectObject(hdcMask, hMask);
    
    // 绘制白色背景
    BitBlt(hdcMask, 0, 0, width, height, NULL, 0, 0, WHITENESS);
    
    // 在掩码上绘制目标区域
    FillRgn(hdcMask, hrgnTotal, (HBRUSH)GetStockObject(BLACK_BRUSH));
    
    // 应用掩码
    BitBlt(hdcMem, 0, 0, width, height,
          hdcMask, 0, 0, SRCPAINT);

    // 6. 保存BMP文件
    BITMAPFILEHEADER bmfh = {0};
    BITMAPINFOHEADER bmih = {0};
    
    bmih.biSize = sizeof(BITMAPINFOHEADER);
    bmih.biWidth = width;
    bmih.biHeight = -height; // 防止倒置
    bmih.biPlanes = 1;
    bmih.biBitCount = 32;
    bmih.biCompression = BI_RGB;
    bmih.biSizeImage = width * height * 4;
    
    bmfh.bfType = 0x4D42;
    bmfh.bfSize = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER) + bmih.biSizeImage;
    bmfh.bfOffBits = sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);

    FILE* file = fopen(filename, "wb");
    if(!file) {
        SelectObject(hdcMem, hOldBitmap);
        DeleteObject(hBitmap);
        DeleteDC(hdcMem);
        ReleaseDC(NULL, hdcScreen);
        DeleteObject(hrgnTotal);
        DeleteObject(hMask);
        DeleteDC(hdcMask);
        return false;
    }

    // 写入文件
    fwrite(&bmfh, sizeof(BITMAPFILEHEADER), 1, file);
    fwrite(&bmih, sizeof(BITMAPINFOHEADER), 1, file);
    
    BYTE* pixels = (BYTE*)malloc(bmih.biSizeImage);
    GetBitmapBits(hBitmap, bmih.biSizeImage, pixels);
    fwrite(pixels, bmih.biSizeImage, 1, file);

    // 7. 清理资源
    free(pixels);
    fclose(file);
    SelectObject(hdcMem, hOldBitmap);
    DeleteObject(hBitmap);
    DeleteDC(hdcMem);
    ReleaseDC(NULL, hdcScreen);
    DeleteObject(hrgnTotal);
    DeleteObject(hMask);
    DeleteDC(hdcMask);

    return true;
}

#endif
