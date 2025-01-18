void mx_add_bsdf(int closureType, vec3 _L, vec3 _V, vec3 _P, float _occlusion, BSDF in1, BSDF in2, out BSDF result)
{
    result.response = in1.response + in2.response;
    result.throughput = in1.throughput + in2.throughput;
}
