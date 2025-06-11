from jinja2 import Environment, FileSystemLoader
import json
import os

def generate_omnet_config(json_path, template_dir, output_dir):
    # 读取 omnet.json 数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 初始化 Jinja2 环境（从模板目录加载）
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # 生成 topology.ini
    ini_template = env.get_template("omnetpp.ini.j2")
    ini_output = ini_template.render(data)
    ini_output_path = os.path.join(output_dir, "topology.ini")
    with open(ini_output_path, 'w', encoding='utf-8') as f:
        f.write(ini_output)
    print(f"生成 topology.ini 至: {ini_output_path}")
    
    # 生成 topology.ned
    ned_template = env.get_template("topology.ned.j2")
    ned_output = ned_template.render(data)
    ned_output_path = os.path.join(output_dir, "topology.ned")
    with open(ned_output_path, 'w', encoding='utf-8') as f:
        f.write(ned_output)
    print(f"生成 topology.ned 至: {ned_output_path}")

if __name__ == "__main__":
    # 配置路径（根据实际目录调整）
    json_path = os.path.join("omnet++", "omnet.json")  # omnet.json 路径
    template_dir = os.path.join("omnet++", "temp")     # 模板目录（含 omnetpp.ini.j2 和 topology.ned.j2）
    output_dir = "omnet++"                             # 输出目录（生成 topology.ini 和 topology.ned）
    
    # 执行生成
    generate_omnet_config(json_path, template_dir, output_dir)