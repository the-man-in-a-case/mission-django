from jinja2 import Environment, FileSystemLoader
import json

def generate_sw_shunts(template_path, data_path, output_path):
    # 加载模板环境
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('sw_shunts_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染 138kV 和 20kV 部分
    content = []
    # 渲染 138kV 开关设备
    if "138kV_sw_shunts" in data:
        rendered_sw_shunts = []
        for shunt in data["138kV_sw_shunts"]["switched_shunts"]:
            full_shunt = {**data["138kV_sw_shunts"]["default_params"], **shunt}
            rendered_sw_shunts.append(full_shunt)
        content.append(template.render(
            voltage_level=data["138kV_sw_shunts"]["voltage_level"],
            switched_shunts=rendered_sw_shunts
        ))
    # 渲染 20kV 开关设备（当前为空）
    if "20kV_sw_shunts" in data and data["20kV_sw_shunts"]["switched_shunts"]:
        rendered_sw_shunts_20kv = []
        for shunt in data["20kV_sw_shunts"]["switched_shunts"]:
            full_shunt_20kv = {**data["20kV_sw_shunts"]["default_params"], **shunt}
            rendered_sw_shunts_20kv.append(full_shunt_20kv)
        content.append(template.render(
            voltage_level=data["20kV_sw_shunts"]["voltage_level"],
            switched_shunts=rendered_sw_shunts_20kv
        ))
    
    # 合并内容并写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_sw_shunts(
#         template_path='templates/sw_shunts_template.dss',
#         data_path='sw_shunts_data.json',
#         output_path='sw_shunts.dss'
#     )
#     print("sw_shunts.dss 生成完成！")