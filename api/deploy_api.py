#!/usr/bin/env python3
"""
部署Lambda函数和API Gateway
"""

import os
import boto3
import json
import time
import sys

# 获取环境变量
AWS_REGION = "ap-southeast-1"  # 直接设置区域
LAMBDA_FUNCTION_NAME = "MovieRecommender"
API_NAME = "MovieRecommenderAPI"
API_STAGE_NAME = "prod"
CAMPAIGN_ARN = "arn:aws:personalize:ap-southeast-1:204529129889:campaign/movie-recommender-campaign"

def create_lambda_role():
    """创建Lambda所需IAM角色"""
    print("创建Lambda IAM角色...")
    
    iam = boto3.client('iam', region_name=AWS_REGION)
    
    # 创建角色
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName="LambdaPersonalizeRole",
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Lambda to call Personalize"
        )
        role_arn = response['Role']['Arn']
        
        # 添加基本执行策略
        iam.attach_role_policy(
            RoleName="LambdaPersonalizeRole",
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        # 创建内联策略允许访问 Personalize
        personalize_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "personalize:GetRecommendations",
                        "personalize:GetPersonalizedRanking"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName="LambdaPersonalizeRole",
            PolicyName="PersonalizeRuntimeAccess",
            PolicyDocument=json.dumps(personalize_policy)
        )
        
        # 等待角色可用
        print("等待IAM角色传播...")
        time.sleep(10)
        
        print(f"创建IAM角色成功: {role_arn}")
        return role_arn
    
    except iam.exceptions.EntityAlreadyExistsException:
        print("角色已存在，获取ARN...")
        response = iam.get_role(RoleName="LambdaPersonalizeRole")
        role_arn = response['Role']['Arn']
        print(f"使用现有角色: {role_arn}")
        return role_arn
    except Exception as e:
        print(f"创建角色失败: {str(e)}")
        raise

def deploy_lambda(role_arn):
    """部署Lambda函数"""
    print(f"部署Lambda函数: {LAMBDA_FUNCTION_NAME}...")
    
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    
    # 检查是否已存在
    try:
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        print("Lambda函数已存在，正在更新...")
        update_function = True
    except Exception:
        print("Lambda函数不存在，正在创建...")
        update_function = False
    
    # 读取ZIP包
    with open('lambda_function.zip', 'rb') as f:
        zip_bytes = f.read()
    
    # 创建或更新函数
    try:
        if update_function:
            response = lambda_client.update_function_code(
                FunctionName=LAMBDA_FUNCTION_NAME,
                ZipFile=zip_bytes,
                Publish=True
            )
            
            # 更新环境变量
            lambda_client.update_function_configuration(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Environment={
                    'Variables': {
                        'CAMPAIGN_ARN': CAMPAIGN_ARN,
                        'MAX_RECOMMENDATIONS': '25',
                        'DEFAULT_RECOMMENDATIONS': '10'
                    }
                }
            )
        else:
            response = lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_bytes},
                Timeout=30,
                MemorySize=128,
                Publish=True,
                Environment={
                    'Variables': {
                        'CAMPAIGN_ARN': CAMPAIGN_ARN,
                        'MAX_RECOMMENDATIONS': '25',
                        'DEFAULT_RECOMMENDATIONS': '10'
                    }
                }
            )
        
        function_arn = response['FunctionArn']
        print(f"Lambda部署成功: {function_arn}")
        return function_arn
    
    except Exception as e:
        print(f"Lambda部署失败: {str(e)}")
        raise

