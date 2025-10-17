import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import time
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
mpl.rcParams['font.family'] = 'sans-serif'

# 设置pandas显示选项
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.float_format', '{:.5f}'.format)


class EquipmentAnalyzer:
    def __init__(self, file_path):
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
        self.discretization_method = 'equal_width'  # 默认使用等宽分箱
        
    def filter_fault_related_rules(self, rules, min_confidence=0.5):
        """
        筛选与故障类型相关的规则
        
        Args:
            rules (pandas.DataFrame): 关联规则DataFrame
            min_confidence (float): 最小置信度阈值
            
        Returns:
            pandas.DataFrame: 筛选后的与故障类型相关的规则
        """
        # 筛选条件:
        # 1. 后件(consequents)必须是故障预测(包含"故障_")
        # 2. 前件(antecedents)不应包含故障信息
        # 3. 置信度必须达到最小阈值
        fault_rules = rules[
            (rules['consequents'].apply(lambda x: '故障_' in list(x)[0] if len(list(x)) > 0 else False)) &
            (~rules['antecedents'].apply(lambda x: any('故障' in item for item in x))) &
            (rules['confidence'] >= min_confidence)
        ].sort_values('lift', ascending=False)
        
        return fault_rules

    def load_data(self):
        """
        加载并验证数据

        Returns:
            pandas.DataFrame: 加载并验证后的 DataFrame
        Raises:
            FileNotFoundError: 如果文件未找到
            ValueError: 如果数据中缺少必要字段
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件 {self.file_path} 未找到。")

        # 先尝试不解析日期列读取文件，检查是否有"时间"列
        try:
            # 首先尝试只读取前几行来检查列名
            df_preview = pd.read_csv(self.file_path, nrows=5, encoding='gbk')
        except UnicodeDecodeError:
            try:
                df_preview = pd.read_csv(self.file_path, nrows=5, encoding='utf-8-sig')
            except UnicodeDecodeError:
                try:
                    df_preview = pd.read_csv(self.file_path, nrows=5, encoding='utf-8')
                except:
                    df_preview = pd.read_csv(self.file_path, nrows=5, encoding='latin1', on_bad_lines='skip')

        # 检查是否有时间列
        has_time_column = '时间' in df_preview.columns
        print(f"CSV文件列名: {list(df_preview.columns)}")

        # 读取完整文件
        try:
            if has_time_column:
                # 如果有时间列，解析为日期
                df = pd.read_csv(self.file_path, parse_dates=['时间'], encoding='gbk')
            else:
                # 如果没有时间列，直接读取
                df = pd.read_csv(self.file_path, encoding='gbk')
        except UnicodeDecodeError:
            try:
                if has_time_column:
                    df = pd.read_csv(self.file_path, parse_dates=['时间'], encoding='utf-8-sig')
                else:
                    df = pd.read_csv(self.file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(self.file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    # 如果尝试多种编码都失败，尝试使用更宽松的编码错误处理
                    df = pd.read_csv(self.file_path, encoding='latin1', on_bad_lines='skip')
        except Exception as e:
            print(f"读取CSV文件时出错: {str(e)}")
            # 最后的尝试，不指定解析日期
            df = pd.read_csv(self.file_path, on_bad_lines='skip')

        # 检查数据是否成功加载
        if df is None or len(df) == 0:
            raise ValueError("无法读取CSV文件或文件为空")

        print(f"成功读取CSV文件，包含 {len(df)} 行，{len(df.columns)} 列")

        # 去重操作
        df = df.drop_duplicates()
        print(f"去重后剩余 {len(df)} 行")

        # 验证必要字段
        missing = [col for col in self.required_cols if col not in df.columns]
        if missing:
            print(f"警告: 缺少必要字段: {missing}")
            print(f"可用列: {list(df.columns)}")

            # 尝试根据常见命名匹配列
            actual_columns = {}
            for req_col in missing:
                # 尝试匹配相似列名
                matched = False
                for col in df.columns:
                    # 检查列名是否包含所需字段名（不区分大小写）
                    if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                        print(f"将列 '{col}' 映射到必要字段 '{req_col}'")
                        actual_columns[req_col] = col
                        matched = True
                        break

            # 重命名列
            for req_col, actual_col in actual_columns.items():
                if actual_col != req_col:  # 避免重命名相同的列
                    df[req_col] = df[actual_col]

        return df

    def set_discretization_method(self, method='equal_width'):
        """
        设置离散化方法

        Args:
            method (str): 离散化方法，可选项：
                          'equal_width' - 等宽分箱
                          'equal_freq' - 等频分箱
                          'kmeans' - K均值聚类分箱
                          'quantile' - 分位数分箱
                          'std_based' - 基于标准差分箱
                          'decision_tree' - 基于决策树分箱
        """
        valid_methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        if method not in valid_methods:
            raise ValueError(f"不支持的离散化方法: {method}。支持的方法有: {valid_methods}")
        self.discretization_method = method

    def auto_discretize(self, df, feature, num_bins=5):
        """
        根据选择的方法自动离散化特征

        Args:
            df (pandas.DataFrame): 数据框
            feature (str): 要离散化的特征
            num_bins (int): 分箱数量，默认为5

        Returns:
            list: 分箱边界
        """
        data = df[feature].dropna().values

        if self.discretization_method == 'equal_width':
            # 等宽分箱
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()

        elif self.discretization_method == 'equal_freq':
            # 等频分箱
            bins = [data.min()] + [np.percentile(data, 100 * i / num_bins) for i in range(1, num_bins)] + [data.max()]

        elif self.discretization_method == 'kmeans':
            # 使用K均值聚类进行分箱
            kmeans = KMeans(n_clusters=num_bins, random_state=0).fit(data.reshape(-1, 1))
            centers = sorted(kmeans.cluster_centers_.flatten())
            # 计算相邻中心点的中点作为边界
            bins = [data.min()]
            for i in range(len(centers) - 1):
                bins.append((centers[i] + centers[i + 1]) / 2)
            bins.append(data.max())

        elif self.discretization_method == 'quantile':
            # 基于分位数分箱
            bins = [np.percentile(data, q) for q in np.linspace(0, 100, num_bins + 1)]
            
        elif self.discretization_method == 'std_based':
            # 基于标准差的分箱
            mean = np.mean(data)
            std = np.std(data)
            # 分箱边界为均值±n个标准差
            if num_bins == 3:
                bins = [data.min(), mean - std, mean + std, data.max()]
            elif num_bins == 5:
                bins = [data.min(), mean - 2*std, mean - std, mean + std, mean + 2*std, data.max()]
            else:
                # 对于其他分箱数量，采用均匀分布标准差的方式
                step = 4 / (num_bins - 1)  # 范围从-2std到+2std
                bins = [mean + (i - (num_bins - 1) / 2) * step * std for i in range(num_bins + 1)]
                bins[0] = data.min()
                bins[-1] = data.max()

        elif self.discretization_method == 'decision_tree':
            # 基于决策树的分箱（监督式）
            # 需要有目标变量，这里使用故障类型作为目标
            if '故障类型' in df.columns:
                # 准备目标变量
                y = df['故障类型'].apply(lambda x: 0 if x == '正常' else 1).values
                # 使用决策树划分
                dt = DecisionTreeClassifier(max_depth=num_bins, random_state=0)
                dt.fit(data.reshape(-1, 1), y)
                # 从决策树提取分裂点
                thresholds = []
                tree = dt.tree_
                for i in range(tree.node_count):
                    if tree.children_left[i] != tree.children_right[i]:  # 非叶节点
                        thresholds.append(tree.threshold[i])
                
                # 确保至少有num_bins-1个分裂点
                if len(thresholds) < num_bins - 1:
                    # 如果决策树找不到足够的分裂点，退回到等宽分箱
                    bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
                else:
                    # 排序分裂点并添加最小值和最大值
                    bins = [data.min()] + sorted(thresholds)[:num_bins-1] + [data.max()]
            else:
                # 如果没有故障类型列，退回到等宽分箱
                bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
        else:
            # 默认使用等宽分箱
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()

        # 确保边界唯一
        bins = sorted(set(bins))
        # 如果因为四舍五入导致边界数量不足，重新生成等宽边界
        if len(bins) < num_bins + 1:
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()

        return bins

    def plot_discretization_performance(self, execution_times, rule_counts, avg_lifts):
        """
        生成离散化方法性能对比图表

        Args:
            execution_times (dict): 各方法执行时间
            rule_counts (dict): 各方法生成的规则数量
            avg_lifts (dict): 各方法的平均提升度
        """
        methods = list(execution_times.keys())
        times = [execution_times[m] for m in methods]
        rules = [rule_counts.get(m, 0) for m in methods]
        lifts = [avg_lifts.get(m, 0) for m in methods]

        # 创建图表目录
        result_dir = os.path.join(os.path.dirname(self.file_path), "apriori_results")
        os.makedirs(result_dir, exist_ok=True)

        # 时间对比图
        plt.figure(figsize=(12, 6))
        bars = plt.bar(methods, times, color='skyblue')
        plt.xlabel('离散化方法')
        plt.ylabel('执行时间 (秒)')
        plt.title('各离散化方法执行时间对比')
        plt.xticks(rotation=45)
        
        # 在柱状图上添加数值标签
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.2f}s', ha='center', va='bottom')
            
        plt.tight_layout()
        time_plot_path = os.path.join(result_dir, "离散化方法执行时间对比.png")
        plt.savefig(time_plot_path, dpi=300)
        plt.close()  # 关闭当前图表
        print(f"已生成执行时间对比图表，保存为'{time_plot_path}'")

        # 规则数量对比图
        methods_with_rules = [m for m, count in zip(methods, rules) if count > 0]
        rules_filtered = [count for count in rules if count > 0]
        
        if methods_with_rules:
            plt.figure(figsize=(12, 6))
            bars = plt.bar(methods_with_rules, rules_filtered, color='lightgreen')
            plt.xlabel('离散化方法')
            plt.ylabel('生成规则数量')
            plt.title('各离散化方法生成规则数量对比')
            plt.xticks(rotation=45)
            
            # 在柱状图上添加数值标签
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom')
                
            plt.tight_layout()
            rules_plot_path = os.path.join(result_dir, "离散化方法规则数量对比.png")
            plt.savefig(rules_plot_path, dpi=300)
            plt.close()  # 关闭当前图表
            print(f"已生成规则数量对比图表，保存为'{rules_plot_path}'")

        # 综合性能图（执行时间与规则数量的对比）
        if methods_with_rules:
            # 创建两个Y轴的图表
            fig, ax1 = plt.subplots(figsize=(14, 8))
            ax2 = ax1.twinx()
            
            # 执行时间柱状图（左Y轴）
            bars1 = ax1.bar([m for m in methods_with_rules], 
                           [execution_times[m] for m in methods_with_rules], 
                           alpha=0.7, color='skyblue', label='执行时间')
            ax1.set_xlabel('离散化方法')
            ax1.set_ylabel('执行时间 (秒)', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')
            
            # 规则数量折线图（右Y轴）
            line = ax2.plot([m for m in methods_with_rules], 
                           [rule_counts.get(m, 0) for m in methods_with_rules], 
                           'ro-', linewidth=2, markersize=8, label='规则数量')
            ax2.set_ylabel('规则数量', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            
            plt.title('离散化方法性能综合对比（执行时间vs规则数量）')
            plt.xticks(rotation=45)
            
            # 合并图例
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper right')
            
            plt.tight_layout()
            performance_plot_path = os.path.join(result_dir, "离散化方法性能综合对比.png")
            plt.savefig(performance_plot_path, dpi=300)
            plt.close(fig)  # 关闭当前图表
            print(f"已生成性能综合对比图表，保存为'{performance_plot_path}'")

    def optimize_discretization(self, df, min_support=0.05, min_lift=2.0, min_confidence=0.5):
        """
        尝试不同的离散化方法，找到产生最佳故障预测规则的方法

        Args:
            df (pandas.DataFrame): 数据框
            min_support (float): 最小支持度
            min_lift (float): 最小提升度
            min_confidence (float): 最小置信度

        Returns:
            str: 最佳离散化方法
            dict: 使用最佳方法的分箱配置
        """
        methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        best_method = None
        best_rules_count = 0
        best_avg_lift = 0
        best_bin_config = None
        execution_times = {}  # 用于存储每种方法的执行时间
        rule_counts = {}      # 用于存储每种方法生成的规则数量
        avg_lifts = {}        # 用于存储每种方法的平均提升度

        print("\n尝试不同的离散化方法寻找最优故障预测规则...")

        for method in methods:
            print(f"测试离散化方法: {method}")
            start_time = time.time()  # 开始计时
            self.set_discretization_method(method)

            # 为每个特征自动计算分箱边界
            for feature in self.bin_config:
                self.bin_config[feature]['bins'] = self.auto_discretize(df, feature)

            # 进行分析
            processed_df = self.preprocess(df)
            transactions = self.generate_transactions(processed_df)

            # 矩阵编码
            te = TransactionEncoder()
            te_ary = te.fit_transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

            # 挖掘频繁项集
            frequent_itemsets = apriori(
                df_encoded,
                min_support=min_support,
                use_colnames=True,
                max_len=5
            )

            end_time = time.time()  # 结束计时
            execution_time = end_time - start_time
            execution_times[method] = execution_time
            print(f"  方法 {method} 执行时间: {execution_time:.2f} 秒")

            if len(frequent_itemsets) == 0:
                print(f"  方法 {method}: 未找到频繁项集")
                rule_counts[method] = 0
                avg_lifts[method] = 0
                continue

            # 生成关联规则
            rules = association_rules(
                frequent_itemsets,
                metric="lift",
                min_threshold=min_lift
            )

            if len(rules) == 0:
                print(f"  方法 {method}: 未找到关联规则")
                rule_counts[method] = 0
                avg_lifts[method] = 0
                continue

            # 过滤与故障类型相关的规则
            valid_rules = self.filter_fault_related_rules(rules, min_confidence)

            rules_count = len(valid_rules)
            avg_lift = valid_rules['lift'].mean() if rules_count > 0 else 0
            max_lift = valid_rules['lift'].max() if rules_count > 0 else 0

            # 保存此方法的规则数量和平均提升度
            rule_counts[method] = rules_count
            avg_lifts[method] = avg_lift

            print(f"  方法 {method}: 找到 {rules_count} 条故障预测规则，平均提升度: {avg_lift:.2f}，最大提升度: {max_lift:.2f}")

            # 评估是否是最佳方法 (优先考虑规则数量，其次考虑平均提升度)
            if rules_count > 0 and (rules_count > best_rules_count or
                                    (rules_count == best_rules_count and avg_lift > best_avg_lift)):
                best_method = method
                best_rules_count = rules_count
                best_avg_lift = avg_lift
                best_bin_config = {}
                for feature in self.bin_config:
                    best_bin_config[feature] = {
                        'bins': self.bin_config[feature]['bins'].copy(),
                        'labels': self.bin_config[feature]['labels'].copy()
                    }

        # 输出所有方法的执行时间
        print("\n各离散化方法执行时间统计:")
        for method, exec_time in execution_times.items():
            print(f"  {method}: {exec_time:.2f} 秒")
        
        # 生成性能对比图表
        try:
            self.plot_discretization_performance(execution_times, rule_counts, avg_lifts)
        except Exception as e:
            print(f"生成性能对比图表时出错: {str(e)}")
        
        if best_method:
            print(f"\n最佳离散化方法是: {best_method}，生成了 {best_rules_count} 条故障预测规则，平均提升度: {best_avg_lift:.2f}")
            print(f"最佳方法 {best_method} 的执行时间: {execution_times[best_method]:.2f} 秒")
            self.discretization_method = best_method
            self.bin_config = best_bin_config
            return best_method, best_bin_config
        else:
            print("没有找到产生有效故障预测规则的离散化方法")
            return None, None

    def preprocess(self, df):
        """
        数据预处理

        Args:
            df (pandas.DataFrame): 原始数据 DataFrame

        Returns:
            pandas.DataFrame: 预处理后的 DataFrame
        """
        processed = df.copy()

        # 如果bin_config中的bins为None，则自动计算
        for col in self.bin_config:
            if self.bin_config[col]['bins'] is None:
                self.bin_config[col]['bins'] = self.auto_discretize(df, col, len(self.bin_config[col]['labels']))
                print(f"{col} 五等分范围:")
                labels = self.bin_config[col]['labels']
                bins = self.bin_config[col]['bins']
                for i in range(len(labels)):
                    print(f"  {labels[i]}: {bins[i]:.2f} - {bins[i + 1]:.2f}")

        # 离散化数值特征
        for col in self.bin_config:
            processed[col + '_level'] = pd.cut(
                processed[col],
                bins=self.bin_config[col]['bins'],
                labels=self.bin_config[col]['labels'],
                include_lowest=True
            )

        # 构建事务项
        processed['department'] = '部门_' + processed['department'].astype(str)
        processed['故障类型'] = processed['故障类型'].apply(lambda x: '正常' if x == '正常' else f'故障_{x}')

        return processed

    def generate_transactions(self, df):
        """
        生成事务型数据

        Args:
            df (pandas.DataFrame): 预处理后的 DataFrame

        Returns:
            list: 事务列表，每个事务是一个物品列表
        """
        features = []
        for row in df.itertuples():
            try:
                transaction = [
                    getattr(row, 'department'),
                    f"temp={getattr(row, 'temp_level')}",
                    f"vibration={getattr(row, 'vibration_level')}",
                    f"voltage={getattr(row, 'voltage_level')}",
                    f"oil_pressure={getattr(row, 'oil_pressure_level')}",
                    f"rpm={getattr(row, 'rpm_level')}",
                    getattr(row, '故障类型')
                ]
                features.append([item for item in transaction if not pd.isna(item)])
            except AttributeError as e:
                print(f"警告: 处理行时出错，跳过: {e}")
                continue
        return features

    def analyze(self, min_support=0.05, min_lift=2.0, min_confidence=0.5, auto_optimize=True):
        """
        执行关联分析

        Args:
            min_support (float): 频繁项集的最小支持度阈值，默认为 0.05
            min_lift (float): 关联规则的最小提升度阈值，默认为 2.0
            min_confidence (float): 最小置信度阈值，默认为 0.5
            auto_optimize (bool): 是否自动优化离散化方法，默认为True

        Returns:
            pandas.DataFrame: 包含有效关联规则的 DataFrame，列有 '规则'、'支持度'、'置信度' 和 '提升度'
        """
        try:
            # 数据准备
            print("正在加载数据...")
            raw_df = self.load_data()
            print(f"数据加载完成，共 {len(raw_df)} 行")

            # 是否自动优化离散化
            if auto_optimize:
                print("正在进行离散化方法优化...")
                optimize_start_time = time.time()
                best_method, _ = self.optimize_discretization(raw_df, min_support, min_lift, min_confidence)
                optimize_end_time = time.time()
                optimize_total_time = optimize_end_time - optimize_start_time
                print(f"离散化方法优化总耗时: {optimize_total_time:.2f} 秒")
                if best_method:
                    print(f"最终选择的离散化方法: {best_method}")

            print("正在预处理数据...")
            processed_df = self.preprocess(raw_df)
            print(f"数据预处理完成")

            print("正在生成事务数据...")
            transactions = self.generate_transactions(processed_df)
            print(f"事务数据生成完成，共 {len(transactions)} 个事务")

            # 矩阵编码
            print("正在进行编码...")
            te = TransactionEncoder()
            te_ary = te.fit_transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
            print(f"编码完成，特征数量: {len(df_encoded.columns)}")

            # 挖掘频繁项集
            print(f"正在挖掘频繁项集 (min_support={min_support})...")
            frequent_itemsets = apriori(
                df_encoded,
                min_support=min_support,
                use_colnames=True,
                max_len=5
            )

            # 统计频繁项数量
            frequent_items_count = len(frequent_itemsets)
            print(f"\n频繁项的数量：{frequent_items_count}")

            if frequent_items_count == 0:
                print("警告: 未找到任何频繁项集，请尝试降低min_support值")
                return pd.DataFrame()

            # 生成关联规则
            print(f"正在生成关联规则 (min_lift={min_lift})...")
            rules = association_rules(
                frequent_itemsets,
                metric="lift",
                min_threshold=min_lift
            )
            print(f"关联规则生成完成，共找到 {len(rules)} 条规则")

            if len(rules) == 0:
                print("警告: 未找到任何关联规则，请尝试降低min_lift值")
                return pd.DataFrame()

            # 过滤与故障类型相关的规则
            print("正在过滤故障预测规则...")
            valid_rules = self.filter_fault_related_rules(rules, min_confidence)

            # 统计故障相关规则数量
            total_rules = len(rules)
            fault_rules_count = len(valid_rules)
            print(f"\n总关联规则数量：{total_rules}")
            print(f"故障预测规则数量：{fault_rules_count}")

            if fault_rules_count == 0:
                print("警告: 未找到任何故障预测规则，请尝试降低min_confidence值或检查数据质量")
                return pd.DataFrame()

            # 保存过滤后但未格式化的规则数量
            original_rule_count = len(valid_rules)

            # 结果格式化
            results = []
            rule_identifiers = set()  # 用于检测完全相同的规则

            for _, row in valid_rules.iterrows():
                # 对 antecedents 进行排序
                antecedents = sorted([item.split('=')[1] if '=' in item else item
                                      for item in list(row['antecedents'])])
                consequent = list(row['consequents'])[0].split('_')[1]

                # 创建规则文本和规则唯一标识
                rule_text = " ∧ ".join(antecedents) + " → " + consequent  # 使用简单箭头代替双箭头
                rule_id = (frozenset(antecedents), consequent)

                # 跳过重复规则
                if rule_id in rule_identifiers:
                    continue
                rule_identifiers.add(rule_id)

                results.append({
                    '规则': rule_text,
                    '支持度': round(row['support'], 4),
                    '置信度': round(row['confidence'], 4),
                    '提升度': round(row['lift'], 2),
                    '原始提升度': row['lift']
                })

            result_df = pd.DataFrame(results)

            # 直接按原始提升度降序排序
            result_df = result_df.sort_values(by='原始提升度', ascending=False)

            # 删除辅助列
            if '原始提升度' in result_df.columns:
                result_df = result_df.drop(columns=['原始提升度'])

            print(f"分析完成，共生成 {len(result_df)} 条故障预测规则 (原始有效规则: {original_rule_count})")

            # 分析丢失的规则数量
            rules_lost = original_rule_count - len(result_df)
            if rules_lost > 0:
                print(
                    f"注意: 格式化和去重过程中丢失了 {rules_lost} 条规则，这通常是由于多种原始规则组合映射到相同的文本表示")

            return result_df

        except Exception as e:
            print(f"错误: 分析过程中出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()


if __name__ == "__main__":
    import os
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "training_dataset.csv")
    try:
        total_start_time = time.time()  # 记录总运行开始时间
        
        # file_path = r'C:\Users\HP\Desktop\quality\pythonProject\training_dataset.csv'
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在，请检查路径")
            # 尝试查找当前目录下的CSV文件
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
            if csv_files:
                print(f"在当前目录找到以下CSV文件：{csv_files}")
                file_path = csv_files[0]
                print(f"使用 {file_path} 作为替代")
            else:
                print("在当前目录下未找到任何CSV文件")
                exit(1)

        analyzer = EquipmentAnalyzer(file_path)

        # 参数设置建议：
        # 小数据集(1000行)：min_support=0.03
        # 大数据集(1万+行)：min_support=0.01
        # auto_optimize=True会自动尝试不同的分箱方法找出最佳规则
        results = analyzer.analyze(min_support=0.005, min_confidence=0.5, min_lift=1.2, auto_optimize=True)

        if results.empty:
            print("\n未找到符合条件的故障预测规则，请尝试调整参数")
        else:
            print("\n设备故障预测规则分析结果（按关联强度从高到低排列）：")
            print(f"共找到 {len(results)} 条故障预测规则")

            # 设置支持度和置信度显示4位小数
            pd.options.display.float_format = '{:.5f}'.format
            print(results.to_markdown(index=False))

            # 保存结果到CSV文件（使用UTF-8编码确保中文正确显示）
            result_dir = script_dir  # 保存到脚本同目录
            os.makedirs(result_dir, exist_ok=True)
            result_path = os.path.join(result_dir, "故障预测规则.csv")
            results.to_csv(result_path, index=False, encoding='utf-8-sig')
            print(f"结果已保存到 '{result_path}'")

            # 如果需要生成可视化图表
            if len(results) > 0:
                # 展示前10条规则的提升度对比
                plt.figure(figsize=(12, 8))
                top_rules = results.head(min(10, len(results)))
                # 翻转以便最高的显示在顶部
                plt.barh(top_rules['规则'][::-1], top_rules['提升度'][::-1], color='skyblue')
                plt.xlabel('提升度')
                plt.ylabel('故障预测规则')
                plt.title('设备故障预测规则分析 - 提升度排名')
                plt.tight_layout()

                image_path = os.path.join(result_dir, "故障预测规则提升度.png")
                plt.savefig(image_path, dpi=300, bbox_inches='tight')
                plt.close()  # 关闭图表
                print(f"已生成故障预测规则提升度图表，保存为'{image_path}'")
        
        # 输出总运行时间
        total_end_time = time.time()
        total_runtime = total_end_time - total_start_time
        print(f"\n程序总运行时间: {total_runtime:.2f} 秒 ({total_runtime/60:.2f} 分钟)")
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback

        traceback.print_exc()