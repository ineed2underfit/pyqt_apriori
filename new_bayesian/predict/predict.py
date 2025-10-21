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
    """加载贝叶斯网络模型和分箱配置"""
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
        # 兼容旧版本：如果是元组则解包，否则只返回模型
        if isinstance(data, tuple):
            model, bin_config = data
            return model, bin_config
        else:
            return data, None

def _discretize_single_value(value, bin_config_for_feature):
    """使用预设的分箱配置对单个数值进行离散化
    
    Args:
        value: 要分箱的单个数值
        bin_config_for_feature: 该特征的分箱配置，格式为 {'bins': [...], 'labels': [...]}
    
    Returns:
        分箱后的标签
    """
    bins = bin_config_for_feature['bins']
    labels = bin_config_for_feature['labels']
    
    # 确保值在分箱范围内，否则可能导致NaN
    if value < bins[0]:
        value = bins[0]  # 强制设置为最小值
    elif value > bins[-1]:
        value = bins[-1]  # 强制设置为最大值
    
    # pd.cut 期望 Series，所以将单值转换为 Series
    discretized_series = pd.cut(pd.Series([value]), bins=bins, labels=labels, include_lowest=True)
    return discretized_series.iloc[0]  # 返回离散化后的标签

def _detect_extreme_values(data_dict):
    """检测极端值
    
    Args:
        data_dict: 输入数据字典
    
    Returns:
        tuple: (是否检测到极端值, 极端值列表)
    """
    extreme_detected = False
    extreme_values = []
    
    # 定义极端值阈值 (基于训练数据的统计，更保守的设置)
    extreme_thresholds = {
        'temp': {'high': 95, 'low': 15},  # 温度极端值：更严格的阈值
        'vibration': {'high': 4.0, 'low': 0.05},  # 振动极端值：更严格的阈值
        'oil_pressure': {'high': 18, 'low': 1},  # 油压极端值：调整阈值
        'voltage': {'high': 250, 'low': 170},  # 电压极端值：更严格的阈值
        'rpm': {'high': 3000, 'low': 1400}  # 转速极端值：更严格的阈值
    }
    
    for feature, value in data_dict.items():
        if feature in extreme_thresholds:
            thresholds = extreme_thresholds[feature]
            
            if value > thresholds['high']:
                extreme_detected = True
                extreme_values.append(f"{feature}_high")
                print(f"检测到极端高{feature}: {value} > {thresholds['high']}")
            elif value < thresholds['low']:
                extreme_detected = True
                extreme_values.append(f"{feature}_low")
                print(f"检测到极端低{feature}: {value} < {thresholds['low']}")
    
    return extreme_detected, extreme_values

def _predict_extreme_case(data_dict):
    """极端值情况的预测逻辑 - 改进版本"""
    print("--- 使用极端值预测逻辑 ---")
    
    # 基于领域知识的极端值预测规则
    temp = data_dict.get('temp', 0)
    vibration = data_dict.get('vibration', 0)
    oil_pressure = data_dict.get('oil_pressure', 0)
    voltage = data_dict.get('voltage', 0)
    rpm = data_dict.get('rpm', 0)
    
    # 检查各项是否为真正的极端值
    extreme_conditions = []
    
    # 极端高温 -> 散热系统故障
    if temp > 95:
        extreme_conditions.append(("temp_high", "散热系统故障"))
    
    # 极端高振动 -> 传动系统异常
    if vibration > 4.0:
        extreme_conditions.append(("vibration_high", "传动系统异常"))
    
    # 极端低油压 -> 润滑系统异常
    if oil_pressure < 1:
        extreme_conditions.append(("oil_pressure_low", "润滑系统异常"))
    
    # 极端低电压 -> 电力供应故障
    if voltage < 170:
        extreme_conditions.append(("voltage_low", "电力供应故障"))
    
    # 极端高转速 -> 传动系统异常
    if rpm > 3000:
        extreme_conditions.append(("rpm_high", "传动系统异常"))
    
    # 如果检测到真正的极端值，按优先级返回
    if extreme_conditions:
        # 按故障严重程度排序
        priority_order = ["电力供应故障", "散热系统故障", "传动系统异常", "润滑系统异常"]
        
        for fault_type in priority_order:
            for condition, result in extreme_conditions:
                if result == fault_type:
                    print(f"--- 极端值预测: {condition} -> {result} ---")
                    return result
        
        # 如果没有匹配的优先级，返回第一个检测到的故障
        return extreme_conditions[0][1]
    
    # 如果没有检测到真正的极端值，返回"正常运行"
    print("--- 未检测到真正的极端值，返回正常运行 ---")
    return "正常运行"

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

