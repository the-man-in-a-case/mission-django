import json
from jinja2 import Environment, FileSystemLoader

def load_json_data(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 修改 render_files 函数
def render_files(json_data, output_dir):
    env = Environment(loader=FileSystemLoader(output_dir))

    # 渲染 NED 文件
    ned_template = env.get_template("topology.ned.j2")
    ned_output = ned_template.render(
        global_params=json_data["global_params"],
        nodedata=json_data["nodedata"],
        connections=json_data["edgedata"]  # 使用 edgedata
    )
    with open(f"{output_dir}/test_topology.ned", "w", encoding="utf-8") as f:
        f.write(ned_output)

    # 渲染 INI 文件
    ini_template = env.get_template("topology.ini.j2")
    ini_output = ini_template.render(
        global_params=json_data["global_params"],
        nodedata=json_data["nodedata"]
    )
    with open(f"{output_dir}/test_topology.ini", "w", encoding="utf-8") as f:
        f.write(ini_output)

if __name__ == "__main__":
    json_data = load_json_data("d:/git/mission-django/user_container/apps/business_flow/genconf/omnet++/new_test/data.json")
    output_directory = "d:/git/mission-django/user_container/apps/business_flow/genconf/omnet++/new_test"
    render_files(json_data, output_directory)
    print("拓扑文件生成完成！")