#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试概率分布显示功能
"""

import sys
import os
import pandas as pd

# 添加路径
sys.path.append(os.path.abspath("new_bayesian/predict"))
from predict import load_model, predict_single

def test_probability_display():
    """测试概率分布显示功能"""
    print("开始测试概率分布显示功能...")
    
    # 加载模型
    model_path = "new_bayesian/pkl/bn_bayesian_model.pkl"
    model, bin_config = load_model(model_path)
    
    # 测试用例 - 您提到的故障数据
    test_data = {
        'timestamp': '2022-08-26T09:42:31',
        'device_id': 'DEV-006',
        'department': '质检部',
        'temp': 54.72788,
        'vibration': 1.37010,
        'oil_pressure': 18.18262,
        'voltage': 180.10450,  # 低电压
        'rpm': 1917.61239
    }
    
    print(f"测试数据: {test_data}")
    print("真实标签: 电力供应故障")
    print("-" * 50)
    
    try:
        # 执行预测
        prediction_result, probability_dist = predict_single(model, test_data, bin_config)
        
        print(f"预测结果: {prediction_result}")
        print(f"概率分布:")
        for fault_type, prob in probability_dist.items():
            print(f"  {fault_type}: {prob:.3f} ({prob:.1%})")
        
        # 检查最高概率
        max_prob = max(probability_dist.values())
        print(f"\n最高概率: {max_prob:.3f} ({max_prob:.1%})")
        
        if max_prob < 0.6:
            print("⚠️ 低置信度警告：预测结果可能不够可靠")
        
        # 分析为什么预测为"正常运行"
        print(f"\n分析:")
        print(f"- 电压 {test_data['voltage']} 被分箱到: {bin_config['voltage']['bins']}")
        print(f"- 电压分箱标签: {bin_config['voltage']['labels']}")
        
        # 找到电压对应的分箱
        voltage = test_data['voltage']
        bins = bin_config['voltage']['bins']
        labels = bin_config['voltage']['labels']
        
        for i in range(len(bins)-1):
            if bins[i] <= voltage <= bins[i+1]:
                print(f"- 电压 {voltage} 落在分箱 [{bins[i]:.2f}, {bins[i+1]:.2f}] -> '{labels[i]}'")
                break
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_probability_display()
