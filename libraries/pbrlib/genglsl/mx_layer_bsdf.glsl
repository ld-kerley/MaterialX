void mx_layer_bsdf_impl(BSDF top, BSDF base, out BSDF result)
{
    result.response = top.response + base.response * top.throughput;
    result.throughput = top.throughput + base.throughput;
}

void mx_layer_bsdf_reflection(vec3 _unused1, vec3 _unused2, vec3 _unused3, float weight, BSDF top, BSDF base, out BSDF result)
{
    mx_layer_bsdf_impl(top, base, result);
}

void mx_layer_bsdf_transmission(vec3 _unused1, BSDF top, BSDF base, out BSDF result)
{
    mx_layer_bsdf_impl(top, base, result);
}

void mx_layer_bsdf_indirect(vec3 _unused1, BSDF top, BSDF base, out BSDF result)
{
    mx_layer_bsdf_impl(top, base, result);
}

void mx_layer_bsdf(int closureType, vec3 _unused1, vec3 _unused2, vec3 _unused3, float weight, BSDF top, BSDF base, out BSDF result)
{

}
