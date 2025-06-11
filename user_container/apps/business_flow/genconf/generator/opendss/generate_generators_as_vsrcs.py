from jinja2 import Environment, FileSystemLoader
import json

def generate_generators_as_vsrcs(template_path, data_path, output_path):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('generators_as_vsrcs_template.dss')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    content = []
    if "138kV_vsources" in data:
        content.append(template.render(
            voltage_level=data["138kV_vsources"]["voltage_level"],
            vsources=data["138kV_vsources"]["vsources"]
        ))
    if "20kV_vsources" in data and data["20kV_vsources"]["vsources"]:
        content.append(template.render(
            voltage_level=data["20kV_vsources"]["voltage_level"],
            vsources=data["20kV_vsources"]["vsources"]
        ))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_generators_as_vsrcs(
#         template_path='templates/generators_as_vsrcs_template.dss',
#         data_path='generators_as_vsrcs_data.json',
#         output_path='generators_as_vsrcs.dss'
#     )
#     print("generators_as_vsrcs.dss 生成完成！")