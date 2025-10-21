"""
调试脚本：检查单次预测为什么总是返回100%正常运行
"""
import sys
import os
import pickle
import pandas as pd

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

# 添加路径
sys.path.append(os.path.abspath("new_bayesian/predict"))
from predict import load_model, predict_single, _discretize_single_value

def debug_prediction():
    print("="*60)
    print("开始调试预测逻辑")
    print("="*60)
    
    # 1. 加载模型和bin_config
    model_path = "new_bayesian/pkl/bn_bayesian_model.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    print(f"\n1️⃣ 加载模型...")
    model, bin_config = load_model(model_path)
    print(f"✅ 模型加载成功")
    
    # 2. 检查bin_config
    print(f"\n2️⃣ 检查分箱配置...")
    if bin_config:
        for feature, config in bin_config.items():
            print(f"\n{feature}:")
            print(f"  bins: {config['bins']}")
            print(f"  labels: {config['labels']}")
    else:
        print("❌ bin_config 为空！这是问题所在！")
        return
    
    # 3. 测试不同的输入值
    print(f"\n3️⃣ 测试不同输入值的分箱结果...")
    
    test_cases = [
        {
            'name': '正常值',
            'temp': 58.0,
            'vibration': 1.4,
            'oil_pressure': 11.0,
            'voltage': 220.0,
            'rpm': 2020.0
        },
        {
            'name': '高温',
            'temp': 85.0,
            'vibration': 1.4,
            'oil_pressure': 11.0,
            'voltage': 220.0,
            'rpm': 2020.0
        },
        {
            'name': '高振动',
            'temp': 58.0,
            'vibration': 2.5,
            'oil_pressure': 11.0,
            'voltage': 220.0,
            'rpm': 2020.0
        },
        {
            'name': '低油压',
            'temp': 58.0,
            'vibration': 1.4,
            'oil_pressure': 5.0,
            'voltage': 220.0,
            'rpm': 2020.0
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- 测试: {test_case['name']} ---")
        
        # 构建输入数据
        data_dict = {
            'timestamp': '2023-06-01T00:00:00',
            'device_id': 'DEV-001',
            'department': '生产部',
            'temp': test_case['temp'],
            'vibration': test_case['vibration'],
            'oil_pressure': test_case['oil_pressure'],
            'voltage': test_case['voltage'],
            'rpm': test_case['rpm']
        }
        
        print(f"输入值:")
        for key in ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']:
            print(f"  {key}: {data_dict[key]}")
        
        # 测试分箱
        print(f"\n分箱结果:")
        for feature in ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']:
            if feature in bin_config:
                original_value = data_dict[feature]
                binned_value = _discretize_single_value(original_value, bin_config[feature])
                print(f"  {feature}: {original_value} → {binned_value}")
        
        # 执行预测
        print(f"\n预测结果:")
        try:
            prediction_result, probability_dist = predict_single(model, data_dict, bin_config)
            print(f"  预测: {prediction_result}")
            print(f"  概率分布:")
            for fault_type, prob in probability_dist.items():
                print(f"    {fault_type}: {prob:.1%}")
        except Exception as e:
            print(f"  ❌ 预测失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. 检查模型的CPD（条件概率分布）
    print(f"\n4️⃣ 检查模型结构...")
    print(f"模型节点: {model.nodes()}")
    print(f"模型边数量: {len(model.edges())}")
    
    # 检查故障类型的CPD
    print(f"\n5️⃣ 检查'故障类型'节点的CPD...")
    try:
        cpd = model.get_cpds('故障类型')
        print(f"CPD变量: {cpd.variable}")
        print(f"CPD状态: {cpd.state_names['故障类型']}")
        print(f"CPD形状: {cpd.values.shape}")
        print(f"CPD父节点: {cpd.variables[1:] if len(cpd.variables) > 1 else '无'}")
    except Exception as e:
        print(f"❌ 获取CPD失败: {e}")
    
    print("\n" + "="*60)
    print("调试完成")
    print("="*60)

if __name__ == "__main__":
    debug_prediction()
