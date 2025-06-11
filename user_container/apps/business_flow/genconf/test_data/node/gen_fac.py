import json
import os

def generate_facility_import_data(json_file_path, facility_type_id):
    """
    从 opendss_devices_adjusted.json 提取母线数据，生成 Facility 表批量导入所需的 JSON 数据

    Args:
        json_file_path (str): opendss_devices_adjusted.json 文件路径
        facility_type_id (str): 设施类型 ID（如 "46f71359-cfd2-43e2-a631-4565caaf2d86"）

    Returns:
        list: 生成的批量导入数据列表
    """
    # 读取并解析 JSON 文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            buses = data.get('buses', {})  # 获取所有母线数据
            bus_names = list(buses.keys())  # 提取母线名称（如 "1_riversde", "2_pokagon" 等）
    except FileNotFoundError:
        raise FileNotFoundError(f"错误：文件 {json_file_path} 不存在")
    except json.JSONDecodeError:
        raise ValueError(f"错误：文件 {json_file_path} 不是有效的 JSON")

    # 构造 Facility 批量导入数据
    facility_data = [
        {
            "facility_name": bus_name,  # 母线名称作为设施名称
            "facility_type": facility_type_id  # 用户指定的 facility_type ID
        }
        for bus_name in bus_names
    ]

    return facility_data


if __name__ == "__main__":
    # 配置参数（需根据实际环境调整）
    import os
    json_path = os.path.join(os.path.dirname(__file__), "opendss_devices_adjusted.json")
    facility_type_uuid = "46f71359-cfd2-43e2-a631-4565caaf2d86"  # 设施类型 ID

    # 生成数据
    try:
        imported_data = generate_facility_import_data(json_path, facility_type_uuid)
    except Exception as e:
        print(f"数据生成失败：{str(e)}")
        exit(1)

    # 输出数据到控制台（或保存为新文件）
    print("生成的批量导入数据：")
    print(json.dumps(imported_data, indent=2))  # 格式化输出

    # 可选：保存到文件（如需）
    output_path = "facility_bulk_import_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(imported_data, f, indent=2)
    print(f"\n数据已保存到：{os.path.abspath(output_path)}")