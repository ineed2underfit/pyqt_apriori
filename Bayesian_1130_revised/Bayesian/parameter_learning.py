from pgmpy.models import BayesianNetwork
from pgmpy.estimators import BayesianEstimator
import numpy as np
import pandas as pd  # 添加 pandas 导入


def learn_parameters(model: BayesianNetwork, data: pd.DataFrame,
                     prior_type="BDeu", equivalent_sample_size=10,
                     memory_limit_nodes=20) -> BayesianNetwork:
    """
    参数学习函数 - 添加内存优化
    """
    # 检查节点数量，如果过多则进行优化
    if len(model.nodes()) > memory_limit_nodes:
        print(f"⚠️ 警告: 节点数量 ({len(model.nodes())}) 超过建议限制 ({memory_limit_nodes})，进行优化...")

        # 限制节点数量，只保留目标节点及其直接父节点
        target_col = [node for node in model.nodes() if 'status' in node.lower()]

        if target_col:
            target_col = target_col[0]  # 假设只有一个目标列
            parents = list(model.predecessors(target_col))

            # 只保留目标节点和其父节点
            relevant_nodes = [target_col] + parents[:memory_limit_nodes - 1]
            sub_edges = [(u, v) for u, v in model.edges() if u in relevant_nodes and v in relevant_nodes]
            model = BayesianNetwork(sub_edges)
            print(f"✅ 优化后网络包含 {len(relevant_nodes)} 个节点")

    # 只保留数据中存在的节点
    available_nodes = [node for node in model.nodes() if node in data.columns]

    # 如果数据中缺少节点，创建子模型
    if len(available_nodes) < len(model.nodes()):
        print(f"⚠️ 警告: 数据中缺少 {len(model.nodes()) - len(available_nodes)} 个节点")
        # 创建子模型
        sub_edges = [(u, v) for u, v in model.edges() if u in available_nodes and v in available_nodes]
        model = BayesianNetwork(sub_edges)
        print(f"✅ 重新构建子模型，包含 {len(available_nodes)} 个节点")

    try:
        # 检查数据中是否包含所有需要的列
        for node in model.nodes():
            if node not in data.columns:
                print(f"❌ 错误: 数据中缺少节点 '{node}'")
                raise ValueError(f"数据中缺少节点 '{node}'")

        model.fit(data, estimator=BayesianEstimator,
                  prior_type=prior_type,
                  equivalent_sample_size=equivalent_sample_size)
        return model
    except MemoryError:
        print("❌ 内存不足，尝试简化学习...")
        try:
            # 尝试使用更简单的先验和更小的样本量
            model.fit(data, estimator=BayesianEstimator,
                      prior_type="dirichlet",
                      pseudo_counts=1)
            return model
        except Exception as e2:
            print(f"❌ 简化学习也失败: {e2}")
            raise
    except Exception as e:
        print(f"❌ 参数学习出错: {e}")
        # 尝试降级学习
        try:
            print("⚠️ 尝试降级学习...")
            model.fit(data, estimator=BayesianEstimator,
                      prior_type="dirichlet",
                      pseudo_counts=1)
            return model
        except Exception as e2:
            print(f"❌ 降级学习也失败: {e2}")
            raise