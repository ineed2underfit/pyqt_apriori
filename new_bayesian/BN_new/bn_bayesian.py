import numpy as np
import pandas as pd
import os
import time
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import BayesianEstimator
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
import pickle
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
warnings.filterwarnings("ignore")

class BayesianNetworkBayesian:
    def __init__(self, data_path, rules_path):
        self.start_time = time.time()
        self.data_path = data_path
        self.rules_path = rules_path
        self.model = None
        self.data = None
        self.processed_data = None
        self.discretization_method = 'std_based'
        self.rules = None
        self.network_structure = []
        os.makedirs('new_bayesian/pkl', exist_ok=True)
        os.makedirs('new_bayesian/result/bayesian_result', exist_ok=True)
        self.bin_config = {
            'temp': {'bins': None, 'labels': ['极低温', '低温', '中温', '高温', '极高温']},
            'vibration': {'bins': None, 'labels': ['极低振动', '低振动', '中振动', '高振动', '极高振动']},
            'oil_pressure': {'bins': None, 'labels': ['极低油压', '低油压', '中油压', '高油压', '极高油压']},
            'voltage': {'bins': None, 'labels': ['极低电力', '低电力', '中电力', '高电力', '极高电力']},
            'rpm': {'bins': None, 'labels': ['极低转速', '低转速', '中转速', '高转速', '极高转速']}
        }
        self.var_mapping = {
            '极低温': 'temp', '低温': 'temp', '中温': 'temp', '高温': 'temp', '极高温': 'temp',
            '极低振动': 'vibration', '低振动': 'vibration', '中振动': 'vibration', '高振动': 'vibration', '极高振动': 'vibration',
            '极低油压': 'oil_pressure', '低油压': 'oil_pressure', '中油压': 'oil_pressure', '高油压': 'oil_pressure', '极高油压': 'oil_pressure',
            '极低电力': 'voltage', '低电力': 'voltage', '中电力': 'voltage', '高电力': 'voltage', '极高电力': 'voltage',
            '极低转速': 'rpm', '低转速': 'rpm', '中转速': 'rpm', '高转速': 'rpm', '极高转速': 'rpm',
            '正常运行': '故障类型', '传动系统异常': '故障类型', '散热系统故障': '故障类型',
            '润滑系统异常': '故障类型', '电力供应故障': '故障类型'
        }

    def load_data(self):
        step_start_time = time.time()
        print(f"正在加载数据: {self.data_path}")
        try:
            self.data = pd.read_csv(self.data_path)
            print(f"数据加载成功，共 {len(self.data)} 条记录，{self.data.columns.size} 个特征")
            print(f"数据加载耗时: {time.time() - step_start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"数据加载错误: {e}")
            return False

    def _calculate_bins(self, data, num_bins=5):
        mean = np.mean(data)
        std = np.std(data)
        if num_bins == 3:
            bins = [data.min(), mean - std, mean + std, data.max()]
        elif num_bins == 5:
            bins = [data.min(), mean - 2*std, mean - std, mean + std, mean + 2*std, data.max()]
        else:
            step = 4 / (num_bins - 1)
            bins = [mean + (i - (num_bins - 1) / 2) * step * std for i in range(num_bins + 1)]
            bins[0] = data.min()
            bins[-1] = data.max()
        bins = np.sort(bins)
        bins = np.unique(bins)
        while len(bins) < num_bins + 1:
            new_bound = bins[-1] + (bins[-1] - bins[-2])
            bins = np.append(bins, new_bound)
        return bins.tolist()

    def preprocess_data(self):
        step_start_time = time.time()
        if self.data is None:
            print("请先加载数据")
            return False
        print("开始数据预处理...")
        self.processed_data = self.data.copy()
        print("\n数据列名:")
        print(self.data.columns.tolist())
        columns_to_keep = ['department', 'temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', '故障类型']
        self.processed_data = self.processed_data[columns_to_keep]
        for var_name, config in self.bin_config.items():
            if var_name in self.data.columns:
                print(f"处理变量: {var_name}")
                bins = self._calculate_bins(self.data[var_name], num_bins=len(config['labels']))
                self.bin_config[var_name]['bins'] = bins
                self.processed_data[var_name] = pd.cut(
                    self.data[var_name],
                    bins=bins,
                    labels=config['labels'],
                    include_lowest=True
                )
        if 'department' in self.data.columns:
            print("处理部门变量")
            self.processed_data['department'] = self.data['department'].astype(str)
            self.processed_data['department'] = '部门_' + self.processed_data['department']
        print("数据预处理完成")
        print(f"数据预处理耗时: {time.time() - step_start_time:.2f} 秒")
        return True

    def load_rules(self):
        step_start_time = time.time()
        print(f"正在加载规则: {self.rules_path}")
        try:
            self.rules = pd.read_csv(self.rules_path)
            print(f"规则加载成功，共 {len(self.rules)} 条规则")
            print(f"规则加载耗时: {time.time() - step_start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"规则加载错误: {e}")
            return False

    def process_rules(self):
        step_start_time = time.time()
        if self.rules is None:
            print("请先加载规则")
            return False
        print("开始处理规则...")
        self.network_structure = []
        print("\n处理规则:")
        for _, rule in self.rules.iterrows():
            antecedent = rule['规则'].split(' → ')[0]
            consequent = rule['规则'].split(' → ')[1]
            print(f"\n规则: {rule['规则']}")
            conditions = antecedent.split(' ∧ ')
            print(f"前因条件: {conditions}")
            for condition in conditions:
                if '_' in condition:
                    var_name = 'department'
                else:
                    var_name = self.var_mapping.get(condition, condition)
                print(f"条件 '{condition}' 映射为变量 '{var_name}'")
                self.network_structure.append((var_name, '故障类型'))
        self.network_structure = list(set(self.network_structure))
        print(f"\n网络结构构建完成，共 {len(self.network_structure)} 条边:")
        for edge in self.network_structure:
            print(f"边: {edge[0]} -> {edge[1]}")
        print(f"规则处理耗时: {time.time() - step_start_time:.2f} 秒")
        return True

    def build_network(self):
        step_start_time = time.time()
        if not self.network_structure:
            print("请先处理规则")
            return False
        print("开始构建贝叶斯网络...")
        try:
            self.model = DiscreteBayesianNetwork(ebunch=self.network_structure)
            print("贝叶斯网络构建成功")
            print(f"网络构建耗时: {time.time() - step_start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"网络构建错误: {e}")
            raise e

    def visualize_network(self, save_path=None):
        if self.model is None:
            print("请先构建网络")
            return False
        print("开始可视化网络结构...")
        try:
            G = nx.DiGraph()
            G.add_edges_from(self.network_structure)
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G, k=1, iterations=50)
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000, alpha=0.7)
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20, width=2, alpha=0.6)
            nx.draw_networkx_labels(G, pos, font_size=10, font_family='SimHei')
            plt.title("贝叶斯网络结构图", fontsize=15, fontfamily='SimHei')
            plt.axis('off')
            plt.tight_layout()
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"网络结构图已保存至: {save_path}")
            else:
                plt.show()
            plt.close()
            return True
        except Exception as e:
            print(f"网络可视化错误: {e}")
            raise e

    def save_model(self):
        if self.model is None:
            print("请先构建并训练模型")
            return False
        try:
            model_path = os.path.join('new_bayesian/pkl', 'bn_bayesian_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump((self.model, self.bin_config), f) # 保存模型和分箱配置
            print(f"模型和分箱配置已保存至: {model_path}")
            return True
        except Exception as e:
            print(f"模型保存错误: {e}")
            return False

    def save_classification_report(self, y_true, y_pred, save_dir):
        try:
            report = classification_report(y_true, y_pred)
            accuracy = np.mean(y_true == y_pred)
            cm = confusion_matrix(y_true, y_pred)
            report_path = os.path.join(save_dir, 'classification_report.txt')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("贝叶斯网络分类报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"总体准确率: {accuracy:.4f}\n\n")
                f.write("分类报告:\n")
                f.write(report)
                f.write("\n混淆矩阵:\n")
                f.write(str(cm))
            print(f"分类报告已保存至: {report_path}")
            return True
        except Exception as e:
            print(f"分类报告保存错误: {e}")
            return False

    def plot_confusion_matrix(self, y_true, y_pred, save_path):
        try:
            cm = confusion_matrix(y_true, y_pred)
            labels = np.unique(np.concatenate([y_true, y_pred]))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            plt.figure(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
            plt.title('混淆矩阵', fontsize=15)
            plt.xlabel('预测标签', fontsize=12)
            plt.ylabel('真实标签', fontsize=12)
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"混淆矩阵已保存至: {save_path}")
            return True
        except Exception as e:
            print(f"混淆矩阵保存错误: {e}")
            raise e

    def estimate_parameters(self, confusion_matrix_save_path, report_save_dir):
        step_start_time = time.time()
        if self.model is None:
            print("请先构建网络")
            return False
        if self.processed_data is None:
            print("请先进行数据预处理")
            return False
        print("开始进行贝叶斯参数估计...")
        try:
            print("\n数据列名:")
            print(self.processed_data.columns.tolist())
            print("\n模型节点:")
            print(self.model.nodes())
            missing_columns = [node for node in self.model.nodes() if node not in self.processed_data.columns]
            if missing_columns:
                print(f"\n错误：数据中缺少以下列: {missing_columns}")
                return False
            extra_columns = [col for col in self.processed_data.columns if col not in self.model.nodes()]
            if extra_columns:
                print(f"\n警告：数据中有模型不需要的列: {extra_columns}")
                self.processed_data = self.processed_data[list(self.model.nodes())]
            bayesian_estimator = BayesianEstimator(self.model, self.processed_data)
            cpd_list = bayesian_estimator.get_parameters(prior_type="BDeu", equivalent_sample_size=10)
            self.model.add_cpds(*cpd_list)
            self.save_model()
            y_true = self.processed_data['故障类型'].values
            predict_data = self.processed_data.drop('故障类型', axis=1)
            y_pred = self.model.predict(predict_data)[['故障类型']].values.flatten()
            self.save_classification_report(y_true, y_pred, report_save_dir)
            self.plot_confusion_matrix(y_true, y_pred, confusion_matrix_save_path)
            print("贝叶斯参数估计完成")
            print(f"参数估计耗时: {time.time() - step_start_time:.2f} 秒")
            print(f"\n总运行时间: {time.time() - self.start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"参数估计错误: {e}")
            import traceback
            traceback.print_exc()
            raise e

def run_analysis(data_path, rules_path, network_structure_save_path, confusion_matrix_save_path, report_save_dir):
    """执行完整的贝叶斯网络分析流程"""
    bn = BayesianNetworkBayesian(data_path, rules_path)
    if bn.load_data():
        bn.preprocess_data()
        if bn.load_rules():
            bn.process_rules()
            if bn.build_network():
                bn.visualize_network(save_path=network_structure_save_path)
                bn.estimate_parameters(confusion_matrix_save_path, report_save_dir)

if __name__ == "__main__":
    base_dir = "E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/new_bayesian/"
    data_path = os.path.join(base_dir, "dataset/data_info/training_dataset.csv")
    rules_path = os.path.join(base_dir, "dataset/optimal_rules.csv")
    network_path = os.path.join(base_dir, "result/bayesian_result/network_structure.png")
    cm_path = os.path.join(base_dir, "result/bayesian_result/confusion_matrix.png")
    report_dir = os.path.join(base_dir, "result/bayesian_result")
    os.makedirs(os.path.dirname(network_path), exist_ok=True)
    run_analysis(data_path, rules_path, network_path, cm_path, report_dir)