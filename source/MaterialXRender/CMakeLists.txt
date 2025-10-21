file(GLOB_RECURSE materialx_source "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
file(GLOB_RECURSE materialx_inlined "${CMAKE_CURRENT_SOURCE_DIR}/*.inl")
file(GLOB_RECURSE materialx_headers "${CMAKE_CURRENT_SOURCE_DIR}/*.h*")

if(NOT MATERIALX_BUILD_OIIO)
    list(REMOVE_ITEM materialx_source "${CMAKE_CURRENT_SOURCE_DIR}/OiioImageLoader.cpp")
endif()

add_library(MaterialXRender_LocalCompileOptions INTERFACE)
if(UNIX)
    target_compile_options(MaterialXRender_LocalCompileOptions INTERFACE -Wno-unused-function)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        target_compile_options(MaterialXRender_LocalCompileOptions INTERFACE -Wno-stringop-overflow)
    endif()
endif()
install(TARGETS MaterialXRender_LocalCompileOptions EXPORT MaterialX)


mx_add_library(MaterialXRender
    SOURCE_FILES
        ${materialx_source}
    INLINED_FILES
        ${materialx_inlined}
    HEADER_FILES
        ${materialx_headers}
    MTLX_MODULES
        MaterialXGenShader
        MaterialXGenHw # TODO - should this dependency be moved to RenderHw - currently needed for GeometryHandler and LightHandler
    EXPORT_DEFINE
        MATERIALX_RENDER_EXPORTS)

target_link_libraries(${TARGET_NAME}
    PRIVATE
        MaterialXRender_LocalCompileOptions
)

if(MATERIALX_BUILD_OIIO)
    find_package(OpenImageIO CONFIG REQUIRED)
    target_link_libraries(${TARGET_NAME} PRIVATE OpenImageIO::OpenImageIO OpenImageIO::OpenImageIO_Util)
    target_compile_definitions(MaterialXRender PUBLIC MATERIALX_BUILD_OIIO)
endif()
