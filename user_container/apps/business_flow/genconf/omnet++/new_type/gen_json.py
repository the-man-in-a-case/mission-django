import re
import json
import os
from jinja2 import Environment, FileSystemLoader


ini_path = os.path.join(os.path.dirname(__file__), 'topology.ini')   # 替换为你的 ini 文件路径
ned_path = os.path.join(os.path.dirname(__file__), 'topology.ned')

# 加载 ini 文件内容
with open(ini_path, "r", encoding="utf-8") as f:
    ini_content = f.read()

# 加载 ned 文件内容
with open(ned_path, "r", encoding="utf-8") as f:
    ned_content = f.read()

# 匹配并提取 node 数据
node_data = {}
node_pattern = re.compile(r"topology\.(\w+)\.(\w+)\s*=\s*([^\n#]+)")

for match in node_pattern.finditer(ini_content):
    node_name, attr, value = match.groups()
    value = value.strip().strip('"')
    try:
        value = float(value) if '.' in value or 'e' in value.lower() else int(value)
    except ValueError:
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
    node_data.setdefault(node_name, {})[attr] = value

# 整理为 nodes 数组
nodes = [{"name": name, **attrs} for name, attrs in node_data.items()]

# 提取边的数据：以 gasPipe/GasPipe 属性作为判断依据
pipe_keys = ["GasPipe.diameter", "GasPipe.length", "gasPipe.flow", "gasPipe.cij", "gasPipe.type", "gasPipe.qij"]
edges = []
for node in nodes:
    edge = {"src": node["name"]}
    has_edge = False
    for key in pipe_keys:
        short_key = key.split('.')[-1]
        if key in node:
            edge[short_key] = node[key]
            has_edge = True
    if has_edge:
        edges.append(edge)

# 组合 JSON 结构
final_json = {
    "nodes": nodes,
    "edges": edges
}

# 初始化 Jinja2 环境
template_env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))

# 渲染 topology.ned.j2 模板
ned_template = template_env.get_template('topology.ned.j2')
ned_output = ned_template.render(nodes=nodes, edges=edges)

# 渲染 topology.ini.j2 模板
ini_template = template_env.get_template('topology.ini.j2')
ini_output = ini_template.render(nodes=nodes, edges=edges)

# 保存生成的文件
with open('new_topology.ned', 'w', encoding='utf-8') as f:
    f.write(ned_output)

with open('new_topology.ini', 'w', encoding='utf-8') as f:
    f.write(ini_output)

# 输出为 JSON 文件或打印
with open("topo_data.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print("✅ 已成功提取并保存为 topo_data.json")
print("✅ 已成功生成 new_topology.ned 和 new_topology.ini")
