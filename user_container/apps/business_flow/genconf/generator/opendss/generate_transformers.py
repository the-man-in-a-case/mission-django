from jinja2 import Environment, FileSystemLoader
import json

def generate_transformers(template_path, data_path, output_path):
    # 加载模板环境
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('transformers_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染双绕组变压器部分
    content = []
    if "2_wdgs_transformers" in data:
        # 合并默认参数和具体变压器参数
        rendered_transformers = []
        for t in data["2_wdgs_transformers"]["transformers"]:
            full_t = {**data["2_wdgs_transformers"]["default_params"], **t}
            rendered_transformers.append(full_t)
        content.append(template.render(
            windings=data["2_wdgs_transformers"]["windings"],
            transformers=rendered_transformers
        ))
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_transformers(
#         template_path='templates/transformers_template.dss',
#         data_path='transformers_data.json',
#         output_path='transformers.dss'
#     )
#     print("transformers.dss 生成完成！")