import re
import configparser
import json

def extract_ned(ned_path):
    with open(ned_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取全局参数（package和import）
    package = re.search(r"package (.*?);", content).group(1)
    imports = re.findall(r"import (.*?);", content)
    display_match = re.search(r'@display\("bgb=([\d,]+)"\);', content)
    display = display_match.group(1) if display_match else "1268,1055"

    # 提取子模块（节点）
    nodes = []
    node_pattern = re.compile(r'(\w+): (\w+) \{\s+@display\("p=(.*?)"\);\s+\}', re.DOTALL)
    for match in node_pattern.finditer(content):
        name, type_, position = match.groups()
        nodes.append({"name": name, "type": type_, "position": position})

    nodes.sort(key=lambda x: int(re.search(r'\d+', x['name']).group()))

    # 修正边提取逻辑 - 支持多格式匹配
    edges = []
    edge_pattern = re.compile(
        r"(\w+)\.out\+\+ --> GasPipe\s*\{([^}]*)\}\s*--> (\w+)\.in\+\+;",
        re.DOTALL
    )
    for match in edge_pattern.finditer(content):
        from_node, props_str, to_node = match.groups()
        props = {}
        # 保留原始属性格式
        for prop in props_str.strip().split(";"):
            if prop.strip() and "=" in prop:
                key, value = prop.strip().split("=", 1)
                props[key.strip()] = value.strip().strip('"')
        edges.append({"from": from_node, "to": to_node, "properties": props})

    return {
        "global_params": {
            "license_comment": "This program is free software...",
            "package": package,
            "imports": imports,
            "display": display
        },
        "nodedata": nodes,
        "edgedata": edges
    }

def extract_ini(ini_path, ned_data):
    config = configparser.ConfigParser()
    config.read(ini_path, encoding="utf-8")
    general_section = config['General']

    # 初始化全局参数（修复compressor_global_props未定义问题）
    global_params = {
        'compressor': {},
        'gas_pipe': {}
    }

    # 提取Compressor全局参数（修正匹配键）
    compressor_params = ['nst', 'np', 'T_in', 'Z_av', 'eta', 'pressRatio', 'readInterval', 'hpCsvFileName']
    for prop in compressor_params:
        key = f"topology.**.{prop}"  # 匹配test_topology.ini中的全局参数格式
        if key in general_section:
            global_params['compressor'][prop] = general_section[key]

    # 提取GasPipe全局参数
    gas_pipe_params = ['diameter', 'length', 'flow', 'cij', 'type', 'qij']
    for prop in gas_pipe_params:
        key = f"**.GasPipe.{prop}"
        if key in general_section:
            global_params['gas_pipe'][prop] = general_section[key]

    ned_data['global_params'].update(global_params)
    # 提取节点数据并按ID排序
    nodes = ned_data.get('nodedata', [])
    nodes.sort(key=lambda x: int(re.search(r'\d+', x['name']).group()))

    # 补充节点属性（修复json_data未定义问题，使用ned_data替代）
    for node in nodes:
        prefix = f"topology.{node['name']}"
        node_props = {}
        if node["type"] == "GasNode":
            props = ["supply", "pressure", "LoadDemand", "TotalDemand"]
        elif node["type"] == "IntegratedNode":
            props = ["LoadDemand", "TotalDemand", "GeneratorConsumption", "csv", "pressure"]
        elif node["type"] == "Compressor":
            node_props = global_params['compressor'].copy()  # 使用已初始化的global_params
            props = []

        for prop in props:
            key = f"{prefix}.{prop}"
            if key in general_section:
                value = general_section[key]
                # 类型转换
                if prop in ["LoadDemand", "nst", "T_in"]:
                    node_props[prop] = int(value)
                elif prop in ["supply", "pressure", "TotalDemand", "GeneratorConsumption", "np", "Z_av", "eta", "pressRatio", "readInterval"]:
                    node_props[prop] = float(value)
                elif prop == "csv":
                    node_props[prop] = value.lower() == "true"
                else:
                    node_props[prop] = value.strip('"')
        
        node["properties"] = node_props

    # 补充管道属性（从INI提取）
    for edge in ned_data["edgedata"]:
        pipe_key = f"topology.{edge['from']}_to_{edge['to']}"
        edge["properties"].update({
            "diameter": int(config.get(pipe_key, "diameter", fallback=5000)),
            "length": int(config.get(pipe_key, "length", fallback=200)),
            "flow": int(config.get(pipe_key, "flow", fallback=100)),
            "type": config.get(pipe_key, "type", fallback="p"),
            "qij": config.get(pipe_key, "qij", fallback="26.7606")
        })

    return ned_data

if __name__ == "__main__":
    ned_path = "d:/git/mission-django/user_container/apps/business_flow/genconf/omnet++/new_test/topology.ned"
    ini_path = "d:/git/mission-django/user_container/apps/business_flow/genconf/omnet++/new_test/topology.ini"

    # 提取NED数据
    ned_data = extract_ned(ned_path)
    # 合并INI数据
    full_json = extract_ini(ini_path, ned_data)

    # 保存为JSON
    with open("d:/git/mission-django/user_container/apps/business_flow/genconf/omnet++/new_test/data.json", "w", encoding="utf-8") as f:
        json.dump(full_json, f, ensure_ascii=False, indent=4)
print("JSON数据提取完成！")

