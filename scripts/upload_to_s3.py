#!/usr/bin/env python3
"""
将处理后的数据上传到S3存储桶
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import AWS_REGION, S3_BUCKET_NAME, PROCESSED_DATA_DIR

def create_bucket_if_not_exists(s3_client, bucket_name, region):
    """创建S3存储桶，如果不存在"""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"存储桶 {bucket_name} 已存在")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # 存储桶不存在，创建它
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': region}
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=location
                )
            print(f"已创建存储桶 {bucket_name}")
        else:
            # 其他错误
            raise

def upload_file(s3_client, file_path, bucket_name, object_name=None):
    """上传文件到S3存储桶"""
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"已上传 {file_path} 到 s3://{bucket_name}/{object_name}")
        return True
    except ClientError as e:
        print(f"上传失败: {e}")
        return False

def main():
    """主函数：上传数据到S3"""
    print(f"正在连接到AWS S3 ({AWS_REGION})...")
    
    # 创建S3客户端
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    # 确保存储桶存在
    create_bucket_if_not_exists(s3_client, S3_BUCKET_NAME, AWS_REGION)
    
    # 上传交互数据
    interactions_file = os.path.join(PROCESSED_DATA_DIR, 'personalize_interactions.csv')
    if os.path.exists(interactions_file):
        upload_file(s3_client, interactions_file, S3_BUCKET_NAME)
    else:
        print(f"错误: 找不到交互数据文件 {interactions_file}")
    
    # 上传物品数据
    items_file = os.path.join(PROCESSED_DATA_DIR, 'personalize_items.csv')
    if os.path.exists(items_file):
        upload_file(s3_client, items_file, S3_BUCKET_NAME)
    else:
        print(f"错误: 找不到物品数据文件 {items_file}")
    
    print("数据上传完成！")
    print(f"S3 存储桶：s3://{S3_BUCKET_NAME}/")

if __name__ == "__main__":
    main()
