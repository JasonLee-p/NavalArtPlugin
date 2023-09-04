#version 330
uniform sampler2D tex;

in vec4 fragCoord;  // 声明gl_FragCoord

out vec4 fragColor;

void main() {
    vec2 resolution = vec2(800.0, 600.0);  // 设置分辨率

    vec3 color = texture(tex, fragCoord.xy / resolution).rgb;

    // FXAA抗锯齿
    vec3 luma = vec3(0.299, 0.587, 0.114);
    float lumaNW = dot(texture(tex, (fragCoord.xy + vec2(-1.0, -1.0)) / resolution).rgb, luma);
    float lumaNE = dot(texture(tex, (fragCoord.xy + vec2(1.0, -1.0)) / resolution).rgb, luma);
    float lumaSW = dot(texture(tex, (fragCoord.xy + vec2(-1.0, 1.0)) / resolution).rgb, luma);
    float lumaSE = dot(texture(tex, (fragCoord.xy + vec2(1.0, 1.0)) / resolution).rgb, luma);
    float lumaM = dot(color, luma);

    vec2 dir = vec2(lumaNW + lumaNE - lumaSW - lumaSE, lumaNW + lumaSW - lumaNE - lumaSE);
    vec2 offset = dir * vec2(1.0 / resolution.x, 1.0 / resolution.y);

    vec3 rgbA = 0.5 * (
        texture(tex, fragCoord.xy / resolution + offset).rgb +
        texture(tex, fragCoord.xy / resolution - offset).rgb
    );

    vec3 rgbB = rgbA * 0.5 + 0.25 * (
        texture(tex, fragCoord.xy / resolution + offset * 2.0).rgb +
        texture(tex, fragCoord.xy / resolution - offset * 2.0).rgb
    );

    fragColor = vec4(mix(rgbA, rgbB, 0.5), 1.0);
}