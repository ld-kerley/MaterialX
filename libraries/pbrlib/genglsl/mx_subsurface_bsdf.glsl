#include "lib/mx_microfacet_diffuse.glsl"

void mx_subsurface_bsdf_reflection(vec3 L, vec3 V, vec3 P, float occlusion, float weight, vec3 color, vec3 radius, float anisotropy, vec3 normal, inout BSDF bsdf)
{
    bsdf.throughput = vec3(0.0);

    if (weight < M_FLOAT_EPS)
    {
        return;
    }

    normal = mx_forward_facing_normal(normal, V);

    vec3 sss = mx_subsurface_scattering_approx(normal, L, P, color, radius);
    float NdotL = clamp(dot(normal, L), M_FLOAT_EPS, 1.0);
    float visibleOcclusion = 1.0 - NdotL * (1.0 - occlusion);
    bsdf.response = sss * visibleOcclusion * weight;
}

void mx_subsurface_bsdf_indirect(vec3 V, float weight, vec3 color, vec3 radius, float anisotropy, vec3 normal, inout BSDF bsdf)
{
    bsdf.throughput = vec3(0.0);

    if (weight < M_FLOAT_EPS)
    {
        return;
    }

    normal = mx_forward_facing_normal(normal, V);

    // For now, we render indirect subsurface as simple indirect diffuse.
    vec3 Li = mx_environment_irradiance(normal);
    bsdf.response = Li * color * weight;
}

void mx_subsurface_bsdf(int closureType, vec3 L, vec3 V, vec3 P, float occlusion, float weight, vec3 color, vec3 radius, float anisotropy, vec3 normal, inout BSDF bsdf)
{
    if (closureType == 1) // reflection
    {
        mx_subsurface_bsdf_reflection(L, V, P, occlusion, weight, color, radius, anisotropy, normal, bsdf);
    }
    else if (closureType == 2) // transmission
    {
    }
    else if (closureType == 3) // indirect
    {
        mx_subsurface_bsdf_indirect(V, weight, color, radius, anisotropy, normal, bsdf);
    }
    else if (closureType == 4) // emission
    {
    }
    else // (closureType == 0) // default
    {
    }
}