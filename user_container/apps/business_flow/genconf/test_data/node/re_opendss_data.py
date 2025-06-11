import json
import os

# 读取 JSON 文件
with open(os.path.join(os.path.dirname(__file__), 'opendss_devices.json'), 'r') as file:
    data = json.load(file)

# 动态获取所有非 buses 的顶层设备类型（如 generators、loads、transformers 等）
device_types = [key for key in data if key != 'buses']

# 遍历每种设备类型
for device_type in device_types:
    if device_type in data:  # 确保设备类型存在（避免空数据）
        for device_name, device_info in data[device_type].items():
            # 确定设备关联的母线（支持单母线 bus 或多母线列表 buses）
            if 'bus' in device_info:
                # 单母线场景（如 generators、loads）
                buses = [device_info['bus']]
            elif 'buses' in device_info:
                # 多母线场景（如 transformers）
                buses = device_info['buses']
            else:
                print(f"Warning: Device {device_name} of type {device_type} has no 'bus' or 'buses' key.")
                continue  # 无关联母线，跳过
            
            # 将设备挂载到所有关联的母线下
            for bus_name in buses:
                if bus_name in data['buses']:  # 确保母线存在（避免无效母线）
                    # 如果母线的设备类型不存在则初始化空字典
                    if device_type not in data['buses'][bus_name]:
                        data['buses'][bus_name][device_type] = {}
                    # 将设备信息添加到母线的对应设备类型下
                    data['buses'][bus_name][device_type][device_name] = device_info

# 删除原始的设备类型顶层键（如 generators、loads 等）
for device_type in device_types:
    if device_type in data:
        del data[device_type]

# 将调整后的 JSON 数据写入新文件
with open(os.path.join(os.path.dirname(__file__), 'opendss_devices_adjusted.json'), 'w') as file:
    json.dump(data, file, indent=4)