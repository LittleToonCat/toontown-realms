// street module - fixes textures seams
// Drewcification 100324

#version 130
in vec4 vColor;
in vec4 texcoord;
in float dist;
out vec4 color;

uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform struct p3d_FogParameters {
  vec4 color;
  float density;
  float start;
  float end;
  float scale; // 1.0 / (end - start)
} p3d_Fog;

void main() {
	vec2 proj_uv = texcoord.xy / texcoord.w / 8.5;
	color = texture(p3d_Texture0, proj_uv) * vColor * p3d_ColorScale;

    if(p3d_Fog.end > p3d_Fog.start){
        // TODO: For some reason this looks SLIGHTLY off in Donald's Dock
        float fogAmt = clamp((p3d_Fog.end - dist) / (p3d_Fog.end - p3d_Fog.start), 0.0, 1.0);
        color = mix(p3d_Fog.color, color, fogAmt);
    }

}