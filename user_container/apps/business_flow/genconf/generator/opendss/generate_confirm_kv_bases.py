from jinja2 import Environment, FileSystemLoader
import json

def generate_confirm_kv_bases(template_path, data_path, output_path):
    # 加载模板
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('confirm_kv_bases_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染并写入文件
    rendered_content = template.render(buses=data['buses'])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_content.strip())  # 去除首行空行

# if __name__ == "__main__":
#     generate_confirm_kv_bases(
#         template_path='templates/confirm_kv_bases_template.dss',
#         data_path='dss_data.json',
#         output_path='confirm_kv_bases.dss'
#     )
#     print("confirm_kv_bases.dss 生成完成！")