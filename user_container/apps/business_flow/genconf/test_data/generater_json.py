import yaml
import json
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

def generate_json_from_template(template_path, yaml_path, sample_json_path, output_path=None):
    """
    从Jinja2模板和YAML配置生成JSON数据
    
    参数:
        template_path: Jinja2模板文件路径
        yaml_path: YAML配置文件路径
        sample_json_path: 样例JSON文件路径
        output_path: 输出JSON文件路径，如果为None则返回JSON字符串
    """
    # 加载YAML配置
    with open(yaml_path, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)
    
    # 加载样例JSON
    with open(sample_json_path, 'r') as json_file:
        sample_data = json.load(json_file)
    
    # 设置Jinja2环境
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    # 自定义过滤器和函数
    def generate_sample_data(key, config, sample_data):
        """根据配置和样例数据生成特定字段的数据"""
        # 这里可以实现您的自定义生成逻辑
        # 例如: 从样例数据中获取，或者根据配置生成
        if key in sample_data:
            return sample_data[key]
        elif key in config:
            return config[key]
        return None
    
    # 添加自定义过滤器到环境
    env.filters['generate'] = lambda key: generate_sample_data(key, config, sample_data)
    
    # 渲染模板
    template = env.get_template(template_name)
    rendered_json = template.render(config=config, sample=sample_data)
    
    # 解析渲染后的JSON
    result = json.loads(rendered_json)
    
    # 输出结果
    if output_path:
        with open(output_path, 'w') as outfile:
            json.dump(result, outfile, indent=4)
        return f"JSON数据已保存到 {output_path}"
    else:
        return json.dumps(result, indent=4)

if __name__ == "__main__":
    # 示例用法
    template_path = "templates/my_template.j2"
    yaml_path = "config/config.yaml"
    sample_json_path = "samples/sample.json"
    output_path = "output/generated.json"
    
    result = generate_json_from_template(template_path, yaml_path, sample_json_path, output_path)
    print(result)
