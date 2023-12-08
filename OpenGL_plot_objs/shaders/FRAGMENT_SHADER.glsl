#version 330 core
in vec3 FragPos;                           // 片段位置
in vec3 Normal;                            // 法向量

uniform vec3 lightPos;                     // 光源位置
uniform vec3 viewPos;                      // 观察者位置
uniform vec3 lightColor;                   // 光源颜色
uniform vec4 objectColor;                  // 物体颜色

uniform float ambientStrength = 0.1;       // 环境光强度
uniform float specularStrength = 0.4;      // 镜面光强度
uniform int shininess = 12;                // 镜面光高光大小

out vec4 FragColor;

void main() {
    // 计算光线方向和法向量之间的角度
    vec3 lightDir = normalize(viewPos - FragPos);
    float diff = max(dot(Normal, lightDir), 0.0);

    // 计算角度的权重
    float angleWeight = (diff + 1.0) / 2.0; // 角度值范围从[-1,1]映射到[0,1]

    // 使用角度权重来混合颜色
    vec3 diffuse = angleWeight * lightColor * objectColor.rgb;

    // 环境光照计算
    vec3 ambient = ambientStrength * lightColor;

    // 镜面光照计算
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, Normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor;

    // 最终颜色
    vec3 result = (ambient + diffuse + specular);
    FragColor = vec4(result, 1.0);
}