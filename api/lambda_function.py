"""
AWS Lambda函数用于处理推荐请求
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

# Personalize运行时客户端
personalize_runtime = boto3.client('personalize-runtime')

# 从环境变量获取市场活动ARN
CAMPAIGN_ARN = os.environ.get('CAMPAIGN_ARN')
MAX_RECOMMENDATIONS = int(os.environ.get('MAX_RECOMMENDATIONS', '25'))
DEFAULT_RECOMMENDATIONS = int(os.environ.get('DEFAULT_RECOMMENDATIONS', '10'))

def lambda_handler(event, context):
    """Lambda处理函数"""
    try:
        # 从路径参数获取用户ID
        user_id = event.get('pathParameters', {}).get('userId')
        
        # 从查询参数获取推荐数量
        query_params = event.get('queryStringParameters', {}) or {}
        count = min(
            int(query_params.get('count', DEFAULT_RECOMMENDATIONS)),
            MAX_RECOMMENDATIONS
        )
        
        # 验证用户ID
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'userId parameter is required'})
            }
        
        # 验证CAMPAIGN_ARN
        if not CAMPAIGN_ARN:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'CAMPAIGN_ARN environment variable is not set'})
            }
        
        # 调用Personalize获取推荐
        response = personalize_runtime.get_recommendations(
            campaignArn=CAMPAIGN_ARN,
            userId=str(user_id),
            numResults=count
        )
        
        # 处理推荐结果
        recommendations = response.get('itemList', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # 允许CORS
            },
            'body': json.dumps({
                'userId': user_id,
                'recommendations': recommendations,
                'count': len(recommendations)
            })
        }
    
    except ValueError as ve:
        # 参数值错误
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Invalid parameter: {str(ve)}'})
        }
    
    except ClientError as ce:
        # Personalize API错误
        error_code = ce.response['Error']['Code']
        error_message = ce.response['Error']['Message']
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Personalize error: {error_code}',
                'message': error_message
            })
        }
    
    except Exception as e:
        # 其他未预期的错误
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }