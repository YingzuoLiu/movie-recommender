#!/usr/bin/env python3
"""
评估推荐系统质量
"""

import pandas as pd
import numpy as np
import requests
import json
import matplotlib.pyplot as plt
from collections import Counter
import os
import sys

# API端点
API_ENDPOINT = "https://ydh03jw2xa.execute-api.ap-southeast-1.amazonaws.com/prod/recommendations/{userId}"

# 数据目录
RAW_DATA_DIR = "../data/raw/ml-100k"

def load_movielens_data():
    """加载MovieLens数据"""
    print("加载MovieLens数据...")
    
    # 确保目录存在
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        print(f"创建目录: {RAW_DATA_DIR}")
        
        # 如果目录是空的，提醒用户下载数据
        print("请下载MovieLens 100K数据并解压到data/raw/ml-100k目录")
        print("下载链接: https://files.grouplens.org/datasets/movielens/ml-100k.zip")
        return None, None
    
    # 检查文件是否存在
    ratings_file = os.path.join(RAW_DATA_DIR, 'u.data')
    movies_file = os.path.join(RAW_DATA_DIR, 'u.item')
    
    if not os.path.exists(ratings_file) or not os.path.exists(movies_file):
        print("警告: 数据文件不存在，跳过数据加载")
        print("请确保u.data和u.item文件位于data/raw/ml-100k目录中")
        return None, None
    
    try:
        # 加载评分数据
        ratings = pd.read_csv(ratings_file, sep='\t', 
                            names=['user_id', 'item_id', 'rating', 'timestamp'])
        
        # 加载电影数据
        movies_cols = ['item_id', 'title', 'release_date', 'video_release_date', 'imdb_url'] +                     [f'genre_{i}' for i in range(19)]
        movies = pd.read_csv(movies_file, sep='|', encoding='latin-1', 
                            names=movies_cols)
        
        # 仅保留需要的列
        movies = movies[['item_id', 'title']]
        
        print(f"加载了 {len(ratings)} 条评分数据")
        print(f"加载了 {len(movies)} 条电影数据")
        
        return ratings, movies
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        return None, None

