
#file(GLOB materialx_source CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
#file(GLOB materialx_headers CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.h*")
#
#list(APPEND materialx_source ${EMBEDDED_LIBRARY_FILENAME})

add_executable(buildMaterialXLibraryTool LibraryBuildingTool.cpp)
target_link_libraries(buildMaterialXLibraryTool
    PUBLIC
        MaterialXFormat
        MaterialXCore)

set(MATERIALX_EMBEDDED_LIBRARY_SOURCE_FILENAME ${CMAKE_CURRENT_SOURCE_DIR}/EmbeddedLibrary_built.cpp)

message("XXX ${MATERIALX_DATA_LIBRARY_BUILD_DIR}")

add_executable(embedMaterialXLibraryTool LibraryEmbeddingTool.cpp)


add_custom_target(embedMaterialXDataLibrary ALL
        COMMAND embedMaterialXLibraryTool ${MATERIALX_DATA_LIBRARY_BUILD_DIR}  ${MATERIALX_EMBEDDED_LIBRARY_SOURCE_FILENAME} ${MTLX_DATA_LIBRARY_BUILD_FILES}
        BYPRODUCTS ${MATERIALX_EMBEDDED_LIBRARY_SOURCE_FILENAME}
        DEPENDS buildMaterialXDataLibrary)




mx_add_library(MaterialXEmbeddedLibrary
    SOURCE_FILES
#        EmbeddedLibrary.cpp
        ${MATERIALX_EMBEDDED_LIBRARY_SOURCE_FILENAME}
    HEADER_FILES
        EmbeddedLibrary.h
    MTLX_MODULES
        MaterialXFormat
    EXPORT_DEFINE
        MATERIALX_EMBEDDEDLIBRARY_EXPORTS)
