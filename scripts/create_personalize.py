#!/usr/bin/env python3
"""
创建AWS Personalize数据集组和数据集
"""

import os
import sys
import json
import time
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    AWS_REGION, DATASET_GROUP_NAME, INTERACTIONS_SCHEMA_NAME, 
    ITEMS_SCHEMA_NAME, INTERACTIONS_DATASET_NAME, ITEMS_DATASET_NAME,
    PERSONALIZE_ROLE_ARN, S3_BUCKET_NAME
)

def create_schema(personalize_client, schema_name, schema_path):
    """创建Schema"""
    print(f"创建Schema: {schema_name}")
    
    # 读取Schema文件
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    try:
        response = personalize_client.create_schema(
            name=schema_name,
            schema=schema
        )
        schema_arn = response['schemaArn']
        print(f"已创建Schema: {schema_arn}")
        return schema_arn
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceAlreadyExistsException':
            # Schema已存在，获取ARN
            response = personalize_client.list_schemas()
            for existing_schema in response['schemas']:
                if existing_schema['name'] == schema_name:
                    schema_arn = existing_schema['schemaArn']
                    print(f"Schema已存在: {schema_arn}")
                    return schema_arn
        else:
            raise

def create_dataset_group(personalize_client, name):
    """创建数据集组"""
    print(f"创建数据集组: {name}")
    
    try:
        response = personalize_client.create_dataset_group(
            name=name
        )
        dataset_group_arn = response['datasetGroupArn']
        
        # 等待数据集组创建完成
        print("等待数据集组创建完成...")
        max_time = 60  # 最多等待60秒
        while max_time > 0:
            response = personalize_client.describe_dataset_group(
                datasetGroupArn=dataset_group_arn
            )
            status = response['datasetGroup']['status']
            
            if status == "ACTIVE":
                print(f"数据集组创建完成: {dataset_group_arn}")
                return dataset_group_arn
            elif status == "CREATE FAILED":
                raise Exception(f"数据集组创建失败: {response}")
            
            time.sleep(5)
            max_time -= 5
            print(f"当前状态: {status}, 继续等待...")
        
        print("等待超时，请手动检查数据集组状态")
        return dataset_group_arn
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceAlreadyExistsException':
            # 数据集组已存在，获取ARN
            response = personalize_client.list_dataset_groups()
            for existing_group in response['datasetGroups']:
                if existing_group['name'] == name:
                    dataset_group_arn = existing_group['datasetGroupArn']
                    print(f"数据集组已存在: {dataset_group_arn}")
                    return dataset_group_arn
        else:
            raise

def create_dataset(personalize_client, dataset_group_arn, dataset_name, schema_arn, dataset_type):
    """创建数据集"""
    print(f"创建{dataset_type}数据集: {dataset_name}")
    
    try:
        response = personalize_client.create_dataset(
            name=dataset_name,
            datasetGroupArn=dataset_group_arn,
            datasetType=dataset_type,
            schemaArn=schema_arn
        )
        dataset_arn = response['datasetArn']
        print(f"已创建数据集: {dataset_arn}")
        return dataset_arn
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceAlreadyExistsException':
            # 数据集已存在，获取ARN
            response = personalize_client.list_datasets(
                datasetGroupArn=dataset_group_arn
            )
            for existing_dataset in response['datasets']:
                if existing_dataset['name'] == dataset_name:
                    dataset_arn = existing_dataset['datasetArn']
                    print(f"数据集已存在: {dataset_arn}")
                    return dataset_arn
        else:
            raise

def create_import_job(personalize_client, job_name, dataset_arn, s3_path, role_arn):
    """创建导入任务"""
    print(f"创建导入任务: {job_name}")
    
    try:
        response = personalize_client.create_dataset_import_job(
            jobName=job_name,
            datasetArn=dataset_arn,
            dataSource={
                "dataLocation": s3_path
            },
            roleArn=role_arn
        )
        import_job_arn = response['datasetImportJobArn']
        
        # 不等待完成，因为导入可能需要较长时间
        print(f"已创建导入任务: {import_job_arn}")
        print("导入任务正在后台运行，可能需要一些时间才能完成...")
        
        return import_job_arn
    except ClientError as e:
        print(f"创建导入任务失败: {e}")
        raise

def main():
    """主函数：设置Personalize资源"""
    if not PERSONALIZE_ROLE_ARN:
        print("错误: 未设置PERSONALIZE_ROLE_ARN环境变量")
        print("请先创建具有Personalize和S3访问权限的IAM角色")
        return
    
    print(f"正在连接到AWS Personalize ({AWS_REGION})...")
    
    # 创建Personalize客户端
    personalize_client = boto3.client('personalize', region_name=AWS_REGION)
    
    # 创建数据集组
    dataset_group_arn = create_dataset_group(personalize_client, DATASET_GROUP_NAME)
    
    # 创建交互Schema
    interactions_schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'schemas', 'interactions_schema.json')
    interactions_schema_arn = create_schema(
        personalize_client, 
        INTERACTIONS_SCHEMA_NAME, 
        interactions_schema_path
    )
    
    # 创建物品Schema
    items_schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'schemas', 'items_schema.json')
    items_schema_arn = create_schema(
        personalize_client,
        ITEMS_SCHEMA_NAME,
        items_schema_path
    )
    
    # 创建交互数据集
    interactions_dataset_arn = create_dataset(
        personalize_client,
        dataset_group_arn,
        INTERACTIONS_DATASET_NAME,
        interactions_schema_arn,
        'INTERACTIONS'
    )
    
    # 创建物品数据集
    items_dataset_arn = create_dataset(
        personalize_client,
        dataset_group_arn,
        ITEMS_DATASET_NAME,
        items_schema_arn,
        'ITEMS'
    )
    
    # 创建交互数据导入任务
    interactions_s3_path = f"s3://{S3_BUCKET_NAME}/personalize_interactions.csv"
    interactions_import_job_arn = create_import_job(
        personalize_client,
        f"{INTERACTIONS_DATASET_NAME}-import",
        interactions_dataset_arn,
        interactions_s3_path,
        PERSONALIZE_ROLE_ARN
    )
    
    # 创建物品数据导入任务
    items_s3_path = f"s3://{S3_BUCKET_NAME}/personalize_items.csv"
    items_import_job_arn = create_import_job(
        personalize_client,
        f"{ITEMS_DATASET_NAME}-import",
        items_dataset_arn,
        items_s3_path,
        PERSONALIZE_ROLE_ARN
    )
    
    # 保存ARN到环境文件
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    with open(env_file, 'a') as f:
        f.write(f"\nDATASET_GROUP_ARN={dataset_group_arn}\n")
        f.write(f"INTERACTIONS_SCHEMA_ARN={interactions_schema_arn}\n")
        f.write(f"ITEMS_SCHEMA_ARN={items_schema_arn}\n")
        f.write(f"INTERACTIONS_DATASET_ARN={interactions_dataset_arn}\n")
        f.write(f"ITEMS_DATASET_ARN={items_dataset_arn}\n")
    
    print("\n资源创建完成！")
    print(f"数据导入正在进行中，请稍后检查导入状态。")
    print("导入完成后，可以继续创建解决方案和训练模型。")
    
    print("\n保存以下信息，用于后续步骤：")
    print(f"数据集组ARN: {dataset_group_arn}")
    print(f"交互数据集ARN: {interactions_dataset_arn}")
    print(f"物品数据集ARN: {items_dataset_arn}")

if __name__ == "__main__":
    main()
