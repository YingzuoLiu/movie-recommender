#!/usr/bin/env python3
"""
部署AWS Personalize市场活动
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import AWS_REGION, CAMPAIGN_NAME, SOLUTION_VERSION_ARN

def create_campaign(personalize_client, campaign_name, solution_version_arn, min_provisioned_tps=1):
    """创建市场活动"""
    print(f"创建市场活动: {campaign_name}")
    
    try:
        response = personalize_client.create_campaign(
            name=campaign_name,
            solutionVersionArn=solution_version_arn,
            minProvisionedTPS=min_provisioned_tps
        )
        campaign_arn = response['campaignArn']
        print(f"已创建市场活动: {campaign_arn}")
        print("市场活动正在部署中，这可能需要一些时间...")
        return campaign_arn
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceAlreadyExistsException':
            # 市场活动已存在，获取ARN
            response = personalize_client.list_campaigns()
            for existing_campaign in response['campaigns']:
                if existing_campaign['name'] == campaign_name:
                    campaign_arn = existing_campaign['campaignArn']
                    print(f"市场活动已存在: {campaign_arn}")
                    return campaign_arn
        else:
            print(f"创建市场活动失败: {e}")
            raise

def wait_for_campaign(personalize_client, campaign_arn, max_wait_seconds=900):
    """等待市场活动部署完成"""
    print(f"等待市场活动部署完成...")
    
    elapsed_time = 0
    while elapsed_time < max_wait_seconds:
        response = personalize_client.describe_campaign(
            campaignArn=campaign_arn
        )
        status = response['campaign']['status']
        
        if status == "ACTIVE":
            print(f"市场活动部署完成！")
            return True
        elif status == "CREATE FAILED":
            print(f"市场活动部署失败: {response['campaign'].get('failureReason', 'Unknown reason')}")
            return False
        
        # 每30秒检查一次状态
        wait_time = 30
        print(f"当前状态: {status}, 已等待: {elapsed_time}秒, 继续等待 {wait_time}秒...")
        time.sleep(wait_time)
        elapsed_time += wait_time
    
    print(f"等待超时！部署可能仍在进行中。请手动检查状态。")
    return False

def test_recommendations(personalize_runtime, campaign_arn, user_id="1", num_results=10):
    """测试推荐结果"""
    print(f"为用户 {user_id} 获取推荐...")
    
    try:
        response = personalize_runtime.get_recommendations(
            campaignArn=campaign_arn,
            userId=user_id,
            numResults=num_results
        )
        
        recommendations = response['itemList']
        print(f"推荐结果 ({len(recommendations)} 个物品):")
        for i, item in enumerate(recommendations):
            print(f"  {i+1}. 物品ID: {item['itemId']}, 分数: {item['score']}")
        
        return recommendations
    except ClientError as e:
        print(f"获取推荐失败: {e}")
        return None

def main():
    """主函数：部署市场活动"""
    if not SOLUTION_VERSION_ARN:
        print("错误: 未设置SOLUTION_VERSION_ARN环境变量")
        print("请先创建解决方案并训练模型")
        return
    
    print(f"正在连接到AWS Personalize ({AWS_REGION})...")
    
    # 创建Personalize客户端
    personalize_client = boto3.client('personalize', region_name=AWS_REGION)
    personalize_runtime = boto3.client('personalize-runtime', region_name=AWS_REGION)
    
    # 创建市场活动
    campaign_arn = create_campaign(personalize_client, CAMPAIGN_NAME, SOLUTION_VERSION_ARN)
    
    # 等待市场活动部署完成
    deployment_success = wait_for_campaign(personalize_client, campaign_arn)
    
    if deployment_success:
        # 保存ARN到环境文件
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        with open(env_file, 'a') as f:
            f.write(f"\nCAMPAIGN_ARN={campaign_arn}\n")
        
        print("\n市场活动部署完成！")
        print(f"市场活动ARN: {campaign_arn}")
        
        # 测试推荐
        test_recommendations(personalize_runtime, campaign_arn)
        
        print("\n你现在可以部署API来提供推荐服务。")
    else:
        print("市场活动部署失败，请检查错误并重试。")

if __name__ == "__main__":
    main()
