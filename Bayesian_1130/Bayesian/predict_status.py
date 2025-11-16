# Bayesian/predict_status.py

import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime

# --- 配置路径 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "Bayesian", "models", "final_bn_model.pkl")  # 请替换为您实际的pkl文件名
DATA_PATH = os.path.join(PROJECT_ROOT, "datas", "device_PA40_data.csv")
BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
RULES_PATH = os.path.join(PROJECT_ROOT, "result", "bayesian_results", "network_rules_with_mapping.json")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result", "bayesian_results")

os.makedirs(RESULT_DIR, exist_ok=True)


def load_binning_config(path):
    """读取分箱配置文件，返回完整配置字典"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_network_rules(path):
    """读取网络规则文件，返回规则列表"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_key_parameters_for_status(predicted_status, network_rules):
    """
    根据预测状态，从规则中提取需要关注的参数
    
    Args:
        predicted_status: 预测的状态
        network_rules: 网络规则列表
    
    Returns:
        list: 需要关注的参数列表（去重后）
    """
    key_parameters = set()
    
    # 遍历所有规则，找到consequent匹配的规则
    for rule in network_rules:
        if rule.get("consequent") == predicted_status:
            # 提取该规则的所有前置条件的original_column
            for antecedent in rule.get("antecedents_mapped", []):
                original_col = antecedent.get("original_column")
                if original_col:
                    key_parameters.add(original_col)
    
    return sorted(list(key_parameters))


def discretize_raw_data_for_prediction(raw_data, binning_config):
    """
    对原始数据进行离散化，使其格式与训练时一致
    这个函数的逻辑必须与 build_model.py 中的 discretize_raw_data 完全相同
    """
    df_discrete = pd.DataFrame(index=raw_data.index)

    # 1. 处理数值特征：离散化为 one-hot 编码
    binning_info = binning_config["data_info"]["binning_info"]
    numerical_cols = binning_config["metadata"]["dataset_config"]["numerical_cols"]

    for col in numerical_cols:
        if col in raw_data.columns and col in binning_info:
            try:
                # 确保列是数值类型
                if raw_data[col].dtype == 'object':
                    numeric_series = pd.to_numeric(raw_data[col], errors='coerce')
                else:
                    numeric_series = raw_data[col]

                if numeric_series.isna().all():
                    print(f"⚠️ 警告: 列 '{col}' 转换后全为 NaN，跳过离散化")
                    continue

                info = binning_info[col]
                # 离散化为标签
                discretized = pd.cut(
                    numeric_series,
                    bins=info["bins"],
                    labels=info["labels"],
                    include_lowest=True
                )

                # 转换为 one-hot 编码
                one_hot = pd.get_dummies(discretized, prefix='', prefix_sep='')
                df_discrete = pd.concat([df_discrete, one_hot], axis=1)

            except Exception as e:
                print(f"⚠️ 警告: 离散化列 '{col}' 时出错: {e}")
                continue

    # 2. 处理类别特征：one-hot编码
    categorical_info = binning_config["data_info"]["categorical_info"]
    categorical_cols = binning_config["metadata"]["dataset_config"]["categorical_cols"]

    for col in categorical_cols:
        if col in raw_data.columns and col in categorical_info:
            try:
                info = categorical_info[col]
                unique_values = info["unique_values"]
                prefix = info.get("prefix", col)

                # 为每个唯一值创建二值列
                for value in unique_values:
                    new_col_name = f"{prefix}_{value}"
                    df_discrete[new_col_name] = (raw_data[col] == value).astype(int)
            except Exception as e:
                print(f"⚠️ 警告: one-hot编码列 '{col}' 时出错: {e}")
                continue

    # 3. 保留目标变量
    dataset_config = binning_config["metadata"]["dataset_config"]
    target_col = dataset_config["target_col"]
    if target_col in raw_data.columns:
        df_discrete[target_col] = raw_data[target_col]

    return df_discrete


