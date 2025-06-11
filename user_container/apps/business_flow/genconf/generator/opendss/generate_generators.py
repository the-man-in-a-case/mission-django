from jinja2 import Environment, FileSystemLoader
import json

def generate_generators(template_path, data_path, output_path):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('generators_template.dss')

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    content = []
    if "138kV_generators" in data:
        content.append(template.render(
            voltage_level=data["138kV_generators"]["voltage_level"],
            generators=data["138kV_generators"]["generators"]
        ))
    if "20kV_generators" in data and data["20kV_generators"]["generators"]:
        content.append(template.render(
            voltage_level=data["20kV_generators"]["voltage_level"],
            generators=data["20kV_generators"]["generators"]
        ))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_generators(
#         template_path='templates/generators_template.dss',
#         data_path='generators_data.json',
#         output_path='generators.dss'
#     )
#     print("generators.dss 生成完成！")