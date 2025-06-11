from jinja2 import Environment, FileSystemLoader
import json

def generate_master_file(template_path, data_path, output_path):
    # 加载模板环境
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('master_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染模板
    rendered_content = template.render(
        default_base_frequency=data["default_base_frequency"],
        circuit_name=data["circuit_name"],
        circuit_params=data["circuit_params"],
        redirect_files=data["redirect_files"],
        voltage_bases=data["voltage_bases"],
        algorithm=data["algorithm"],
        ignore_gen_q_limits=data["ignore_gen_q_limits"]
    )
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_content)

# if __name__ == "__main__":
#     generate_master_file(
#         template_path='templates/master_template.dss',
#         data_path='master_data.json',
#         output_path='master_file.dss'
#     )
#     print("master_file.dss 生成完成！")