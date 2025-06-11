from jinja2 import Environment, FileSystemLoader
import json, os

class OmnetConfigGenerator:
    def __init__(self, template_dir="jinja_template/omnet"):
        # 初始化Jinja2环境，指定模板目录
        self.template_env = Environment(loader=FileSystemLoader(template_dir))
        # 模板与数据键的映射（根据omnet.json结构定义）
        self.template_to_data_key = {
            'omnetpp.ini.j2': 'omnetpp',       # 对应omnet.json中的"omnetpp"部分
            'topology.ned.j2': 'topology'      # 对应omnet.json中的"topology"部分
        }

    def generate_omnet_config(self, data_path, output_dir="."):
        """
        生成Omnet配置文件（去掉.j2后缀）
        
        Args:
            data_path: omnet.json数据文件路径
            output_dir: 输出目录（默认当前目录）
        """
        # 加载omnet.json数据
        with open(data_path, 'r', encoding='utf-8') as f:
            facility_data = json.load(f)

        # 定义模板列表（需与template_to_data_key中的键一致）
        template_files = ['omnetpp.ini.j2', 'topology.ned.j2']

        # 遍历模板生成文件
        for tpl_name in template_files:
            # 获取模板对应的数据键（如'omnetpp.ini.j2'对应'omnetpp'）
            data_key = self.template_to_data_key[tpl_name]
            # 获取Jinja2模板对象
            template = self.template_env.get_template(tpl_name)
            # 渲染模板（使用facility_data中对应的数据）
            rendered_content = template.render(facility_data[data_key])
            # 生成输出文件名（去掉.j2后缀）
            output_filename = tpl_name.replace('.j2', '')
            # 拼接输出路径
            output_path = os.path.join(output_dir, output_filename)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            print(f"生成文件成功：{output_path}")

# if __name__ == "__main__":
#     # 使用示例
#     generator = OmnetConfigGenerator()
#     # 假设omnet.json路径
#     data_path = "demo_app/test_data/omnet.json"
#     # 生成到当前目录（可自定义输出目录）
#     generator.generate_omnet_config(data_path, output_dir="demo_app/output/omnet_configs")