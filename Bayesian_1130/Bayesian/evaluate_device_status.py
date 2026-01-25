# Bayesian/evaluate_device_status.py

import os
import sys
import pickle
import pandas as pd
import numpy as np
import json
import importlib.util
from pgmpy.inference import VariableElimination
import re

# --- 配置路径 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "Bayesian", "models", "final_bn_model.pkl") # 请替换为您实际的pkl文件名
BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
# 假设规则文件路径
RULES_CSV_PATH = os.path.join(PROJECT_ROOT, "result", "apriori_results", "关联规则分析结果.csv")

_UTILS_MODULE = None


def _load_utils_module():
    global _UTILS_MODULE
    if _UTILS_MODULE is None:
        utils_path = os.path.join(PROJECT_ROOT, "Bayesian", "utils.py")
        spec = importlib.util.spec_from_file_location("bayesian_utils", utils_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 utils 模块: {utils_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _UTILS_MODULE = module
    return _UTILS_MODULE

def load_model_and_config():
    """加载模型和配置文件"""
    print(f"📦 加载模型: {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"✅ 模型加载成功，包含 {len(model.nodes())} 个节点")

    print(f"⚙️ 加载配置: {BINNING_CONFIG_PATH}")
    with open(BINNING_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("✅ 配置加载成功")

    # 尝试加载规则（用于反推）
    rules_df = None
    try:
        utils_module = _load_utils_module()
        rules_df = utils_module.load_association_rules(RULES_CSV_PATH)
        print(f"✅ 关联规则加载成功，有效规则数: {len(rules_df)}")
    except FileNotFoundError:
        print(f"⚠️ 警告: 未找到关联规则文件 {RULES_CSV_PATH}，将无法进行基于规则的反推。")
        print("   将尝试基于模型结构进行灵敏度分析。")
    except Exception as e:
        print(f"⚠️ 警告: 加载关联规则时出错: {e}")
        print("   将尝试基于模型结构进行灵敏度分析。")

    return model, config, rules_df

def get_user_input(config):
    """根据配置文件引导用户输入原始特征值"""
    user_inputs = {}

    # --- 从 metadata 获取列名 (这是关键，确保使用模型训练时的列名) ---
    dataset_config = config["metadata"]["dataset_config"]
    id_cols = dataset_config["id_cols"]
    categorical_cols = dataset_config["categorical_cols"]
    target_col = dataset_config["target_col"]
    numerical_cols = dataset_config["numerical_cols"]
    # --- 从 metadata 获取列名 ---

    print("\n--- 请输入设备当前的实时参数 ---")

    # 输入数值特征
    for col in numerical_cols:
        current_col = col
        while True:
            try:
                # --- 尝试从 binning_info 读取 original_stats ---
                min_val = config["data_info"]["binning_info"][current_col]["original_stats"]["min"]
                max_val = config["data_info"]["binning_info"][current_col]["original_stats"]["max"]
                print(f"  {current_col} (范围: {min_val:.4f} ~ {max_val:.4f}, 当前输入): ", end="")
                val = float(input())
                # 验证输入值是否在原始数据范围内（可选）
                if not (min_val <= val <= max_val):
                    print(f"    ⚠️ 警告: 输入值 {val} 超出训练数据范围 [{min_val:.4f}, {max_val:.4f}]")
                user_inputs[current_col] = val
                break
            except KeyError:
                print(f"    ❌ 配置文件中找不到 'binning_info.{current_col}.original_stats' 的路径。")
                print(f"  {current_col} (未知范围, 当前输入): ", end="")
                val = float(input())
                user_inputs[current_col] = val
                break
            except ValueError:
                print("    ❌ 输入无效，请输入一个数字。")

    # 输入类别特征
    for col in categorical_cols:
        current_col = col
        # --- 尝试从 categorical_info 读取 unique_values ---
        try:
            possible_values = config["data_info"]["categorical_info"][current_col]["unique_values"]
        except KeyError:
            print(f"⚠️ 警告: 无法从配置中获取 '{current_col}' 的可能值列表。")
            # 使用默认值或从其他地方推断
            possible_values = ["生产部", "质检部", "维修部", "研发部"] # 默认值
            print(f"   使用默认列表: {possible_values}")

        while True:
            print(f"  {current_col} (可选值: {possible_values}, 当前输入): ", end="")
            val = input().strip()
            if val in possible_values:
                user_inputs[current_col] = val
                break
            else:
                print(f"    ❌ 输入无效，请从 {possible_values} 中选择一个。")

    return user_inputs

def discretize_single_input(user_inputs, config):
    """
    对单次用户输入的数据进行离散化
    生成 one-hot 编码格式的离散化数据
    注意：必须确保生成的离散化节点名与模型中的节点名完全一致
    """
    df_discrete = pd.DataFrame(index=[0]) # 创建一个只有一行的DataFrame

    # --- 从 metadata 获取列名 (确保使用模型训练时的列名) ---
    numerical_cols = config["metadata"]["dataset_config"]["numerical_cols"]
    categorical_cols = config["metadata"]["dataset_config"]["categorical_cols"]
    # --- 从 metadata 获取列名 ---

    # 1. 处理数值特征：离散化为 one-hot 编码
    for col in numerical_cols:
        if col in user_inputs:
            val = user_inputs[col]
            # --- 从 binning_info 读取 discretization_details ---
            try:
                # 尝试读取 normalization_details (如果存在)
                if "normalization_details" in config["data_info"]["binning_info"][col]:
                    details = config["data_info"]["binning_info"][col]["normalization_details"]
                    bins = details["bin_boundaries"]
                    labels = details["bin_labels"]
                else:
                    # 否则直接读取 bins 和 labels
                    info = config["data_info"]["binning_info"][col]
                    bins = info["bins"]
                    labels = info["labels"]
            except KeyError as e:
                print(f"❌ 错误: 无法找到特征 '{col}' 的离散化详情 (bins/labels): {e}")
                continue

            # 使用 pd.cut 进行离散化
            discretized_series = pd.cut(
                pd.Series([val]),
                bins=bins,
                labels=labels,
                include_lowest=True
            )
            discretized_label = discretized_series.iloc[0]

            # 创建 one-hot 编码列
            # 关键：这里生成的列名（discretized_label）必须与模型中的节点名一致
            for label in labels:
                df_discrete[label] = 0
            if discretized_label is not None:
                df_discrete.loc[0, discretized_label] = 1
            else:
                print(f"⚠️ 警告: 数值特征 '{col}' 的输入值 {val} 无法离散化。")

    # 2. 处理类别特征：one-hot编码
    for col in categorical_cols:
        if col in user_inputs:
            val = user_inputs[col]
            # --- 从 categorical_info 读取 unique_values 和 encoding_format ---
            try:
                info = config["data_info"]["categorical_info"][col]
                unique_values = info["unique_values"]
                # 尝试读取编码格式，如果不存在则使用默认格式
                encoding_format = info.get("normalization_details", {}).get("encoding_format", f"{col}_{{value}}")
            except KeyError as e:
                print(f"❌ 错误: 无法找到类别特征 '{col}' 的配置信息: {e}")
                continue

            # 为每个唯一值创建二值列
            for value in unique_values:
                new_col_name = encoding_format.replace("{value}", value)
                df_discrete[new_col_name] = 0
            # 激活对应的列
            target_col_name = encoding_format.replace("{value}", val)
            df_discrete.loc[0, target_col_name] = 1

    return df_discrete

def predict_status_and_analyze(model, discrete_input_data, target_col="status", rules_df=None):
    """
    使用模型预测状态，并进行规则反推或灵敏度分析
    """
    infer = VariableElimination(model)

    # 准备证据（所有离散化后的特征）
    evidence = {}
    for col in discrete_input_data.columns:
        if col != target_col and discrete_input_data[col].iloc[0] == 1:
            evidence[col] = int(discrete_input_data[col].iloc[0])

    print(f"\n🔍 正在进行状态预测，使用证据: {evidence}")

    try:
        # 查询目标变量的概率分布
        result = infer.query(variables=[target_col], evidence=evidence)

        # 获取所有状态及其概率
        state_probs = {state: prob for state, prob in zip(result.state_names[target_col], result.values)}

        # 排序
        sorted_probs = sorted(state_probs.items(), key=lambda item: item[1], reverse=True)

        # 找到最可能的状态
        most_likely_state, highest_prob = sorted_probs[0]

        print("\n--- 预测结果 ---")
        print("各状态概率:")
        for state, prob in sorted_probs:
            if state == most_likely_state:
                print(f"  🎯 {state}: {prob:.4f} (最可能)")
            else:
                print(f"     {state}: {prob:.4f}")

        # --- 规则反推 / 灵敏度分析 ---
        print("\n--- 影响因素分析 ---")
        contributing_factors = []

        if rules_df is not None:
            # 方法一：基于规则的反推
            print("  尝试基于关联规则进行分析...")
            for _, rule_row in rules_df.iterrows():
                rule_str = rule_row['rules']
                if " → " not in rule_str:
                    continue
                ant_str, con_str = rule_str.split(" → ", 1)
                antecedents = [a.strip() for a in re.split(r'[∧\s]+', ant_str) if a.strip()]
                consequent = con_str.strip()

                # 检查规则的前提条件是否被当前证据满足
                matched_antecedents = [ant for ant in antecedents if ant in evidence and evidence[ant] == 1]
                if matched_antecedents and consequent == most_likely_state:
                    # 如果规则的前件被满足，并且后件是预测的最可能状态
                    # 认为这些前件是导致该状态的潜在因素
                    contributing_factors.extend(matched_antecedents)
                    print(f"    规则触发: {rule_str} (置信度: {rule_row['confidence']:.3f}, 提升度: {rule_row['lift']:.3f})")
                    print(f"      满足的前件: {matched_antecedents}")

        # 如果规则反推没有找到或没有规则文件，则尝试基于模型结构的灵敏度分析
        if not contributing_factors:
            print("  基于模型结构进行灵敏度分析...")
            # 获取 status 节点的父节点（即直接影响它的特征）
            parent_nodes = list(model.predecessors(target_col))
            print(f"    {target_col} 的父节点: {parent_nodes}")

            # 检查这些父节点中，哪些在当前证据中被激活（值为1）
            active_parents = [node for node in parent_nodes if node in evidence and evidence[node] == 1]
            print(f"    当前激活的父节点: {active_parents}")

            # 这些激活的父节点就是对当前预测结果有直接影响的特征
            contributing_factors = active_parents

        if contributing_factors:
            # 去重并按重要性排序（这里简单地按输入顺序或字母顺序，可以根据置信度等规则排序）
            unique_contributing_factors = sorted(list(set(contributing_factors)))
            print(f"\n  🔍 建议重点关注的参数: {unique_contributing_factors}")
        else:
            print("  未能识别出明确的影响因素。")

        return sorted_probs, most_likely_state, highest_prob

    except Exception as e:
        print(f"❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def main():
    """主函数"""
    print("🔍 开始设备状态评估...")

    try:
        # 1. 加载模型、配置和规则
        model, config, rules_df = load_model_and_config()

        # 2. 获取用户输入 (使用 metadata 中的列名)
        user_inputs = get_user_input(config)

        print("\n--- 用户输入汇总 ---")
        for k, v in user_inputs.items():
            print(f"  {k}: {v}")

        # 3. 离散化输入 (使用 metadata 中的列名)
        print("\n🔄 对输入数据进行离散化...")
        discrete_input = discretize_single_input(user_inputs, config)
        print(f"✅ 离散化完成，特征: {list(discrete_input.columns)}")
        print(f"   离散化结果 (one-hot): {discrete_input.iloc[0].to_dict()}")

        # 4. 预测状态并分析 (确保离散化数据的列名与模型节点匹配)
        print("\n--- 开始预测与分析 ---")
        sorted_probs, most_likely_state, highest_prob = predict_status_and_analyze(model, discrete_input, rules_df=rules_df)

        if sorted_probs is not None:
            print(f"\n✅ 预测完成！最可能的状态是: {most_likely_state} (概率: {highest_prob:.4f})")
        else:
            print("❌ 预测失败。")

    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
    except KeyError as e:
        print(f"❌ 配置文件格式错误或缺少键: {e}")
        print("   请检查您的分箱配置.json文件结构是否与代码逻辑匹配，特别是 metadata.dataset_config 和 data_info.binning_info 部分。")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
