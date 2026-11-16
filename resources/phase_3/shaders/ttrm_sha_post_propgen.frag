// propgen outline post process
// drewcification 091724
#version 130

uniform sampler2D p3d_Texture0;
uniform sampler2D outline_depth_texture;
uniform sampler2D scene_depth_texture;

in vec2 texcoord;
out vec4 color;

#define line_thickness 0.002

void main() {
	// sample the alpha of our postprocess texture at the offset texcoords
	float this_pixel = texture(p3d_Texture0, texcoord).a;
	float alpha_top = texture(p3d_Texture0, vec2(texcoord.x, texcoord.y - line_thickness)).a;
	float alpha_right = texture(p3d_Texture0, vec2(texcoord.x + line_thickness, texcoord.y)).a;
	float alpha_topRight = texture(p3d_Texture0, vec2(texcoord.x + line_thickness, texcoord.y - line_thickness)).a;

	// clip it down under a certain value - this prevents it from attempting to outline every pixel on transparent
	// stuff, like dropshadows which would just create a solid blue circle
	this_pixel = (this_pixel < .8) ? 0 : 1.0;
	alpha_top = (alpha_top < .8) ? 0 : 1.0;
	alpha_right = (alpha_right < .8) ? 0 : 1.0;
	alpha_topRight = (alpha_topRight < .8) ? 0 : 1.0;

	// get teh differences between our actual pixel (mC) and the sampled neighbor pixel
	float diff_top  = abs(this_pixel - alpha_top);
	float diff_right  = abs(this_pixel - alpha_right);
	float diff_topRight = abs(this_pixel - alpha_topRight);

	float delta = 0.0;
	delta = max(delta, diff_top);
	delta = max(delta, diff_right);
	delta = max(delta, diff_topRight);

	if(delta != 0){
		// make the outline a light blue color
		color = vec4(0.0, 0.85, 1.0, 1.0);
	}
	else if (this_pixel > 0.1){
		float sceneDepth = texture(scene_depth_texture, texcoord).r;
		float outlineDepth = texture(outline_depth_texture, texcoord).r;

		if (outlineDepth - sceneDepth >= 0.00001){
			// If the object is behind another object we're rendering,
			// let's put a silhouette of it
			color = vec4(0.0, 0.85, 1.0, 0.3);
		}
	}
	else{
		discard;
	}


}
