import numpy as np
import pandas as pd
import os
import time
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator
import networkx as nx
import matplotlib.pyplot as plt
import warnings
import pickle
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
warnings.filterwarnings("ignore")

class BayesianNetworkMLE:
    def __init__(self, data_path, rules_path):
        """
        初始化贝叶斯网络MLE模型
        
        参数:
        data_path: 数据文件路径
        rules_path: 规则文件路径
        """
        self.start_time = time.time()  # 记录开始时间
        self.data_path = data_path
        self.rules_path = rules_path
        self.model = None
        self.data = None
        self.processed_data = None
        self.discretization_method = 'std_based'
        self.rules = None
        self.network_structure = []
        
        # 创建必要的目录
        os.makedirs('../pkl', exist_ok=True)
        os.makedirs('../mle_result', exist_ok=True)
        
        # 定义分箱配置
        self.bin_config = {
            'temp': {'bins': None, 'labels': ['极低温', '低温', '中温', '高温', '极高温']},
            'vibration': {'bins': None, 'labels': ['极低振动', '低振动', '中振动', '高振动', '极高振动']},
            'oil_pressure': {'bins': None, 'labels': ['极低油压', '低油压', '中油压', '高油压', '极高油压']},
            'voltage': {'bins': None, 'labels': ['极低电力', '低电力', '中电力', '高电力', '极高电力']},
            'rpm': {'bins': None, 'labels': ['极低转速', '低转速', '中转速', '高转速', '极高转速']}
        }
        
        # 定义变量名映射
        self.var_mapping = {
            # 状态值到变量名的映射
            '极低温': 'temp', '低温': 'temp', '中温': 'temp', '高温': 'temp', '极高温': 'temp',
            '极低振动': 'vibration', '低振动': 'vibration', '中振动': 'vibration', '高振动': 'vibration', '极高振动': 'vibration',
            '极低油压': 'oil_pressure', '低油压': 'oil_pressure', '中油压': 'oil_pressure', '高油压': 'oil_pressure', '极高油压': 'oil_pressure',
            '极低电力': 'voltage', '低电力': 'voltage', '中电力': 'voltage', '高电力': 'voltage', '极高电力': 'voltage',
            '极低转速': 'rpm', '低转速': 'rpm', '中转速': 'rpm', '高转速': 'rpm', '极高转速': 'rpm',
            # 故障类型映射
            '正常运行': '故障类型', '传动系统异常': '故障类型', '散热系统故障': '故障类型',
            '润滑系统异常': '故障类型', '电力供应故障': '故障类型'
        }
        
    def load_data(self):
        """加载数据"""
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
        """
        基于标准差计算分箱边界
        
        参数:
        data: 输入数据
        num_bins: 分箱数量
        
        返回:
        bins: 分箱边界列表
        """
        mean = np.mean(data)
        std = np.std(data)
        
        if num_bins == 3:
            bins = [data.min(), mean - std, mean + std, data.max()]
        elif num_bins == 5:
            bins = [data.min(), mean - 2*std, mean - std, mean + std, mean + 2*std, data.max()]
        else:
            step = 4 / (num_bins - 1)  # 范围从-2std到+2std
            bins = [mean + (i - (num_bins - 1) / 2) * step * std for i in range(num_bins + 1)]
            bins[0] = data.min()
            bins[-1] = data.max()
            
        # 确保分箱边界单调递增
        bins = np.sort(bins)
        # 处理可能的重复值
        bins = np.unique(bins)
        
        # 如果分箱数量不足，添加额外的边界
        while len(bins) < num_bins + 1:
            # 在最大边界处添加新的边界
            new_bound = bins[-1] + (bins[-1] - bins[-2])
            bins = np.append(bins, new_bound)
            
        return bins.tolist()
        
    def preprocess_data(self):
        """
        数据预处理：对连续变量进行分箱处理
        """
        step_start_time = time.time()
        if self.data is None:
            print("请先加载数据")
            return False
            
        print("开始数据预处理...")
        self.processed_data = self.data.copy()
        
        # 打印数据列名，用于调试
        print("\n数据列名:")
        print(self.data.columns.tolist())
        
        # 移除无关列
        columns_to_keep = ['department', 'temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', '故障类型']
        self.processed_data = self.processed_data[columns_to_keep]
        
        # 对每个变量进行分箱处理
        for var_name, config in self.bin_config.items():
            if var_name in self.data.columns:
                print(f"处理变量: {var_name}")
                # 计算分箱边界
                bins = self._calculate_bins(self.data[var_name], num_bins=len(config['labels']))
                # 更新分箱配置
                self.bin_config[var_name]['bins'] = bins
                # 进行分箱
                self.processed_data[var_name] = pd.cut(
                    self.data[var_name],
                    bins=bins,
                    labels=config['labels'],
                    include_lowest=True
                )
        
        # 处理部门变量
        if 'department' in self.data.columns:
            print("处理部门变量")
            # 将部门变量转换为字符串类型
            self.processed_data['department'] = self.data['department'].astype(str)
            # 添加部门前缀
            self.processed_data['department'] = '部门_' + self.processed_data['department']
            
        print("数据预处理完成")
        print(f"数据预处理耗时: {time.time() - step_start_time:.2f} 秒")
        return True

    def load_rules(self):
        """
        加载并处理规则
        """
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
        """
        处理规则，构建网络结构
        """
        step_start_time = time.time()
        if self.rules is None:
            print("请先加载规则")
            return False
            
        print("开始处理规则...")
        self.network_structure = []
        
        print("\n处理规则:")
        for _, rule in self.rules.iterrows():
            # 解析规则
            antecedent = rule['规则'].split(' → ')[0]
            consequent = rule['规则'].split(' → ')[1]
            print(f"\n规则: {rule['规则']}")
            
            # 处理前因（可能有多个条件）
            conditions = antecedent.split(' ∧ ')
            print(f"前因条件: {conditions}")
            
            # 构建边
            for condition in conditions:
                # 从条件中提取变量名
                if '_' in condition:
                    # 处理部门变量
                    var_name = 'department'  # 使用统一的部门变量名
                else:
                    # 从状态值获取变量名
                    var_name = self.var_mapping.get(condition, condition)
                print(f"条件 '{condition}' 映射为变量 '{var_name}'")
                        
                # 添加边，使用与数据列名一致的节点名
                self.network_structure.append((var_name, '故障类型'))
                
        # 去重
        self.network_structure = list(set(self.network_structure))
        print(f"\n网络结构构建完成，共 {len(self.network_structure)} 条边:")
        for edge in self.network_structure:
            print(f"边: {edge[0]} -> {edge[1]}")
        print(f"规则处理耗时: {time.time() - step_start_time:.2f} 秒")
        return True
        
    def build_network(self):
        """
        构建贝叶斯网络
        """
        step_start_time = time.time()
        if not self.network_structure:
            print("请先处理规则")
            return False
            
        print("开始构建贝叶斯网络...")
        try:
            self.model = BayesianNetwork(ebunch=self.network_structure)
            print("贝叶斯网络构建成功")
            print(f"网络构建耗时: {time.time() - step_start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"网络构建错误: {e}")
            return False

    def visualize_network(self, save_path=None):
        """
        可视化网络结构
        
        参数:
        save_path: 保存图片的路径，如果为None则显示图片
        """
        if self.model is None:
            print("请先构建网络")
            return False
            
        print("开始可视化网络结构...")
        try:
            # 创建有向图
            G = nx.DiGraph()
            
            # 添加边
            G.add_edges_from(self.network_structure)
            
            # 设置图形大小
            plt.figure(figsize=(12, 8))
            
            # 使用spring布局
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # 绘制节点
            nx.draw_networkx_nodes(G, pos, 
                                 node_color='lightblue',
                                 node_size=2000,
                                 alpha=0.7)
            
            # 绘制边
            nx.draw_networkx_edges(G, pos,
                                 edge_color='gray',
                                 arrows=True,
                                 arrowsize=20,
                                 width=2,
                                 alpha=0.6)
            
            # 添加标签
            nx.draw_networkx_labels(G, pos,
                                  font_size=10,
                                  font_family='SimHei')  # 使用中文字体
            
            # 设置标题
            plt.title("贝叶斯网络结构图", fontsize=15, fontfamily='SimHei')
            
            # 去除坐标轴
            plt.axis('off')
            
            # 调整布局
            plt.tight_layout()
            
            # 保存或显示图片
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"网络结构图已保存至: {save_path}")
            else:
                plt.show()
                
            plt.close()
            return True
            
        except Exception as e:
            print(f"网络可视化错误: {e}")
            return False

    def save_model(self):
        """保存模型到pkl文件"""
        if self.model is None:
            print("请先构建并训练模型")
            return False
            
        try:
            # 保存模型
            model_path = os.path.join('../pkl', 'bn_mle_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"模型已保存至: {model_path}")
            return True
        except Exception as e:
            print(f"模型保存错误: {e}")
            return False

    def save_classification_report(self, y_true, y_pred):
        """保存分类报告"""
        try:
            # 生成分类报告
            report = classification_report(y_true, y_pred)
            
            # 计算总体准确率
            accuracy = np.mean(y_true == y_pred)
            
            # 计算混淆矩阵
            cm = confusion_matrix(y_true, y_pred)
            
            # 保存报告
            report_path = os.path.join('../mle_result', 'classification_report.txt')
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

    def plot_confusion_matrix(self, y_true, y_pred):
        """绘制并保存混淆矩阵"""
        try:
            # 计算混淆矩阵
            cm = confusion_matrix(y_true, y_pred)
            
            # 获取唯一的标签
            labels = np.unique(np.concatenate([y_true, y_pred]))
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            
            # 绘制混淆矩阵
            plt.figure(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=labels,
                       yticklabels=labels)
            plt.title('混淆矩阵', fontsize=15)
            plt.xlabel('预测标签', fontsize=12)
            plt.ylabel('真实标签', fontsize=12)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图片
            cm_path = os.path.join('../mle_result', 'confusion_matrix.png')
            plt.savefig(cm_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"混淆矩阵已保存至: {cm_path}")
            return True
        except Exception as e:
            print(f"混淆矩阵保存错误: {e}")
            return False

    def estimate_parameters(self):
        """
        使用MLE方法估计网络参数
        """
        step_start_time = time.time()
        if self.model is None:
            print("请先构建网络")
            return False
            
        if self.processed_data is None:
            print("请先进行数据预处理")
            return False
            
        print("开始进行MLE参数估计...")
        try:
            # 打印数据列名和模型节点，用于调试
            print("\n数据列名:")
            print(self.processed_data.columns.tolist())
            print("\n模型节点:")
            print(self.model.nodes())
            
            # 检查数据中是否包含所有必要的列
            missing_columns = [node for node in self.model.nodes() if node not in self.processed_data.columns]
            if missing_columns:
                print(f"\n错误：数据中缺少以下列: {missing_columns}")
                return False
                
            # 检查数据中是否有模型不需要的列
            extra_columns = [col for col in self.processed_data.columns if col not in self.model.nodes()]
            if extra_columns:
                print(f"\n警告：数据中有模型不需要的列: {extra_columns}")
                # 只保留模型需要的列
                self.processed_data = self.processed_data[self.model.nodes()]
            
            # 创建MLE估计器
            mle = MaximumLikelihoodEstimator(self.model, self.processed_data)
            
            # 估计CPT
            self.model.fit(self.processed_data, estimator=MaximumLikelihoodEstimator)
            
            # 保存模型
            self.save_model()
            
            # 获取预测结果
            y_true = self.processed_data['故障类型'].values
            
            # 创建用于预测的数据（排除目标变量）
            predict_data = self.processed_data.drop('故障类型', axis=1)
            y_pred = self.model.predict(predict_data)[['故障类型']].values.flatten()
            
            # 保存分类报告和混淆矩阵
            self.save_classification_report(y_true, y_pred)
            self.plot_confusion_matrix(y_true, y_pred)
            
            print("MLE参数估计完成")
            print(f"参数估计耗时: {time.time() - step_start_time:.2f} 秒")
            print(f"\n总运行时间: {time.time() - self.start_time:.2f} 秒")
            return True
            
        except Exception as e:
            print(f"参数估计错误: {e}")
            return False

if __name__ == "__main__":
    # 测试代码
    total_start_time = time.time()
    data_path = "../dataset/data_info/training_dataset.csv"
    rules_path = "../dataset/optimal_rules.csv"
    bn = BayesianNetworkMLE(data_path, rules_path)
    if bn.load_data():
        bn.preprocess_data()
        if bn.load_rules():
            bn.process_rules()
            if bn.build_network():
                # 可视化网络结构
                bn.visualize_network(save_path="../mle_result/network_structure.png")
                # 进行参数估计
                bn.estimate_parameters()
    print(f"\n程序总运行时间: {time.time() - total_start_time:.2f} 秒")
