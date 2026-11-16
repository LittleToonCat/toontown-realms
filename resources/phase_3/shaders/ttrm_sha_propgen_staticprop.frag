// Propgen base
// Drewcification 081524

#version 130


in vec4 vColor;
in vec2 texcoord;

out vec4 color;

uniform float hue;
uniform float saturation;
uniform float value;
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;

void main() {
	color = texture(p3d_Texture0, texcoord) * vColor;
	// todo: saturation and value sliders

	// apply color adjustments after saturation and value sliders
	color *= p3d_ColorScale;
}