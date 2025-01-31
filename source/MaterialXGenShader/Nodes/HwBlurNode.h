//
// Copyright Contributors to the MaterialX Project
// SPDX-License-Identifier: Apache-2.0
//

#ifndef MATERIALX_BLURNODEMSL_H
#define MATERIALX_BLURNODEMSL_H

#include <MaterialXGenShader/HwShaderGenerator.h>

#include <MaterialXGenShader/Nodes/BlurNode.h>

MATERIALX_NAMESPACE_BEGIN

/// Blur node implementation for Hw shader languages
class MX_GENSHADER_API HwBlurNode : public BlurNode
{
  public:
    // HwBlurNode(const string& samplingIncludeFilename) : _samplingIncludeFilename(_samplingIncludeFilename)
    // {}
    // ~HwBlurNode() {}

  static  ShaderNodeImplPtr create(const string& samplingIncludeFilename);

    void emitSamplingFunctionDefinition(const ShaderNode& node, GenContext& context, ShaderStage& stage) const override;
  private:
    string _samplingIncludeFilename;
};

MATERIALX_NAMESPACE_END

#endif
