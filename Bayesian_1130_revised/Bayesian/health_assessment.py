import pandas as pd
import numpy as np
import json
import re
from scipy.spatial.distance import mahalanobis


class HealthAssessor:
    def __init__(self, data_path, binning_config_path, rules_csv_path):
        # 权重配置: [CI(概率), FMI(距离), RI(抗扰), RSI(规则)]
        self.weights = [0.20, 0.30, 0.20, 0.30]

        # 1. 加载配置
        with open(binning_config_path, 'r', encoding='utf-8') as f:
            self.binning_config = json.load(f)

        dataset_config = self.binning_config['metadata']['dataset_config']
        self.numerical_cols = dataset_config['numerical_cols']
        self.categorical_cols = dataset_config['categorical_cols']
        self.target_col = dataset_config['target_col']
        self.normal_val = dataset_config['normal_value']

        # 2. 加载历史数据 (用于 FMI)
        self.raw_data = pd.read_csv(data_path)

        # 3. 加载并解析 CSV 规则 (用于 RSI)
        self.rules_csv_path = rules_csv_path
        self.normal_rules = []
        self._load_csv_rules()

        # 初始化占位符
        self.mu_N = None
        self.inv_cov_matrix = None
        self.max_dist = 1.0
        self.valid_columns = []
        self.feature_columns = []

        # 4. 建立基准
        self._prepare_baselines()

    def _load_csv_rules(self):
        """
        从CSV加载规则，并筛选出指向 '正常' 的规则
        """
        try:
            df = pd.read_csv(self.rules_csv_path)
            # 确保列名正确 (去除可能的空格)
            df.columns = [c.strip() for c in df.columns]

            print(f"\n[规则加载] 从 CSV 读取了 {len(df)} 条规则...")

            # 筛选后件为正常的规则
            # 假设规则格式为 "A ∧ B → 正常"
            target_str = f"→ {self.normal_val}"
            normal_df = df[df['规则'].str.contains(target_str, regex=False)].copy()

            parsed_rules = []
            for _, row in normal_df.iterrows():
                rule_str = row['规则']
                # 解析前件: "A ∧ B → C" -> "A ∧ B"
                antecedent_part = rule_str.split('→')[0].strip()
                # 分割条件
                conditions = [c.strip() for c in antecedent_part.split('∧')]

                parsed_rules.append({
                    'original_rule': rule_str,
                    'conditions': conditions,
                    'confidence': row['置信度'],
                    'lift': row['提升度'],
                    'weight': row['置信度'] * row['提升度']  # 规则权重
                })

            # 按权重降序排列
            self.normal_rules = sorted(parsed_rules, key=lambda x: x['weight'], reverse=True)
            print(f"[规则加载] 筛选出指向 '{self.normal_val}' 的规则共 {len(self.normal_rules)} 条。")

            # 【关键优化】计算 RSI 的饱和阈值
            # 只要命中的规则权重之和，达到前5条最强规则的总和，就认为是满分
            # 避免规则太多导致分母无限大
            top_n = min(5, len(self.normal_rules))
            self.saturation_threshold = sum([r['weight'] for r in self.normal_rules[:top_n]])
            if self.saturation_threshold == 0: self.saturation_threshold = 1.0
            # print(f"[调试] RSI 满分阈值 (Top-{top_n} Sum): {self.saturation_threshold:.2f}")

        except Exception as e:
            print(f"[错误] 加载规则CSV失败: {e}")
            self.normal_rules = []

    def _prepare_baselines(self):
        # A. 筛选正常样本
        self.normal_data = self.raw_data[self.raw_data[self.target_col] == self.normal_val].copy()

        if len(self.normal_data) < 2:
            print(f"!!! 警告: 正常样本不足，无法计算 FMI。")
            return

        # B. 打印 One-Hot 特征检查 (专门解决 Department 问题)
        print("-" * 50)
        print(f"[基准检查] 历史正常样本中的分类特征分布:")
        for col in self.categorical_cols:
            unique_vals = self.normal_data[col].unique()
            print(f"  * {col} (正常态包含): {unique_vals}")
            # 这里你可以一眼看出 '维修部C' 是否在列表里
        print("-" * 50)

        # C. 特征工程
        feature_data = self.normal_data[self.numerical_cols + self.categorical_cols]
        feature_data = feature_data.fillna(0)
        self.encoded_df = pd.get_dummies(feature_data, columns=self.categorical_cols)

        # 剔除方差为0的列
        self.valid_columns = self.encoded_df.columns[self.encoded_df.std() > 1e-6].tolist()
        self.encoded_df = self.encoded_df[self.valid_columns]

        # 同步给外部调用的接口
        self.feature_columns = self.valid_columns

        # D. 计算矩阵参数
        self.mu_N = self.encoded_df.mean().values
        cov_matrix = self.encoded_df.cov().values
        cov_matrix = np.nan_to_num(cov_matrix, nan=0.0)

        try:
            self.inv_cov_matrix = np.linalg.inv(cov_matrix)
        except np.linalg.LinAlgError:
            self.inv_cov_matrix = np.linalg.pinv(cov_matrix)

        dists = []
        for row in self.encoded_df.values:
            d = mahalanobis(row, self.mu_N, self.inv_cov_matrix)
            if not np.isnan(d): dists.append(d)

        self.max_dist = np.max(dists) if dists else 1.0

        # E. 评分阈值 (动态计算)
        if dists:
            # 宽松一点的 FMI 评分映射
            fmis = [max(0.0, 1 - d / (self.max_dist * 1.2)) * 100 for d in dists]
            self.thresholds = {
                'A+': 85, 'A': 75, 'B': 60  # 固定阈值可能更直观
            }
        else:
            self.thresholds = {'A+': 90, 'A': 75, 'B': 60}

    def calculate_fmi(self, raw_input_dict):
        if self.mu_N is None: return 0.0

        df = pd.DataFrame([raw_input_dict])
        for col in self.categorical_cols:
            if col not in df.columns: df[col] = raw_input_dict.get(col)

        encoded_input = pd.get_dummies(df[self.numerical_cols + self.categorical_cols],
                                       columns=self.categorical_cols)

        # 对齐列
        for col in self.valid_columns:
            if col not in encoded_input.columns: encoded_input[col] = 0
        encoded_input = encoded_input[self.valid_columns]

        try:
            input_vec = encoded_input.values[0]
            dist = mahalanobis(input_vec, self.mu_N, self.inv_cov_matrix)
            if np.isnan(dist): return 0.0

            # 稍微放宽惩罚，使得接近边界的值也能得分
            fmi = max(0.0, 1 - (dist / (self.max_dist * 1.5)))
            return fmi
        except:
            return 0.0

    def calculate_rsi(self, discrete_input_dict):
        """
        基于 CSV 解析的规则进行匹配
        """
        if not self.normal_rules: return 0.0

        matched_weight = 0.0
        hit_rules_count = 0

        # 调试用：记录输入特征的集合表示
        # 将 {'气压': '高气压', 'department': '维修部C'} 转换为集合 {'高气压', 'department_维修部C'}
        input_features = set()
        for k, v in discrete_input_dict.items():
            # 处理数值离散化特征
            input_features.add(str(v))
            # 处理分类特征 (CSV里的规则通常带有前缀，如 department_生产部A)
            input_features.add(f"{k}_{v}")

        # 遍历所有正常规则
        for rule in self.normal_rules:
            # 检查规则的所有条件是否都在输入特征中
            # 规则条件示例: ['department_生产部C', '低露点']

            is_match = True
            for condition in rule['conditions']:
                # 模糊匹配：只要条件字符串出现在输入特征集合的任何元素中即可
                # (CSV里的 '低露点' 对应输入的 '低露点')
                condition_met = False
                for feat in input_features:
                    if condition == feat:
                        condition_met = True
                        break
                if not condition_met:
                    is_match = False
                    break

            if is_match:
                matched_weight += rule['weight']
                hit_rules_count += 1
                # print(f"  [命中] {rule['original_rule']}")

        # 计算得分：命中总权重 / 饱和阈值 (最高 1.0)
        rsi = min(1.0, matched_weight / self.saturation_threshold)

        # if hit_rules_count == 0:
        #     print(f"  [提示] 未命中任何 CSV 规则。输入特征集: {input_features}")

        return rsi

    def calculate_ri(self, raw_input, predict_callback, discretize_callback, K=5):
        if not raw_input: return 0.0
        probs_sum = 0.0
        valid_k = 0
        for k in range(K):
            perturbed = raw_input.copy()
            for col in self.numerical_cols:
                val = perturbed.get(col, 0)
                # 减小扰动幅度，避免跳变太剧烈
                perturbed[col] = val * (1 + 0.03 * np.random.randn())
            try:
                disc = discretize_callback(perturbed)
                prob = predict_callback(disc)
                probs_sum += prob
                valid_k += 1
            except:
                pass

        return probs_sum / valid_k if valid_k > 0 else 0

    def assess(self, raw_input, discrete_input, base_prob, predict_cb, disc_cb):
        ci = base_prob
        fmi = self.calculate_fmi(raw_input)
        ri = self.calculate_ri(raw_input, predict_cb, disc_cb)
        rsi = self.calculate_rsi(discrete_input)

        # 加权求和
        score = (self.weights[0] * ci + self.weights[1] * fmi +
                 self.weights[2] * ri + self.weights[3] * rsi) * 100

        return {"score": score, "metrics": {"CI": ci, "FMI": fmi, "RI": ri, "RSI": rsi}}

    def get_grade(self, score):
        if score >= self.thresholds['A+']: return "卓越 (A+)"
        if score >= self.thresholds['A']: return "优秀 (A)"
        if score >= self.thresholds['B']: return "良好 (B)"
        return "合格 (C)"