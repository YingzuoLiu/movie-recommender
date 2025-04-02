#!/usr/bin/env python3
"""
测试推荐API
"""

import requests
import json
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# API端点
API_ENDPOINT = "https://ydh03jw2xa.execute-api.ap-southeast-1.amazonaws.com/prod/recommendations/{userId}"

# 测试用户列表 (从MovieLens数据中抽取)
TEST_USERS = [1, 24, 156, 253, 301, 450, 521, 603, 700, 888]

# 性能指标
latencies = []
success_count = 0
error_count = 0

def test_recommendations():
    """测试API性能和响应"""
    global success_count, error_count
    print("开始API测试...")
    print(f"API端点: {API_ENDPOINT}")
    
    # 测试每个用户的推荐结果
    for user_id in TEST_USERS:
        start_time = time.time()
        try:
            url = API_ENDPOINT.replace("{userId}", str(user_id))
            print(f"请求: {url}")
            response = requests.get(url)
            elapsed = time.time() - start_time
            latencies.append(elapsed * 1000)  # 转换为毫秒
            
            if response.status_code == 200:
                success_count += 1
                data = response.json()
                recommendations = data.get('recommendations', [])
                print(f"用户 {user_id} 获得了 {len(recommendations)} 条推荐, 延迟: {elapsed*1000:.2f}ms")
                # 显示前3条推荐
                for i, item in enumerate(recommendations[:3]):
                    print(f"  {i+1}. 物品ID: {item['itemId']}, 分数: {item['score']:.4f}")
            else:
                error_count += 1
                print(f"用户 {user_id} 请求失败: {response.status_code}, {response.text}")
        except Exception as e:
            error_count += 1
            print(f"用户 {user_id} 请求异常: {str(e)}")
        
        # 请求之间暂停一下，避免过快
        time.sleep(0.5)
    
    # 计算性能指标
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        
        print("\n性能指标:")
        print(f"总请求数: {len(TEST_USERS)}")
        print(f"成功率: {success_count/len(TEST_USERS)*100:.2f}%")
        print(f"平均延迟: {avg_latency:.2f}ms")
        print(f"P95延迟: {p95_latency:.2f}ms")
        print(f"P99延迟: {p99_latency:.2f}ms")
        
        # 绘制延迟分布图
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=20, alpha=0.7)
        plt.axvline(avg_latency, color='r', linestyle='dashed', linewidth=1, label=f'平均值: {avg_latency:.2f}ms')
        plt.axvline(p95_latency, color='g', linestyle='dashed', linewidth=1, label=f'P95: {p95_latency:.2f}ms')
        plt.title('推荐API响应时间分布')
        plt.xlabel('延迟 (毫秒)')
        plt.ylabel('请求数')
        plt.legend()
        plt.savefig('latency_distribution.png')
        
        return {
            'success_rate': success_count/len(TEST_USERS),
            'avg_latency': avg_latency,
            'p95_latency': p95_latency,
            'p99_latency': p99_latency
        }
    else:
        print("无延迟数据收集")
        return None

if __name__ == "__main__":
    test_recommendations()
