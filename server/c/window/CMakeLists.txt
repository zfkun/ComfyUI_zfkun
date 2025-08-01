cmake_minimum_required(VERSION 3.26)
project(libwindow C)

set(CMAKE_C_STANDARD 90)
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")

# 根据编译器类型设置编码选项
if(CMAKE_C_COMPILER_ID STREQUAL "MSVC")
    # MSVC 编译器使用 /utf-8 选项
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /utf-8")
elseif(CMAKE_C_COMPILER_ID STREQUAL "GNU")
    # GCC 编译器使用 -finput-charset 选项
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -finput-charset=UTF-8")
endif()

include_directories(include)

file(GLOB SOURCES "src/*.c")

add_library(${PROJECT_NAME} SHARED ${SOURCES})

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)

#file(COPY include/ DESTINATION ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})

if(WIN32)
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            gdi32
            user32
    )
elseif(APPLE)
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            "-framework ApplicationServices"
    )
else()
    # For Linux/Unix systems
    target_link_libraries(${PROJECT_NAME}
            PRIVATE
            # Add required libraries here
    )
endif()

# local test
if(WIN32)
    add_executable(${PROJECT_NAME}_test main.c ${SOURCES})
    target_link_libraries(${PROJECT_NAME}_test
            PRIVATE
            gdi32
            user32
    )
elseif(APPLE)
    target_link_libraries(${PROJECT_NAME}_test
            PRIVATE
            "-framework ApplicationServices"
    )
else()
    target_link_libraries(${PROJECT_NAME}_test
            PRIVATE
            # Add required libraries here
    )
endif()


# cmake -S . -B build
# cmake --build build
