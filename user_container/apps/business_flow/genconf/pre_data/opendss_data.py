import json
from typing import Dict, List, Any, Tuple

def extract_and_split_opendss_data(data: Dict) -> Tuple[Dict, Dict]:
    """
    从OpenDSS JSON数据中提取设备参数和拓扑连接关系
    
    返回:
        - devices: 设备参数字典
        - topology: 拓扑连接关系字典
    """
    
    # 1. 设备参数提取
    devices = {
        "buses": {},
        "generators": {},
        "loads": {},
        "shunts": {},
        "switched_shunts": {},
        "transformers": {},
        "vsources": {}
    }
    
    # 提取母线信息
    if "confirm_kv_bases" in data and "buses" in data["confirm_kv_bases"]:
        for bus in data["confirm_kv_bases"]["buses"]:
            devices["buses"][bus["name"]] = {
                "kVLL": float(bus["kVLL"])
            }
    
    # 提取发电机信息
    if "generators" in data:
        for voltage_level, gen_data in data["generators"].items():
            if "generators" in gen_data:
                for gen in gen_data["generators"]:
                    gen_id = gen["name"]
                    devices["generators"][gen_id] = {
                        "bus": gen["bus1"],
                        "phases": int(gen["phases"]),
                        "kV": float(gen["kV"]),
                        "kW": float(gen["kW"]),
                        "model": int(gen["model"]),
                        "PVFactor": float(gen["PVFactor"]),
                        "Vpu": float(gen["Vpu"]),
                        "maxkvar": float(gen["maxkvar"]),
                        "minkvar": float(gen["minkvar"])
                    }
    
    # 提取电压源形式的发电机
    if "generators_as_vsrcs" in data:
        for voltage_level, vsrc_data in data["generators_as_vsrcs"].items():
            if "vsources" in vsrc_data:
                for vsrc in vsrc_data["vsources"]:
                    vsrc_id = vsrc["name"]
                    devices["vsources"][vsrc_id] = {
                        "bus": vsrc["bus"],
                        "basekv": float(vsrc["basekv"]),
                        "phases": int(vsrc["phases"]),
                        "pu": float(vsrc["pu"]),
                        "angle": float(vsrc["angle"]),
                        "frequency": float(vsrc["frequency"]),
                        "baseMVA": float(vsrc["baseMVA"]),
                        "puZ1": vsrc["puZ1"],
                        "description": vsrc["description"]
                    }
    
    # 提取负荷信息
    if "loads" in data:
        for voltage_level, load_data in data["loads"].items():
            if "loads" in load_data:
                for load in load_data["loads"]:
                    load_id = load["name"]
                    devices["loads"][load_id] = {
                        "bus": load["bus"],
                        "phases": int(load_data["default_params"]["phases"]),
                        "kv": float(load_data["default_params"]["kv"]),
                        "kW": float(load["kW"]),
                        "kvar": float(load["kvar"]),
                        "model": int(load["model"])
                    }
    
    # 提取并联设备（电容器和电抗器）
    if "shunts" in data:
        for voltage_level, shunt_data in data["shunts"].items():
            if "shunts" in shunt_data:
                for shunt in shunt_data["shunts"]:
                    shunt_id = shunt["name"]
                    devices["shunts"][shunt_id] = {
                        "type": shunt["type"],
                        "bus": shunt["bus"],
                        "kvar": float(shunt["kvar"]),
                        "phases": int(shunt_data["default_params"]["phases"]),
                        "kv": float(shunt_data["default_params"]["kv"]),
                        "R": float(shunt_data["default_params"]["R"])
                    }
    
    # 提取可切换并联设备
    if "sw_shunts" in data:
        for voltage_level, sw_shunt_data in data["sw_shunts"].items():
            if "switched_shunts" in sw_shunt_data:
                for sw_shunt in sw_shunt_data["switched_shunts"]:
                    # 这个例子中没有实际的可切换并联设备
                    pass
    
    # 提取变压器信息
    if "transformers" in data:
        for winding_type, xfmr_data in data["transformers"].items():
            if "transformers" in xfmr_data:
                for xfmr in xfmr_data["transformers"]:
                    xfmr_id = xfmr["name"]
                    devices["transformers"][xfmr_id] = {
                        "buses": xfmr["buses"],
                        "kVs": [float(kv) for kv in xfmr["kVs"]],
                        "kVA": float(xfmr_data["default_params"]["kVA"]),
                        "taps": [float(tap) for tap in xfmr["taps"]],
                        "Xhl": float(xfmr["Xhl"]),
                        "conns": xfmr["conns"],
                        "percent_rs": [float(r) for r in xfmr_data["default_params"]["percent_rs"]]
                    }
    
    # 2. 拓扑连接关系提取
    topology = {
        "line_connections": {},
        "transformer_connections": {},
        "generator_connections": {},
        "load_connections": {},
        "shunt_connections": {}
    }
    
    # 提取线路连接关系
    if "lines" in data:
        for voltage_level, line_data in data["lines"].items():
            if "lines" in line_data:
                for line in line_data["lines"]:
                    line_id = line["name"]
                    topology["line_connections"][line_id] = {
                        "from_bus": line["bus1"],
                        "to_bus": line["bus2"],
                        "parameters": {
                            "r1": float(line["r1"]),
                            "x1": float(line["x1"]),
                            "r0": float(line["r0"]),
                            "x0": float(line["x0"]),
                            "c1": float(line["c1"]),
                            "c0": float(line["c0"]),
                            "phases": int(line_data["default_params"]["phases"]),
                            "length": float(line_data["default_params"]["length"]),
                            "normamps": float(line_data["default_params"]["normamps"]),
                            "emergamps": float(line_data["default_params"]["emergamps"])
                        }
                    }
    
    # 提取变压器连接关系
    for xfmr_id, xfmr_data in devices["transformers"].items():
        topology["transformer_connections"][xfmr_id] = {
            "buses": xfmr_data["buses"],
            "type": "transformer"
        }
    
    # 提取发电机连接关系
    for gen_id, gen_data in devices["generators"].items():
        topology["generator_connections"][gen_id] = {
            "bus": gen_data["bus"],
            "type": "generator"
        }
    
    # 提取电压源连接关系
    for vsrc_id, vsrc_data in devices["vsources"].items():
        topology["generator_connections"][vsrc_id] = {
            "bus": vsrc_data["bus"],
            "type": "vsource"
        }
    
    # 提取负荷连接关系
    for load_id, load_data in devices["loads"].items():
        topology["load_connections"][load_id] = {
            "bus": load_data["bus"],
            "type": "load"
        }
    
    # 提取并联设备连接关系
    for shunt_id, shunt_data in devices["shunts"].items():
        topology["shunt_connections"][shunt_id] = {
            "bus": shunt_data["bus"],
            "type": shunt_data["type"].lower()
        }
    
    # 清理空字典
    devices = {k: v for k, v in devices.items() if v}
    topology = {k: v for k, v in topology.items() if v}
    
    return devices, topology


