from jinja2 import Environment, FileSystemLoader
import json

def generate_loads(template_path, data_path, output_path):
    # 加载模板
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('loads_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染 138kV 和 20kV 部分
    content = []
    # 渲染 138kV 负载
    if "138kV_loads" in data:
        # 合并默认参数和具体负载参数
        rendered_loads = []
        for load in data["138kV_loads"]["loads"]:
            full_load = {**data["138kV_loads"]["default_params"], **load}
            rendered_loads.append(full_load)
        content.append(template.render(
            voltage_level=data["138kV_loads"]["voltage_level"],
            loads=rendered_loads
        ))
    # 渲染 20kV 负载（当前文件未涉及，可按需填充）
    if "20kV_loads" in data and data["20kV_loads"]["loads"]:
        rendered_loads_20kv = []
        for load in data["20kV_loads"]["loads"]:
            full_load_20kv = {**data["20kV_loads"]["default_params"], **load}
            rendered_loads_20kv.append(full_load_20kv)
        content.append(template.render(
            voltage_level=data["20kV_loads"]["voltage_level"],
            loads=rendered_loads_20kv
        ))
    
    # 合并内容并写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_loads(
#         template_path='templates/loads_template.dss',
#         data_path='loads_data.json',
#         output_path='loads.dss'
#     )
#     print("loads.dss 生成完成！")