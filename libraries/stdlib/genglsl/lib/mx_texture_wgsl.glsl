struct MxTexture
{
    texture2D tex_texture;
    sampler tex_sampler;

    // needed for Storm
    int get_width() { return tex.get_width(); }
    int get_height() { return tex.get_height(); }
    int get_num_mip_levels() { return tex.get_num_mip_levels(); }
};

float4 texture(MxTexture mxTex, float2 uv)
{
    return mxTex.tex.sample(mxTex.s, uv);
}

float4 textureLod(MxTexture mxTex, float2 uv, float lod)
{
    return mxTex.tex.sample(mxTex.s, uv, level(lod));
}

float4 textureGrad(MxTexture mtlTex, float2 uv, float2 dx, float2 dy)
{
    return mxTex.tex.sample(mxTex.s, uv, gradient2d(dx, dy));
}

int2 textureSize(MxTexture mxTex, int mipLevel)
{
    return int2(mxTex.tex.get_width(), mxTex.tex.get_height());
}
