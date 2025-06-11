import json
import os

def convert_puZ1_in_json(input_file_path, output_file_path=None):
    """
    将 JSON 文件中所有 "puZ1" 字段的字符串值（如 "[0.001, 0.2]"）转换为 JSON 数组
    
    Args:
        input_file_path (str): 输入 JSON 文件路径
        output_file_path (str): 输出 JSON 文件路径（默认覆盖原文件）
    """
    # 读取原始数据
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 遍历所有设施数据项
    for item in data:
        parameter_data = item.get('parameter_data', {})
        vsources = parameter_data.get('vsources', {})
        # 遍历所有 vsources 下的设备（如 "Vsrc_at_1_1"）
        for vsource in vsources.values():
            if 'puZ1' in vsource:
                puZ1_str = vsource['puZ1']
                # 检查是否是字符串格式的数组
                if isinstance(puZ1_str, str) and puZ1_str.startswith('['):
                    # 转换为 JSON 数组
                    vsource['puZ1'] = json.loads(puZ1_str)
    
    # 写入输出文件（默认覆盖原文件）
    output_path = output_file_path or input_file_path
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # 配置路径（根据实际环境调整）
    input_json_path = "f:/代码库/项目开发/开发1.0/django_project/facility_parameter_bulk_import_data.json"
    # 建议先备份原文件，再执行转换
    backup_path = input_json_path.replace('.json', '_backup.json')
    os.system(f'copy "{input_json_path}" "{backup_path}"')  # Windows 备份命令
    # 执行转换（输出到原文件）
    convert_puZ1_in_json(input_json_path)
    print("转换完成！已自动备份原文件为：", backup_path)