def merge_to_complete_json(devices: Dict, topology: Dict, master_info: Dict = None) -> Dict:
    """
    将拆分的设备参数和拓扑连接关系合并回完整的OpenDSS JSON格式
    
    参数:
        - devices: 设备参数字典
        - topology: 拓扑连接关系字典
        - master_info: 主文件信息（可选）
    
    返回:
        - 完整的OpenDSS JSON数据
    """
    
    # 初始化完整数据结构
    complete_data = {}
    
    # 1. 重建母线信息
    if "buses" in devices and devices["buses"]:
        complete_data["confirm_kv_bases"] = {
            "buses": []
        }
        for bus_name, bus_data in devices["buses"].items():
            complete_data["confirm_kv_bases"]["buses"].append({
                "name": bus_name,
                "kVLL": str(bus_data["kVLL"])
            })
    
    # 2. 重建发电机信息
    generators_138kv = []
    generators_20kv = []
    
    if "generators" in devices:
        for gen_id, gen_data in devices["generators"].items():
            gen_dict = {
                "name": gen_id,
                "bus1": gen_data["bus"],
                "phases": str(gen_data["phases"]),
                "kV": str(gen_data["kV"]),
                "kW": str(gen_data["kW"]),
                "model": str(gen_data["model"]),
                "PVFactor": str(gen_data["PVFactor"]),
                "Vpu": str(gen_data["Vpu"]),
                "maxkvar": str(gen_data["maxkvar"]),
                "minkvar": str(gen_data["minkvar"])
            }
            
            if gen_data["kV"] == 138.0:
                generators_138kv.append(gen_dict)
            elif gen_data["kV"] == 20.0:
                generators_20kv.append(gen_dict)
    
    complete_data["generators"] = {
        "138kV_generators": {
            "voltage_level": "138.0",
            "generators": generators_138kv
        },
        "20kV_generators": {
            "voltage_level": "20.0",
            "generators": generators_20kv
        }
    }
    
    # 3. 重建电压源信息
    vsources_138kv = []
    vsources_20kv = []
    
    if "vsources" in devices:
        for vsrc_id, vsrc_data in devices["vsources"].items():
            vsrc_dict = {
                "name": vsrc_id,
                "bus": vsrc_data["bus"],
                "basekv": str(vsrc_data["basekv"]),
                "phases": str(vsrc_data["phases"]),
                "pu": str(vsrc_data["pu"]),
                "angle": str(vsrc_data["angle"]),
                "frequency": str(vsrc_data["frequency"]),
                "baseMVA": str(vsrc_data["baseMVA"]),
                "puZ1": vsrc_data["puZ1"],
                "description": vsrc_data["description"]
            }
            
            if vsrc_data["basekv"] == 138.0:
                vsources_138kv.append(vsrc_dict)
            elif vsrc_data["basekv"] == 20.0:
                vsources_20kv.append(vsrc_dict)
    
    complete_data["generators_as_vsrcs"] = {
        "138kV_vsources": {
            "voltage_level": "138.0",
            "vsources": vsources_138kv
        },
        "20kV_vsources": {
            "voltage_level": "20.0",
            "vsources": vsources_20kv
        }
    }
    
    # 4. 重建线路信息
    lines_138kv = []
    lines_20kv = []
    
    if "line_connections" in topology:
        for line_id, line_conn in topology["line_connections"].items():
            line_dict = {
                "name": line_id,
                "bus1": line_conn["from_bus"],
                "bus2": line_conn["to_bus"],
                "r1": str(line_conn["parameters"]["r1"]),
                "x1": str(line_conn["parameters"]["x1"]),
                "r0": str(line_conn["parameters"]["r0"]),
                "x0": str(line_conn["parameters"]["x0"]),
                "c1": str(line_conn["parameters"]["c1"]),
                "c0": str(line_conn["parameters"]["c0"])
            }
            
            # 根据母线电压判断线路电压等级
            if "buses" in devices and line_conn["from_bus"] in devices["buses"]:
                if devices["buses"][line_conn["from_bus"]]["kVLL"] == 138.0:
                    lines_138kv.append(line_dict)
                elif devices["buses"][line_conn["from_bus"]]["kVLL"] == 20.0:
                    lines_20kv.append(line_dict)
    
    complete_data["lines"] = {
        "138kV_lines": {
            "voltage_level": "138.0",
            "default_params": {
                "phases": "3",
                "length": "1.0",
                "normamps": "418.36976028233755",
                "emergamps": "627.5546404235063",
                "enabled": "true"
            },
            "lines": lines_138kv
        },
        "20kV_lines": {
            "voltage_level": "20.0",
            "default_params": {
                "phases": "3",
                "length": "1.0",
                "normamps": "418.36976028233755",
                "emergamps": "627.5546404235063",
                "enabled": "true"
            },
            "lines": lines_20kv
        }
    }
    
    # 5. 重建负荷信息
    loads_138kv = []
    loads_20kv = []
    
    if "loads" in devices:
        for load_id, load_data in devices["loads"].items():
            load_dict = {
                "name": load_id,
                "bus": load_data["bus"],
                "kW": str(load_data["kW"]),
                "kvar": str(load_data["kvar"]),
                "model": str(load_data["model"])
            }
            
            if load_data["kv"] == 138.0:
                loads_138kv.append(load_dict)
            elif load_data["kv"] == 20.0:
                loads_20kv.append(load_dict)
    
    complete_data["loads"] = {
        "138kV_loads": {
            "voltage_level": "138.0",
            "default_params": {
                "phases": "3",
                "kv": "138.0",
                "daily": "Default",
                "spectrum": "Linear"
            },
            "loads": loads_138kv
        },
        "20kV_loads": {
            "voltage_level": "20.0",
            "default_params": {
                "phases": "3",
                "kv": "20.0",
                "daily": "Default",
                "spectrum": "Linear"
            },
            "loads": loads_20kv
        }
    }
    
    # 6. 重建并联设备信息
    shunts_138kv = []
    shunts_20kv = []
    
    if "shunts" in devices:
        for shunt_id, shunt_data in devices["shunts"].items():
            shunt_dict = {
                "type": shunt_data["type"],
                "name": shunt_id,
                "bus": shunt_data["bus"],
                "kvar": str(shunt_data["kvar"])
            }
            
            if shunt_data["kv"] == 138.0:
                shunts_138kv.append(shunt_dict)
            elif shunt_data["kv"] == 20.0:
                shunts_20kv.append(shunt_dict)
    
    complete_data["shunts"] = {
        "138kV_shunts": {
            "voltage_level": "138.0",
            "default_params": {
                "phases": "3",
                "kv": "138.0",
                "R": "0.0",
                "enabled": "True"
            },
            "shunts": shunts_138kv
        },
        "20kV_shunts": {
            "voltage_level": "20.0",
            "default_params": {
                "phases": "3",
                "kv": "20.0",
                "R": "0.0",
                "enabled": "True"
            },
            "shunts": shunts_20kv
        }
    }
    
    # 7. 重建变压器信息
    if "transformers" in devices and devices["transformers"]:
        transformers_list = []
        for xfmr_id, xfmr_data in devices["transformers"].items():
            xfmr_dict = {
                "name": xfmr_id,
                "buses": xfmr_data["buses"],
                "kVs": [str(kv) for kv in xfmr_data["kVs"]],
                "taps": [str(tap) for tap in xfmr_data["taps"]],
                "Xhl": str(xfmr_data["Xhl"]),
                "conns": xfmr_data["conns"]
            }
            transformers_list.append(xfmr_dict)
        
        complete_data["transformers"] = {
            "2_wdgs_transformers": {
                "windings": "2",
                "default_params": {
                    "kVA": "100000.0",
                    "percent_rs": ["0.0005", "0.0005"]
                },
                "transformers": transformers_list
            }
        }
    
    # 8. 添加主文件信息
    if master_info:
        complete_data["master_file"] = master_info
    
    # 9. 添加空的可切换并联设备和直流设备信息
    complete_data["sw_shunts"] = {
        "138kV_sw_shunts": {
            "voltage_level": "138.0",
            "default_params": {
                "phases": "3",
                "kv": "138.0",
                "R": "0.0",
                "enabled": "True",
                "steps": "5",
                "min_step": "0",
                "max_step": "5"
            },
            "switched_shunts": []
        },
        "20kV_sw_shunts": {
            "voltage_level": "20.0",
            "default_params": {
                "phases": "3",
                "kv": "20.0",
                "R": "0.0",
                "enabled": "True",
                "steps": "3",
                "min_step": "0",
                "max_step": "3"
            },
            "switched_shunts": []
        }
    }
    
    complete_data["dc_and_facts_templates"] = {
        "138kV_dc_elements": {
            "voltage_level": "138.0",
            "default_params": {
                "phases": "3",
                "kv": "138.0",
                "enabled": "True"
            },
            "dc_elements": []
        },
        "20kV_dc_elements": {
            "voltage_level": "20.0",
            "default_params": {
                "phases": "3",
                "kv": "20.0",
                "enabled": "True"
            },
            "dc_elements_20kv": []
        }
    }
    
    return complete_data


