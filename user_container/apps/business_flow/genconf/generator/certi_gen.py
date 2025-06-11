from jinja2 import Template
import json
import os

# 定义路径
template_path = os.path.join(os.path.dirname(__file__), '..', 'jinja_template', 'certi', 'certi.jinja2')
json_data_path = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'certi.json')

# 读取 Jinja2 模板文件
with open(template_path, 'r', encoding='utf-8') as template_file:
    template_str = template_file.read()

# 读取 JSON 数据文件
with open(json_data_path, 'r', encoding='utf-8') as json_file:
    json_data = json.load(json_file)


def render_configuration(template_str, json_data):
    template = Template(template_str)
    rendered_output = template.render(json_data)
    return rendered_output


# output = render_configuration(template_str, json_data)
# print(output)