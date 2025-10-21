"""
检查温度分箱边界，找出为什么温度变化1度会导致概率剧变
"""
import sys
import os
sys.path.append(os.path.abspath("new_bayesian/predict"))
from predict import load_model, _discretize_single_value

def check_binning():
    print("="*60)
    print("检查分箱边界")
    print("="*60)
    
    # 加载模型和bin_config
    model_path = "new_bayesian/pkl/bn_bayesian_model.pkl"
    model, bin_config = load_model(model_path)
    
    # 检查温度分箱
    if 'temp' in bin_config:
        temp_config = bin_config['temp']
        print(f"\n温度分箱配置:")
        print(f"bins: {temp_config['bins']}")
        print(f"labels: {temp_config['labels']}")
        
        # 测试关键温度值
        test_temps = [68.0, 68.5, 68.8764, 69.0, 69.5, 69.8764, 70.0, 70.5]
        
        print(f"\n温度分箱测试:")
        print(f"{'温度':<10} {'分箱结果':<15} {'说明'}")
        print("-" * 60)
        
        for temp in test_temps:
            binned = _discretize_single_value(temp, temp_config)
            
            # 标记关键值
            marker = ""
            if temp == 68.8764:
                marker = " ← 你的测试1"
            elif temp == 69.8764:
                marker = " ← 你的测试2"
            
            print(f"{temp:<10.4f} {str(binned):<15} {marker}")
        
        # 找出分箱边界
        print(f"\n🔍 关键发现:")
        bins = temp_config['bins']
        labels = temp_config['labels']
        
        for i in range(len(bins) - 1):
            print(f"  [{bins[i]:.2f}, {bins[i+1]:.2f}] → {labels[i]}")
        
        # 检查68.8764和69.8764分别在哪个区间
        print(f"\n📊 你的测试值分析:")
        for temp in [68.8764, 69.8764]:
            binned = _discretize_single_value(temp, temp_config)
            
            # 找出所在区间
            for i in range(len(bins) - 1):
                if bins[i] <= temp <= bins[i+1]:
                    print(f"  温度 {temp:.4f}°C:")
                    print(f"    → 分箱: {binned}")
                    print(f"    → 区间: [{bins[i]:.2f}, {bins[i+1]:.2f}]")
                    print(f"    → 标签: {labels[i]}")
                    break
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_binning()
