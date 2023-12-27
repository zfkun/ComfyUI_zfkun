cmake_minimum_required(VERSION 3.26)
project(window C)

set(CMAKE_C_STANDARD 90)
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")

include_directories(include)

file(GLOB SOURCES main.c "src/*.c")

#add_library(libwindow SHARED ${SOURCES})

add_executable(${PROJECT_NAME} ${SOURCES})

target_link_libraries(${PROJECT_NAME}
        "-framework ApplicationServices"
)
