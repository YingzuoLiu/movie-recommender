"""
将MovieLens 100K数据转换为AWS Personalize格式
"""

import os
import pandas as pd
import numpy as np
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

def main():
    """主函数：转换MovieLens数据为Personalize格式"""
    print("开始转换MovieLens数据...")
    
    # 确保输出目录存在
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # 读取评分数据
    ratings_file = os.path.join(RAW_DATA_DIR, 'u.data')
    print(f"读取评分数据: {ratings_file}")
    ratings = pd.read_csv(ratings_file, sep='\t', 
                         names=['USER_ID', 'ITEM_ID', 'RATING', 'TIMESTAMP'])
    
    # 读取电影元数据
    movies_file = os.path.join(RAW_DATA_DIR, 'u.item')
    print(f"读取电影数据: {movies_file}")
    movies_cols = ['ITEM_ID', 'TITLE', 'RELEASE_DATE', 'VIDEO_RELEASE_DATE', 'IMDb_URL'] + \
                 [f'GENRE_{i}' for i in range(19)]
    movies = pd.read_csv(movies_file, sep='|', encoding='latin-1', 
                        names=movies_cols)
    
    # 合并电影类型为一个字段
    genre_columns = [f'GENRE_{i}' for i in range(19)]
    genre_names = ['unknown', 'Action', 'Adventure', 'Animation', 'Children',
                 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
                 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller',
                 'War', 'Western']
    
    def get_genres(row):
        """提取电影类型"""
        genres = []
        for i, genre in enumerate(genre_names):
            if row[f'GENRE_{i}'] == 1:
                genres.append(genre)
        return '|'.join(genres)
    
    movies['GENRES'] = movies.apply(get_genres, axis=1)
    
    # 提取发行年份
    movies['RELEASE_YEAR'] = movies['RELEASE_DATE'].apply(
        lambda x: str(x[-4:]) if isinstance(x, str) and len(x) >= 4 else 'unknown')
    
    # 准备Personalize交互数据
    print("准备交互数据...")
    interactions = ratings[['USER_ID', 'ITEM_ID', 'TIMESTAMP']]
    # 添加事件类型 (将评分>=4的记录标记为"watch"，其他为"click")
    interactions['EVENT_TYPE'] = ratings['RATING'].apply(lambda x: 'watch' if x >= 4 else 'click')
    interactions['EVENT_VALUE'] = ratings['RATING']
    
    # 准备物品元数据
    print("准备物品元数据...")
    items = movies[['ITEM_ID', 'TITLE', 'GENRES', 'RELEASE_YEAR']]
    
    # 保存为CSV (不含标题行，符合Personalize要求)
    interactions_file = os.path.join(PROCESSED_DATA_DIR, 'personalize_interactions.csv')
    items_file = os.path.join(PROCESSED_DATA_DIR, 'personalize_items.csv')
    
    print(f"保存交互数据: {interactions_file}")
    interactions.to_csv(interactions_file, index=False, header=False)
    
    print(f"保存物品数据: {items_file}")
    items.to_csv(items_file, index=False, header=False)
    
    print(f"数据转换完成！")
    print(f"处理了 {len(interactions)} 条交互记录")
    print(f"处理了 {len(items)} 条物品记录")

if __name__ == "__main__":
    main()