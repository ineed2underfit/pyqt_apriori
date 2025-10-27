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
from PySide6.QtCore import QObject, Signal

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
mpl.rcParams['font.family'] = 'sans-serif'

# 设置pandas显示选项
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.float_format', '{:.5f}'.format)


class EquipmentAnalyzer(QObject):
    log_message = Signal(str)
    progress_updated = Signal(int, str)
    analysis_succeeded = Signal(object)
    analysis_failed = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.required_cols = ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', '故障类型']
        self.bin_config = {
            'temp': {'bins': None, 'labels': ['极低温', '低温', '中温', '高温', '极高温']},
            'vibration': {'bins': None, 'labels': ['极低振动', '低振动', '中振动', '高振动', '极高振动']},
            'oil_pressure': {'bins': None, 'labels': ['极低油压', '低油压', '中油压', '高油压', '极高油压']},
            'voltage': {'bins': None, 'labels': ['极低电力', '低电力', '中电力', '高电力', '极高电力']},
            'rpm': {'bins': None, 'labels': ['极低转速', '低转速', '中转速', '高转速', '极高转速']}
        }
        self.discretization_method = 'equal_width'  # 默认使用等宽分箱

    def _log(self, message):
        """辅助方法，用于发送日志信号"""
        print(message)  # 保留控制台打印，方便调试
        self.log_message.emit(message)

    def filter_fault_related_rules(self, rules, min_confidence=0.5):
        fault_rules = rules[
            (rules['consequents'].apply(lambda x: '故障_' in list(x)[0] if len(list(x)) > 0 else False)) &
            (~rules['antecedents'].apply(lambda x: any('故障' in item for item in x))) &
            (rules['confidence'] >= min_confidence)
        ].sort_values('lift', ascending=False)
        return fault_rules

    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件 {self.file_path} 未找到。")
        try:
            df_preview = pd.read_csv(self.file_path, nrows=5, encoding='gbk')
        except UnicodeDecodeError:
            try:
                df_preview = pd.read_csv(self.file_path, nrows=5, encoding='utf-8-sig')
            except UnicodeDecodeError:
                try:
                    df_preview = pd.read_csv(self.file_path, nrows=5, encoding='utf-8')
                except:
                    df_preview = pd.read_csv(self.file_path, nrows=5, encoding='latin1', on_bad_lines='skip')

        has_time_column = '时间' in df_preview.columns
        self._log(f"CSV文件列名: {list(df_preview.columns)}")

        try:
            if has_time_column:
                df = pd.read_csv(self.file_path, parse_dates=['时间'], encoding='gbk')
            else:
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
                    df = pd.read_csv(self.file_path, encoding='latin1', on_bad_lines='skip')
        except Exception as e:
            self._log(f"读取CSV文件时出错: {str(e)}")
            df = pd.read_csv(self.file_path, on_bad_lines='skip')

        if df is None or len(df) == 0:
            raise ValueError("无法读取CSV文件或文件为空")

        self._log(f"成功读取CSV文件，包含 {len(df)} 行，{len(df.columns)} 列")
        df = df.drop_duplicates()
        self._log(f"去重后剩余 {len(df)} 行")

        missing = [col for col in self.required_cols if col not in df.columns]
        if missing:
            self._log(f"警告: 缺少必要字段: {missing}")
            self._log(f"可用列: {list(df.columns)}")
            actual_columns = {}
            for req_col in missing:
                matched = False
                for col in df.columns:
                    if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                        self._log(f"将列 '{col}' 映射到必要字段 '{req_col}'")
                        actual_columns[req_col] = col
                        matched = True
                        break
            for req_col, actual_col in actual_columns.items():
                if actual_col != req_col:
                    df[req_col] = df[actual_col]
        return df

    def set_discretization_method(self, method='equal_width'):
        valid_methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        if method not in valid_methods:
            raise ValueError(f"不支持的离散化方法: {method}。支持的方法有: {valid_methods}")
        self.discretization_method = method

    def auto_discretize(self, df, feature, num_bins=5):
        data = df[feature].dropna().values
        if self.discretization_method == 'equal_width':
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
        elif self.discretization_method == 'equal_freq':
            bins = [data.min()] + [np.percentile(data, 100 * i / num_bins) for i in range(1, num_bins)] + [data.max()]
        elif self.discretization_method == 'kmeans':
            kmeans = KMeans(n_clusters=num_bins, random_state=0, n_init='auto').fit(data.reshape(-1, 1))
            centers = sorted(kmeans.cluster_centers_.flatten())
            bins = [data.min()]
            for i in range(len(centers) - 1):
                bins.append((centers[i] + centers[i + 1]) / 2)
            bins.append(data.max())
        elif self.discretization_method == 'quantile':
            bins = [np.percentile(data, q) for q in np.linspace(0, 100, num_bins + 1)]
        elif self.discretization_method == 'std_based':
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
        elif self.discretization_method == 'decision_tree':
            if '故障类型' in df.columns:
                y = df['故障类型'].apply(lambda x: 0 if x == '正常' else 1).values
                dt = DecisionTreeClassifier(max_depth=num_bins, random_state=0)
                dt.fit(data.reshape(-1, 1), y)
                thresholds = []
                tree = dt.tree_
                for i in range(tree.node_count):
                    if tree.children_left[i] != tree.children_right[i]:
                        thresholds.append(tree.threshold[i])
                if len(thresholds) < num_bins - 1:
                    bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
                else:
                    bins = [data.min()] + sorted(thresholds)[:num_bins-1] + [data.max()]
            else:
                bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
        else:
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
        bins = sorted(set(bins))
        if len(bins) < num_bins + 1:
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()
        return bins

    def plot_discretization_performance(self, execution_times, rule_counts, avg_lifts):
        methods = list(execution_times.keys())
        times = [execution_times[m] for m in methods]
        rules = [rule_counts.get(m, 0) for m in methods]
        result_dir = os.path.join(os.path.dirname(self.file_path), "apriori_results")
        os.makedirs(result_dir, exist_ok=True)

        plt.figure(figsize=(12, 6))
        bars = plt.bar(methods, times, color='skyblue')
        plt.xlabel('离散化方法')
        plt.ylabel('执行时间 (秒)')
        plt.title('各离散化方法执行时间对比')
        plt.xticks(rotation=45)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{height:.2f}s', ha='center', va='bottom')
        plt.tight_layout()
        time_plot_path = os.path.join(result_dir, "离散化方法执行时间对比.png")
        plt.savefig(time_plot_path, dpi=300)
        plt.close()
        self._log(f"已生成执行时间对比图表，保存为'{time_plot_path}'")

        methods_with_rules = [m for m, count in zip(methods, rules) if count > 0]
        rules_filtered = [count for count in rules if count > 0]
        if methods_with_rules:
            plt.figure(figsize=(12, 6))
            bars = plt.bar(methods_with_rules, rules_filtered, color='lightgreen')
            plt.xlabel('离散化方法')
            plt.ylabel('生成规则数量')
            plt.title('各离散化方法生成规则数量对比')
            plt.xticks(rotation=45)
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}', ha='center', va='bottom')
            plt.tight_layout()
            rules_plot_path = os.path.join(result_dir, "离散化方法规则数量对比.png")
            plt.savefig(rules_plot_path, dpi=300)
            plt.close()
            self._log(f"已生成规则数量对比图表，保存为'{rules_plot_path}'")

        if methods_with_rules:
            fig, ax1 = plt.subplots(figsize=(14, 8))
            ax2 = ax1.twinx()
            ax1.bar([m for m in methods_with_rules], [execution_times[m] for m in methods_with_rules], alpha=0.7, color='skyblue', label='执行时间')
            ax1.set_xlabel('离散化方法')
            ax1.set_ylabel('执行时间 (秒)', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')
            ax2.plot([m for m in methods_with_rules], [rule_counts.get(m, 0) for m in methods_with_rules], 'ro-', linewidth=2, markersize=8, label='规则数量')
            ax2.set_ylabel('规则数量', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            plt.title('离散化方法性能综合对比（执行时间vs规则数量）')
            plt.xticks(rotation=45)
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper right')
            plt.tight_layout()
            performance_plot_path = os.path.join(result_dir, "离散化方法性能综合对比.png")
            plt.savefig(performance_plot_path, dpi=300)
            plt.close(fig)
            self._log(f"已生成性能综合对比图表，保存为'{performance_plot_path}'")

    def optimize_discretization(self, df, min_support=0.05, min_lift=2.0, min_confidence=0.5):
        methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        best_method, best_rules_count, best_avg_lift, best_bin_config = None, 0, 0, None
        execution_times, rule_counts, avg_lifts = {}, {}, {}

        self._log("\n尝试不同的离散化方法寻找最优故障预测规则...")
        total_methods = len(methods)
        base_progress = 10
        stage_allocation = 50

        for i, method in enumerate(methods):
            self.progress_updated.emit(int(base_progress + ((i / total_methods) * stage_allocation)), f"测试离散化方法: {method}")
            self._log(f"测试离散化方法: {method}")
            start_time = time.time()
            self.set_discretization_method(method)
            for feature in self.bin_config:
                self.bin_config[feature]['bins'] = self.auto_discretize(df, feature)
            processed_df = self.preprocess(df, log_details=False)
            transactions = self.generate_transactions(processed_df)
            te = TransactionEncoder()
            te_ary = te.fit_transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True, max_len=5)
            end_time = time.time()
            execution_times[method] = end_time - start_time
            self._log(f"  方法 {method} 执行时间: {execution_times[method]:.2f} 秒")

            if len(frequent_itemsets) == 0:
                self._log(f"  方法 {method}: 未找到频繁项集")
                rule_counts[method], avg_lifts[method] = 0, 0
                continue

            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
            if len(rules) == 0:
                self._log(f"  方法 {method}: 未找到关联规则")
                rule_counts[method], avg_lifts[method] = 0, 0
                continue

            valid_rules = self.filter_fault_related_rules(rules, min_confidence)
            rules_count = len(valid_rules)
            avg_lift = valid_rules['lift'].mean() if rules_count > 0 else 0
            max_lift = valid_rules['lift'].max() if rules_count > 0 else 0
            rule_counts[method], avg_lifts[method] = rules_count, avg_lift
            self._log(f"  方法 {method}: 找到 {rules_count} 条故障预测规则，平均提升度: {avg_lift:.2f}，最大提升度: {max_lift:.2f}")

            if rules_count > 0 and (rules_count > best_rules_count or (rules_count == best_rules_count and avg_lift > best_avg_lift)):
                best_method, best_rules_count, best_avg_lift = method, rules_count, avg_lift
                best_bin_config = {ft: {'bins': self.bin_config[ft]['bins'].copy(), 'labels': self.bin_config[ft]['labels'].copy()} for ft in self.bin_config}

        self.progress_updated.emit(int(base_progress + stage_allocation), "优化完成，正在生成图表...")
        self._log("\n各离散化方法执行时间统计:")
        for method, exec_time in execution_times.items():
            self._log(f"  {method}: {exec_time:.2f} 秒")
        try:
            self.plot_discretization_performance(execution_times, rule_counts, avg_lifts)
        except Exception as e:
            self._log(f"生成性能对比图表时出错: {str(e)}")
        if best_method:
            self._log(f"\n最佳离散化方法是: {best_method}，生成了 {best_rules_count} 条故障预测规则，平均提升度: {best_avg_lift:.2f}")
            self._log(f"最佳方法 {best_method} 的执行时间: {execution_times[best_method]:.2f} 秒")
            self.discretization_method = best_method
            self.bin_config = best_bin_config
            return best_method, best_bin_config
        else:
            self._log("没有找到产生有效故障预测规则的离散化方法")
            return None, None

    def preprocess(self, df, log_details=True):
        processed = df.copy()
        for col in self.bin_config:
            if self.bin_config[col]['bins'] is None:
                self.bin_config[col]['bins'] = self.auto_discretize(df, col, len(self.bin_config[col]['labels']))
                if log_details:
                    self._log(f"{col} 五等分范围:")
                    labels = self.bin_config[col]['labels']
                    bins = self.bin_config[col]['bins']
                    for i in range(len(labels)):
                        self._log(f"  {labels[i]}: {bins[i]:.2f} - {bins[i + 1]:.2f}")
        for col in self.bin_config:
            processed[col + '_level'] = pd.cut(processed[col], bins=self.bin_config[col]['bins'], labels=self.bin_config[col]['labels'], include_lowest=True)
        processed['department'] = '部门_' + processed['department'].astype(str)
        processed['故障类型'] = processed['故障类型'].apply(lambda x: '正常' if x == '正常' else f'故障_{x}')
        return processed

    def generate_transactions(self, df):
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
                self._log(f"警告: 处理行时出错，跳过: {e}")
                continue
        return features

    def analyze(self, min_support=0.05, min_lift=2.0, min_confidence=0.5, auto_optimize=True):
        try:
            self.progress_updated.emit(5, "正在加载数据...")
            self._log("正在加载数据...")
            raw_df = self.load_data()
            self._log(f"数据加载完成，共 {len(raw_df)} 行")

            if auto_optimize:
                self.progress_updated.emit(10, "正在优化离散化方法...")
                self._log("正在进行离散化方法优化...")
                optimize_start_time = time.time()
                best_method, _ = self.optimize_discretization(raw_df, min_support, min_lift, min_confidence)
                optimize_end_time = time.time()
                optimize_total_time = optimize_end_time - optimize_start_time
                self._log(f"离散化方法优化总耗时: {optimize_total_time:.2f} 秒")
                if best_method:
                    self._log(f"最终选择的离散化方法: {best_method}")

            self.progress_updated.emit(60, "正在预处理数据...")
            self._log("正在预处理数据...")
            processed_df = self.preprocess(raw_df)
            self._log(f"数据预处理完成")

            self.progress_updated.emit(70, "正在生成事务数据...")
            self._log("正在生成事务数据...")
            transactions = self.generate_transactions(processed_df)
            self._log(f"事务数据生成完成，共 {len(transactions)} 个事务")

            self.progress_updated.emit(75, "正在编码和挖掘频繁项集...")
            self._log("正在进行编码...")
            te = TransactionEncoder()
            te_ary = te.fit_transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
            self._log(f"编码完成，特征数量: {len(df_encoded.columns)}")

            self._log(f"正在挖掘频繁项集 (min_support={min_support})...")
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True, max_len=5)
            frequent_items_count = len(frequent_itemsets)
            self._log(f"\n频繁项的数量：{frequent_items_count}")

            if frequent_items_count == 0:
                self._log("警告: 未找到任何频繁项集，请尝试降低min_support值")
                return pd.DataFrame()

            self.progress_updated.emit(90, "正在生成和筛选规则...")
            self._log(f"正在生成关联规则 (min_lift={min_lift})...")
            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
            self._log(f"关联规则生成完成，共找到 {len(rules)} 条规则")

            if len(rules) == 0:
                self._log("警告: 未找到任何关联规则，请尝试降低min_lift值")
                return pd.DataFrame()

            self._log("正在过滤故障预测规则...")
            valid_rules = self.filter_fault_related_rules(rules, min_confidence)
            fault_rules_count = len(valid_rules)
            self._log(f"\n总关联规则数量：{len(rules)}")
            self._log(f"故障预测规则数量：{fault_rules_count}")

            if fault_rules_count == 0:
                self._log("警告: 未找到任何故障预测规则，请尝试降低min_confidence值或检查数据质量")
                return pd.DataFrame()

            self.progress_updated.emit(98, "正在格式化结果...")
            original_rule_count = len(valid_rules)
            results = []
            rule_identifiers = set()

            for _, row in valid_rules.iterrows():
                antecedents = sorted([item.split('=')[1] if '=' in item else item for item in list(row['antecedents'])])
                consequent = list(row['consequents'])[0].split('_')[1]
                rule_text = " ∧ ".join(antecedents) + " → " + consequent
                rule_id = (frozenset(antecedents), consequent)
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
            result_df = result_df.sort_values(by='原始提升度', ascending=False)
            if '原始提升度' in result_df.columns:
                result_df = result_df.drop(columns=['原始提升度'])

            self._log(f"分析完成，共生成 {len(result_df)} 条故障预测规则 (原始有效规则: {original_rule_count})")
            self.progress_updated.emit(100, "分析完成")
            return result_df

        except Exception as e:
            import traceback
            self._log(f"错误: 分析过程中出现异常: {str(e)}")
            traceback.print_exc()
            self.analysis_failed.emit(f"分析失败: {str(e)}")
            return pd.DataFrame()

if __name__ == "__main__":
    import os
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "training_dataset.csv")
    try:
        total_start_time = time.time()  # 记录总运行开始时间
        
        # file_path = r'相对路径已使用，无需硬编码绝对路径'
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
