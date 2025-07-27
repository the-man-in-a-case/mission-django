import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def generate_files(template_path, data_path, output_dir):
    """根据模板和JSON数据生成文件"""
    
    # 设置Jinja2环境
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    
    # 读取JSON数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 渲染模板
    rendered = template.render(data=data)
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 根据文件夹类型处理文件
    folder_type = Path(output_dir).name
    
    if 'certi' in str(output_dir):
        # certi文件夹 - 生成exchange.fed
        output_file = Path(output_dir) / "exchange.fed"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rendered.strip())
            
    elif 'omnet' in str(output_dir):
        # omnet++文件夹 - 分割为topology.ini和topology.ned
        files = rendered.split('---')
        
        ini_file = Path(output_dir) / "topology.ini"
        ned_file = Path(output_dir) / "topology.ned"
        
        if len(files) >= 2:
            with open(ini_file, 'w', encoding='utf-8') as f:
                f.write(files[0].replace('# topology.ini文件内容', '').strip())
            with open(ned_file, 'w', encoding='utf-8') as f:
                f.write(files[1].replace('# topology.ned文件内容', '').strip())
                
    elif 'opendss' in str(output_dir):
        # opendss文件夹 - 分割为多个.dss文件
        files = rendered.split('---')
        file_names = [
            'master_file.dss',
            'loads.dss', 
            'generators.dss',
            'generators_as_vsrcs.dss',
            'lines.dss',
            'transformers.dss',
            'shunts.dss',
            'sw_shunts.dss',
            'dc_and_facts_equiv_elements.dss',
            'confirm_kv_bases.dss'
        ]
        
        for i, content in enumerate(files):
            if i < len(file_names):
                file_path = Path(output_dir) / file_names[i]
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 移除注释行
                    lines = content.strip().split('\n')
                    clean_lines = [line for line in lines if not line.strip().startswith('#')]
                    f.write('\n'.join(clean_lines).strip())

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='从模板和JSON数据生成文件')
    parser.add_argument('template', help='模板文件路径')
    parser.add_argument('data', help='JSON数据文件路径')
    parser.add_argument('output', help='输出文件夹路径')
    
    args = parser.parse_args()
    
    generate_files(args.template, args.data, args.output)
    print(f"成功生成文件到: {args.output}")

if __name__ == "__main__":
    main()