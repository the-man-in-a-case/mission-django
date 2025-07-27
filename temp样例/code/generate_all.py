import os
import subprocess
import sys
from pathlib import Path

# 配置路径
BASE_DIR = r"c:\Users\admin\Downloads\【电气耦合仿真】配置文件以及日志样例-0527"
CODE_DIR = os.path.join(BASE_DIR, "code")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 文件夹映射
FOLDERS = {
    "certi": {
        "template": os.path.join(CODE_DIR, "certi", "exchange.fed.j2"),
        "data": os.path.join(DATA_DIR, "certi_data.json"),
        "output": os.path.join(BASE_DIR, "【电气耦合仿真】配置文件以及日志样例-0527", "certi")
    },
    "omnet": {
        "template": os.path.join(CODE_DIR, "omnet", "omnet.j2"),
        "data": os.path.join(DATA_DIR, "omnet_data.json"),
        "output": os.path.join(BASE_DIR, "【电气耦合仿真】配置文件以及日志样例-0527", "omnet++")
    },
    "opendss": {
        "template": os.path.join(CODE_DIR, "opendss", "dss.j2"),
        "data": os.path.join(DATA_DIR, "opendss_data.json"),
        "output": os.path.join(BASE_DIR, "【电气耦合仿真】配置文件以及日志样例-0527", "opendss-待补充", "IEEE118Bus_modified")
    }
}

def create_data_files():
    """创建JSON数据文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # certi数据
    certi_data = {
        "node": {"federation": "EnergySystem", "version": "v1.3"},
        "topo": {
            "files": {
                "exchange.fed": {
                    "federation": "EnergySystem",
                    "version": "v1.3",
                    "spaces": [],
                    "objects": [
                        {"name": "PowerPlant", "attributes": ["Power", "Load", "Step", "Time", "Compressor26", "Compressor58", "Compressor60"]},
                        {"name": "GasPipeline", "attributes": ["GasFlow", "FlowRate", "Step", "SimTime", "NodeName", "GeneratorConsumption", "IntegratedNode4", "IntegratedNode7", "IntegratedNode8", "IntegratedNode9", "IntegratedNode10", "IntegratedNode18", "IntegratedNode20"]}
                    ],
                    "interactions": [{"name": "EnergyDataExchange", "parameters": ["PowerValue", "GasFlowValue"]}]
                }
            }
        }
    }
    
    # omnet数据
    omnet_data = {
        "node": {
            "package": "",
            "network_name": "Topology",
            "parameters": [{"name": "sim-time-limit", "type": "string", "value": "\"1000s\""}],
            "node_types": [{"name": "Node", "parameters": [{"name": "address", "type": "int", "value": "0"}], "gates": [{"direction": "inout", "name": "gate[]"}]}],
            "modules": [{"name": "node0", "type": "Node", "parameters": [{"name": "address", "value": "0"}]}]
        },
        "topo": {"connections": [{"from_node": "node0", "from_gate": "gate[0]", "to_node": "node1", "to_gate": "gate[0]"}]}
    }
    
    # opendss数据
    opendss_data = {
        "node": {
            "circuit": {
                "name": "ieee118bus", "basekv": 138.0, "phases": 3, "pu": 1.005, "angle": 39.69,
                "frequency": 60.0, "baseMVA": 728.5374813610073, "puZ1": [0.001, 0.2], "model": "ideal", "bus1": "89_clinchrv"
            }
        },
        "topo": {
            "files": {
                "master_file.dss": {
                    "circuit": {"name": "ieee118bus", "basekv": 138.0, "phases": 3, "pu": 1.005, "angle": 39.69, "frequency": 60.0, "baseMVA": 728.5374813610073, "puZ1": [0.001, 0.2], "model": "ideal", "bus1": "89_clinchrv"},
                    "redirects": [{"file": "generators.dss", "comment": "! definitions for generators"}],
                    "voltageBases": [138.0], "algorithm": "NCIM"
                },
                "loads.dss": {
                    "loads": [{"name": "Load_at_1_1", "phases": 3, "bus": "1_riversde", "kv": 138.0, "kW": 51000.0, "kvar": 27000.0, "model": 1}]
                }
            }
        }
    }
    
    with open(os.path.join(DATA_DIR, "certi_data.json"), 'w') as f:
        json.dump(certi_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA_DIR, "omnet_data.json"), 'w') as f:
        json.dump(omnet_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA_DIR, "opendss_data.json"), 'w') as f:
        json.dump(opendss_data, f, indent=2, ensure_ascii=False)

def generate_all():
    """一键生成所有文件"""
    create_data_files()
    
    # 安装依赖
    try:
        import jinja2
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "jinja2"])
    
    # 生成文件
    for folder_name, config in FOLDERS.items():
        if os.path.exists(config["template"]) and os.path.exists(config["data"]):
            cmd = [
                sys.executable,
                "generate_from_template.py",
                config["template"],
                config["data"],
                config["output"]
            ]
            subprocess.run(cmd)
            print(f"已生成 {folder_name} 文件夹文件")
        else:
            print(f"模板或数据文件不存在: {folder_name}")

if __name__ == "__main__":
    generate_all()