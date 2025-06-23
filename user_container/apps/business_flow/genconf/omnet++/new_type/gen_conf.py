import json
from jinja2 import Environment, FileSystemLoader

# 加载 JSON 数据
with open('topo_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 设置 Jinja2 模板环境
env = Environment(loader=FileSystemLoader('./'), trim_blocks=True, lstrip_blocks=True)

# 渲染 topology.ini
template_ini = env.get_template('topology.ini.j2')
output_ini = template_ini.render(nodes=data['nodes'], edges=data['edges'])
with open('topology.ini', 'w', encoding='utf-8') as f:
    f.write(output_ini)

# 渲染 topology.ned
template_ned = env.get_template('topology.ned.j2')
output_ned = template_ned.render(nodes=data['nodes'], edges=data['edges'])
with open('topology.ned', 'w', encoding='utf-8') as f:
    f.write(output_ned)

print("✅ 生成完毕：topology.ini 和 topology.ned")