def predict_with_model(model, test_data, target_col="status", normal_value=None):
    """
    使用模型进行预测
    
    Args:
        model: 贝叶斯网络模型
        test_data: 测试数据（已离散化）
        target_col: 目标变量列名
        normal_value: 正常状态的值，如果为None则从配置文件中读取
    """
    from pgmpy.inference import VariableElimination

    # 如果没有提供normal_value，尝试从配置文件中读取
    if normal_value is None:
        try:
            binning_config = load_binning_config(BINNING_CONFIG_PATH)
            normal_value = binning_config.get("metadata", {}).get("dataset_config", {}).get("normal_value")
            if normal_value is None:
                normal_value = binning_config.get("data_info", {}).get("target_info", {}).get("normal_value")
        except Exception as e:
            print(f"⚠️ 警告: 无法从配置文件读取正常值: {e}，使用默认值'正常运行'")
            normal_value = "正常运行"
    
    if normal_value is None:
        normal_value = "正常运行"  # 最后的默认值

    # 初始化推理器
    infer = VariableElimination(model)

    predictions = []
    prediction_probs = []

    print(f"🔮 开始预测，样本数: {len(test_data)}")

    # 为每一行数据进行预测
    for idx, row in test_data.iterrows():
        # 准备证据（除了目标变量）
        evidence = {}
        for col in test_data.columns:
            if col != target_col and not pd.isna(row[col]) and row[col] is not None:
                # 检查该列是否在模型中存在
                if col in model.nodes():
                    # 对于one-hot编码的二元节点，只有值为1的才应作为证据
                    val = row[col]
                    if isinstance(val, (int, float)) and val == 1:
                        evidence[col] = int(val)

        if not evidence:
            # print(f"   警告: 第 {idx} 行没有可用的证据变量")
            # 如果预测失败，返回最常见的状态或默认状态
            predictions.append(normal_value)  # 使用从配置读取的正常值
            prediction_probs.append({})
            continue

        try:
            # 查询目标变量的概率分布
            result = infer.query(variables=[target_col], evidence=evidence)

            # 获取最可能的状态
            most_likely_state_idx = np.argmax(result.values)
            most_likely_state = result.state_names[target_col][most_likely_state_idx]
            predictions.append(most_likely_state)

            # 获取所有状态的概率
            state_probs = {state: prob for state, prob in zip(result.state_names[target_col], result.values)}
            prediction_probs.append(state_probs)

            if idx % 100 == 0:  # 每100个样本打印一次进度
                print(f"   处理进度: {idx + 1}/{len(test_data)}")

        except Exception as e:
            print(f"⚠️ 预测第 {idx} 行时出错: {e}")
            print(f"   证据: {evidence}")
            # 如果预测失败，返回最常见的状态或默认状态
            predictions.append(normal_value)  # 使用从配置读取的正常值
            prediction_probs.append({})  # 空概率字典

    print(f"✅ 预测完成，成功预测 {len(predictions)} 个样本")
    return predictions, prediction_probs


def save_prediction_report(y_true, y_pred, prediction_probs, model_path, report_save_path):
    """
    生成并保存预测报告
    """
    # 计算准确度
    accuracy = accuracy_score(y_true, y_pred)

    # 获取所有唯一的真实和预测状态
    all_states = sorted(list(set(y_true + y_pred)))

    # 生成分类报告
    class_report = classification_report(y_true, y_pred, labels=all_states, output_dict=True, zero_division=0.0)

    # 生成报告文本
    report_text = f"""贝叶斯网络预测报告
===========================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
模型路径: {model_path}
测试样本数: {len(y_true)}
使用状态: {all_states}

总体准确度: {accuracy:.4f}

详细分类报告:
"""
    report_text += classification_report(y_true, y_pred, labels=all_states, zero_division=0.0)

    # 计算每个类别的支持度、精确率、召回率、F1分数
    report_text += f"""

类别详细统计:
"""
    for state in all_states:
        if state in class_report:
            report_text += f"  {state}:\n"
            report_text += f"    支持样本数 (Support): {class_report[state].get('support', 0)}\n"
            report_text += f"    精确率 (Precision): {class_report[state].get('precision', 0):.4f}\n"
            report_text += f"    召回率 (Recall): {class_report[state].get('recall', 0):.4f}\n"
            report_text += f"    F1分数 (F1-Score): {class_report[state].get('f1-score', 0):.4f}\n"
            report_text += "\n"

    with open(report_save_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"✅ 预测报告已保存至: {report_save_path}")


