void mx_multiply_bsdf_float(int closureType, vec3 _L, vec3 _V, vec3 _P, float _occlusion, BSDF in1, float in2, out BSDF result)
{
    float weight = clamp(in2, 0.0, 1.0);
    result.response = in1.response * weight;
    result.throughput = in1.throughput * weight;
}
