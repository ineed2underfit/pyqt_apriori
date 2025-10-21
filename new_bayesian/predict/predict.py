import os
import pandas as pd
import numpy as np
import pickle
import time
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from tqdm import tqdm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def std_based_binning(data, num_bins=5, var_name=None):
    """基于标准差的分箱方法，与BN_MLE.py完全相同"""
    mean = np.mean(data)
    std = np.std(data)
    
    # 确保边界值单调递增
    bins = [data.min()]  # 初始化边界值列表
    
    # 根据标准差生成中间边界值
    if num_bins == 3:
        middle_bins = [mean - std, mean + std]
    elif num_bins == 5:
        middle_bins = [mean - 2*std, mean - std, mean + std, mean + 2*std]
    else:
        # 对于其他分箱数量，采用均匀分布标准差的方式
        step = 4 / (num_bins - 1)  # 范围从-2std到+2std
        middle_bins = [mean + (i - (num_bins - 1) / 2) * step * std for i in range(1, num_bins)]
    
    # 添加中间边界值，确保单调递增
    for b in middle_bins:
        if b > bins[-1]:
            bins.append(b)
    
    # 添加最大值
    if data.max() > bins[-1]:
        bins.append(data.max())
    
    # 确保边界值不重复
    bins = sorted(list(set(bins)))
    
    # 生成标签
    if var_name in ['温度', '振动', '油压', '电力', '转速']:
        # 根据变量名和边界数量生成标签
        num_labels = len(bins) - 1
        
        if var_name == '温度':
            prefix = '温'
        elif var_name == '振动':
            prefix = '振动'
        elif var_name == '油压':
            prefix = '油压'
        elif var_name == '电力':
            prefix = '电力'
        elif var_name == '转速':
            prefix = '转速'
        
        # 根据实际分箱数量生成标签
        if num_labels == 5:
            labels = [f'极低{prefix}', f'低{prefix}', f'中{prefix}', f'高{prefix}', f'极高{prefix}']
        elif num_labels == 4:
            labels = [f'低{prefix}', f'中低{prefix}', f'中高{prefix}', f'高{prefix}']
        elif num_labels == 3:
            labels = [f'低{prefix}', f'中{prefix}', f'高{prefix}']
        elif num_labels == 2:
            labels = [f'低{prefix}', f'高{prefix}']
        else:
            labels = [f'{prefix}等级{i+1}' for i in range(num_labels)]
    else:
        labels = [f'等级{i+1}' for i in range(len(bins)-1)]
    
    return pd.cut(data, bins=bins, labels=labels, include_lowest=True)

def preprocess_data(data_path):
    """预处理数据，与BN_MLE.py使用相同的逻辑"""
    # 读取数据
    print("读取数据...")
    df = pd.read_csv(data_path)
    
    # 重命名列以匹配规则中的变量名
    print("重命名列...")
    df = df.rename(columns={
        'temp': '温度',
        'vibration': '振动',
        'oil_pressure': '油压',
        'voltage': '电力',
        'rpm': '转速',
        'department': '部门'
    })
    
    # 对连续变量进行分箱
    print("对连续变量进行分箱...")
    for col in ['温度', '振动', '油压', '电力', '转速']:
        if col in df.columns:
            df[col] = std_based_binning(df[col], num_bins=5, var_name=col)
    
    # 修改部门名称
    df['部门'] = '部门_' + df['部门']
    
    # 删除不需要的列
    if 'timestamp' in df.columns:
        df = df.drop('timestamp', axis=1)
    if 'device_id' in df.columns:
        df = df.drop('device_id', axis=1)
    
    return df

