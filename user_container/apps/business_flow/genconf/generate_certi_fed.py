import configparser
import json

# 读取 OMNeT++ 的 topology.ini
def parse_omnet_topology(omnet_ini_path):
    config = configparser.ConfigParser()
    config.read(omnet_ini_path)
    integrated_nodes = {}
    for section in config.sections():
        if "integratedNode" in section:
            node_id = section.split(".")[-1]
            integrated_nodes[node_id] = {
                "GeneratorConsumption": config.get(section, "GeneratorConsumption", fallback="0"),
                "pressure": config.get(section, "pressure", fallback="0")
            }
    return integrated_nodes

# 读取 OpenDSS 的 config.py（简化为读取关键变量）
def parse_opendss_config(opendss_config_path):
    with open(opendss_config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    # 提取 GAS_NODE_TO_GENERATOR_MAP 和 COMPRESSOR_LOAD_NAMES（简化解析）
    gas_node_map = {
        "integratedNode20": "Gen_at_10_1",
        "integratedNode7": "Gen_at_12_1",
        "integratedNode4": "Gen_at_69_1"
    }  # 实际从文件解析
    compressor_loads = ["compressor_at_26_1", "compressor_at_58_2", "compressor_at_60_2"]
    return gas_node_map, compressor_loads

# 生成 CERTI 的 exchange.fed 文件
def generate_certi_fed(integrated_nodes, gas_node_map, compressor_loads, output_path):
    # 生成 PowerPlant 类的属性（压缩机负载）
    powerplant_attrs = [f"(attribute {compressor} reliable timestamp)" for compressor in compressor_loads]
    powerplant_attrs += [
        "(attribute Power reliable timestamp)",
        "(attribute Load reliable timestamp)",
        "(attribute Step reliable timestamp)",
        "(attribute Time reliable timestamp)"
    ]

    # 生成 GasPipeline 类的属性（集成节点）
    gaspipeline_attrs = [f"(attribute IntegratedNode{node_id} reliable timestamp)" 
                        for node_id in gas_node_map.keys() if "integratedNode" in node_id]
    gaspipeline_attrs += [
        "(attribute GasFlow reliable timestamp)",
        "(attribute FlowRate reliable timestamp)",
        "(attribute Step reliable timestamp)",
        "(attribute SimTime reliable timestamp)",
        "(attribute NodeName reliable timestamp)",
        "(attribute GeneratorConsumption reliable timestamp)"
    ]


    # 构建 FED 文件内容
    fed_content = """(FED
      (Federation EnergySystem)
      (FEDversion v1.3)
      (spaces
      )
      (objects
        (class ObjectRoot
          (attribute privilegeToDelete reliable timestamp)
          (class PowerPlant
            {powerplant_attrs_str}
          )
          (class GasPipeline
            {gaspipeline_attrs_str}
          )
        )
      )
      (interactions
        (class InteractionRoot reliable timestamp
          (class EnergyDataExchange reliable timestamp
            (parameter PowerValue)
            (parameter GasFlowValue)
          )
        )
      )
    )"""

    # 使用 format 方法填充变量
    fed_content = fed_content.format(
        powerplant_attrs_str='\n        '.join(powerplant_attrs),
        gaspipeline_attrs_str='\n        '.join(gaspipeline_attrs)
)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fed_content.strip())

if __name__ == "__main__":
    # 输入路径（根据实际路径调整）
    import os
    omnet_ini_path = os.path.join("omnet++", "topology.ini")
    opendss_config_path = os.path.join("opendss配置和日志", "opendss", "配置", "config.py")
    output_fed_path = os.path.join("certi", "test_exchange.fed")

    # 解析配置
    integrated_nodes = parse_omnet_topology(omnet_ini_path)
    gas_node_map, compressor_loads = parse_opendss_config(opendss_config_path)

    # 生成 CERTI 配置
    generate_certi_fed(integrated_nodes, gas_node_map, compressor_loads, output_fed_path)
    print(f"CERTI FOM 文件已生成至: {output_fed_path}")