# 示例使用函数
def process_opendss_data(json_file_path: str):
    """处理OpenDSS JSON文件的示例函数"""
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 拆分数据
    devices, topology = extract_and_split_opendss_data(data)

    # 保存主文件信息
    master_info = data.get("master_file", None)
    # output_path = os.path.join(os.path.dirname(__file__), 'devices.json')
    # 保存拆分后的数据
    with open('devices.json', 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)
    
    with open('topology.json', 'w', encoding='utf-8') as f:
        json.dump(topology, f, indent=2, ensure_ascii=False)
    
    with open('master_file.json', 'w', encoding='utf-8') as f:
        json.dump(master_info, f, indent=2, ensure_ascii=False)

    # 测试合并功能
    merged_data = merge_to_complete_json(devices, topology, master_info)
    
    with open('merged_complete.json', 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print("数据处理完成！")
    print(f"设备数量统计：")
    print(f"  - 母线: {len(devices.get('buses', {}))}")
    print(f"  - 发电机: {len(devices.get('generators', {}))}")
    print(f"  - 电压源: {len(devices.get('vsources', {}))}")
    print(f"  - 负荷: {len(devices.get('loads', {}))}")
    print(f"  - 并联设备: {len(devices.get('shunts', {}))}")
    print(f"  - 变压器: {len(devices.get('transformers', {}))}")
    print(f"\n连接关系统计：")
    print(f"  - 线路连接: {len(topology.get('line_connections', {}))}")
    print(f"  - 变压器连接: {len(topology.get('transformer_connections', {}))}")
    print(f"  - 发电机连接: {len(topology.get('generator_connections', {}))}")
    print(f"  - 负荷连接: {len(topology.get('load_connections', {}))}")
    print(f"  - 并联设备连接: {len(topology.get('shunt_connections', {}))}")


# if __name__ == "__main__":
#     # 使用示例
#     import os
#     openss_data = os.path.join(os.path.dirname(__file__), '..', 'opendss.json')
#     process_opendss_data(openss_data)
    
#     # 或者直接使用已有的数据
#     # 这里你可以将你的JSON数据作为字典传入
#     # data = {...}  # 你的JSON数据
#     # devices, topology = extract_and_split_opendss_data(data)
#     pass