from jinja2 import Environment, FileSystemLoader
import json

def generate_lines(template_path, data_path, output_path):
    # 加载模板环境
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('lines_template.dss')
    
    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染 138kV 和 20kV 部分
    content = []
    # 渲染 138kV 线路
    if "138kV_lines" in data:
        rendered_lines = []
        for line in data["138kV_lines"]["lines"]:
            full_line = {**data["138kV_lines"]["default_params"], **line}
            rendered_lines.append(full_line)
        content.append(template.render(
            voltage_level=data["138kV_lines"]["voltage_level"],
            lines=rendered_lines
        ))
    # 渲染 20kV 线路（当前为空）
    if "20kV_lines" in data and data["20kV_lines"]["lines"]:
        rendered_lines_20kv = []
        for line in data["20kV_lines"]["lines"]:
            full_line_20kv = {**data["20kV_lines"]["default_params"], **line}
            rendered_lines_20kv.append(full_line_20kv)
        content.append(template.render(
            voltage_level=data["20kV_lines"]["voltage_level"],
            lines=rendered_lines_20kv
        ))
    
    # 合并内容并写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

# if __name__ == "__main__":
#     generate_lines(
#         template_path='templates/lines_template.dss',
#         data_path='lines_data.json',
#         output_path='lines.dss'
#     )
#     print("lines.dss 生成完成！")