def deploy_api_gateway(lambda_arn):
    """部署API Gateway"""
    print(f"部署API Gateway: {API_NAME}...")
    
    apigw = boto3.client('apigateway', region_name=AWS_REGION)
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    
    # 创建API
    try:
        response = apigw.create_rest_api(
            name=API_NAME,
            description='API for movie recommendations',
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
        api_id = response['id']
        print(f"API Gateway创建成功: {api_id}")
    except Exception as e:
        print(f"创建API失败，尝试查找现有API: {str(e)}")
        # 尝试查找现有API
        apis = apigw.get_rest_apis()
        api_id = None
        for api in apis['items']:
            if api['name'] == API_NAME:
                api_id = api['id']
                print(f"找到现有API: {api_id}")
                break
        
        if not api_id:
            print("无法找到API，退出")
            raise
    
    # 获取根资源
    resources = apigw.get_resources(restApiId=api_id)
    root_id = None
    for resource in resources['items']:
        if resource['path'] == '/':
            root_id = resource['id']
            break
    
    if not root_id:
        print("无法找到根资源，退出")
        raise Exception("找不到根资源")
    
    # 创建资源结构: /recommendations/{userId}
    try:
        # 创建/recommendations
        recommendations_resource = apigw.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='recommendations'
        )
        recommendations_id = recommendations_resource['id']
        
        # 创建/recommendations/{userId}
        user_id_resource = apigw.create_resource(
            restApiId=api_id,
            parentId=recommendations_id,
            pathPart='{userId}'
        )
        user_id_id = user_id_resource['id']
    except Exception as e:
        print(f"创建资源失败，尝试查找现有资源: {str(e)}")
        # 尝试查找现有资源
        resources = apigw.get_resources(restApiId=api_id)
        recommendations_id = None
        user_id_id = None
        
        for resource in resources['items']:
            if resource['path'] == '/recommendations':
                recommendations_id = resource['id']
            elif resource['path'] == '/recommendations/{userId}':
                user_id_id = resource['id']
        
        if not recommendations_id or not user_id_id:
            print("无法找到必要的资源，退出")
            raise Exception("找不到必要的资源")
    
    # 创建GET方法
    try:
        apigw.put_method(
            restApiId=api_id,
            resourceId=user_id_id,
            httpMethod='GET',
            authorizationType='NONE',
            requestParameters={
                'method.request.path.userId': True
            }
        )
        print("创建GET方法成功")
    except Exception as e:
        print(f"创建方法失败，可能已存在: {str(e)}")
    
    # 创建Lambda集成
    try:
        apigw.put_integration(
            restApiId=api_id,
            resourceId=user_id_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        print("创建Lambda集成成功")
    except Exception as e:
        print(f"创建集成失败，可能已存在: {str(e)}")
    
    # 添加Lambda权限
    try:
        source_arn = f'arn:aws:execute-api:{AWS_REGION}:*:{api_id}/*/*'
        lambda_client.add_permission(
            FunctionName=LAMBDA_FUNCTION_NAME,
            StatementId=f'apigateway-invoke-{int(time.time())}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
        )
        print("添加Lambda权限成功")
    except Exception as e:
        print(f"添加权限失败，可能已存在: {str(e)}")
    
    # 部署API
    try:
        apigw.create_deployment(
            restApiId=api_id,
            stageName=API_STAGE_NAME
        )
        print(f"API部署成功: {API_STAGE_NAME}")
    except Exception as e:
        print(f"部署API失败: {str(e)}")
    
    # 获取API URL
    api_url = f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/{API_STAGE_NAME}"
    endpoint_url = f"{api_url}/recommendations/{{userId}}"
    
    print(f"\nAPI Gateway端点URL: {endpoint_url}")
    print(f"使用方式: 将{{userId}}替换为实际用户ID，例如: {api_url}/recommendations/1")
    
    # 保存API URL到环境文件
    with open('../.env', 'a') as f:
        f.write(f"\nAPI_ENDPOINT={endpoint_url}\n")
    print("API端点URL已保存到.env文件")
    
    return endpoint_url

def main():
    """主函数"""
    print("开始API服务部署...\n")
    
    # 确保CAMPAIGN_ARN已设置
    if not CAMPAIGN_ARN:
        print("错误: CAMPAIGN_ARN未设置，请先创建市场活动")
        return
    
    # 创建角色
    role_arn = create_lambda_role()
    
    # 部署Lambda
    lambda_arn = deploy_lambda(role_arn)
    
    # 部署API Gateway
    api_url = deploy_api_gateway(lambda_arn)
    
    print("\nAPI服务部署完成!")
    print(f"测试命令: curl {api_url.replace('{userId}', '1')}")

if __name__ == "__main__":
    main()
