// Propgen pulse effect
// Drewcification 081524

#version 130


in vec4 vColor;
in vec2 texcoord;

out vec4 color;

uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform float osg_FrameTime;

void main() {
	color = p3d_ColorScale * texture(p3d_Texture0, texcoord) * vColor;

	float dither = 0.4 * sin(osg_FrameTime*4) + 0.6;
    if (dither != 1.0){
        mat4 tm = mat4(
            vec4(1.0 / 17.0, 13.0 / 17.0, 4.0 / 17.0, 16.0 / 17.0),
            vec4(9.0 / 17.0, 5.0 / 17.0, 12.0 / 17.0, 8.0 / 17.0),
            vec4(3.0 / 17.0, 15.0 / 17.0, 2.0 / 17.0, 14.0 / 17.0),
            vec4(11.0 / 17.0, 7.0 / 17.0, 10.0 / 17.0, 6.0 / 17.0)
        );
        if (min(color.a, dither) < tm[int(gl_FragCoord.x) % 4][int(gl_FragCoord.y) % 4]){
            discard;
        }
    }
}