def save_confusion_matrix(y_true, y_pred, target_states, cm_save_path):
    """
    生成并保存混淆矩阵
    """
    # 确保所有类别都在混淆矩阵中，即使某些类别没有被预测到或真实出现
    cm = confusion_matrix(y_true, y_pred, labels=target_states)

    plt.figure(figsize=(10, 8))
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=target_states, yticklabels=target_states,
                cbar_kws={'label': '样本数量'})
    plt.title('混淆矩阵')
    plt.xlabel('预测状态')
    plt.ylabel('真实状态')
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(cm_save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 混淆矩阵已保存至: {cm_save_path}")


def save_prediction_results(y_true, y_pred, prediction_probs, results_save_path):
    """
    保存预测结果
    """
    results_df = pd.DataFrame({
        '真实状态': y_true,
        '预测状态': y_pred
    })

    # 如果有概率信息，也保存
    if prediction_probs and len(prediction_probs) > 0 and prediction_probs[0]:
        # 提取最高概率状态及其概率
        most_likely_states = []
        max_probs = []
        for prob_dict in prediction_probs:
            if prob_dict:
                most_likely_state = max(prob_dict, key=prob_dict.get)
                max_prob = prob_dict[most_likely_state]
                most_likely_states.append(most_likely_state)
                max_probs.append(max_prob)
            else:
                most_likely_states.append('N/A')
                max_probs.append(0.0)

        results_df['最高概率状态'] = most_likely_states
        results_df['最高概率'] = max_probs

    results_df.to_csv(results_save_path, index=False, encoding='utf-8')
    print(f"📋 预测结果已保存至: {results_save_path}")


# --- 新增：单条数据预测主函数 ---
def main_one():
    """
    主函数：单条数据预测
    引导用户输入参数，调用离散化函数，使用模型进行预测，并输出概率和结论。
    """
    print("🔍 开始单条设备状态预测...")

    # 1. 加载模型
    print(f"📦 加载模型: {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"✅ 模型加载成功，包含 {len(model.nodes())} 个节点")

    # 2. 加载配置
    print("⚙️ 加载配置...")
    binning_config = load_binning_config(BINNING_CONFIG_PATH)

    # 3. 从配置获取列名
    dataset_config = binning_config["metadata"]["dataset_config"]
    id_cols = dataset_config["id_cols"]
    categorical_cols = dataset_config["categorical_cols"]
    target_col = dataset_config["target_col"]
    numerical_cols = dataset_config["numerical_cols"]

    # 4. 引导用户逐个输入参数
    print("\n--- 请输入设备当前的实时参数 ---")
    user_inputs = {}

    # 4a. 输入数值特征
    binning_info = binning_config["data_info"]["binning_info"]
    for col in numerical_cols:
        while True:
            try:
                # 从配置中获取范围以提供提示
                min_val = binning_info[col]["original_stats"]["min"]
                max_val = binning_info[col]["original_stats"]["max"]
                print(f"  {col} (范围: {min_val:.4f} ~ {max_val:.4f}): ", end="")
                user_val = float(input())
                user_inputs[col] = user_val
                break
            except ValueError:
                print("    ❌ 请输入一个有效的数字。")
            except KeyError:
                # 如果配置中没有范围信息，也允许输入
                print(f"  {col}: ", end="")
                user_val = float(input())
                user_inputs[col] = user_val
                break

    # 4b. 输入类别特征
    categorical_info = binning_config["data_info"]["categorical_info"]
    for col in categorical_cols:
        while True:
            try:
                possible_values = categorical_info[col]["unique_values"]
                print(f"  {col} (可选值: {possible_values}): ", end="")
                user_val = input().strip()
                if user_val in possible_values:
                    user_inputs[col] = user_val
                    break
                else:
                    print(f"    ❌ 请输入一个有效的值，例如: {possible_values[0]}")
            except (KeyError, IndexError):
                # 如果配置中没有unique_values，也允许输入（但风险较高）
                print(f"  {col}: ", end="")
                user_val = input().strip()
                user_inputs[col] = user_val
                break

    # 5. 将用户输入转换为单行DataFrame
    # 注意：目标列需要添加一个占位符，因为离散化函数会处理所有列
    user_inputs[target_col] = "占位符"
    single_row_df = pd.DataFrame([user_inputs])

    # 6. 调用离散化函数
    print("\n🔄 正在处理输入数据...")
    discrete_input = discretize_raw_data_for_prediction(single_row_df, binning_config)

    # 7. 调用预测函数
    print("🔮 正在进行状态预测...")
    # 从配置中获取正常值
    normal_value = binning_config.get("metadata", {}).get("dataset_config", {}).get("normal_value") or \
                   binning_config.get("data_info", {}).get("target_info", {}).get("normal_value")
    predictions, prediction_probs = predict_with_model(model, discrete_input, target_col=target_col, normal_value=normal_value)

    # 8. 加载网络规则
    print("📋 加载网络规则...")
    try:
        network_rules = load_network_rules(RULES_PATH)
        print(f"✅ 成功加载 {len(network_rules)} 条规则")
    except Exception as e:
        print(f"⚠️ 警告: 加载规则文件失败: {e}")
        network_rules = []

    # 9. 输出结果
    predicted_status = predictions[0]  # 只有一条数据
    all_status_probs = prediction_probs[0]  # 只有一条数据的概率字典
    max_prob = all_status_probs.get(predicted_status, 0.0)

    # 根据预测状态提取需要关注的参数
    key_parameters = get_key_parameters_for_status(predicted_status, network_rules)
    key_params_str = "/".join(key_parameters) if key_parameters else "无"

    print("\n" + "=" * 50)
    print("📊 预测结果")
    print("=" * 50)
    print(f"最可能的状态是: {predicted_status}，概率为{max_prob:.4f} (最高概率)")
    print(f"需要特别关注的参数为: {key_params_str}")
    print("\n各状态的预测概率:")

    # 对概率进行降序排序
    sorted_probs = sorted(all_status_probs.items(), key=lambda x: x[1], reverse=True)
    for status, prob in sorted_probs:
        if status == predicted_status:
            print(f"  🎯 {status}: {prob:.4f} (最高概率)")
        else:
            print(f"     {status}: {prob:.4f}")

    print("=" * 50)

    # 10. 生成并保存报告
    report_text = f"""设备状态预测报告
===========================
最可能的状态是: {predicted_status}，概率为{max_prob:.4f} (最高概率)
需要特别关注的参数为: {key_params_str}

各状态的预测概率:
"""
    for status, prob in sorted_probs:
        if status == predicted_status:
            report_text += f"  {status}: {prob:.4f} (最高概率)\n"
        else:
            report_text += f"  {status}: {prob:.4f}\n"

    # 如果有需要关注的参数，添加详细信息
    if key_parameters:
        report_text += f"\n需要关注的参数说明:\n"
        for param in key_parameters:
            report_text += f"  - {param}\n"

    # 保存报告
    report_filename = "single_prediction_report.txt"
    report_path = os.path.join(RESULT_DIR, report_filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"📄 预测报告已保存至: {report_path}")
    print("✅ 预测完成！")


def main():
    """
    主函数（批量预测，保留但不使用）
    """
    print("🔍 开始贝叶斯网络预测...")

    # 1. 加载模型
    print(f"📦 加载模型: {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"✅ 模型加载成功，包含 {len(model.nodes())} 个节点")

    # 2. 加载配置
    print("⚙️ 加载配置...")
    binning_config = load_binning_config(BINNING_CONFIG_PATH)

    # 3. 加载测试数据
    print(f"📊 加载测试数据: {DATA_PATH}")
    raw_test_data = pd.read_csv(DATA_PATH, encoding='utf-8')

    # 从配置获取列名
    dataset_config = binning_config["metadata"]["dataset_config"]
    id_cols = dataset_config["id_cols"]
    categorical_cols = dataset_config["categorical_cols"]
    target_col = dataset_config["target_col"]
    numerical_cols = dataset_config["numerical_cols"]

    all_cols = id_cols + categorical_cols + [target_col] + numerical_cols

    # 验证列名是否匹配
    if list(raw_test_data.columns) != all_cols:
        print(f"⚠️ 警告: CSV 列名与配置不完全匹配")
        print(f"   CSV 列: {list(raw_test_data.columns)}")
        print(f"   配置列: {all_cols}")
        # 如果顺序不一致，需要重新排序
        if set(raw_test_data.columns) == set(all_cols):
            print("   ✅ 列名匹配，仅顺序不同，重新排序...")
            raw_test_data = raw_test_data[all_cols]
        else:
            print("   ❌ 列名不匹配，请检查数据文件和配置")
            # 尝试使用配置顺序（如果 CSV 没有表头）
            raw_test_data = pd.read_csv(DATA_PATH, header=None, names=all_cols, encoding='utf-8')

    print(f"   数据形状: {raw_test_data.shape}")

    # 4. 对测试数据进行离散化（与训练时一致！）
    print("🔄 对测试数据进行离散化（与训练时一致）...")
    discrete_test_data = discretize_raw_data_for_prediction(raw_test_data, binning_config)

    # 5. 获取真实标签
    y_true = discrete_test_data[target_col].tolist()
    print(f"   真实标签数量: {len(y_true)}")
    print(f"   真实标签类别: {sorted(list(set(y_true)))}")

    # 6. 进行预测
    print("🔮 执行预测...")
    # 从配置中获取正常值
    normal_value = binning_config.get("metadata", {}).get("dataset_config", {}).get("normal_value") or \
                   binning_config.get("data_info", {}).get("target_info", {}).get("normal_value")
    y_pred, prediction_probs = predict_with_model(model, discrete_test_data, target_col, normal_value=normal_value)

    # 7. 获取目标状态列表
    target_states = sorted(list(set(y_true + y_pred)))
    print(f"   涉及状态类别: {target_states}")

    # 8. 生成文件名
    report_filename = f"prediction_report.txt"
    cm_filename = f"confusion_matrix.png"
    results_filename = f"prediction_results.csv"

    report_path = os.path.join(RESULT_DIR, report_filename)
    cm_path = os.path.join(RESULT_DIR, cm_filename)
    results_path = os.path.join(RESULT_DIR, results_filename)

    # 9. 生成并保存报告
    save_prediction_report(y_true, y_pred, prediction_probs, MODEL_PATH, report_path)

    # 10. 生成并保存混淆矩阵
    save_confusion_matrix(y_true, y_pred, target_states, cm_path)

    # 11. 生成并保存预测结果
    save_prediction_results(y_true, y_pred, prediction_probs, results_path)

    # 12. 打印摘要
    accuracy = accuracy_score(y_true, y_pred)
    print("\n" + "=" * 60)
    print("预测完成！摘要信息:")
    print(f"  模型路径: {MODEL_PATH}")
    print(f"  总体准确度: {accuracy:.4f}")
    print(f"  测试样本数: {len(y_true)}")
    print(f"  涉及状态数: {len(target_states)}")
    print(f"  预测报告: {report_path}")
    print(f"  混淆矩阵: {cm_path}")
    print(f"  预测结果: {results_path}")
    print("=" * 60)


if __name__ == "__main__":
    #批量预测
    # main()
    # 直接调用单条预测函数
    main_one()