def get_recommendations(user_id, count=10):
    """从API获取推荐"""
    try:
        url = API_ENDPOINT.replace("{userId}", str(user_id))
        if "?" not in url:
            url += f"?count={count}"
        else:
            url += f"&count={count}"
            
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('recommendations', [])
        else:
            print(f"获取推荐失败: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        print(f"获取推荐异常: {str(e)}")
        return []

def evaluate_relevance(test_users=None, num_samples=10, num_recommendations=10):
    """评估推荐相关性"""
    # 加载数据
    ratings, movies = load_movielens_data()
    if ratings is None or movies is None:
        print("错误: 无法加载数据进行评估")
        return None
        
    if test_users is None:
        # 随机抽取用户
        all_users = ratings['user_id'].unique()
        test_users = np.random.choice(all_users, size=min(num_samples, len(all_users)), replace=False)
    
    print(f"评估 {len(test_users)} 名用户的推荐相关性")
    
    # 评估指标
    hit_rate = 0
    avg_precision = 0
    avg_ndcg = 0
    
    for user_id in test_users:
        # 获取用户的历史评分
        user_ratings = ratings[ratings['user_id'] == user_id]
        liked_items = set(user_ratings[user_ratings['rating'] >= 4]['item_id'].tolist())
        
        if not liked_items:
            continue
            
        # 获取推荐
        recommendations = get_recommendations(user_id, num_recommendations)
        if not recommendations:
            continue
            
        rec_items = [int(item['itemId']) for item in recommendations]
        
        # 计算命中率
        hits = set(rec_items).intersection(liked_items)
        if hits:
            hit_rate += 1
        
        # 计算准确率
        precision = len(hits) / len(rec_items) if rec_items else 0
        avg_precision += precision
        
        # 计算NDCG
        relevance = [1 if int(item['itemId']) in liked_items else 0 for item in recommendations]
        dcg = sum((rel / np.log2(i + 2)) for i, rel in enumerate(relevance))
        idcg = sum((1 / np.log2(i + 2)) for i in range(min(len(liked_items), len(rec_items))))
        ndcg = dcg / idcg if idcg > 0 else 0
        avg_ndcg += ndcg
        
        print(f"用户 {user_id}: 推荐 {len(rec_items)} 个物品, 命中 {len(hits)}, 准确率 {precision:.4f}, NDCG {ndcg:.4f}")
    
    # 计算平均指标
    num_evaluated = len(test_users)
    if num_evaluated > 0:
        hit_rate = hit_rate / num_evaluated
        avg_precision = avg_precision / num_evaluated
        avg_ndcg = avg_ndcg / num_evaluated
        
        print("\n推荐效果评估:")
        print(f"覆盖率 (至少一个命中): {hit_rate:.4f}")
        print(f"平均准确率: {avg_precision:.4f}")
        print(f"平均NDCG: {avg_ndcg:.4f}")
        
        return {
            'hit_rate': hit_rate,
            'avg_precision': avg_precision,
            'avg_ndcg': avg_ndcg
        }
    else:
        print("没有可评估的用户")
        return None

def analyze_diversity(num_samples=20, num_recommendations=10):
    """分析推荐多样性"""
    # 加载数据
    ratings, movies = load_movielens_data()
    if ratings is None or movies is None:
        print("错误: 无法加载数据进行评估")
        return None
        
    # 随机抽取用户
    all_users = ratings['user_id'].unique()
    test_users = np.random.choice(all_users, size=min(num_samples, len(all_users)), replace=False)
    
    print(f"分析 {len(test_users)} 名用户的推荐多样性")
    
    # 收集所有推荐
    all_recommendations = []
    user_recommendations = {}
    
    for user_id in test_users:
        recommendations = get_recommendations(user_id, num_recommendations)
        if recommendations:
            item_ids = [int(item['itemId']) for item in recommendations]
            all_recommendations.extend(item_ids)
            user_recommendations[user_id] = item_ids
    
    # 计算多样性指标
    if all_recommendations:
        # 推荐物品的总数
        total_items = len(all_recommendations)
        
        # 唯一物品的数量
        unique_items = len(set(all_recommendations))
        
        # 计算基尼系数
        item_counts = Counter(all_recommendations)
        sorted_counts = sorted(item_counts.values())
        cumulative = np.cumsum(sorted_counts)
        n = len(sorted_counts)
        gini = (2 * np.sum((np.arange(1, n+1) * sorted_counts))) / (n * np.sum(sorted_counts)) - (n+1)/n
        
        # 计算用户间的多样性
        user_overlap = 0
        user_pairs = 0
        
        for i, user1 in enumerate(user_recommendations.keys()):
            for j, user2 in enumerate(user_recommendations.keys()):
                if i < j:  # 避免重复比较
                    set1 = set(user_recommendations[user1])
                    set2 = set(user_recommendations[user2])
                    overlap = len(set1.intersection(set2)) / num_recommendations
                    user_overlap += overlap
                    user_pairs += 1
        
        avg_user_overlap = user_overlap / user_pairs if user_pairs > 0 else 0
        
        print("\n推荐多样性分析:")
        print(f"推荐物品总数: {total_items}")
        print(f"唯一物品数量: {unique_items}")
        print(f"物品覆盖率: {unique_items / len(movies):.4f}")
        print(f"推荐集中度 (基尼系数): {gini:.4f}")
        print(f"用户间平均重叠率: {avg_user_overlap:.4f}")
        
        # 绘制推荐分布图
        plt.figure(figsize=(12, 6))
        
        # 最常推荐的前20个物品
        common_items = item_counts.most_common(20)
        items, counts = zip(*common_items)
        
        # 获取物品标题
        item_titles = []
        for item_id in items:
            title = movies[movies['item_id'] == item_id]['title'].values
            if len(title) > 0:
                # 截断标题以适应图表
                item_titles.append(title[0][:20] + '...' if len(title[0]) > 20 else title[0])
            else:
                item_titles.append(f"Item {item_id}")
        
        plt.barh(range(len(counts)), counts, align='center')
        plt.yticks(range(len(counts)), item_titles)
        plt.xlabel('推荐次数')
        plt.title('最常推荐的20部电影')
        plt.tight_layout()
        plt.savefig('recommendation_distribution.png')
        
        return {
            'unique_ratio': unique_items / total_items,
            'coverage': unique_items / len(movies),
            'gini': gini,
            'user_overlap': avg_user_overlap
        }
    else:
        print("没有收集到推荐")
        return None

def main():
    """主函数"""
    print("开始推荐系统评估...\n")
    
    # 评估推荐相关性 (使用较少样本节省时间)
    relevance = evaluate_relevance(num_samples=10)
    
    # 分析推荐多样性 (使用较少样本节省时间)
    diversity = analyze_diversity(num_samples=20)
    
    # 生成评估报告
    report_file = 'evaluation_report.md'
    with open(report_file, "w") as f:
        f.write("# 推荐系统评估报告\n\n")
        
        f.write("## 1. 推荐相关性\n\n")
        if relevance:
            f.write(f"- 覆盖率 (至少一个命中): {relevance['hit_rate']:.4f}\n")
            f.write(f"- 平均准确率: {relevance['avg_precision']:.4f}\n")
            f.write(f"- 平均NDCG: {relevance['avg_ndcg']:.4f}\n")
        else:
            f.write("未收集到相关性数据\n")
        
        f.write("\n## 2. 推荐多样性\n\n")
        if diversity:
            f.write(f"- 唯一物品比例: {diversity['unique_ratio']:.4f}\n")
            f.write(f"- 物品覆盖率: {diversity['coverage']:.4f}\n")
            f.write(f"- 推荐集中度 (基尼系数): {diversity['gini']:.4f}\n")
            f.write(f"- 用户间平均重叠率: {diversity['user_overlap']:.4f}\n")
        else:
            f.write("未收集到多样性数据\n")
        
        f.write("\n## 3. 总结\n\n")
        f.write("该推荐系统基于AWS Personalize构建，使用MovieLens 100K数据集。")
        
        if relevance and diversity:
            # 根据指标评估系统表现
            precision_good = relevance['avg_precision'] > 0.1
            diversity_good = diversity['gini'] < 0.8
            
            if precision_good and diversity_good:
                overall = "系统整体表现良好，兼顾了相关性和多样性。"
            elif precision_good:
                overall = "系统相关性表现良好，但可以提高推荐多样性。"
            elif diversity_good:
                overall = "系统多样性表现良好，但可以提高推荐相关性。"
            else:
                overall = "系统各方面均有提升空间，建议进一步优化模型和参数。"
                
            f.write(overall)
        
        f.write("\n\n*注: 本报告基于有限样本测试，仅供参考。*")
        
    print(f"\n评估报告已生成: {report_file}")

if __name__ == "__main__":
    main()
