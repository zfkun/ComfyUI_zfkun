cmake_minimum_required(VERSION 3.26)
project(window C)

set(CMAKE_C_STANDARD 90)
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")

include_directories(include)

file(GLOB SOURCES main.c "src/*.c")

add_library(libwindow SHARED ${SOURCES})

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)

#file(COPY include/ DESTINATION ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})

#add_executable(${PROJECT_NAME} ${SOURCES})

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
endif()
