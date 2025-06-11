from jinja2 import Environment, FileSystemLoader
import json, os

class OpenDSSConfigGenerator:
    def __init__(self, template_dir="jinja_template/opendss"):
        # 初始化Jinja2环境，指定模板目录
        self.template_env = Environment(loader=FileSystemLoader(template_dir))
        # 模板与数据键的映射（根据opendss.json结构定义）
        self.template_to_data_key = {
            'confirm_kv_bases.dss.j2': 'confirm_kv_bases',
            'generators.dss.j2': 'generators',
            'lines.dss.j2': 'lines',
            'loads.dss.j2': 'loads',
            'transformers.dss.j2': 'transformers',
            'shunts.dss.j2': 'shunts',
            'sw_shunts.dss.j2': 'sw_shunts',
            'generators_as_vsrcs.dss.j2': 'generators_as_vsrcs',
            'dc_and_facts_equiv_elements.dss.j2': 'dc_and_facts_equiv_elements',
            'master_file.dss.j2': 'master_file'
        }

    def generate_opendss_config(self, data_path, output_dir="."):
        """
        生成OpenDSS配置文件（去掉.j2后缀）
        
        Args:
            data_path: opendss.json数据文件路径
            output_dir: 输出目录（默认当前目录）
        """
        # 加载opendss.json数据
        with open(data_path, 'r', encoding='utf-8') as f:
            facility_data = json.load(f)

        # 定义模板列表（需与template_to_data_key中的键一致）
        template_files = [
            'confirm_kv_bases.dss.j2',
            'generators.dss.j2',
            'lines.dss.j2',
            'loads.dss.j2',
            'transformers.dss.j2',
            'shunts.dss.j2',
            'sw_shunts.dss.j2',
            'generators_as_vsrcs.dss.j2',
            'dc_and_facts_equiv_elements.dss.j2',
            'master_file.dss.j2'
        ]

        # 遍历模板生成文件
        for tpl_name in template_files:
            # 获取模板对应的数据键
            data_key = self.template_to_data_key[tpl_name]
            # 获取Jinja2模板对象
            template = self.template_env.get_template(tpl_name)
            # 渲染模板（使用facility_data中对应的数据）
            rendered_content = template.render(facility_data.get(data_key, {}))
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
#     generator = OpenDSSConfigGenerator()
#     # 假设opendss.json路径
#     data_path = "demo_app/test_data/opendss.json"
#     # 生成到当前目录（可自定义输出目录）
#     generator.generate_opendss_config(data_path, output_dir="demo_app/output/opendss_configs")