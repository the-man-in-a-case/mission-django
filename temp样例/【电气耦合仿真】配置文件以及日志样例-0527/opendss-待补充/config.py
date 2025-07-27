# coding=utf-8
# 程序配置

# 燃气发电机名称列表
GAS_GENERATOR_NAMES = [
    "Gen_at_10_1",
    "Gen_at_12_1",
    "Gen_at_18_1",
    "Gen_at_19_1",
    "Gen_at_46_1",
    "Gen_at_49_1",
    "Gen_at_69_1"
]

# 压缩机负载名称列表
COMPRESSOR_LOAD_NAMES = [
    "compressor_at_26_1",
    "compressor_at_58_2",
    "compressor_at_60_2"
]

# 燃气节点到发电机的映射
GAS_NODE_TO_GENERATOR_MAP = {
    "integratedNode20": "Gen_at_10_1",
    "integratedNode7": "Gen_at_12_1",
    "integratedNode4": "Gen_at_69_1",
    "integratedNode10": "Gen_at_49_1",
    "integratedNode18": "Gen_at_18_1",
    "integratedNode9": "Gen_at_46_1",
    "integratedNode8": "Gen_at_19_1"
}

# 确保单位一致，燃气功率转换关系参数
ALPHA = 0.0  # 基础燃气消耗 - 启动需要的最小燃气量 (MMSCM)
BETA = 0.00516 # 一次项系数 (MMSCM/MW)
GAMMA = 0.0  # 二次项系数 (MMSCM/MW²)

## --- 文件路径 ---
# 包含 master DSS 文件和其他相关DSS的目录
# 假设此配置文件与 "IEEE118Bus_modified" 目录在同一级
BASE_DSS_DIRECTORY = "IEEE118Bus_modified"
MASTER_DSS_FILE_NAME = "master_file.dss"

## --- 仿真参数 ---
SIMULATION_SETTINGS = {
    "hour": 0, # 仿真时间
    "mode": "daily", # 仿真模式
    "maxiterations": 5000, # 最大迭代次数
    "stepsize": "30s", # 仿真时间步长 (例如: 1h, 30m, 30s)
    "number": 1 # 步长乘数
}
# 应用仿真设置的命令（可能并不需要）
SIMULATION_SETUP_COMMANDS = [
    "Set hour={}".format(SIMULATION_SETTINGS['hour']),
    "Set mode={}".format(SIMULATION_SETTINGS['mode']),
    "Set maxiterations={}".format(SIMULATION_SETTINGS['maxiterations']),
    "Set stepsize={}".format(SIMULATION_SETTINGS['stepsize']),
    "Set number={}".format(SIMULATION_SETTINGS['number'])
]


## --- 故障仿真参数 ---
# BUS_FAILURE_SEQUENCE = ["Bus7_xxx", "Bus12_xxxx", "Bus25_xxx"]
BUS_FAILURE_SEQUENCE = [] # 占位符，需要填写

# 故障仿真函数参数
# def run_failure_simulation_for_bus(target_bus, failure_time_step=2, max_steps=12, max_wait_time=300):
FAILURE_SIMULATION_PARAMS = {
    "failure_time_step": 2,  # 在仿真中发生故障的时间步
    "max_steps": 12,         # 故障仿真的最大步数
    "max_wait_time": 300     # 等待燃气信息的的最大时间 (秒)
}

