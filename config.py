"""
推荐系统配置参数
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# AWS配置
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")

# S3配置
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "movie-recommender-data")

# 数据文件路径
RAW_DATA_DIR = "data/raw/ml-100k"
PROCESSED_DATA_DIR = "data/processed"
INTERACTIONS_FILE = f"{PROCESSED_DATA_DIR}/personalize_interactions.csv"
ITEMS_FILE = f"{PROCESSED_DATA_DIR}/personalize_items.csv"

# Personalize配置
DATASET_GROUP_NAME = "MovieRecommender"
INTERACTIONS_SCHEMA_NAME = "interactions-schema"
ITEMS_SCHEMA_NAME = "items-schema"
INTERACTIONS_DATASET_NAME = "interactions-dataset"
ITEMS_DATASET_NAME = "items-dataset"
SOLUTION_NAME = "movie-recommender-solution"
CAMPAIGN_NAME = "movie-recommender-campaign"

# API配置
API_NAME = "MovieRecommenderAPI"
LAMBDA_FUNCTION_NAME = "MovieRecommender"
API_STAGE_NAME = "prod"

# Personalize ARNs (运行时填充)
DATASET_GROUP_ARN = os.getenv("DATASET_GROUP_ARN", "")
INTERACTIONS_SCHEMA_ARN = os.getenv("INTERACTIONS_SCHEMA_ARN", "")
ITEMS_SCHEMA_ARN = os.getenv("ITEMS_SCHEMA_ARN", "")
INTERACTIONS_DATASET_ARN = os.getenv("INTERACTIONS_DATASET_ARN", "")
ITEMS_DATASET_ARN = os.getenv("ITEMS_DATASET_ARN", "")
SOLUTION_ARN = os.getenv("SOLUTION_ARN", "")
SOLUTION_VERSION_ARN = os.getenv("SOLUTION_VERSION_ARN", "")
CAMPAIGN_ARN = os.getenv("CAMPAIGN_ARN", "")

# IAM角色
PERSONALIZE_ROLE_ARN = os.getenv("PERSONALIZE_ROLE_ARN", "")
LAMBDA_ROLE_ARN = os.getenv("LAMBDA_ROLE_ARN", "")

# 推荐配置
DEFAULT_NUM_RECOMMENDATIONS = 10
MAX_NUM_RECOMMENDATIONS = 25