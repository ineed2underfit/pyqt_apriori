# Bayesian/build_model.py

import os
import pandas as pd
import pickle
import numpy as np
import json
import re
import networkx as nx
from datetime import datetime
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import BayesianEstimator
import matplotlib.pyplot as plt

# --- 配置路径 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
RULES_CSV_PATH = os.path.join(PROJECT_ROOT, "result", "apriori_results", "关联规则分析结果.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "datas")
MODEL_SAVE_DIR = os.path.join(PROJECT_ROOT, "Bayesian", "models")
BAYESIAN_RESULT_DIR = os.path.join(PROJECT_ROOT, "result", "bayesian_results")

os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
os.makedirs(BAYESIAN_RESULT_DIR, exist_ok=True)


def load_binning_config(path):
    """读取分箱配置文件，返回完整配置字典"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_association_rules(path):
    """读取关联规则 CSV（无 header），确保数值列为数值类型"""
    df = pd.read_csv(path, header=None, names=["rules", "support", "confidence", "lift"], encoding='utf-8')

    # 确保数值列被转换为float
    for col in ['support', 'confidence', 'lift']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 删除包含NaN的行
    df = df.dropna()
    print(f"✅ 关联规则加载完成，有效规则数: {len(df)}")
    return df


def create_node_to_column_mapping(binning_config):
    """
    从分箱配置文件中直接创建离散化节点名到原始列名的映射字典
    例如: {'低工作电流_A': '工作电流_A', '中工作电流_A': '工作电流_A', ... , 'department_生产部': 'department'}
    """
    node_to_col_map = {}

    # 1. 处理数值特征的映射
    binning_info = binning_config["data_info"]["binning_info"]
    # 从 metadata 获取数值列列表
    numerical_cols = binning_config["metadata"]["dataset_config"]["numerical_cols"]

    for col_name in numerical_cols:
        if col_name in binning_info:
            info = binning_info[col_name]
            # 从 normalization_details 或直接从 info 获取 labels
            if "normalization_details" in info:
                # 尝试新路径
                labels = info["normalization_details"].get("bin_labels") or info.get("labels")
            else:
                # 尝试旧路径或直接获取
                labels = info.get("labels")

            if labels:
                for label in labels:
                    # 离散化后的标签 -> 原始列名
                    node_to_col_map[label] = col_name
            else:
                print(f"⚠️ 警告: 数值特征 '{col_name}' 在配置中找不到 'labels' 或 'normalization_details.bin_labels'")

    # 2. 处理类别特征的映射
    categorical_info = binning_config["data_info"]["categorical_info"]
    # 从 metadata 获取类别列列表
    categorical_cols = binning_config["metadata"]["dataset_config"]["categorical_cols"]

    for col_name in categorical_cols:
        if col_name in categorical_info:
            info = categorical_info[col_name]
            unique_values = info.get("unique_values")
            # 获取 one-hot 编码的前缀格式
            # 尝试从 normalization_details 获取，如果不存在则使用默认格式
            encoding_format = info.get("normalization_details", {}).get("encoding_format", f"{col_name}_{{value}}")

            if unique_values:
                for value in unique_values:
                    # 使用配置的格式生成 one-hot 编码后的节点名
                    node_name = encoding_format.format(value=value)
                    # one-hot 编码后的节点名 -> 原始列名
                    node_to_col_map[node_name] = col_name
            else:
                print(f"⚠️ 警告: 类别特征 '{col_name}' 在配置中找不到 'unique_values'")
        else:
            print(f"⚠️ 警告: 类别特征 '{col_name}' 在 'data_info.categorical_info' 中未定义")

    return node_to_col_map


def rules_to_dag(rules_df, binning_config, max_rules_per_consequent=3, max_total_edges=None):
    """
    将关联规则转换为贝叶斯网络的有向无环图 (DAG)
    通过限制每种后件的规则数量和去冗余来控制复杂度
    从 binning_config 中动态读取目标状态
    保存筛选后的规则
    """
    # 1. 从配置文件动态获取目标状态列表
    target_info = binning_config.get("data_info", {}).get("target_info", {})
    target_states = target_info.get("unique_values") or list(target_info.get("class_distribution", {}).keys())
    if not target_states:
        print("❌ 无法从配置文件获取目标状态列表。")
        return [], []

    # 2. 获取目标列名
    target_col = binning_config["metadata"]["dataset_config"]["target_col"]

    # 3. 按后件（Consequent，即目标状态）分组规则
    from collections import defaultdict
    rules_by_consequent = defaultdict(list)
    for _, row in rules_df.iterrows():
        rule_str = row['rules']
        if " → " not in rule_str:
            continue

        ant_str, con_str = rule_str.split(" → ", 1)
        antecedents = [a.strip() for a in re.split(r'[∧\s]+', ant_str) if a.strip()]
        consequent = con_str.strip()

        # 只处理在配置文件中定义的目标状态
        if consequent in target_states:
            # 计算规则质量分数 (Quality Score)
            quality_score = row['confidence'] * row['lift'] * (row['support'] ** 0.5)
            rules_by_consequent[consequent].append({
                'antecedents': antecedents,
                'quality_score': quality_score,
                'confidence': row['confidence'],
                'lift': row['lift'],
                'support': row['support'],
                'original_rule': rule_str  # 保存原始规则字符串
            })

    edges = set()
    total_edges_added = 0
    final_rules_for_network = []  # 存储最终用于构建网络的规则

    # 4. 为每种目标状态选择最优且非冗余的规则
    for consequent, rules_list in rules_by_consequent.items():
        print(f"   处理后件: {consequent}, 候选规则数: {len(rules_list)}")

        # 4a. 按质量分数排序
        sorted_rules = sorted(rules_list, key=lambda x: x['quality_score'], reverse=True)

        # 4b. 选择最优规则并去冗余
        selected_antecedents = set()  # 记录已选规则的所有前件，用于去冗余
        rules_added = 0

        for rule_info in sorted_rules:
            if rules_added >= max_rules_per_consequent:
                print(f"     已达到最大规则数限制 ({max_rules_per_consequent})，停止添加。")
                break

            current_antecedents = set(rule_info['antecedents'])

            # 4c. 计算当前规则与已选规则的重叠度 (Jaccard Similarity)
            overlap_ratio = 0
            if selected_antecedents:  # 如果已有选中的前件
                intersection = current_antecedents & selected_antecedents
                union = current_antecedents | selected_antecedents
                overlap_ratio = len(intersection) / len(union) if union else 0

            # 4d. 如果重叠度低于阈值，则添加此规则的边和信息
            overlap_threshold = 0.5
            if overlap_ratio < overlap_threshold:
                for a in current_antecedents:
                    edge = (a, target_col)
                    if max_total_edges is None or total_edges_added < max_total_edges:
                        edges.add(edge)
                        total_edges_added += 1
                    else:
                        print(f"   已达到总边数限制 ({max_total_edges})，停止添加边。")
                        break  # 退出内层循环

                selected_antecedents.update(current_antecedents)  # 更新已选集合
                final_rules_for_network.append(rule_info)  # 添加到最终规则列表
                rules_added += 1
                print(
                    f"     添加规则 (Quality: {rule_info['quality_score']:.4f}, Overlap: {overlap_ratio:.2f}): {rule_info['original_rule']}")
            else:
                print(f"     跳过冗余规则 (Overlap: {overlap_ratio:.2f}): {rule_info['original_rule']}")

        print(f"   为 {consequent} 选择了 {rules_added} 条规则。")

    print(f"✅ 最终网络包含 {len(edges)} 条边。")
    print(f"✅ 最终用于构建网络的规则数: {len(final_rules_for_network)}")

    # 5. 构建图并处理环（如果有的话）
    G = nx.DiGraph(list(edges))
    if not nx.is_directed_acyclic_graph(G):
        print("⚠️ 规则图含环，尝试去环...")
        try:
            order = list(nx.topological_sort(G))
            dag_edges = [(u, v) for u, v in edges if u in order and v in order and order.index(u) < order.index(v)]
        except nx.NetworkXUnfeasible:
            print("   ❌ 无法自动去环，保留部分边")
            dag_edges = list(edges)[:max_rules_per_consequent * 2]  # 限制边数作为降级策略
    else:
        dag_edges = list(G.edges())

    return dag_edges, final_rules_for_network


def discretize_raw_data(raw_data, binning_config):
    """
    对原始数据进行离散化，生成 one-hot 编码的二元节点
    例如：工作电流_A (0.55) -> ['低工作电流_A', '中工作电流_A', '高工作电流_A'] (one-hot)
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


def learn_parameters(model: BayesianNetwork, data: pd.DataFrame,
    prior_type = "BDeu", equivalent_sample_size = 10) -> BayesianNetwork:
    """
    参数学习函数
    """
    try:
        model.fit(data, estimator=BayesianEstimator,
                  prior_type=prior_type,
                  equivalent_sample_size=equivalent_sample_size)
    except ValueError as e:
        if "Product space too large" in str(e):
            print("❌ 标准参数学习因维度爆炸失败。尝试简化等效样本量...")
            try:
                model.fit(data, estimator=BayesianEstimator,
                          prior_type="dirichlet",
                          pseudo_counts=1)
                print("✅ 使用等效样本量=1成功学习参数。")
            except ValueError as e2:
                if "Product space too large" in str(e2):
                    print("❌ 即使等效样本量为1也失败。模型结构可能过于复杂。")
                    raise
                else:
                    print("✅ 使用等效样本量=1成功学习参数。")
                    return model
        else:
            raise  # 重新抛出其他类型的错误
    except Exception as e:
        print(f"❌ 参数学习失败: {e}")
        raise

    return model


def visualize_bayesian_network(bn_model, save_path=None):
    """
    可视化贝叶斯网络结构（支持中文字体）
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    if save_path is None:
        save_path = os.path.join(BAYESIAN_RESULT_DIR, "bayesian_network_structure.png")

    # 创建有向图
    G = nx.DiGraph()
    for node in bn_model.nodes():
        G.add_node(node)
    for edge in bn_model.edges():
        G.add_edge(edge[0], edge[1])

    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=3, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color='lightblue', alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, edge_color='gray', arrows=True, arrowsize=20)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    plt.title("贝叶斯网络结构图", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 网络结构图已保存至: {save_path}")

    # 输出网络统计信息
    print(f"📊 网络统计:")
    print(f"   节点数: {len(G.nodes())}")
    print(f"   边数: {len(G.edges())}")
    in_degrees = {node: G.in_degree(node) for node in G.nodes()}
    out_degrees = {node: G.out_degree(node) for node in G.nodes()}
    max_in_degree = max(in_degrees.values()) if in_degrees else 0
    max_out_degree = max(out_degrees.values()) if out_degrees else 0
    print(f"   最大入度: {max_in_degree}")
    print(f"   最大出度: {max_out_degree}")
    high_in_nodes = [node for node, degree in in_degrees.items() if degree > 10]
    if high_in_nodes:
        print(f"   高入度节点 (>10): {high_in_nodes}")
    return G


def save_network_rules_with_mapping(final_rules, node_to_col_map, save_path=None):
    """
    保存用于构建网络的规则到 JSON 文件，并包含节点-列映射
    """
    if save_path is None:
        save_path = os.path.join(BAYESIAN_RESULT_DIR, "network_rules_with_mapping.json")

    # 准备要保存的数据
    rules_to_save = []
    for rule_info in final_rules:
        # 只保留需要的信息，并添加列名映射
        mapped_antecedents = []
        for ant_node in rule_info['antecedents']:
            original_col = node_to_col_map.get(ant_node, "Unknown_Column")  # 如果找不到映射，标记为 Unknown
            mapped_antecedents.append({
                "node_name": ant_node,
                "original_column": original_col
            })

        simplified_rule = {
            "original_rule": rule_info["original_rule"],
            "antecedents_mapped": mapped_antecedents,  # 包含节点名和原始列名
            "consequent": rule_info["original_rule"].split(" → ")[1].strip(),  # 后件（目标状态）
            "quality_score": rule_info["quality_score"],
            "confidence": rule_info["confidence"],
            "lift": rule_info["lift"],
            "support": rule_info["support"]
        }
        rules_to_save.append(simplified_rule)

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(rules_to_save, f, ensure_ascii=False, indent=2)

    print(f"✅ 用于构建网络的规则（含列映射）已保存至: {save_path}")


def build_and_save_bayesian_model(data_filename: str, model_name: str = None):
    # 1. 加载配置
    binning_config = load_binning_config(BINNING_CONFIG_PATH)

    # 2. 从配置获取列名
    dataset_config = binning_config["metadata"]["dataset_config"]
    id_cols = dataset_config["id_cols"]
    categorical_cols = dataset_config["categorical_cols"]
    target_col = dataset_config["target_col"]
    numerical_cols = dataset_config["numerical_cols"]

    all_cols = id_cols + categorical_cols + [target_col] + numerical_cols

    # 3. 加载原始数据（有表头！）
    data_path = os.path.join(DATA_DIR, data_filename)
    raw_data = pd.read_csv(data_path, encoding='utf-8')  # 移除 header=None
    print(f"✅ 原始数据加载完成: {raw_data.shape}，列数: {len(raw_data.columns)}")

    # 验证列名是否匹配
    if list(raw_data.columns) != all_cols:
        print(f"⚠️ 警告: CSV 列名与配置不完全匹配")
        print(f"   CSV 列: {list(raw_data.columns)}")
        print(f"   配置列: {all_cols}")
        # 如果顺序不一致，需要重新排序
        if set(raw_data.columns) == set(all_cols):
            print("   ✅ 列名匹配，仅顺序不同，重新排序...")
            raw_data = raw_data[all_cols]
        else:
            print("   ❌ 列名不匹配，请检查数据文件和配置")
            # 尝试使用配置顺序（如果 CSV 没有表头）
            raw_data = pd.read_csv(data_path, header=None, names=all_cols, encoding='utf-8')

    print(f"✅ 数据列名: {list(raw_data.columns)}")

    # 4. 离散化（生成 one-hot 编码的二元节点）
    discrete_data = discretize_raw_data(raw_data, binning_config)
    print(f"✅ 离散化完成，列数: {len(discrete_data.columns)}")
    print(f"   示例列: {list(discrete_data.columns)[:10]}...")

    # 5. 加载规则
    rules_df = load_association_rules(RULES_CSV_PATH)

    # 6. 构建网络结构（基于离散化后的节点名，并获取筛选后的规则）
    edges, final_rules = rules_to_dag(rules_df, binning_config, max_rules_per_consequent=3, max_total_edges=50)
    bn_model = BayesianNetwork(edges)
    print(f"✅ 网络结构构建完成，包含 {len(edges)} 条边")

    # 7. 创建节点到列的映射
    node_to_col_map = create_node_to_column_mapping(binning_config)
    print(f"✅ 创建节点-列映射，映射数量: {len(node_to_col_map)}")

    # 8. 保存筛选后的规则（含列映射）
    save_network_rules_with_mapping(final_rules, node_to_col_map)

    # 9. 可视化网络结构
    graph_path = os.path.join(BAYESIAN_RESULT_DIR, f"bn_structure.png")
    visualize_bayesian_network(bn_model, save_path=graph_path)

    # 10. 验证节点
    available_nodes = [node for node in bn_model.nodes() if node in discrete_data.columns]
    missing_nodes = set(bn_model.nodes()) - set(available_nodes)
    if missing_nodes:
        print(f"⚠️ 警告: 以下节点在离散化后数据中缺失: {missing_nodes}")
    aligned_data = discrete_data[available_nodes].copy()
    print(f"✅ 使用 {len(available_nodes)} 个节点进行训练")

    # 11. 参数学习
    print("🔍 贝叶斯参数学习中...")
    bn_model = learn_parameters(bn_model, aligned_data, prior_type="BDeu", equivalent_sample_size=10)
    print("✅ 参数学习完成")

    # 12. 保存模型
    if model_name is None:
        model_name = f"final_bn_model.pkl"
    model_path = os.path.join(MODEL_SAVE_DIR, model_name)
    with open(model_path, 'wb') as f:
        pickle.dump(bn_model, f)
    print(f"✅ 模型已保存至: {model_path}")

    # 13. 验证目标变量
    if target_col in aligned_data.columns:
        status_values = sorted(aligned_data[target_col].unique())
        print(f"📊 {target_col} 取值: {status_values}")

    return model_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python build_model.py <data_filename.csv> [model_name.pkl]")
        sys.exit(1)
    build_and_save_bayesian_model(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)