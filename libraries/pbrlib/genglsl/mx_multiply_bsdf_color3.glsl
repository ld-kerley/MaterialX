void mx_multiply_bsdf_color3(int closureType, vec3 _L, vec3 _V, vec3 _P, float _occlusion, BSDF in1, vec3 in2, out BSDF result)
{
    vec3 weight = clamp(in2, 0.0, 1.0);
    result.response = in1.response * weight;
    result.throughput = in1.throughput * weight;
}
