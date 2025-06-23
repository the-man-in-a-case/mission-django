import json
import os
from jinja2 import Environment, FileSystemLoader

# Get absolute path to current script directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Fix JSON path with proper escaping
json_path = os.path.join(base_dir, 'data.json')

# 2. Set correct template directory path (templates are in the same directory as script)
template_dir = base_dir  # 修改为当前目录

# 3. Set output directory to IEEE118Bus_modified
output_dir = os.path.normpath(os.path.join(base_dir, '..', 'modified'))  # 修改输出目录

# Verify required directories exist
if not os.path.exists(template_dir):
    raise FileNotFoundError(f"Template directory not found: {template_dir}")
os.makedirs(output_dir, exist_ok=True)

# Load JSON data
with open(json_path, 'r') as f:
    data = json.load(f)

# 新增：数据预处理 - 将nodedata和edgedata转换为模板所需格式
node_map = {node['id']: node for node in data.get('nodedata', [])}

# 处理电压基准数据
data['confirm_kv_bases'] = [
    {
        'bus': f"{node['id']}_{node['name']}",
        'kVLL': data['global_params'].get('voltage_bases', '138.0')
    } for node in data.get('nodedata', [])
]

# 处理线路数据
data['lines'] = []
for edge in data.get('edgedata', []):
    from_id = edge.get('from')
    to_id = edge.get('to')
    from_node = node_map.get(from_id)
    to_node = node_map.get(to_id)
    if from_node and to_node:
        line_name = f"{from_id}_{to_id}_1_1"
        data['lines'].append({
            'name': line_name,
            'bus1': f"{from_node['id']}_{from_node['name']}",
            'bus2': f"{to_node['id']}_{to_node['name']}",
            'phases': 3,
            'r1': edge['properties'].get('r1', '0'),
            'x1': edge['properties'].get('x1', '0'),
            'r0': edge['properties'].get('r0', '0'),
            'x0': edge['properties'].get('x0', '0'),
            'c1': edge['properties'].get('c1', '0'),
            'c0': edge['properties'].get('c0', '0'),
            'length': '1.0',
            'normamps': '418.36976028233755',
            'emergamps': '627.5546404235063',
            'enabled': 'true'
        })

# Configure Jinja2 environment with proper template directory
env = Environment(
    loader=FileSystemLoader(template_dir),
    trim_blocks=True,
    lstrip_blocks=True
)

# List of template files to process
template_files = [
    'confirm_kv_bases.dss.j2',
    'dc_and_facts_equiv_elements.dss.j2',
    'generators.dss.j2',
    'generators_as_vsrcs.dss.j2',
    'lines.dss.j2',
    'loads.dss.j2',
    'master_file.dss.j2',
    'shunts.dss.j2',
    'sw_shunts.dss.j2',
    'transformers.dss.j2'
]

# Generate each DSS file
for template_file in template_files:
    try:
        template = env.get_template(template_file)
        output_content = template.render(**data)
        output_filename = os.path.splitext(template_file)[0]
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w') as f:
            f.write(output_content)
        print(f'Successfully generated: {output_filename}')
    except Exception as e:
        print(f'Error generating {template_file}: {str(e)}')

print(f'All files generated to: {output_dir}')