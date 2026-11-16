// Reflective water Fragment Shader dreamy drive outcove
// Drewcification 091624

#version 130

uniform vec4 p3d_ColorScale;

in vec4 vColor;
in vec2 texcoord;
in vec4 refltexcoord;

out vec4 color;

uniform float osg_FrameTime;
uniform sampler2D p3d_Texture0;
uniform sampler2D refl_texture;


void main() {
	// we dont (yet) have a texture for the water, just make it blue now
	color = vec4(0.2, 0.5, 0.7, 1.0);

    vec2 proj_uv = refltexcoord.xy / refltexcoord.w;
	proj_uv.x = clamp(proj_uv.x + sin(32 * texcoord.y + 32 * texcoord.x + osg_FrameTime * 2) / 512, 0, 1);
	proj_uv.y = clamp(proj_uv.y + sin(32 * texcoord.y + 32 * texcoord.x + osg_FrameTime * 2) / 512, 0, 1);

    vec4 refl_tex = texture(refl_texture, proj_uv);
    color += refl_tex*.1;
	if (color.a < 0.1) {
        discard;
    }
}