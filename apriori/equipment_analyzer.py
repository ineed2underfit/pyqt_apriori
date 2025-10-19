from PySide6.QtCore import QObject, Signal
import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import time
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier

class EquipmentAnalyzer(QObject):
    # 定义信号
    log_message = Signal(str)
    progress_updated = Signal(int, str)
    analysis_succeeded = Signal(object)  # 传递DataFrame对象
    analysis_failed = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.required_cols = ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', '故障类型']
        # 所有特征统一使用五等分配置
        self.bin_config = {
            'temp': {'bins': None, 'labels': ['极低温', '低温', '中温', '高温', '极高温']},
            'vibration': {'bins': None, 'labels': ['极低振动', '低振动', '中振动', '高振动', '极高振动']},
            'oil_pressure': {'bins': None, 'labels': ['极低油压', '低油压', '中油压', '高油压', '极高油压']},
            'voltage': {'bins': None, 'labels': ['极低电力', '低电力', '中电力', '高电力', '极高电力']},
            'rpm': {'bins': None, 'labels': ['极低转速', '低转速', '中转速', '高转速', '极高转速']}
        }
        self.discretization_method = 'equal_width'

    def analyze(self, min_support=0.005, min_confidence=0.005, min_lift=1.2):
        try:
            # 阶段1: 数据加载 (10%)
            self.progress_updated.emit(0, "开始加载数据...")
            df = pd.read_csv(self.file_path)
            self.progress_updated.emit(10, "数据加载完成")
            self.log_message.emit(f"成功加载数据集: {self.file_path}")

            # 阶段2: 离散化方法优化 (50%)
            self.progress_updated.emit(10, "开始优化离散化方法...")
            best_method, best_rules = self.optimize_discretization(df, min_support, min_confidence, min_lift)
            self.progress_updated.emit(60, f"最佳离散化方法确定: {best_method}")

            # 阶段3: 数据预处理 (10%)
            self.progress_updated.emit(60, "开始数据预处理...")
            discretized_data = self.preprocess_data(df, best_method)
            self.progress_updated.emit(70, "数据预处理完成")

            # 阶段4: 生成事务 (5%)
            self.progress_updated.emit(70, "正在生成事务...")
            transactions = self.generate_transactions(discretized_data)
            self.progress_updated.emit(75, "事务生成完成")

            # 阶段5: 挖掘频繁项集 (15%)
            self.progress_updated.emit(75, "正在挖掘频繁项集...")
            frequent_itemsets = apriori(transactions, min_support=min_support, use_colnames=True)
            self.progress_updated.emit(90, "频繁项集挖掘完成")

            # 阶段6: 生成规则 (8%)
            self.progress_updated.emit(90, "正在生成关联规则...")
            rules = association_rules(frequent_itemsets, metric="confidence",
                                   min_threshold=min_confidence)
            rules = rules[rules['lift'] >= min_lift]
            self.progress_updated.emit(98, "关联规则生成完成")

            # 阶段7: 结果整理 (2%)
            self.progress_updated.emit(98, "正在整理结果...")
            rules = self.format_rules(rules)
            self.progress_updated.emit(100, "分析完成")

            # 发送成功信号
            self.analysis_succeeded.emit(rules)

        except Exception as e:
            self.analysis_failed.emit(str(e))

    def optimize_discretization(self, df, min_support, min_confidence, min_lift):
        methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        best_method = None
        best_rules = None
        best_lift = 0
        execution_times = {}
        base_progress = 10
        stage_allocation = 50

        for i, method in enumerate(methods):
            start_time = time.time()
            self.log_message.emit(f"正在测试离散化方法: {method}...")

            try:
                # 使用当前方法进行离散化
                discretized_data = self.preprocess_data(df.copy(), method)
                transactions = self.generate_transactions(discretized_data)
                frequent_itemsets = apriori(transactions, min_support=min_support, use_colnames=True)
                rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
                rules = rules[rules['lift'] >= min_lift]

                if len(rules) > 0 and rules['lift'].mean() > best_lift:
                    best_method = method
                    best_rules = rules
                    best_lift = rules['lift'].mean()

                end_time = time.time()
                execution_times[method] = round(end_time - start_time, 2)

                # 更新进度
                current_progress = base_progress + ((i + 1) / len(methods)) * stage_allocation
                self.progress_updated.emit(int(current_progress), f"测试完成: {method}")
                self.log_message.emit(f"{method} 方法执行时间: {execution_times[method]} 秒")

            except Exception as e:
                self.log_message.emit(f"{method} 方法执行失败: {str(e)}")
                execution_times[method] = None

        # 输出优化结果
        self.log_message.emit("\n各离散化方法执行时间统计:")
        for method, time_taken in execution_times.items():
            if time_taken is not None:
                self.log_message.emit(f"  {method}: {time_taken:.2f} 秒")

        if best_method:
            self.log_message.emit(f"\n最佳离散化方法是: {best_method}，生成了 {len(best_rules)} 条故障预测规则，平均提升度: {best_lift:.2f}")
            self.log_message.emit(f"最佳方法 {best_method} 的执行时间: {execution_times[best_method]} 秒")
        else:
            self.analysis_failed.emit("未找到合适的离散化方法")

        return best_method, best_rules

    def format_rules(self, rules):
        """格式化规则输出"""
        formatted_rules = []
        for _, rule in rules.iterrows():
            antecedents = ' ∧ '.join(rule['antecedents'])
            consequents = ' ∧ '.join(rule['consequents'])
            support = rule['support']
            confidence = rule['confidence']
            lift = rule['lift']

            formatted_rule = {
                'rule': f"{antecedents} → {consequents}",
                'support': support,
                'confidence': confidence,
                'lift': lift
            }
            formatted_rules.append(formatted_rule)

        # 按照提升度降序排序
        formatted_rules.sort(key=lambda x: x['lift'], reverse=True)
        return pd.DataFrame(formatted_rules)

    # ... 其他必要的方法 ...
