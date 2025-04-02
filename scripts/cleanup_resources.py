#!/usr/bin/env python3
"""
清理AWS Personalize资源
"""

import os
import sys
import boto3
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    AWS_REGION, CAMPAIGN_ARN, SOLUTION_ARN, SOLUTION_VERSION_ARN,
    DATASET_GROUP_ARN, INTERACTIONS_DATASET_ARN, ITEMS_DATASET_ARN,
    S3_BUCKET_NAME, LAMBDA_FUNCTION_NAME, API_NAME
)

def confirm(prompt):
    """获取用户确认"""
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("请输入 'y' 或 'n'")

def delete_campaign(personalize_client, campaign_arn):
    """删除市场活动"""
    if not campaign_arn:
        print("未设置市场活动ARN，跳过")
        return

    print(f"删除市场活动: {campaign_arn}")
    try:
        personalize_client.delete_campaign(campaignArn=campaign_arn)
        print("市场活动删除请求已提交，正在等待删除完成...")
        
        # 等待市场活动删除完成
        while True:
            try:
                response = personalize_client.describe_campaign(campaignArn=campaign_arn)
                status = response['campaign']['status']
                print(f"市场活动状态: {status}")
                if status == "DELETE IN_PROGRESS":
                    time.sleep(10)
                    continue
            except personalize_client.exceptions.ResourceNotFoundException:
                print("市场活动已删除")
                break
            except Exception as e:
                print(f"检查状态时出错: {e}")
                break
    except Exception as e:
        print(f"删除市场活动时出错: {e}")

def delete_solution_version(personalize_client, solution_version_arn):
    """删除解决方案版本"""
    if not solution_version_arn:
        print("未设置解决方案版本ARN，跳过")
        return

    print(f"删除解决方案版本: {solution_version_arn}")
    try:
        personalize_client.delete_solution_version(solutionVersionArn=solution_version_arn)
        print("解决方案版本删除请求已提交")
    except Exception as e:
        print(f"删除解决方案版本时出错: {e}")

def delete_solution(personalize_client, solution_arn):
    """删除解决方案"""
    if not solution_arn:
        print("未设置解决方案ARN，跳过")
        return

    print(f"删除解决方案: {solution_arn}")
    try:
        personalize_client.delete_solution(solutionArn=solution_arn)
        print("解决方案删除请求已提交")
    except Exception as e:
        print(f"删除解决方案时出错: {e}")

def delete_datasets(personalize_client, dataset_arns):
    """删除数据集"""
    for dataset_arn in dataset_arns:
        if not dataset_arn:
            continue
            
        print(f"删除数据集: {dataset_arn}")
        try:
            personalize_client.delete_dataset(datasetArn=dataset_arn)
            print("数据集删除请求已提交")
        except Exception as e:
            print(f"删除数据集时出错: {e}")

def delete_dataset_group(personalize_client, dataset_group_arn):
    """删除数据集组"""
    if not dataset_group_arn:
        print("未设置数据集组ARN，跳过")
        return

    print(f"删除数据集组: {dataset_group_arn}")
    try:
        personalize_client.delete_dataset_group(datasetGroupArn=dataset_group_arn)
        print("数据集组删除请求已提交")
    except Exception as e:
        print(f"删除数据集组时出错: {e}")

def delete_s3_files(s3_client, bucket_name):
    """删除S3存储桶中的文件"""
    if not bucket_name:
        print("未设置S3存储桶名称，跳过")
        return
        
    print(f"删除S3存储桶中的文件: {bucket_name}")
    try:
        # 列出存储桶中的所有对象
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"删除文件: {obj['Key']}")
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
            
            print("所有文件已删除")
        else:
            print("存储桶为空")
    except Exception as e:
        print(f"删除S3文件时出错: {e}")

def delete_lambda_function(lambda_client, function_name):
    """删除Lambda函数"""
    if not function_name:
        print("未设置Lambda函数名称，跳过")
        return
        
    print(f"删除Lambda函数: {function_name}")
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print("Lambda函数已删除")
    except Exception as e:
        print(f"删除Lambda函数时出错: {e}")

def delete_api_gateway(apigw_client, api_name):
    """删除API Gateway"""
    if not api_name:
        print("未设置API名称，跳过")
        return
        
    print(f"查找API Gateway: {api_name}")
    try:
        # 查找API ID
        response = apigw_client.get_rest_apis()
        api_id = None
        
        for api in response['items']:
            if api['name'] == api_name:
                api_id = api['id']
                break
        
        if api_id:
            print(f"删除API Gateway: {api_id}")
            apigw_client.delete_rest_api(restApiId=api_id)
            print("API Gateway已删除")
        else:
            print(f"未找到名为 {api_name} 的API")
    except Exception as e:
        print(f"删除API Gateway时出错: {e}")

def main():
    """主函数：清理AWS资源"""
    print("即将清理AWS Personalize资源...")
    
    if not confirm("此操作将删除所有已创建的资源。确定要继续吗?"):
        print("操作已取消")
        return
    
    print(f"正在连接到AWS服务 ({AWS_REGION})...")
    
    # 创建客户端
    personalize_client = boto3.client('personalize', region_name=AWS_REGION)
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    apigw_client = boto3.client('apigateway', region_name=AWS_REGION)
    
    # 删除资源（按依赖顺序）
    print("\n=== 清理API和Lambda ===")
    delete_api_gateway(apigw_client, API_NAME)
    delete_lambda_function(lambda_client, LAMBDA_FUNCTION_NAME)
    
    print("\n=== 清理Personalize资源 ===")
    delete_campaign(personalize_client, CAMPAIGN_ARN)
    delete_solution_version(personalize_client, SOLUTION_VERSION_ARN)
    delete_solution(personalize_client, SOLUTION_ARN)
    delete_datasets(personalize_client, [INTERACTIONS_DATASET_ARN, ITEMS_DATASET_ARN])
    delete_dataset_group(personalize_client, DATASET_GROUP_ARN)
    
    print("\n=== 清理S3资源 ===")
    if confirm(f"是否要删除S3存储桶 {S3_BUCKET_NAME} 中的文件?"):
        delete_s3_files(s3_client, S3_BUCKET_NAME)
    
    print("\n所有资源清理完成！")

if __name__ == "__main__":
    main()
