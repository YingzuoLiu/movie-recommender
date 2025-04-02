#!/usr/bin/env python3
"""
使用 Python 创建 Lambda 部署包
"""
import os
import zipfile
import glob

print("安装依赖...")
os.system("pip install boto3 -t .")

print("创建 ZIP 包...")
with zipfile.ZipFile('lambda_function.zip', 'w') as zipf:
    # 添加 lambda_function.py
    zipf.write('lambda_function.py')
    
    # 添加所有依赖库
    for folder in ['boto3', 'botocore', 'urllib3', 'dateutil', 'jmespath', 's3transfer']:
        if os.path.exists(folder):
            for file_path in glob.glob(f"{folder}/**", recursive=True):
                if os.path.isfile(file_path):
                    zipf.write(file_path)
    
    # 添加 python_dateutil 库
    if os.path.exists('python_dateutil'):
        for file_path in glob.glob("python_dateutil/**", recursive=True):
            if os.path.isfile(file_path):
                zipf.write(file_path)
    
    # 添加 six.py
    if os.path.exists('six.py'):
        zipf.write('six.py')

print("完成！")
