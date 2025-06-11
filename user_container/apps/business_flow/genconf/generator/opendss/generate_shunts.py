from jinja2 import Environment, FileSystemLoader
import json

def generate_shunts(template_path, data_path, output_path):
    # 加载模板环境
    env = Environment(loader=FileSystemLoader(template_path))
    # template_name = template_path.split('/')[-1] if '/' in template_path else template_path
    # template_name = template_name.split('\\')[-1] if '\\' in template_name else template_name
    template = env.get_template('shunts.dss.j2')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = data["shunts"]  # 假设数据在 "shunts_data" 键下
    
    # 渲染 138kV 和 20kV 部分
    content = []
    # 渲染 138kV 设备
    if "138kV_shunts" in data:
        # 合并默认参数和具体设备参数
        rendered_shunts = []
        for shunt in data["138kV_shunts"]["shunts"]:
            full_shunt = {**data["138kV_shunts"]["default_params"], **shunt}
            rendered_shunts.append(full_shunt)
        content.append(template.render(
            voltage_level=data["138kV_shunts"]["voltage_level"],
            shunts=rendered_shunts
        ))
    # 渲染 20kV 设备（当前为空）
    if "20kV_shunts" in data and data["20kV_shunts"]["shunts"]:
        rendered_shunts_20kv = []
        for shunt in data["20kV_shunts"]["shunts"]:
            full_shunt_20kv = {**data["20kV_shunts"]["default_params"], **shunt}
            rendered_shunts_20kv.append(full_shunt_20kv)
        content.append(template.render(
            voltage_level=data["20kV_shunts"]["voltage_level"],
            shunts=rendered_shunts_20kv
        ))
    print(content)
    # 合并内容并写入文件
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     f.write('\n'.join(content))

# if __name__ == "__main__":
#     import os
#     template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'jinja_template', 'opendss')
#     data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test_data', 'opendss.json')
#     generate_shunts(
#         template_path=template_path,
#         data_path=data_path,
#         output_path='shunts.dss'
#     )
#     print("shunts.dss 生成完成！")