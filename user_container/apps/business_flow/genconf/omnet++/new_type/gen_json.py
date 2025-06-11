import re
import json
import os



ini_path = os.path.join(os.path.dirname(__file__), 'topology.ini')   # 替换为你的 ini 文件路径

# 加载 ini 文件内容
with open(ini_path, "r", encoding="utf-8") as f:
    content = f.read()

# 匹配并提取 node 数据
node_data = {}
node_pattern = re.compile(r"topology\.(\w+)\.(\w+)\s*=\s*([^\n#]+)")

for match in node_pattern.finditer(content):
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
print(final_json)
# 输出为 JSON 文件或打印
with open("topo_data.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print("✅ 已成功提取并保存为 topo_data.json")