def load_model(model_path):
    """加载贝叶斯网络模型"""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def plot_confusion_matrix(cm, classes, output_path):
    """绘制混淆矩阵"""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title('混淆矩阵')
    plt.ylabel('真实标签')
    plt.xlabel('预测标签')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def predict_with_naive_bayes(data, output_dir):
    """使用朴素贝叶斯方法进行预测"""
    # 可能的故障类型
    unique_fault_types = data['故障类型'].unique()
    print(f"可能的故障类型: {unique_fault_types}")
    
    # 预计算条件概率表以加速预测
    print("预计算条件概率表...")
    cond_probs = {}
    priors = {}
    
    # 计算先验概率
    for fault_type in unique_fault_types:
        priors[fault_type] = (data['故障类型'] == fault_type).sum() / len(data)
    
    # 计算条件概率
    for col in data.columns:
        if col != '故障类型':
            for fault_type in unique_fault_types:
                for state in data[col].unique():
                    # 计算条件概率 P(var=state|故障类型=fault_type)
                    matching_data = data[
                        (data[col] == state) & 
                        (data['故障类型'] == fault_type)
                    ]
                    total_fault = (data['故障类型'] == fault_type).sum()
                    
                    # 拉普拉斯平滑
                    prob = (len(matching_data) + 1) / (total_fault + len(data[col].unique()))
                    cond_probs[(col, state, fault_type)] = prob
    
    # 对每行数据进行预测，使用进度条显示
    print("开始预测...")
    predictions = []
    
    # 使用tqdm显示进度条
    for _, row in tqdm(list(data.iterrows()), desc="预测进度"):
        # 提取当前行的证据（不包括故障类型）
        evidence = row.drop('故障类型').to_dict()
        
        # 为每种故障类型计算概率得分
        scores = {}
        for fault_type in unique_fault_types:
            # 从先验概率开始
            score = priors[fault_type]
            
            # 使用预计算的条件概率
            for var, state in evidence.items():
                score *= cond_probs.get((var, state, fault_type), 0.01)  # 默认值防止未知状态
            
            scores[fault_type] = score
        
        # 选择得分最高的故障类型
        if scores:
            prediction = max(scores.items(), key=lambda x: x[1])[0]
        else:
            # 如果没有得分，使用训练数据中最常见的故障类型
            prediction = data['故障类型'].mode()[0]
        
        predictions.append(prediction)
    
    # 将预测结果转换为DataFrame
    predictions_df = pd.DataFrame({'故障类型': predictions})
    
    # 计算准确率
    accuracy = accuracy_score(data['故障类型'], predictions_df['故障类型'])
    
    # 计算混淆矩阵
    classes = sorted(data['故障类型'].unique())
    cm = confusion_matrix(data['故障类型'], predictions_df['故障类型'], labels=classes)
    
    # 生成分类报告
    report = classification_report(data['故障类型'], predictions_df['故障类型'])
    
    # 打印评估结果
    print(f"预测准确率: {accuracy:.4f}")
    print("\n混淆矩阵:")
    print(cm)
    print("\n分类报告:")
    print(report)
    
    # 绘制混淆矩阵
    plot_confusion_matrix(cm, classes, os.path.join(output_dir, 'confusion_matrix.png'))
    
    # 保存预测结果
    results_df = pd.DataFrame({
        '真实标签': data['故障类型'].values,
        '预测标签': predictions_df['故障类型'].values
    })
    results_df.to_csv(os.path.join(output_dir, 'prediction_results.csv'), index=False)
    
    # 保存评估报告
    with open(os.path.join(output_dir, 'evaluation_report.txt'), 'w', encoding='utf-8') as f:
        f.write(f"预测准确率: {accuracy:.4f}\n\n")
        f.write("混淆矩阵:\n")
        f.write(str(cm))
        f.write("\n\n类别标签:\n")
        for i, label in enumerate(classes):
            f.write(f"{i}: {label}\n")
        f.write("\n\n分类报告:\n")
        f.write(report)
    
    return predictions_df, accuracy, cm, report

def predict_single(model, data_dict):
    """对单条数据进行预测"""
    print(f"--- predict_single: 原始输入数据: {data_dict} ---") # DEBUG
    # 1. 将字典转换为单行DataFrame
    df = pd.DataFrame([data_dict])
    print(f"--- predict_single: 转换为DataFrame后: {df} ---") # DEBUG

    # 2. 执行与批量预测相同的预处理 (保持原始英文列名)
    # 对连续变量进行分箱
    for col in ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']:
        if col in df.columns:
            df[col] = std_based_binning(df[col], num_bins=5, var_name=col) # var_name 传入原始英文名
    
    # 修改部门名称
    if 'department' in df.columns:
        df['department'] = '部门_' + df['department']

    print(f"--- predict_single: 分箱和部门处理后: {df} ---") # DEBUG

    # 移除模型不需要的列 (model_nodes 应该包含原始英文名)
    model_nodes = model.nodes()
    df = df[[col for col in df.columns if col in model_nodes]]
    print(f"--- predict_single: 过滤模型节点后: {df} ---") # DEBUG

    # 3. 执行预测
    prediction = model.predict(df)
    print(f"--- predict_single: 模型预测结果: {prediction} ---") # DEBUG
    
    # 4. 返回预测结果
    return prediction['故障类型'].iloc[0]

def main(model_path, test_data_path):
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(root_dir, 'predict', 'results')

    # 检查模型文件是否存在且非空
    if not os.path.exists(model_path):
        print(f"错误：模型文件不存在: {model_path}")
        print("请先运行模型训练程序生成模型文件。")
        return
    if os.path.getsize(model_path) == 0:
        print(f"错误：模型文件为空: {model_path}")
        print("请重新运行模型训练程序。")
        return
        
    # 检查测试数据文件是否存在
    if not os.path.exists(test_data_path):
        print(f"错误：测试数据文件不存在: {test_data_path}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 加载模型
        print(f"正在加载模型: {model_path}")
        model = load_model(model_path)
        print(f"模型加载完成，耗时: {time.time() - start_time:.4f}秒")
        
        # 预处理数据
        print(f"正在加载并预处理测试数据: {test_data_path}")
        processed_data = preprocess_data(test_data_path)
        preprocess_time = time.time() - start_time
        print(f"数据预处理完成，耗时: {preprocess_time:.4f}秒")
        
        # 显示数据和模型的基本信息
        print(f"测试数据行数: {len(processed_data)}")
        print(f"测试数据列: {processed_data.columns.tolist()}")
        print(f"测试数据故障类型分布:\n{processed_data['故障类型'].value_counts()}")
        print("\n模型节点:")
        for node in model.nodes():
            print(f"- {node}")
        
        # 进行预测
        print("\n开始预测过程...")
        predict_start_time = time.time()
        predictions, accuracy, cm, report = predict_with_naive_bayes(processed_data, output_dir)
        predict_time = time.time() - predict_start_time
        print(f"预测完成，耗时: {predict_time:.4f}秒")
        
        print(f"\n总耗时: {time.time() - start_time:.4f}秒")
        print(f"结果已保存到: {output_dir}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print("请确保模型训练已完成，并且模型文件正确生成。")
        return

if __name__ == "__main__":
    # 定义默认路径用于独立测试
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(root_dir, 'pkl', 'bn_bayesian_model.pkl')
    test_data_path = os.path.join(root_dir, 'dataset', 'testdata_info', 'training_dataset.csv')
    main(model_path, test_data_path)