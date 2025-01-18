void mx_mix_bsdf(int closureType, vec3 _L, vec3 _V, vec3 _P, float _occlusion, BSDF fg, BSDF bg, float mixValue, out BSDF result)
{
    result.response = mix(bg.response, fg.response, mixValue);
    result.throughput = mix(bg.throughput, fg.throughput, mixValue);
}
