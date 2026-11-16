// street module - fixes textures seams
// Drewcification 100324

#version 130
in vec4 p3d_Vertex;
in vec4 p3d_Color;
in vec2 p3d_MultiTexCoord0;

in vec4 transform_weight;
in uvec4 transform_index;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

out vec4 vColor;
out vec4 texcoord;
out float dist;

void main() {
	gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
	dist = length(gl_Position.xyz);
	vColor = p3d_Color;
	texcoord = p3d_ModelMatrix * p3d_Vertex;
}