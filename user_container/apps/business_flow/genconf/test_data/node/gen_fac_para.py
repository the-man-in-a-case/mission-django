import json
import os

def generate_facility_and_parameter_data(json_file_path, facility_type_id):
    """
    从 opendss_devices_adjusted.json 提取母线数据，生成 Facility 和 FacilityParameter 表的批量导入数据
    """
    # 读取并解析 JSON 文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            buses = data.get('buses', {})  # 所有母线数据（key为母线名称）
    except FileNotFoundError:
        raise FileNotFoundError(f"错误：文件 {json_file_path} 不存在")
    except json.JSONDecodeError:
        raise ValueError(f"错误：文件 {json_file_path} 不是有效的 JSON")

    # 初始化结果列表
    facility_data = []
    facility_parameter_data = []

    # 遍历每个母线，生成 Facility 和 FacilityParameter 数据
    for bus_name, bus_info in buses.items():
        # 1. 生成 Facility 数据（已有逻辑）
        facility_entry = {
            "facility_name": bus_name,
            "facility_type": facility_type_id
        }
        facility_data.append(facility_entry)

        # 2. 提取设备参数（generators/loads/transformers 等）生成 FacilityParameter 数据
        parameter_entry = {
            "facility_name": bus_name,  # 临时字段，后续需替换为 facility_id
            "parameter_data": {
                "generators": bus_info.get("generators", {}),  # 发电机参数
                "loads": bus_info.get("loads", {}),            # 负荷参数
                "transformers": bus_info.get("transformers", {}),  # 变压器参数
                "shunts": bus_info.get("shunts", {}),          # 并联设备参数
                "vsources": bus_info.get("vsources", {})       # 电压源参数
            }
        }
        # 过滤空参数（可选）
        parameter_entry["parameter_data"] = {
            k: v for k, v in parameter_entry["parameter_data"].items() if v
        }
        facility_parameter_data.append(parameter_entry)

    return facility_data, facility_parameter_data

if __name__ == "__main__":
    # 配置参数（需根据实际环境调整）
    json_path = os.path.join(os.path.dirname(__file__), "opendss_devices_adjusted.json")
    facility_type_uuid = "46f71359-cfd2-43e2-a631-4565caaf2d86"  # 设施类型 ID

    # 生成数据
    try:
        facility_data, parameter_data = generate_facility_and_parameter_data(
            json_path, facility_type_uuid
        )
    except Exception as e:
        print(f"数据生成失败：{str(e)}")
        exit(1)

    # 输出 Facility 批量导入数据（原逻辑）
    print("生成的 Facility 批量导入数据：")
    print(json.dumps(facility_data, indent=2))

    # 输出 FacilityParameter 批量导入数据（新增）
    print("\n生成的 FacilityParameter 批量导入数据：")
    print(json.dumps(parameter_data, indent=2))

    # 保存到文件
    facility_output_path = "facility_bulk_import_data.json"
    with open(facility_output_path, 'w', encoding='utf-8') as f:
        json.dump(facility_data, f, indent=2)
    print(f"\nFacility 数据已保存到：{os.path.abspath(facility_output_path)}")

    parameter_output_path = "facility_parameter_bulk_import_data.json"
    with open(parameter_output_path, 'w', encoding='utf-8') as f:
        json.dump(parameter_data, f, indent=2)
    print(f"FacilityParameter 数据已保存到：{os.path.abspath(parameter_output_path)}")