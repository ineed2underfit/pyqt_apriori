#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的预测功能
"""

import sys
import os
import pandas as pd

# 添加路径
sys.path.append(os.path.abspath("new_bayesian/predict"))
from predict import load_model, predict_single

def test_improved_prediction():
    """测试改进的预测功能"""
    print("开始测试改进的预测功能...")
    
    # 加载模型
    model_path = "new_bayesian/pkl/bn_bayesian_model.pkl"
    model, bin_config = load_model(model_path)
    
    # 测试用例
    test_cases = [
        {
            "name": "正常情况",
            "data": {
                'timestamp': '2024-01-01T10:00:00',
                'device_id': 'Device_001',
                'department': 'A',
                'temp': 60.0,
                'vibration': 0.5,
                'oil_pressure': 0.6,
                'voltage': 220.0,
                'rpm': 1500.0
            }
        },
        {
            "name": "极端高温(299°C)",
            "data": {
                'timestamp': '2024-01-01T10:00:00',
                'device_id': 'Device_001',
                'department': 'A',
                'temp': 299.0,  # 极端高温
                'vibration': 0.5,
                'oil_pressure': 0.6,
                'voltage': 220.0,
                'rpm': 1500.0
            }
        },
        {
            "name": "多项极端值",
            "data": {
                'timestamp': '2024-01-01T10:00:00',
                'device_id': 'Device_001',
                'department': 'A',
                'temp': 299.0,  # 极端高温
                'vibration': 3.5,  # 极端高振动
                'oil_pressure': 1.0,  # 极端低油压
                'voltage': 150.0,  # 极端低电压
                'rpm': 3000.0  # 极端高转速
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        print(f"输入数据: {test_case['data']}")
        
        try:
            prediction = predict_single(model, test_case['data'], bin_config)
            print(f"预测结果: {prediction}")
        except Exception as e:
            print(f"预测失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_improved_prediction()