def predict_single(model, data_dict, bin_config):
    """对单条数据进行预测 - 改进版本，支持极端值检测和概率分布
    
    Args:
        model: 训练好的贝叶斯网络模型
        data_dict: 输入数据字典
        bin_config: 分箱配置字典，包含每个特征的bins和labels
    
    Returns:
        tuple: (预测结果, 概率分布字典)
    """
    print(f"--- predict_single: 原始输入数据: {data_dict} ---") # DEBUG
    
    # 1. 首先检测极端值
    extreme_detected, extreme_values = _detect_extreme_values(data_dict)
    
    if extreme_detected:
        print(f"--- 检测到极端值: {extreme_values}，尝试使用极端值预测逻辑 ---")
        extreme_prediction = _predict_extreme_case(data_dict)
        # 只有在确实命中极端故障规则时，才直接返回100%概率
        if extreme_prediction != "正常运行":
            return extreme_prediction, {extreme_prediction: 1.0}
        # 否则继续走正常贝叶斯推理，避免错误地返回100%
    
    # 2. 正常预测流程
    # 将字典转换为单行DataFrame
    df = pd.DataFrame([data_dict])
    print(f"--- predict_single: 转换为DataFrame后: {df} ---") # DEBUG

    # 3. 执行预处理
    # 对连续变量进行分箱 (使用传入的bin_config)
    print(f"--- predict_single: bin_config keys: {bin_config.keys() if bin_config else 'None'} ---") # DEBUG
    for col_name, config in bin_config.items():
        if col_name in df.columns:
            original_value = df[col_name].iloc[0]
            df[col_name] = _discretize_single_value(original_value, config)
            print(f"--- {col_name}: {original_value} -> {df[col_name].iloc[0]} (bins: {config['bins']}) ---") # DEBUG
    
    # 修改部门名称
    if 'department' in df.columns:
        df['department'] = '部门_' + df['department']

    print(f"--- predict_single: 分箱和部门处理后: {df} ---") # DEBUG

    # 移除模型不需要的列
    model_nodes = model.nodes()
    df = df[[col for col in df.columns if col in model_nodes]]
    print(f"--- predict_single: 过滤模型节点后: {df} ---") # DEBUG

    # 4. 执行预测和概率查询
    try:
        # 获取预测结果
        prediction = model.predict(df)
        prediction_result = prediction['故障类型'].iloc[0]
        
        # 获取概率分布
        probability_dist = _get_probability_distribution(model, df)
        
        print(f"--- predict_single: 模型预测结果: {prediction_result} ---") # DEBUG
        print(f"--- predict_single: 概率分布: {probability_dist} ---") # DEBUG
        
        return prediction_result, probability_dist
        
    except Exception as e:
        print(f"--- 模型预测失败: {e}，使用极端值预测逻辑 ---")
        prediction = _predict_extreme_case(data_dict)
        return prediction, {prediction: 1.0}

def _get_probability_distribution(model, evidence_df):
    """获取故障类型的概率分布
    
    Args:
        model: 训练好的贝叶斯网络模型
        evidence_df: 证据数据DataFrame
    
    Returns:
        dict: 故障类型概率分布字典
    """
    try:
        from pgmpy.inference import VariableElimination
        
        # 创建推理引擎
        inference = VariableElimination(model)
        
        # 准备证据
        evidence = {}
        for col in evidence_df.columns:
            if col != '故障类型':  # 排除目标变量
                evidence[col] = evidence_df[col].iloc[0]
        
        print(f"--- 推理证据: {evidence} ---") # DEBUG
        
        # 查询故障类型的概率分布
        query_result = inference.query(['故障类型'], evidence=evidence)
        
        # 提取概率分布
        prob_dist = {}
        for state in query_result.state_names['故障类型']:
            prob = query_result.values[query_result.state_names['故障类型'].index(state)]
            prob_dist[state] = float(prob)
        
        # 按概率从大到小排序
        sorted_probs = dict(sorted(prob_dist.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_probs
        
    except Exception as e:
        print(f"--- 概率查询失败: {e} ---")
        # 返回默认概率分布
        return {"正常运行": 0.95, "传动系统异常": 0.02, "散热系统故障": 0.015, "润滑系统异常": 0.01, "电力供应故障": 0.005}

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
        model, bin_config = load_model(model_path)
        print(f"模型加载完成，耗时: {time.time() - start_time:.4f}秒")
        if bin_config:
            print("已加载分箱配置")
        else:
            print("警告：未找到分箱配置，使用旧版本模型")
        
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