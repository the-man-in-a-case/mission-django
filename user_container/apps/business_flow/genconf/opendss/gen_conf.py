from jinja2 import Environment, FileSystemLoader
import json
import os

def generate_config(template_path, params_path, output_path):
    # 获取脚本所在目录的绝对路径（避免相对路径问题）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 初始化 Jinja2 环境（从脚本目录加载模板）
    env = Environment(loader=FileSystemLoader(script_dir))
    # 自定义过滤器：格式化 JSON 为缩进美观的字符串
    env.filters['tojson'] = lambda x: json.dumps(x, indent=4, ensure_ascii=False)
    
    # 加载模板和参数
    template = env.get_template(os.path.basename(template_path))
    with open(params_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    # 渲染并生成配置文件
    output_content = template.render(params)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)

if __name__ == "__main__":
    # 配置路径（根据实际目录调整）
    template_path = os.path.join(os.path.dirname(__file__), "config.py.j2")
    params_path = os.path.join(os.path.dirname(__file__), "config.json")
    output_path = os.path.join(os.path.dirname(__file__), "config.py")
    
    # 生成配置文件
    generate_config(template_path, params_path, output_path)
    print(f"配置文件已生成至: {output_path}")