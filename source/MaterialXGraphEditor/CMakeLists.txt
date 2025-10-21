set(DEAR_IMGUI_PREFIX "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGui" CACHE STRING "Path to Dear ImGui")

# Build GLFW
set(GLFW_BUILD_EXAMPLES OFF)
set(GLFW_BUILD_TESTS OFF)
set(GLFW_BUILD_DOCS OFF)
set(GLFW_INSTALL OFF)

# Explicitly build GLFW with static libraries, independent of the broader build settings.
set(BUILD_SHARED_LIBS OFF)

add_subdirectory(External/Glfw)
set_property(TARGET glfw_minimal PROPERTY FOLDER "External")

target_compile_options(glfw_minimal
        PRIVATE
        -Wno-deprecated-declarations
)


# Build ImGUI
if (NOT IS_DIRECTORY "${DEAR_IMGUI_PREFIX}/backends")
    message(FATAL_ERROR "Building the MaterialX graph editor requires the ImGui submodule "
        "to be present. Update your repository by calling the following:\n"
        "git submodule update --init --recursive")
endif()

file(GLOB imgui_source "${DEAR_IMGUI_PREFIX}/*.cpp")
file(GLOB imgui_headers "${DEAR_IMGUI_PREFIX}/*.h*")
LIST(APPEND imgui_source
        "${DEAR_IMGUI_PREFIX}/backends/imgui_impl_glfw.cpp"
        "${DEAR_IMGUI_PREFIX}/backends/imgui_impl_opengl3.cpp"
        "${DEAR_IMGUI_PREFIX}/misc/cpp/imgui_stdlib.cpp")
LIST(APPEND imgui_headers
        "${DEAR_IMGUI_PREFIX}/backends/imgui_impl_glfw.h"
        "${DEAR_IMGUI_PREFIX}/backends/imgui_impl_opengl3.h"
        "${DEAR_IMGUI_PREFIX}/misc/cpp/imgui_stdlib.h")

file(GLOB imguinode_source "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/*.cpp")
file(GLOB imguinode_headers "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/*.h*")
LIST(APPEND imguinode_source
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/examples/blueprints-example/utilities/drawing.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/examples/blueprints-example/utilities/widgets.cpp")
LIST(APPEND imguinode_headers
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/examples/blueprints-example/utilities/drawing.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/examples/blueprints-example/utilities/widgets.h")

add_library(imgui STATIC
        ${imgui_source}
        ${imguinode_source})

target_link_libraries(imgui
    PUBLIC
        glfw_minimal)

target_include_directories(imgui
    PUBLIC
        "${DEAR_IMGUI_PREFIX}"
        "${DEAR_IMGUI_PREFIX}/backends"
        "${DEAR_IMGUI_PREFIX}/misc/cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor"
        "${CMAKE_CURRENT_SOURCE_DIR}/External/ImGuiNodeEditor/examples/blueprints-example/utilities"
)


# Build MaterialXGraphEditor

# LocalCompileOptions target is used here to control the order that the compile options are
# included, if applied directly to MaterialXGraphEditor, then they will be added first
add_library(LocalCompileOptions INTERFACE)
if(MSVC)
    target_compile_options(LocalCompileOptions
            INTERFACE
            -wd4100 -wd4152 -wd4201 -wd4244 -wd4456)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(LocalCompileOptions
            INTERFACE
            -Wno-unused -Wno-deprecated -Wno-comment -Wno-unused-variable -Wno-unused-parameter)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    target_compile_options(LocalCompileOptions
            INTERFACE
            -Wno-format-truncation -Wno-use-after-free -Wno-comment -Wno-unused-but-set-variable -Wno-unused-parameter)
endif()

file(GLOB materialx_source "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
file(GLOB materialx_headers "${CMAKE_CURRENT_SOURCE_DIR}/*.h*")

if (APPLE)
    list(APPEND materialx_source ${CMAKE_CURRENT_SOURCE_DIR}/FileDialog_Darwin.mm)
endif ()

assign_source_group("Source Files" ${materialx_source} ${imgui_source} ${imguinode_source})
assign_source_group("Header Files" ${materialx_headers} ${imgui_headers} ${imguinode_headers})

if(MSVC)
    SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} /ENTRY:mainCRTStartup")
endif()

add_executable(MaterialXGraphEditor
    ${materialx_source}
    ${materialx_headers})

target_link_libraries(MaterialXGraphEditor
    PRIVATE
        MaterialXFormat
        MaterialXGenGlsl
        MaterialXRenderGlsl
 	    glfw_minimal
        imgui
        CommonCompileOptions
#        LocalCompileOptions
)

if(APPLE)
    find_library(CORE_FOUNDATION Foundation REQUIRED)
    target_link_libraries(MaterialXGraphEditor
        PRIVATE
            ${CORE_FOUNDATION}
    )
endif()

install(TARGETS MaterialXGraphEditor
    EXPORT MaterialX
    RUNTIME DESTINATION ${MATERIALX_INSTALL_BIN_PATH})
if(MSVC)
    install(FILES $<TARGET_PDB_FILE:MaterialXGraphEditor>
            DESTINATION ${MATERIALX_INSTALL_BIN_PATH} OPTIONAL)
endif()
