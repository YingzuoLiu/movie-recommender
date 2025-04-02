#!/usr/bin/env python3
"""
创建并训练AWS Personalize解决方案
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import AWS_REGION, SOLUTION_NAME, DATASET_GROUP_ARN

def create_solution(personalize_client, solution_name, dataset_group_arn, recipe_arn):
    """创建解决方案"""
    print(f"创建解决方案: {solution_name}")
    
    try:
        response = personalize_client.create_solution(
            name=solution_name,
            datasetGroupArn=dataset_group_arn,
            recipeArn=recipe_arn
        )
        solution_arn = response['solutionArn']
        print(f"已创建解决方案: {solution_arn}")
        return solution_arn
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceAlreadyExistsException':
            # 解决方案已存在，获取ARN
            response = personalize_client.list_solutions(
                datasetGroupArn=dataset_group_arn
            )
            for existing_solution in response['solutions']:
                if existing_solution['name'] == solution_name:
                    solution_arn = existing_solution['solutionArn']
                    print(f"解决方案已存在: {solution_arn}")
                    return solution_arn
        else:
            raise

def create_solution_version(personalize_client, solution_arn):
    """创建解决方案版本（训练模型）"""
    print(f"创建解决方案版本...")
    
    try:
        response = personalize_client.create_solution_version(
            solutionArn=solution_arn
        )
        solution_version_arn = response['solutionVersionArn']
        print(f"已创建解决方案版本: {solution_version_arn}")
        print("解决方案版本正在训练中，这可能需要一些时间...")
        return solution_version_arn
    except ClientError as e:
        print(f"创建解决方案版本失败: {e}")
        raise

def wait_for_solution_version(personalize_client, solution_version_arn, max_wait_seconds=1800):
    """等待解决方案版本训练完成"""
    print(f"等待解决方案版本训练完成...")
    
    elapsed_time = 0
    while elapsed_time < max_wait_seconds:
        response = personalize_client.describe_solution_version(
            solutionVersionArn=solution_version_arn
        )
        status = response['solutionVersion']['status']
        
        if status == "ACTIVE":
            print(f"解决方案版本训练完成！")
            return True
        elif status == "CREATE FAILED":
            print(f"解决方案版本训练失败: {response['solutionVersion'].get('failureReason', 'Unknown reason')}")
            return False
        
        # 每60秒检查一次状态
        wait_time = 60
        print(f"当前状态: {status}, 已等待: {elapsed_time}秒, 继续等待 {wait_time}秒...")
        time.sleep(wait_time)
        elapsed_time += wait_time
    
    print(f"等待超时！训练可能仍在进行中。请手动检查状态。")
    return False

def get_solution_metrics(personalize_client, solution_version_arn):
    """获取解决方案指标"""
    print(f"获取解决方案指标...")
    
    try:
        response = personalize_client.get_solution_metrics(
            solutionVersionArn=solution_version_arn
        )
        metrics = response['metrics']
        print(f"解决方案指标:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")
        return metrics
    except ClientError as e:
        print(f"获取指标失败: {e}")
        return None

def main():
    """主函数：创建并训练解决方案"""
    if not DATASET_GROUP_ARN:
        print("错误: 未设置DATASET_GROUP_ARN环境变量")
        print("请先创建数据集组和数据集")
        return
    
    print(f"正在连接到AWS Personalize ({AWS_REGION})...")
    
    # 创建Personalize客户端
    personalize_client = boto3.client('personalize', region_name=AWS_REGION)
    
    # 创建解决方案
    recipe_arn = "arn:aws:personalize:::recipe/aws-user-personalization"  # 使用用户个性化配方
    solution_arn = create_solution(personalize_client, SOLUTION_NAME, DATASET_GROUP_ARN, recipe_arn)
    
    # 创建解决方案版本（训练模型）
    solution_version_arn = create_solution_version(personalize_client, solution_arn)
    
    # 等待训练完成
    training_success = wait_for_solution_version(personalize_client, solution_version_arn)
    
    if training_success:
        # 获取模型指标
        metrics = get_solution_metrics(personalize_client, solution_version_arn)
        
        # 保存ARN到环境文件
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        with open(env_file, 'a') as f:
            f.write(f"\nSOLUTION_ARN={solution_arn}\n")
            f.write(f"SOLUTION_VERSION_ARN={solution_version_arn}\n")
        
        print("\n训练完成！")
        print("你可以继续创建市场活动，部署推荐服务。")
        print(f"解决方案ARN: {solution_arn}")
        print(f"解决方案版本ARN: {solution_version_arn}")
    else:
        print("训练失败，请检查错误并重试。")

if __name__ == "__main__":
    main()
