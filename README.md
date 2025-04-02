# 电影推荐系统

基于AWS Personalize的电影推荐系统，使用MovieLens 100K数据集。

## 项目概述

本项目实现了一个完整的电影推荐系统，包括数据处理、模型训练和API部署。系统使用AWS Personalize作为推荐引擎，提供个性化电影推荐。

### 特性

- 基于协同过滤的个性化推荐
- 低延迟API响应
- 成本优化设计
- 完整的评估指标

## 安装与设置

### 前提条件

- Python 3.8+
- AWS账号
- AWS CLI已配置

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境配置

1. 复制示例环境文件
   ```bash
   cp .env.example .env
   ```

2. 编辑`.env`文件设置AWS凭证和配置参数

## 使用方法

### 1. 数据准备

下载并处理MovieLens数据：

```bash
# 下载数据 (下载链接: https://files.grouplens.org/datasets/movielens/ml-100k.zip)
mkdir -p data/raw
cd data/raw
# 下载并解压MovieLens 100K到ml-100k目录

# 转换数据为Personalize格式
cd ../..
python scripts/transform_data.py

# 上传数据到S3
python scripts/upload_to_s3.py
```

### 2. 创建Personalize资源

```bash
# 创建数据集组和数据集
python scripts/create_personalize.py

# 训练推荐模型
python scripts/train_model.py

# 部署市场活动
python scripts/deploy_campaign.py
```

### 3. 部署API

```bash
# 部署Lambda函数和API Gateway
cd api
python package.py
python deploy_api.py
```

### 4. 测试与评估

```bash
# 测试API
python tests/test_api.py

# 评估推荐质量
python tests/evaluate_recommendations.py
```

### 5. 清理资源

```bash
# 清理AWS资源
python scripts/cleanup_resources.py
```

## 项目结构

- `data/`: 数据文件和Schema定义
- `scripts/`: 用于设置和运行系统的脚本
- `api/`: API服务代码
- `tests/`: 测试和评估脚本
- `web/`: 前端演示页面
- `docs/`: 项目文档

## 文档

详细文档请参见`docs/`目录：

- [系统设计文档](docs/system_design.md)
- [标准操作程序](docs/sop.md)
- [用户体验报告](docs/user_experience_report.md)

## 作者

[YingzuoLiu](https://github.com/YingzuoLiu)

## 许可证

MIT
