struct MxTexture
{
    sampler2D tex;

    // needed for Storm
//    int get_width() { return tex.get_width(); }
//    int get_height() { return tex.get_height(); }
//    int get_num_mip_levels() { return tex.get_num_mip_levels(); }
};

vec4 texture(MxTexture mxTex, vec2 uv)
{
    return texture(mxTex.tex, uv);
}

vec4 textureLod(MxTexture mxTex, vec2 uv, float lod)
{
    return textureLod(mxTex.tex, uv, lod);
}

vec4 textureGrad(MxTexture mxTex, vec2 uv, vec2 dx, vec2 dy)
{
    return textureGrad(mxTex.tex, uv, dx, dy);
}

ivec2 textureSize(MxTexture mxTex, int mipLevel)
{
    return textureSize(mxTex.tex, mipLevel);
}

