import json
import pandas as pd
import re
import networkx as nx
import matplotlib.pyplot as plt
import os
import matplotlib

matplotlib.use('Agg')  # 使用非交互式后端


def load_binning_config(path):
    """读取分箱配置文件，返回完整配置字典"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_association_rules(path):
    """读取关联规则 CSV，兼容新旧表头与无表头格式"""
    df = pd.read_csv(path, encoding='utf-8-sig')
    columns = list(df.columns)

    if '规则' in columns:
        support_col = '完整支持度' if '完整支持度' in columns else '支持度'
        required_cols = ['规则', support_col, '置信度', '提升度']
        missing = [col for col in required_cols if col not in columns]
        if missing:
            raise ValueError(f"关联规则 CSV 缺少必要列: {missing}")
        df = df[required_cols].rename(
            columns={
                '规则': 'rules',
                support_col: 'support',
                '置信度': 'confidence',
                '提升度': 'lift'
            }
        )
    elif {'rules', 'support', 'confidence', 'lift'}.issubset(columns):
        df = df[['rules', 'support', 'confidence', 'lift']].copy()
    else:
        df = pd.read_csv(path, header=None, encoding='utf-8-sig')
        if df.shape[1] < 4:
            raise ValueError(f"关联规则 CSV 列数不足: {df.shape[1]}")
        df = df.iloc[:, :4]
        df.columns = ['rules', 'support', 'confidence', 'lift']

    for col in ['support', 'confidence', 'lift']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()
    print(f"✅ 关联规则加载完成，有效规则数: {len(df)}")
    return df


def get_target_states(binning_config):
    """从配置中获取目标变量的所有可能状态"""
    target_info = binning_config.get("data_info", {}).get("target_info", {})
    class_dist = target_info.get("class_distribution", {})
    if class_dist:
        return list(class_dist.keys())
    return None


def discretize_raw_data(raw_data, binning_config):
    """
    修正版：将每个特征作为一个多状态节点
    1. 数值特征：离散化为标签状态
    2. 类别特征：one-hot编码
    """
    df_discrete = pd.DataFrame(index=raw_data.index)

    # 1. 处理数值特征：每个特征作为一个多状态节点
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
                # 直接将离散化结果作为该特征的值
                discretized = pd.cut(
                    numeric_series,
                    bins=info["bins"],
                    labels=info["labels"],
                    include_lowest=True
                )

                # 直接使用原始特征名作为列名，值为离散化标签
                df_discrete[col] = discretized

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


def visualize_bayesian_network(bn_model, save_path=None):
    """
    可视化贝叶斯网络结构（支持中文字体）
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    if save_path is None:
        import sys
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(PROJECT_ROOT)
        from Bayesian.config import BAYESIAN_RESULT_DIR
        save_path = os.path.join(BAYESIAN_RESULT_DIR, "bayesian_network_structure.png")

    # 创建有向图
    G = nx.DiGraph()

    # 添加节点
    for node in bn_model.nodes():
        G.add_node(node)

    # 添加边
    for edge in bn_model.edges():
        G.add_edge(edge[0], edge[1])

    # 创建图形
    plt.figure(figsize=(16, 12))

    # 使用spring布局
    pos = nx.spring_layout(G, k=3, iterations=50)

    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color='lightblue', alpha=0.8)

    # 绘制边
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, edge_color='gray', arrows=True, arrowsize=20)

    # 绘制标签（使用英文标题，避免中文问题）
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

    plt.title("Bayesian Network Structure", fontsize=16)  # 使用英文标题
    plt.axis('off')
    plt.tight_layout()

    # 保存图片
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 网络结构图已保存至: {save_path}")

    # 输出网络统计信息
    print(f"📊 网络统计:")
    print(f"   节点数: {len(G.nodes())}")
    print(f"   边数: {len(G.edges())}")

    # 计算入度和出度
    in_degrees = {node: G.in_degree(node) for node in G.nodes()}
    out_degrees = {node: G.out_degree(node) for node in G.nodes()}

    max_in_degree = max(in_degrees.values()) if in_degrees else 0
    max_out_degree = max(out_degrees.values()) if out_degrees else 0

    print(f"   最大入度: {max_in_degree}")
    print(f"   最大出度: {max_out_degree}")

    # 找出高入度节点（可能的瓶颈）
    high_in_nodes = [node for node, degree in in_degrees.items() if degree > 10]
    if high_in_nodes:
        print(f"   高入度节点 (>10): {high_in_nodes}")

    return G
