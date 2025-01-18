void mx_layer_bsdf(int closureType, vec3 _L, vec3 _V, vec3 _P, float _occlusion, BSDF top, BSDF base, out BSDF result)
{
    result.response = top.response + base.response * top.throughput;
    result.throughput = top.throughput + base.throughput;
}
