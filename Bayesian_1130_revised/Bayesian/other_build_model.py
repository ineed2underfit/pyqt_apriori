# Bayesian/other_build_model.py

import os
import pandas as pd
import pickle
import json
import re
from datetime import datetime
from collections import defaultdict
import networkx as nx
from pgmpy.models import BayesianNetwork
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免在无GUI环境下出错
import matplotlib.pyplot as plt

# --- 配置路径 (复用原有配置) ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
RULES_CSV_PATH = os.path.join(PROJECT_ROOT, "result", "apriori_results", "关联规则分析结果.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "datas")
OTHER_MODEL_SAVE_DIR = os.path.join(PROJECT_ROOT, "Bayesian", "other_models")  # 保存到独立目录
BAYESIAN_RESULT_DIR = os.path.join(PROJECT_ROOT, "result", "bayesian_results")

os.makedirs(OTHER_MODEL_SAVE_DIR, exist_ok=True)
os.makedirs(BAYESIAN_RESULT_DIR, exist_ok=True)


def load_binning_config(path):
    """读取分箱配置文件"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_association_rules(path):
    """读取关联规则 CSV"""
    df = pd.read_csv(path, header=None, names=["rules", "support", "confidence", "lift"], encoding='utf-8')
    for col in ['support', 'confidence', 'lift']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()
    return df


def discretize_raw_data(raw_data, binning_config):
    """
    数据离散化 (复用原有逻辑)
    """
    df_discrete = pd.DataFrame(index=raw_data.index)

    # 1. 数值特征离散化为 one-hot
    binning_info = binning_config["data_info"]["binning_info"]
    numerical_cols = binning_config["metadata"]["dataset_config"]["numerical_cols"]
    for col in numerical_cols:
        if col in raw_data.columns and col in binning_info:
            try:
                if raw_data[col].dtype == 'object':
                    numeric_series = pd.to_numeric(raw_data[col], errors='coerce')
                else:
                    numeric_series = raw_data[col]
                if numeric_series.isna().all():
                    continue
                info = binning_info[col]
                discretized = pd.cut(numeric_series, bins=info["bins"], labels=info["labels"], include_lowest=True)
                one_hot = pd.get_dummies(discretized, prefix='', prefix_sep='')
                df_discrete = pd.concat([df_discrete, one_hot], axis=1)
            except Exception as e:
                print(f"⚠️ 警告: 离散化列 '{col}' 时出错: {e}")
                continue

    # 2. 类别特征 one-hot 编码
    categorical_info = binning_config["data_info"]["categorical_info"]
    categorical_cols = binning_config["metadata"]["dataset_config"]["categorical_cols"]
    for col in categorical_cols:
        if col in raw_data.columns and col in categorical_info:
            try:
                info = categorical_info[col]
                unique_values = info["unique_values"]
                prefix = info.get("prefix", col)
                for value in unique_values:
                    new_col_name = f"{prefix}_{value}"
                    df_discrete[new_col_name] = (raw_data[col] == value).astype(int)
            except Exception as e:
                print(f"⚠️ 警告: one-hot编码列 '{col}' 时出错: {e}")
                continue

    # 3. 保留目标变量
    target_col = binning_config["metadata"]["dataset_config"]["target_col"]
    if target_col in raw_data.columns:
        df_discrete[target_col] = raw_data[target_col]

    return df_discrete


def rules_to_dag(rules_df, binning_config, max_rules_per_consequent=3):
    """
    将关联规则转换为 DAG (复用原有核心逻辑)
    """
    # 从配置获取目标状态
    target_info = binning_config.get("data_info", {}).get("target_info", {})
    target_states = target_info.get("unique_values") or list(target_info.get("class_distribution", {}).keys())
    if not target_states:
        raise ValueError("无法从配置文件获取目标状态列表。")

    target_col = binning_config["metadata"]["dataset_config"]["target_col"]
    rules_by_consequent = defaultdict(list)

    for _, row in rules_df.iterrows():
        if " → " not in row['rules']:
            continue
        ant_str, con_str = row['rules'].split(" → ", 1)
        antecedents = [a.strip() for a in re.split(r'[∧\s]+', ant_str) if a.strip()]
        consequent = con_str.strip()

        if consequent in target_states:
            quality_score = row['confidence'] * row['lift'] * (row['support'] ** 0.5)
            rules_by_consequent[consequent].append({
                'antecedents': antecedents,
                'quality_score': quality_score
            })

    edges = set()
    for consequent, rules_list in rules_by_consequent.items():
        sorted_rules = sorted(rules_list, key=lambda x: x['quality_score'], reverse=True)
        selected_antecedents = set()
        rules_added = 0
        for rule_info in sorted_rules:
            if rules_added >= max_rules_per_consequent:
                break
            current_antecedents = set(rule_info['antecedents'])
            overlap_ratio = 0
            if selected_antecedents:
                intersection = current_antecedents & selected_antecedents
                union = current_antecedents | selected_antecedents
                overlap_ratio = len(intersection) / len(union) if union else 0
            if overlap_ratio < 0.5:  # 去冗余
                for a in current_antecedents:
                    edges.add((a, target_col))
                selected_antecedents.update(current_antecedents)
                rules_added += 1

    # 构建图
    G = nx.DiGraph(list(edges))
    if not nx.is_directed_acyclic_graph(G):
        try:
            order = list(nx.topological_sort(G))
            dag_edges = [(u, v) for u, v in edges if u in order and v in order and order.index(u) < order.index(v)]
        except nx.NetworkXUnfeasible:
            dag_edges = list(edges)[:max_rules_per_consequent * 2]
    else:
        dag_edges = list(G.edges())

    return dag_edges


# --- 新增：从 pgmpy.utils 导入绘图函数或自定义 ---
def visualize_bayesian_network(bn_model, save_path=None):
    """
    可视化贝叶斯网络结构（支持中文字体）
    """
    # --- 关键修改：设置中文字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 尝试列表中的字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题
    # --- 关键修改结束 ---

    if save_path is None:
        save_path = os.path.join(BAYESIAN_RESULT_DIR, "other_bn_structure.png")

    # 创建有向图
    G = nx.DiGraph()
    for node in bn_model.nodes():
        G.add_node(node)
    for edge in bn_model.edges():
        G.add_edge(edge[0], edge[1])

    # 绘制图形
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=3, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color='lightblue', alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, edge_color='gray', arrows=True, arrowsize=20)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

    plt.title("贝叶斯网络结构图", fontsize=16)
    plt.axis('off')
    plt.tight_layout()

    # 保存图片
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 网络结构图已保存至: {save_path}")


# --- 主函数 ---
def other_build_and_save_bayesian_model(data_filename: str, learning_method: str = "mle", model_name: str = None):
    """
    使用指定的参数学习方法（MLE 或 EM）构建并保存贝叶斯网络模型。

    Args:
        data_filename: 训练数据文件名。
        learning_method: 参数学习方法，可选 "mle" 或 "em"。
        model_name: 保存的模型文件名。
    """
    print(f"🚀 开始使用 {learning_method.upper()} 方法构建贝叶斯网络...")

    # 1. 加载配置和数据
    binning_config = load_binning_config(BINNING_CONFIG_PATH)
    data_path = os.path.join(DATA_DIR, data_filename)
    raw_data = pd.read_csv(data_path, encoding='utf-8')

    dataset_config = binning_config["metadata"]["dataset_config"]
    all_cols = (dataset_config["id_cols"] + dataset_config["categorical_cols"] +
                [dataset_config["target_col"]] + dataset_config["numerical_cols"])

    if list(raw_data.columns) != all_cols:
        if set(raw_data.columns) == set(all_cols):
            raw_data = raw_data[all_cols]
        else:
            raise ValueError("CSV 列名与配置不匹配。")

    # 2. 离散化数据
    print("🔄 对训练数据进行离散化...")
    discrete_data = discretize_raw_data(raw_data, binning_config)

    # 3. 构建网络结构
    print("🏗️ 构建网络结构...")
    rules_df = load_association_rules(RULES_CSV_PATH)
    edges = rules_to_dag(rules_df, binning_config, max_rules_per_consequent=3)
    model = BayesianNetwork(edges)
    print(f"✅ 网络结构构建完成，包含 {len(edges)} 条边")

    # 4. 可视化
    visualize_bayesian_network(model, os.path.join(BAYESIAN_RESULT_DIR, f"other_bn_structure_{learning_method}.png"))

    # 5. 验证并准备训练数据
    model_nodes_set = set(model.nodes())
    data_cols_set = set(discrete_data.columns)
    missing_in_data = model_nodes_set - data_cols_set
    if missing_in_data:
        raise ValueError(f"模型中的节点在离散化数据中缺失: {missing_in_data}")

    training_nodes = list(model_nodes_set)
    training_data = discrete_data[training_nodes].copy()
    print(f"✅ 使用 {len(training_nodes)} 个节点进行训练")

    # 6. 参数学习 (调用新的模块)
    print("🔍 执行参数学习...")
    from .other_parameter_learning import learn_parameters_mle, learn_parameters_em

    if learning_method == "mle":
        model = learn_parameters_mle(model, training_data)
    elif learning_method == "em":
        # --- 修正：移除 tol 参数 ---
        model = learn_parameters_em(model, training_data, max_iter=100)    # --- 修正：移除 tol 参数 ---
    else:
        raise ValueError("不支持的学习方法。请使用 'mle' 或 'em'。")

    # 7. 保存模型
    if model_name is None:
        model_name = f"other_bn_model_{learning_method}.pkl"
    model_path = os.path.join(OTHER_MODEL_SAVE_DIR, model_name)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ 模型已保存至: {model_path}")

    return model_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python other_build_model.py <data_filename.csv> <learning_method>")
        print("      learning_method: mle | em")
        sys.exit(1)

    data_file = sys.argv[1]
    method = sys.argv[2].lower()
    if method not in ["mle", "em"]:
        print("错误: learning_method 必须是 'mle' 或 'em'")
        sys.exit(1)

    other_build_and_save_bayesian_model(data_file, method)