# Bayesian/other_parameter_learning.py

from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator, ExpectationMaximization
import pandas as pd
import numpy as np


def learn_parameters_mle(model: BayesianNetwork, data: pd.DataFrame) -> BayesianNetwork:
    """
    使用最大似然估计 (MLE) 方法学习贝叶斯网络参数。

    MLE 通过计算训练数据中每个状态组合的频率来直接估计条件概率。
    该方法计算速度快，但要求输入数据是完整的（无缺失值）。

    Args:
        model: 待学习参数的贝叶斯网络结构。
         用于学习的离散化后的完整训练数据。

    Returns:
        已学习好参数的贝叶斯网络模型。
    """
    print("🔍 使用 MLE (最大似然估计) 方法进行参数学习...")
    try:
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        print("✅ MLE 参数学习完成")
    except Exception as e:
        print(f"❌ MLE 参数学习失败: {e}")
        raise e
    return model


def learn_parameters_em(model: BayesianNetwork, data: pd.DataFrame,
    max_iter: int = 100) -> BayesianNetwork:
    """
    使用期望最大化 (EM) 算法学习贝叶斯网络参数。

    EM 是一种迭代算法，用于处理包含缺失值的数据。它通过在“期望步”(E-step)
    估计缺失值的期望，并在“最大化步”(M-step) 使用完整数据更新模型参数，
    反复迭代直至收敛。

    注意: 不同版本的 pgmpy，ExpectationMaximization 的 API 可能不同。
    本实现移除了 'tol' 参数，以兼容较新或较旧的 pgmpy 版本。
    收敛性由算法内部逻辑或 max_iter 控制。

    Args:
        model: 待学习参数的贝叶斯网络结构。
         用于学习的数据（缺失值需用 np.nan 表示）。
        max_iter: 最大迭代次数，默认为 100。

    Returns:
        已学习好参数的贝叶斯网络模型。
    """
    print(f"🔍 使用 EM (期望最大化) 算法进行参数学习...")
    print(f"    - 最大迭代次数: {max_iter}")

    try:
        # 创建 EM 估计器实例
        em_estimator = ExpectationMaximization(model, data)

        # --- 修正：仅传入 max_iter 参数 ---
        # 根据错误信息，当前 pgmpy 版本的 get_parameters() 不接受 'tol'
        cpds_list = em_estimator.get_parameters(max_iter=max_iter)
        # --- 修正：仅传入 max_iter 参数 ---

        # 将学习到的 CPD 列表添加到模型中
        model.add_cpds(*cpds_list)

        # 验证模型
        if not model.check_model():
            print("⚠️ 警告: EM 学习后的模型 CPD 验证未通过。")

        print("✅ EM 参数学习完成")
    except Exception as e:
        print(f"❌ EM 参数学习失败: {e}")
        raise e
    return model