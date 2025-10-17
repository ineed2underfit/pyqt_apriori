import pandas as pd
import numpy as np

def load_rules(file_path):
    """加载规则文件"""
    return pd.read_csv(file_path)

def filter_optimal_rules(rules_df, min_support=0.005, min_confidence=0.5, min_lift=10):
    """
    根据设定的阈值筛选最优规则
    
    参数:
    rules_df: 规则数据框
    min_support: 最小支持度阈值
    min_confidence: 最小置信度阈值
    min_lift: 最小提升度阈值
    
    返回:
    筛选后的规则数据框
    """
    # 筛选满足阈值的规则
    optimal_rules = rules_df[
        (rules_df['支持度'] >= min_support) &
        (rules_df['置信度'] >= min_confidence) &
        (rules_df['提升度'] >= min_lift)
    ]
    
    return optimal_rules

def get_best_rule_per_fault(rules_df, by='提升度'):
    """
    为每个故障类型获取一条最优规则
    
    参数:
    rules_df: 规则数据框
    by: 排序指标，可选 '支持度', '置信度', '提升度'
    
    返回:
    每个故障类型的最优规则
    """
    # 提取故障类型
    rules_df['故障类型'] = rules_df['规则'].str.split('→').str[-1].str.strip()
    
    # 按故障类型分组，每组取提升度最高的规则
    best_rules = rules_df.groupby('故障类型').apply(
        lambda x: x.nlargest(1, by)
    ).reset_index(drop=True)
    
    # 删除临时添加的故障类型列
    best_rules = best_rules.drop('故障类型', axis=1)
    
    return best_rules

def main():
    # 加载规则
    rules_df = load_rules('dataset/rules.csv')
    
    # 筛选最优规则
    optimal_rules = filter_optimal_rules(rules_df)
    
    # 获取每个故障类型的最优规则
    best_rules = get_best_rule_per_fault(optimal_rules, by='提升度')
    
    # 打印结果
    print("每个故障类型的最优规则：")
    print(best_rules[['规则', '支持度', '置信度', '提升度']].to_string(index=False))
    
    # 保存结果到CSV文件
    best_rules.to_csv('dataset/optimal_rules.csv', index=False)
    print("\n最优规则已保存到 dataset/optimal_rules.csv")

if __name__ == "__main__":
    main() 