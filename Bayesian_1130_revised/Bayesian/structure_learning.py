import pandas as pd
import networkx as nx
from pgmpy.models import BayesianNetwork
import re
from collections import defaultdict


def get_feature_states(binning_config):
    """获取所有特征的离散化状态"""
    feature_states = {}

    # 1. 数值特征的离散化状态
    binning_info = binning_config["data_info"]["binning_info"]
    for feature, info in binning_info.items():
        if "labels" in info:
            feature_states[feature] = info["labels"]

    # 2. 类别特征的状态
    categorical_info = binning_config["data_info"]["categorical_info"]
    for feature, info in categorical_info.items():
        if "unique_values" in info:
            # 生成 one-hot 编码列名
            prefix = info.get("prefix", feature)
            feature_states[feature] = [f"{prefix}_{value}" for value in info["unique_values"]]

    return feature_states


def parse_rule_for_structure(rule_str, feature_states):
    """
    解析规则，用于构建网络结构
    例如：'中信号频率_Hz ∧ 中工作电流_A → 传动系统异常'
    返回：(['信号频率_Hz', '工作电流_A'], 'status')  # 状态节点统一为target_col
    """
    if " → " not in rule_str:
        return [], ""

    ant_str, con_str = rule_str.split(" → ", 1)
    antecedents = [a.strip() for a in re.split(r'[∧\s]+', ant_str) if a.strip()]
    consequents = [c.strip() for c in re.split(r'[∧\s]+', con_str) if c.strip()]

    # 解析前件特征
    antecedent_features = []
    for ant in antecedents:
        # 查找该状态属于哪个特征
        found = False
        for feature, states in feature_states.items():
            if ant in states:
                antecedent_features.append(feature)
                found = True
                break
        if not found:
            print(f"⚠️ 警告: 无法识别前件状态 '{ant}'")

    # 后件统一为目标变量
    return antecedent_features, "status"


def rules_to_dag(rules_df, binning_config, max_parents_per_node=15):
    """
    将规则转换为 DAG，完全动态
    """
    # 获取特征状态
    feature_states = get_feature_states(binning_config)

    # 收集所有规则
    all_rules = []
    for _, rule in rules_df.iterrows():
        # 修正：确保数值列被转换为float
        try:
            confidence = float(rule['confidence'])
            lift = float(rule['lift'])
            support = float(rule['support'])
        except (ValueError, TypeError):
            print(f"⚠️ 警告: 规则的数值列无法转换，跳过: {rule['rules']}")
            continue

        # 解析规则
        antecedent_features, consequent = parse_rule_for_structure(
            rule['rules'], feature_states
        )

        if antecedent_features and consequent:
            all_rules.append({
                'antecedent_features': antecedent_features,
                'consequent': consequent,
                'confidence': confidence,
                'lift': lift,
                'support': support
            })

    # 按质量评分排序（综合置信度、提升度、支持度）
    def calculate_quality_score(rule):
        try:
            return rule['confidence'] * rule['lift'] * (rule['support'] ** 0.5)
        except (TypeError, ValueError):
            return 0.0  # 如果计算失败，返回0

    all_rules.sort(key=calculate_quality_score, reverse=True)

    # 为每个目标状态选择规则
    edges = set()
    rule_count_by_target = defaultdict(int)

    for rule in all_rules:
        # 限制每个目标状态的规则数量
        if rule_count_by_target[rule['consequent']] < max_parents_per_node // 2:  # 假设最多2种状态
            # 为每个前件特征添加边
            for feature in rule['antecedent_features']:
                edges.add((feature, rule['consequent']))
            rule_count_by_target[rule['consequent']] += 1

    # 构建 DAG（去环）
    G = nx.DiGraph()
    G.add_edges_from(edges)
    if not nx.is_directed_acyclic_graph(G):
        print("⚠️ 规则图含环，尝试去环...")
        try:
            order = list(nx.topological_sort(G))
            dag_edges = [(u, v) for u, v in edges if u in order and v in order and order.index(u) < order.index(v)]
        except nx.NetworkXUnfeasible:
            # 降级策略：保留高质量规则
            dag_edges = list(edges)[:max_parents_per_node * 2]
    else:
        dag_edges = list(G.edges())

    return dag_edges


def build_bayesian_network_structure(rules_df, binning_config, max_parents_per_node=15):
    edges = rules_to_dag(rules_df, binning_config, max_parents_per_node)
    print(f"✅ 网络结构构建完成，包含 {len(edges)} 条边")
    return BayesianNetwork(edges)