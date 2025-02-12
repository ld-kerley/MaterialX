//
// Copyright Contributors to the MaterialX Project
// SPDX-License-Identifier: Apache-2.0
//

#ifndef MATERIALX_EMBEDDED_LIBRARY_H
#define MATERIALX_EMBEDDED_LIBRARY_H

/// @file
/// Cross-platform environment variable functionality

#include <MaterialXCore/Library.h>

#include <MaterialXLibrary/Export.h>

MATERIALX_NAMESPACE_BEGIN

MX_EMBEDDEDLIBRARY_API const std::string& readEmbeddedSourceFile(const std::string& filename);

MATERIALX_NAMESPACE_END

#endif // MATERIALX_EMBEDDED_LIBRARY_H
