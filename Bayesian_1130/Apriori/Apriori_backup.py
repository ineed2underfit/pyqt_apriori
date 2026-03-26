import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import matplotlib as mpl
mpl.use("Agg")  # 使用无界面后端，避免后台线程绘图报错
import matplotlib.pyplot as plt
import os
import time
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier

# 4，5，6，7，8，9，10，11，12，13，14，15，16，17，18，19，20

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
mpl.rcParams['font.family'] = 'sans-serif'

# 设置pandas显示选项
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.float_format', '{:.5f}'.format)


class EquipmentAnalyzer:
    def __init__(self, file_path=None, num_bins=5, dataset_config=None):
        self.file_path = file_path
        self.num_bins = num_bins  # 可配置的分箱个数

        # 数据集配置 - 支持任意数据集
        if dataset_config is None:
            # 默认设备监控数据集配置
            self.dataset_config = {
                'numerical_cols': ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm'],
                'categorical_cols': ['department'],
                'target_col': '故障类型',
                'id_cols': ['timestamp', 'device_id'],  # ID列，不参与分析
                'normal_value': '正常',  # 正常状态的标识
                'col_mapping': {},  # 列名映射，用于适配不同数据集
                'feature_names': {  # 特征中文名称
                    'temp': '温度',
                    'vibration': '振动',
                    'oil_pressure': '油压',
                    'voltage': '电压',
                    'rpm': '转速'
                }
            }
        else:
            self.dataset_config = dataset_config

        # 动态设置必要列
        self.required_cols = (self.dataset_config['numerical_cols'] +
                              self.dataset_config['categorical_cols'] +
                              [self.dataset_config['target_col']])

        # 根据分箱个数动态生成标签
        self.bin_config = self._generate_bin_config(num_bins)
        self.discretization_method = 'equal_width'  # 默认使用等宽分箱
        self.cleaning_report = {}  # 数据清洗报告

        # 关联规则配置
        self.rule_config = {
            'target_in_consequent': True,  # 目标变量是否在后件
            'target_in_antecedent': False,  # 目标变量是否可以在前件
            'rule_pattern': 'prediction',  # 规则模式：'prediction'(预测), 'association'(关联), 'custom'(自定义)
            'custom_filter': None  # 自定义规则筛选函数
        }

    def get_result_dir(self):
        """
        获取结果输出目录（使用相对路径）
        结果目录在项目根目录下的result/apriori_results
        
        Returns:
            str: 结果输出目录路径
        """
        # 获取当前脚本所在目录（Apriori目录）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上找到项目根目录（Apriori的父目录）
        project_root = os.path.dirname(script_dir)
        # 在项目根目录下创建result/apriori_results
        result_dir = os.path.join(project_root, 'result', 'apriori_results')
        return result_dir

    def get_apriori_dir(self):
        """
        获取Apriori目录路径（用于存放JSON配置文件）
        
        Returns:
            str: Apriori目录路径
        """
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return current_dir

    def _generate_bin_config(self, num_bins):
        """
        根据分箱个数动态生成分箱配置

        Args:
            num_bins (int): 分箱个数

        Returns:
            dict: 分箱配置字典
        """

        # 生成通用标签
        def generate_labels(feature_name, num_bins):
            if num_bins == 3:
                return [f'低{feature_name}', f'中{feature_name}', f'高{feature_name}']
            elif num_bins == 5:
                return [f'极低{feature_name}', f'低{feature_name}', f'中{feature_name}', f'高{feature_name}',
                        f'极高{feature_name}']
            else:
                return [f'{feature_name}_等级{i + 1}' for i in range(num_bins)]

        bin_config = {}
        # 动态生成数值特征的分箱配置
        for feature in self.dataset_config['numerical_cols']:
            # 获取特征的中文名称，如果没有则使用英文名
            feature_name = self.dataset_config['feature_names'].get(feature, feature)
            bin_config[feature] = {
                'bins': None,
                'labels': generate_labels(feature_name, num_bins)
            }

        return bin_config

    def interactive_config_setup(self, df):
        """
        交互式配置数据集结构

        Args:
            df (pandas.DataFrame): 数据框

        Returns:
            dict: 用户配置的数据集结构
        """
        print("\n" + "=" * 60)
        print("🔧 交互式数据集配置")
        print("=" * 60)

        print(f"📊 数据概览:")
        print(f"  数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"  列名: {list(df.columns)}")

        # 显示每列的基本信息
        print(f"\n📋 列信息详情:")
        for i, col in enumerate(df.columns):
            dtype = df[col].dtype
            unique_count = df[col].nunique()
            sample_values = df[col].dropna().head(3).tolist()
            print(
                f"  {i + 1:2d}. {col:15s} | 类型: {str(dtype):10s} | 唯一值: {unique_count:5d} | 示例: {sample_values}")

        config = {
            'numerical_cols': [],
            'categorical_cols': [],
            'target_col': None,
            'id_cols': [],
            'normal_value': '正常',
            'col_mapping': {},
            'feature_names': {}
        }

        # 1. 选择目标列
        print(f"\n🎯 步骤1: 选择目标列（要预测的列）")
        while True:
            try:
                target_input = input(f"请输入目标列的序号或列名 (1-{len(df.columns)}): ").strip()
                if target_input.isdigit():
                    target_idx = int(target_input) - 1
                    if 0 <= target_idx < len(df.columns):
                        config['target_col'] = df.columns[target_idx]
                        break
                elif target_input in df.columns:
                    config['target_col'] = target_input
                    break
                else:
                    print("❌ 输入无效，请重新输入")
            except:
                print("❌ 输入格式错误，请重新输入")

        print(f"✅ 目标列设置为: {config['target_col']}")

        # 显示目标列的值分布
        target_values = df[config['target_col']].value_counts()
        print(f"📊 目标列 '{config['target_col']}' 的值分布:")
        for value, count in target_values.head(10).items():
            print(f"    - {value}: {count} ({count / len(df) * 100:.1f}%)")

        # 2. 选择正常值标识
        print(f"\n✅ 步骤2: 选择正常值标识")
        print("可选的值:", list(target_values.index[:5]))
        normal_input = input("请输入正常状态的值（直接回车使用默认值'正常'）: ").strip()
        if normal_input:
            config['normal_value'] = normal_input
        print(f"✅ 正常值设置为: '{config['normal_value']}'")

        # 3. 选择数值列
        print(f"\n📊 步骤3: 选择数值列（用于离散化的连续数值特征）")
        remaining_cols = [col for col in df.columns if col != config['target_col']]
        print("可选列:")
        for i, col in enumerate(remaining_cols):
            dtype = df[col].dtype
            unique_count = df[col].nunique()
            print(f"  {i + 1:2d}. {col:15s} | 类型: {str(dtype):10s} | 唯一值: {unique_count:5d}")

        print("请选择数值列（多个列用逗号分隔，支持中英文逗号）:")
        print("示例: 4,5,6,7 或 安装间隙_mm,阻尼幅值_mV,阻尼频率_Hz")
        num_input = input("数值列: ").strip()

        if num_input:
            # 支持中文逗号和英文逗号
            items = num_input.replace('，', ',').split(',')
            print(f"🔍 解析输入: {items}")  # 调试信息

            for item in items:
                item = item.strip()
                matched = False

                if item.isdigit():
                    idx = int(item) - 1
                    if 0 <= idx < len(remaining_cols):
                        col = remaining_cols[idx]
                        config['numerical_cols'].append(col)
                        config['feature_names'][col] = col
                        print(f"  ✅ 通过序号匹配: {item} → {col}")
                        matched = True
                elif item in remaining_cols:
                    config['numerical_cols'].append(item)
                    config['feature_names'][item] = item
                    print(f"  ✅ 精确匹配: {item}")
                    matched = True
                else:
                    # 模糊匹配列名（处理可能的输入错误）
                    for col in remaining_cols:
                        if item in col or col in item:
                            if col not in config['numerical_cols']:
                                config['numerical_cols'].append(col)
                                config['feature_names'][col] = col
                                print(f"  ✅ 模糊匹配: {item} → {col}")
                                matched = True
                            break

                if not matched:
                    print(f"  ❌ 未找到匹配: '{item}'")

        print(f"✅ 数值列设置为: {config['numerical_cols']}")

        # 4. 选择分类列
        print(f"\n🏷️  步骤4: 选择分类列（离散的分类特征）")
        remaining_cols = [col for col in remaining_cols if col not in config['numerical_cols']]
        if remaining_cols:
            print("剩余可选列:")
            for i, col in enumerate(remaining_cols):
                dtype = df[col].dtype
                unique_count = df[col].nunique()
                print(f"  {i + 1:2d}. {col:15s} | 类型: {str(dtype):10s} | 唯一值: {unique_count:5d}")

            print("请选择分类列（多个列用逗号分隔，支持中英文逗号，直接回车跳过）:")
            print("示例: 1,3 或 department,category")
            cat_input = input("分类列: ").strip()

            if cat_input:
                # 支持中文逗号和英文逗号
                items = cat_input.replace('，', ',').split(',')
                for item in items:
                    item = item.strip()
                    if item.isdigit():
                        idx = int(item) - 1
                        if 0 <= idx < len(remaining_cols):
                            config['categorical_cols'].append(remaining_cols[idx])
                    elif item in remaining_cols:
                        config['categorical_cols'].append(item)
                    else:
                        # 模糊匹配列名
                        for col in remaining_cols:
                            if item in col or col in item:
                                if col not in config['categorical_cols']:
                                    config['categorical_cols'].append(col)
                                break

        print(f"✅ 分类列设置为: {config['categorical_cols']}")

        # 5. 其余列自动设为ID列
        remaining_cols = [col for col in df.columns
                          if col not in config['numerical_cols']
                          and col not in config['categorical_cols']
                          and col != config['target_col']]
        config['id_cols'] = remaining_cols
        print(f"🆔 ID列（不参与分析）: {config['id_cols']}")

        # 6. 确认配置
        print(f"\n📋 配置总结:")
        print(f"  目标列: {config['target_col']}")
        print(f"  正常值: '{config['normal_value']}'")
        print(f"  数值列: {config['numerical_cols']}")
        print(f"  分类列: {config['categorical_cols']}")
        print(f"  ID列: {config['id_cols']}")

        confirm = input("\n确认使用此配置？(y/n，直接回车确认): ").strip().lower()
        if confirm and confirm not in ['y', 'yes', '']:
            print("❌ 配置已取消，将使用自动检测")
            return None

        print("✅ 配置已确认！")
        return config

    def interactive_rule_config(self):
        """
        交互式配置关联规则参数
        """
        print(f"\n" + "=" * 60)
        print("🎯 交互式规则配置")
        print("=" * 60)

        # 1. 选择规则模式
        print("📋 可选的规则模式:")
        print("  1. prediction  - 预测模式（目标变量在后件，用于预测分析）")
        print("  2. association - 关联模式（目标变量可在前件或后件，探索所有关联）")
        print("  3. custom      - 自定义模式（使用自定义筛选函数）")

        strict_target_consequent = False
        while True:
            mode_input = input("请选择规则模式 (1-3，直接回车使用预测模式): ").strip()
            if mode_input == '' or mode_input == '1':
                rule_pattern = 'prediction'
                target_in_consequent = True
                target_in_antecedent = False
                break
            elif mode_input == '2':
                rule_pattern = 'association'
                target_in_consequent = True
                target_in_antecedent = True
                # 询问是否严格限制后件
                strict_input = input("是否严格限制后件只包含目标变量？(y/n，直接回车为否): ").strip().lower()
                strict_target_consequent = strict_input in ['y', 'yes']
                break
            elif mode_input == '3':
                rule_pattern = 'custom'
                target_in_consequent = True
                target_in_antecedent = False
                print("⚠️  自定义模式需要在代码中定义筛选函数")
                break
            else:
                print("❌ 输入无效，请输入 1、2 或 3")

        self.set_rule_config(
            rule_pattern=rule_pattern,
            target_in_consequent=target_in_consequent,
            target_in_antecedent=target_in_antecedent,
            strict_target_consequent=strict_target_consequent
        )

        # 2. 设置分析参数
        print(f"\n📊 分析参数设置:")

        # 最小完整支持度（全局支持度）
        while True:
            try:
                support_input = input("最小完整支持度 (0.001-0.1，直接回车使用0.005): ").strip()
                if support_input == '':
                    min_support = 0.005
                    break
                min_support = float(support_input)
                if 0.001 <= min_support <= 0.1:
                    break
                else:
                    print("❌ 完整支持度应在 0.001-0.1 之间")
            except:
                print("❌ 请输入有效的数字")

        # 最小支持度（故障类型支持度）
        while True:
            try:
                new_support_input = input("最小支持度-规则占该故障类型的占比 (0.1-1.0，直接回车使用0.3): ").strip()
                if new_support_input == '':
                    min_new_support = 0.3
                    break
                min_new_support = float(new_support_input)
                if 0.1 <= min_new_support <= 1.0:
                    break
                else:
                    print("❌ 故障类型支持度应在 0.1-1.0 之间")
            except:
                print("❌ 请输入有效的数字")

        # 最小置信度
        while True:
            try:
                confidence_input = input("最小置信度 (0.1-1.0，直接回车使用0.5): ").strip()
                if confidence_input == '':
                    min_confidence = 0.5
                    break
                min_confidence = float(confidence_input)
                if 0.1 <= min_confidence <= 1.0:
                    break
                else:
                    print("❌ 置信度应在 0.1-1.0 之间")
            except:
                print("❌ 请输入有效的数字")

        # 最小提升度
        while True:
            try:
                lift_input = input("最小提升度 (1.0-5.0，直接回车使用1.2): ").strip()
                if lift_input == '':
                    min_lift = 1.2
                    break
                min_lift = float(lift_input)
                if 1.0 <= min_lift <= 5.0:
                    break
                else:
                    print("❌ 提升度应在 1.0-5.0 之间")
            except:
                print("❌ 请输入有效的数字")

        # 分箱数量
        while True:
            try:
                bins_input = input("分箱数量 (3-10，直接回车使用5): ").strip()
                if bins_input == '':
                    num_bins = 5
                    break
                num_bins = int(bins_input)
                if 3 <= num_bins <= 10:
                    break
                else:
                    print("❌ 分箱数量应在 3-10 之间")
            except:
                print("❌ 请输入有效的整数")

        # 是否自动优化离散化
        optimize_input = input("是否自动优化离散化方法？(y/n，直接回车为是): ").strip().lower()
        auto_optimize = optimize_input in ['', 'y', 'yes']

        print(f"\n✅ 参数配置完成:")
        print(f"  规则模式: {rule_pattern}")
        print(f"  最小完整支持度: {min_support}")
        print(f"  最小支持度（故障类型占比）: {min_new_support}")
        print(f"  最小置信度: {min_confidence}")
        print(f"  最小提升度: {min_lift}")
        print(f"  分箱数量: {num_bins}")
        print(f"  自动优化: {'是' if auto_optimize else '否'}")

        # 更新分箱数量
        self.num_bins = num_bins
        self.bin_config = self._generate_bin_config(num_bins)

        return {
            'min_support': min_support,
            'min_new_support': min_new_support,
            'min_confidence': min_confidence,
            'min_lift': min_lift,
            'auto_optimize': auto_optimize
        }

    def auto_detect_dataset_structure(self, df):
        """
        自动检测数据集结构并生成配置

        Args:
            df (pandas.DataFrame): 数据框

        Returns:
            dict: 自动生成的数据集配置
        """
        print("\n🔍 自动检测数据集结构...")

        auto_config = {
            'numerical_cols': [],
            'categorical_cols': [],
            'target_col': None,
            'id_cols': [],
            'normal_value': '正常',
            'col_mapping': {},
            'feature_names': {}
        }

        # 检测各类型列
        for col in df.columns:
            col_lower = col.lower()

            # 检测ID列（通常包含id、时间等关键词）
            if any(keyword in col_lower for keyword in ['id', 'time', 'timestamp', '时间', '编号']):
                auto_config['id_cols'].append(col)
                print(f"  🆔 检测到ID列: {col}")

            # 检测目标列（通常包含故障、类型、标签等关键词）
            elif any(keyword in col_lower for keyword in ['故障', 'fault', 'label', 'class', 'target', '类型', '标签']):
                auto_config['target_col'] = col
                print(f"  🎯 检测到目标列: {col}")

            # 检测数值列
            elif pd.api.types.is_numeric_dtype(df[col]):
                # 检查是否为连续数值（唯一值数量 > 10）
                unique_count = df[col].nunique()
                if unique_count > 10:
                    auto_config['numerical_cols'].append(col)
                    # 生成中文特征名
                    auto_config['feature_names'][col] = col
                    print(f"  📊 检测到数值列: {col} (唯一值: {unique_count})")
                else:
                    auto_config['categorical_cols'].append(col)
                    print(f"  🏷️  检测到分类列: {col} (唯一值: {unique_count})")

            # 检测分类列
            else:
                unique_count = df[col].nunique()
                if unique_count < len(df) * 0.5:  # 唯一值少于总数的50%
                    auto_config['categorical_cols'].append(col)
                    print(f"  🏷️  检测到分类列: {col} (唯一值: {unique_count})")
                else:
                    auto_config['id_cols'].append(col)
                    print(f"  🆔 可能的ID列: {col} (唯一值过多)")

        # 如果没有检测到目标列，尝试从最后几列中找
        if auto_config['target_col'] is None:
            for col in reversed(df.columns):
                if col not in auto_config['id_cols'] and not pd.api.types.is_numeric_dtype(df[col]):
                    auto_config['target_col'] = col
                    print(f"  🎯 推测目标列: {col}")
                    break

        # 检测正常值标识
        if auto_config['target_col']:
            target_values = df[auto_config['target_col']].value_counts()
            print(f"  📋 目标列 '{auto_config['target_col']}' 的值分布:")
            for value, count in target_values.head(10).items():
                print(f"    - {value}: {count} ({count / len(df) * 100:.1f}%)")

            # 尝试识别正常值
            for value in target_values.index:
                if any(keyword in str(value).lower() for keyword in ['正常', 'normal', 'ok', '0']):
                    auto_config['normal_value'] = value
                    print(f"  ✅ 检测到正常值标识: '{value}'")
                    break

        return auto_config

    def set_dataset_config(self, dataset_config):
        """
        设置数据集配置

        Args:
            dataset_config (dict): 数据集配置字典
        """
        self.dataset_config = dataset_config
        self.required_cols = (self.dataset_config['numerical_cols'] +
                              self.dataset_config['categorical_cols'] +
                              [self.dataset_config['target_col']])
        # 重新生成分箱配置
        self.bin_config = self._generate_bin_config(self.num_bins)
        print("✅ 数据集配置已更新")

    def set_rule_config(self, rule_pattern='prediction', target_in_consequent=True,
                        target_in_antecedent=False, custom_filter=None, strict_target_consequent=False):
        """
        设置关联规则配置

        Args:
            rule_pattern (str): 规则模式 - 'prediction', 'association', 'custom'
            target_in_consequent (bool): 目标变量是否在后件
            target_in_antecedent (bool): 目标变量是否可以在前件
            custom_filter (function): 自定义规则筛选函数
            strict_target_consequent (bool): 是否严格限制后件只包含目标变量
        """
        self.rule_config = {
            'rule_pattern': rule_pattern,
            'target_in_consequent': target_in_consequent,
            'target_in_antecedent': target_in_antecedent,
            'custom_filter': custom_filter,
            'strict_target_consequent': strict_target_consequent
        }
        print(f"✅ 关联规则配置已更新: {rule_pattern} 模式")

    def detect_data_quality_issues(self, df):
        """
        检测数据质量问题

        Args:
            df (pandas.DataFrame): 原始数据

        Returns:
            dict: 数据质量问题报告
        """
        print("\n=== 数据质量检测 ===")
        issues = {}

        # 1. 检测缺失值
        missing_data = df.isnull().sum()
        missing_cols = missing_data[missing_data > 0]
        if len(missing_cols) > 0:
            issues['missing_values'] = missing_cols.to_dict()
            print(f"🔍 发现缺失值:")
            for col, count in missing_cols.items():
                percentage = (count / len(df)) * 100
                print(f"  - {col}: {count} 个缺失值 ({percentage:.2f}%)")
        else:
            print("✅ 未发现缺失值")

        # 2. 检测重复行
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            issues['duplicates'] = duplicate_count
            print(f"🔍 发现重复行: {duplicate_count} 行 ({(duplicate_count / len(df) * 100):.2f}%)")
        else:
            print("✅ 未发现重复行")

        # 3. 检测异常值（针对数值列）
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        outliers_info = {}

        for col in numerical_cols:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    outliers_info[col] = {
                        'count': len(outliers),
                        'percentage': (len(outliers) / len(df)) * 100,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound,
                        'min_value': df[col].min(),
                        'max_value': df[col].max()
                    }

        if outliers_info:
            issues['outliers'] = outliers_info
            print(f"📊 检测到异常值（仅报告，不处理）:")
            for col, info in outliers_info.items():
                print(f"  - {col}: {info['count']} 个异常值 ({info['percentage']:.2f}%)")
                print(f"    统计范围: [{info['lower_bound']:.2f}, {info['upper_bound']:.2f}]")
                print(f"    实际范围: [{info['min_value']:.2f}, {info['max_value']:.2f}]")
        else:
            print("✅ 未发现明显异常值")

        # 4. 检测数据类型问题
        type_issues = {}
        for col in df.columns:
            if col in self.dataset_config['numerical_cols']:
                # 数值列应该是数值类型
                if not pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        # 尝试转换为数值
                        pd.to_numeric(df[col], errors='raise')
                    except:
                        type_issues[col] = f"应为数值类型，当前为 {df[col].dtype}"

        if type_issues:
            issues['type_issues'] = type_issues
            print(f"🔍 发现数据类型问题:")
            for col, issue in type_issues.items():
                print(f"  - {col}: {issue}")
        else:
            print("✅ 数据类型正常")

        # 5. 检测数据范围问题
        range_issues = {}
        range_expectations = {
            'temp': (0, 200),  # 温度范围 0-200°C
            'vibration': (0, 50),  # 振动范围 0-50
            'oil_pressure': (0, 500),  # 油压范围 0-500
            'voltage': (0, 1000),  # 电压范围 0-1000V
            'rpm': (0, 10000)  # 转速范围 0-10000
        }

        for col, (min_expected, max_expected) in range_expectations.items():
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                actual_min = df[col].min()
                actual_max = df[col].max()

                if actual_min < min_expected or actual_max > max_expected:
                    range_issues[col] = {
                        'expected_range': (min_expected, max_expected),
                        'actual_range': (actual_min, actual_max),
                        'out_of_range_count': len(df[(df[col] < min_expected) | (df[col] > max_expected)])
                    }

        if range_issues:
            issues['range_issues'] = range_issues
            print(f"🔍 发现数据范围问题:")
            for col, info in range_issues.items():
                print(f"  - {col}: {info['out_of_range_count']} 个值超出预期范围")
                print(f"    预期范围: {info['expected_range']}")
                print(f"    实际范围: {info['actual_range']}")
        else:
            print("✅ 数据范围正常")

        # 6. 检测字符串数据问题
        string_issues = {}
        for col in df.select_dtypes(include=['object']).columns:
            # 检测空字符串
            empty_strings = (df[col] == '').sum()
            # 检测只包含空格的字符串
            whitespace_only = df[col].str.strip().eq('').sum()
            # 检测异常字符
            if col == '故障类型':
                # 不预设有效故障类型，保持原始分类
                pass
            elif empty_strings > 0 or whitespace_only > 0:
                string_issues[col] = {
                    'empty_strings': empty_strings,
                    'whitespace_only': whitespace_only
                }

        if string_issues:
            issues['string_issues'] = string_issues
            print(f"🔍 发现字符串数据问题:")
            for col, info in string_issues.items():
                if info.get('empty_strings', 0) > 0:
                    print(f"  - {col}: {info['empty_strings']} 个空字符串")
                if info.get('whitespace_only', 0) > 0:
                    print(f"  - {col}: {info['whitespace_only']} 个仅包含空格的字符串")
        else:
            print("✅ 字符串数据正常")

        return issues

    def clean_data(self, df):
        """
        执行数据清洗

        Args:
            df (pandas.DataFrame): 原始数据

        Returns:
            pandas.DataFrame: 清洗后的数据
        """
        print(f"\n=== 数据清洗处理 ===")
        print(f"原始数据规模: {len(df)} 行 × {len(df.columns)} 列")

        cleaned_df = df.copy()
        cleaning_actions = []

        # 1. 处理缺失值
        missing_data = cleaned_df.isnull().sum()
        missing_cols = missing_data[missing_data > 0]

        if len(missing_cols) > 0:
            print(f"\n🧹 处理缺失值:")
            for col in missing_cols.index:
                missing_count = missing_cols[col]
                missing_percentage = (missing_count / len(cleaned_df)) * 100

                if missing_percentage > 50:
                    # 如果缺失值超过50%，删除该列
                    cleaned_df = cleaned_df.drop(columns=[col])
                    action = f"删除列 '{col}' (缺失率 {missing_percentage:.1f}%)"
                    print(f"  ✂️  {action}")
                    cleaning_actions.append(action)

                elif col in self.dataset_config['numerical_cols']:
                    # 数值列用中位数填充
                    median_value = cleaned_df[col].median()
                    cleaned_df[col] = cleaned_df[col].fillna(median_value)
                    action = f"用中位数 {median_value:.2f} 填充 '{col}' 的 {missing_count} 个缺失值"
                    print(f"  🔧 {action}")
                    cleaning_actions.append(action)

                elif col == self.dataset_config['target_col']:
                    # 目标列用众数填充，如果没有众数则删除缺失值行
                    if len(cleaned_df[col].mode()) > 0:
                        mode_value = cleaned_df[col].mode()[0]
                        cleaned_df[col] = cleaned_df[col].fillna(mode_value)
                        action = f"用众数 '{mode_value}' 填充 '{col}' 的 {missing_count} 个缺失值"
                        print(f"  🔧 {action}")
                        cleaning_actions.append(action)
                    else:
                        # 如果没有众数，删除缺失值行
                        cleaned_df = cleaned_df.dropna(subset=[col])
                        action = f"删除 '{col}' 列中包含缺失值的 {missing_count} 行"
                        print(f"  🗑️  {action}")
                        cleaning_actions.append(action)

                else:
                    # 其他列删除包含缺失值的行
                    cleaned_df = cleaned_df.dropna(subset=[col])
                    action = f"删除 '{col}' 列中包含缺失值的 {missing_count} 行"
                    print(f"  🗑️  {action}")
                    cleaning_actions.append(action)

        # 2. 处理重复行
        duplicate_count = cleaned_df.duplicated().sum()
        if duplicate_count > 0:
            cleaned_df = cleaned_df.drop_duplicates()
            action = f"删除 {duplicate_count} 行重复数据"
            print(f"\n🧹 处理重复数据:")
            print(f"  🗑️  {action}")
            cleaning_actions.append(action)

        # 3. 处理数据类型（先处理，避免异常值计算出错）
        print(f"\n🧹 处理数据类型:")
        numerical_cols = self.dataset_config['numerical_cols']
        type_actions = []

        for col in numerical_cols:
            if col in cleaned_df.columns and not pd.api.types.is_numeric_dtype(cleaned_df[col]):
                try:
                    # 尝试转换为数值类型
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    # 处理转换后产生的NaN
                    nan_count = cleaned_df[col].isnull().sum()
                    if nan_count > 0:
                        median_value = cleaned_df[col].median()
                        cleaned_df[col] = cleaned_df[col].fillna(median_value)
                        action = f"转换 '{col}' 为数值类型，用中位数 {median_value:.2f} 填充 {nan_count} 个无效值"
                    else:
                        action = f"转换 '{col}' 为数值类型"

                    print(f"  🔄 {action}")
                    type_actions.append(action)
                    cleaning_actions.append(action)
                except Exception as e:
                    print(f"  ❌ 无法转换 '{col}' 为数值类型: {str(e)}")

        if not type_actions:
            print("  ✅ 数据类型正常")

        # 4. 跳过异常值处理，保持数据原始状态
        print(f"\n🧹 异常值处理:")
        print("  ✅ 跳过异常值处理，保持数据原始状态")

        # 5. 处理字符串数据
        print(f"\n🧹 处理字符串数据:")
        string_actions = []

        for col in cleaned_df.select_dtypes(include=['object']).columns:
            # 处理空字符串和只包含空格的字符串
            empty_mask = (cleaned_df[col] == '') | (cleaned_df[col].str.strip() == '')
            empty_count = empty_mask.sum()

            if empty_count > 0:
                # 所有字符串列的空值都删除对应行，不做默认填充
                cleaned_df = cleaned_df[~empty_mask]
                action = f"删除 '{col}' 中包含空值的 {empty_count} 行"

                print(f"  🔧 {action}")
                string_actions.append(action)
                cleaning_actions.append(action)

            # 保持目标列原样，不进行标准化
            if col == self.dataset_config['target_col']:
                # 只处理空值，不修改目标列名称
                pass

        if not string_actions:
            print("  ✅ 字符串数据正常")

        # 6. 最终数据验证
        print(f"\n🧹 最终数据验证:")

        # 确保必要列存在
        missing_required = [col for col in self.required_cols if col not in cleaned_df.columns]
        if missing_required:
            print(f"  ⚠️  警告: 缺少必要列 {missing_required}")
        else:
            print(f"  ✅ 所有必要列都存在")

        # 检查数据完整性
        final_missing = cleaned_df.isnull().sum().sum()
        if final_missing > 0:
            print(f"  ⚠️  警告: 仍有 {final_missing} 个缺失值")
        else:
            print(f"  ✅ 无缺失值")

        # 保存清洗报告
        self.cleaning_report = {
            'original_shape': df.shape,
            'cleaned_shape': cleaned_df.shape,
            'rows_removed': len(df) - len(cleaned_df),
            'columns_removed': len(df.columns) - len(cleaned_df.columns),
            'cleaning_actions': cleaning_actions,
            'data_quality_improvement': {
                'missing_values_before': df.isnull().sum().sum(),
                'missing_values_after': cleaned_df.isnull().sum().sum(),
                'duplicates_removed': duplicate_count,
                'outliers_processed': len([a for a in cleaning_actions if '异常值' in a or '截断' in a])
            }
        }

        print(f"\n📊 数据清洗总结:")
        print(f"  原始数据: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"  清洗后数据: {cleaned_df.shape[0]} 行 × {cleaned_df.shape[1]} 列")
        print(f"  删除行数: {len(df) - len(cleaned_df)}")
        print(f"  删除列数: {len(df.columns) - len(cleaned_df.columns)}")
        print(f"  执行清洗操作: {len(cleaning_actions)} 项")

        return cleaned_df

    def print_cleaning_report(self):
        """
        打印详细的数据清洗报告
        """
        if not self.cleaning_report:
            print("暂无数据清洗报告")
            return

        print(f"\n{'=' * 60}")
        print("📋 详细数据清洗报告")
        print(f"{'=' * 60}")

        report = self.cleaning_report

        print(f"📊 数据规模变化:")
        print(f"  原始数据: {report['original_shape'][0]} 行 × {report['original_shape'][1]} 列")
        print(f"  清洗后数据: {report['cleaned_shape'][0]} 行 × {report['cleaned_shape'][1]} 列")
        print(
            f"  删除行数: {report['rows_removed']} ({report['rows_removed'] / report['original_shape'][0] * 100:.1f}%)")
        print(f"  删除列数: {report['columns_removed']}")

        print(f"\n🎯 数据质量改善:")
        improvement = report['data_quality_improvement']
        print(f"  缺失值: {improvement['missing_values_before']} → {improvement['missing_values_after']}")
        print(f"  重复行: 删除 {improvement['duplicates_removed']} 行")
        print(f"  异常值: 处理 {improvement['outliers_processed']} 个特征")

        print(f"\n🔧 执行的清洗操作 ({len(report['cleaning_actions'])} 项):")
        for i, action in enumerate(report['cleaning_actions'], 1):
            print(f"  {i}. {action}")

        print(f"\n✅ 数据清洗完成，数据质量显著提升！")

    def filter_target_related_rules(self, rules, min_confidence=0.5):
        """
        筛选与目标变量相关的规则（支持多种规则模式）

        Args:
            rules (pandas.DataFrame): 关联规则DataFrame
            min_confidence (float): 最小置信度阈值

        Returns:
            pandas.DataFrame: 筛选后的规则
        """
        if len(rules) == 0:
            return rules

        target_col = self.dataset_config['target_col']
        normal_value = self.dataset_config['normal_value']

        # 根据规则模式进行筛选
        if self.rule_config['rule_pattern'] == 'prediction':
            # 预测模式：目标变量在后件，非目标变量在前件
            if self.rule_config['target_in_consequent']:
                # 后件必须包含目标变量（包含正常值和故障值），且后件只能有一个项目且必须是目标变量
                target_rules = rules[
                    rules['consequents'].apply(lambda x:
                                               len(x) == 1 and  # 后件只能有一个项目
                                               any(f'{target_col}_' in str(item) or str(item) == normal_value for item
                                                   in x)) &  # 包含目标变量（正常值和故障值都要）
                    (~rules['antecedents'].apply(lambda x:
                                                 any(f'{target_col}_' in str(item) or str(item) == normal_value for item
                                                     in x))) &
                    (rules['confidence'] >= min_confidence)
                    ]
            else:
                # 前件必须包含目标变量
                target_rules = rules[
                    rules['antecedents'].apply(lambda x:
                                               any(f'{target_col}_' in str(item) for item in x)) &
                    (rules['confidence'] >= min_confidence)
                    ]

        elif self.rule_config['rule_pattern'] == 'association':
            # 关联模式：目标变量可以在前件或后件
            # 如果设置了strict_target_consequent，则后件中的目标变量必须是唯一项
            if self.rule_config.get('strict_target_consequent', False):
                target_rules = rules[
                    ((rules['consequents'].apply(lambda x:
                                                 len(x) == 1 and any(f'{target_col}_' in str(item) for item in
                                                                     x))) |  # 后件严格限制：只能有一个项目且必须是目标变量
                     (rules['antecedents'].apply(lambda x:
                                                 any(f'{target_col}_' in str(item) for item in x)))) &
                    (rules['confidence'] >= min_confidence)
                    ]
            else:
                target_rules = rules[
                    (rules['consequents'].apply(lambda x:
                                                any(f'{target_col}_' in str(item) for item in x)) |
                     rules['antecedents'].apply(lambda x:
                                                any(f'{target_col}_' in str(item) for item in x))) &
                    (rules['confidence'] >= min_confidence)
                    ]

        elif self.rule_config['rule_pattern'] == 'custom' and self.rule_config['custom_filter']:
            # 自定义模式：使用用户提供的筛选函数
            target_rules = self.rule_config['custom_filter'](rules, min_confidence)

        else:
            # 默认返回所有满足置信度的规则
            target_rules = rules[rules['confidence'] >= min_confidence]

        return target_rules.sort_values('lift', ascending=False)

    def filter_fault_related_rules(self, rules, min_confidence=0.5):
        """
        保持向后兼容的故障规则筛选方法
        """
        return self.filter_target_related_rules(rules, min_confidence)

    def load_data(self, auto_detect=True, interactive=False):
        """
        加载并验证数据

        Args:
            auto_detect (bool): 是否自动检测数据集结构
            interactive (bool): 是否使用交互式配置

        Returns:
            pandas.DataFrame: 加载并验证后的 DataFrame
        Raises:
            FileNotFoundError: 如果文件未找到
            ValueError: 如果数据中缺少必要字段
        """
        if self.file_path is None:
            raise ValueError("未指定数据文件路径")

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

        # 配置数据集结构
        if interactive:
            # 交互式配置
            interactive_config = self.interactive_config_setup(df)
            if interactive_config:
                self.set_dataset_config(interactive_config)
        elif auto_detect:
            # 自动检测数据集结构
            detected_config = self.auto_detect_dataset_structure(df)

            # 如果检测到的配置与当前配置不同，询问是否更新
            if (detected_config['target_col'] != self.dataset_config['target_col'] or
                    set(detected_config['numerical_cols']) != set(self.dataset_config['numerical_cols'])):

                print(f"\n🤔 检测到的数据结构与当前配置不同:")
                print(f"  当前目标列: {self.dataset_config['target_col']}")
                print(f"  检测到目标列: {detected_config['target_col']}")
                print(f"  当前数值列: {self.dataset_config['numerical_cols']}")
                print(f"  检测到数值列: {detected_config['numerical_cols']}")

                # 询问是否使用交互式配置
                use_interactive = input("是否使用交互式配置？(y/n，直接回车自动更新): ").strip().lower()
                if use_interactive in ['y', 'yes']:
                    interactive_config = self.interactive_config_setup(df)
                    if interactive_config:
                        self.set_dataset_config(interactive_config)
                else:
                    # 自动更新配置
                    print("🔄 自动更新数据集配置...")
                    self.set_dataset_config(detected_config)

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

    def auto_discretize(self, df, feature, num_bins=None):
        """
        根据选择的方法自动离散化特征

        Args:
            df (pandas.DataFrame): 数据框
            feature (str): 要离散化的特征
            num_bins (int): 分箱数量，如果为None则使用self.num_bins

        Returns:
            list: 分箱边界
        """
        if num_bins is None:
            num_bins = self.num_bins
        data = df[feature].dropna().values

        if self.discretization_method == 'equal_width':
            # 等宽分箱
            bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()

        elif self.discretization_method == 'equal_freq':
            # 等频分箱
            bins = [data.min()] + [np.percentile(data, 100 * i / num_bins) for i in range(1, num_bins)] + [data.max()]

        elif self.discretization_method == 'kmeans':
            # 使用K均值聚类进行分箱
            try:
                # 尝试使用更简单的KMeans配置避免环境问题
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    kmeans = KMeans(n_clusters=num_bins, random_state=0, n_init=10, algorithm='lloyd').fit(
                        data.reshape(-1, 1))
                centers = sorted(kmeans.cluster_centers_.flatten())
                # 计算相邻中心点的中点作为边界
                bins = [data.min()]
                for i in range(len(centers) - 1):
                    bins.append((centers[i] + centers[i + 1]) / 2)
                bins.append(data.max())
            except Exception:
                # 静默失败，直接使用等宽分箱替代
                bins = np.linspace(data.min(), data.max(), num_bins + 1).tolist()

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
                bins = [data.min(), mean - 2 * std, mean - std, mean + std, mean + 2 * std, data.max()]
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
                    bins = [data.min()] + sorted(thresholds)[:num_bins - 1] + [data.max()]
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
        result_dir = self.get_result_dir()
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
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
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
                plt.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
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

    def check_memory_requirements(self, df):
        """
        检查内存需求并提供建议

        Args:
            df (pandas.DataFrame): 数据框

        Returns:
            dict: 内存检查结果和建议
        """
        import psutil

        # 获取系统内存信息
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024 ** 3)

        # 估算所需内存
        num_rows = len(df)
        num_features = len(self.dataset_config['numerical_cols']) + len(self.dataset_config['categorical_cols'])
        estimated_combinations = num_rows * num_features * self.num_bins
        estimated_memory_gb = estimated_combinations * 8 / (1024 ** 3)  # 假设每个元素8字节

        result = {
            'available_memory_gb': available_gb,
            'estimated_memory_gb': estimated_memory_gb,
            'memory_sufficient': estimated_memory_gb < available_gb * 0.8,  # 保留20%缓冲
            'recommendations': []
        }

        if not result['memory_sufficient']:
            result['recommendations'].extend([
                f"数据量过大，预计需要 {estimated_memory_gb:.1f} GB 内存，但只有 {available_gb:.1f} GB 可用",
                "建议：1. 减少特征数量（选择最重要的特征）",
                "建议：2. 减少分箱数量（从5改为3）",
                "建议：3. 使用数据采样（随机选择部分数据）",
                "建议：4. 跳过自动优化，直接使用单一离散化方法"
            ])

        return result

    def optimize_discretization(self, df, min_support=0.05, min_new_support=0.3, min_lift=2.0, min_confidence=0.5):
        """
        尝试不同的离散化方法，找到产生最佳故障预测规则的方法

        Args:
            df (pandas.DataFrame): 数据框
            min_support (float): 最小支持度
            min_new_support (float): 最小支持度（规则占该故障类型的占比）
            min_lift (float): 最小提升度
            min_confidence (float): 最小置信度

        Returns:
            str: 最佳离散化方法
            dict: 使用最佳方法的分箱配置
        """
        # 检查内存需求
        memory_check = self.check_memory_requirements(df)
        print(f"\n💾 内存检查结果:")
        print(f"  可用内存: {memory_check['available_memory_gb']:.1f} GB")
        print(f"  预计需要: {memory_check['estimated_memory_gb']:.1f} GB")

        if not memory_check['memory_sufficient']:
            print("⚠️  内存不足警告:")
            for rec in memory_check['recommendations']:
                print(f"  {rec}")

            # 提供选择
            choice = input(
                "\n选择处理方式:\n  1. 继续执行（可能失败）\n  2. 使用数据采样\n  3. 减少特征数量\n  4. 跳过优化\n请选择 (1-4): ").strip()

            if choice == '2':
                # 数据采样
                sample_size = min(2000, len(df) // 2)
                df = df.sample(n=sample_size, random_state=42)
                print(f"✅ 已采样到 {len(df)} 行数据")
            elif choice == '3':
                # 减少特征数量
                print("当前数值特征:", self.dataset_config['numerical_cols'])
                keep_features = input("请输入要保留的特征序号（用逗号分隔，如：1,2,3）: ").strip()
                if keep_features:
                    try:
                        indices = [int(x.strip()) - 1 for x in keep_features.split(',')]
                        selected_features = [self.dataset_config['numerical_cols'][i] for i in indices
                                             if 0 <= i < len(self.dataset_config['numerical_cols'])]
                        self.dataset_config['numerical_cols'] = selected_features
                        self.bin_config = self._generate_bin_config(self.num_bins)
                        print(f"✅ 已选择特征: {selected_features}")
                    except:
                        print("❌ 输入格式错误，继续使用所有特征")
            elif choice == '4':
                # 跳过优化
                print("✅ 跳过离散化优化，使用默认方法")
                return 'equal_width', self.bin_config
        methods = ['equal_width', 'equal_freq', 'kmeans', 'quantile', 'std_based', 'decision_tree']
        best_method = None
        best_rules_count = 0
        best_avg_lift = 0
        best_bin_config = None
        execution_times = {}  # 用于存储每种方法的执行时间
        rule_counts = {}  # 用于存储每种方法生成的规则数量
        avg_lifts = {}  # 用于存储每种方法的平均提升度

        print("\n尝试不同的离散化方法寻找最优故障预测规则...")

        for method in methods:
            print(f"测试离散化方法: {method}")
            start_time = time.time()  # 开始计时

            try:
                self.set_discretization_method(method)

                # 为每个特征自动计算分箱边界
                for feature in self.bin_config:
                    if feature in df.columns:
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

                # 计算故障类型支持度并应用 min_new_support 筛选
                target_col = self.dataset_config['target_col']
                normal_value = self.dataset_config['normal_value']
                
                # 计算每个故障类型的总数量
                fault_type_counts = {}
                for _, row in processed_df.iterrows():
                    fault_value = row[target_col]
                    if '_' in fault_value and fault_value.startswith(f'{target_col}_'):
                        fault_type = fault_value.split('_', 1)[1]
                    else:
                        fault_type = fault_value
                    fault_type_counts[fault_type] = fault_type_counts.get(fault_type, 0) + 1
                
                # 为每条规则计算故障类型支持度
                filtered_rules = []
                for _, row in valid_rules.iterrows():
                    consequent_item = list(row['consequents'])[0]
                    
                    if consequent_item == normal_value:
                        consequent = consequent_item
                    elif '_' in consequent_item and consequent_item.startswith(f'{target_col}_'):
                        consequent = consequent_item.split('_', 1)[1]
                    else:
                        consequent = consequent_item
                    
                    # 计算故障类型支持度
                    if consequent in fault_type_counts:
                        rule_sample_count = row['support'] * len(processed_df)
                        fault_type_support = rule_sample_count / fault_type_counts[consequent]
                        
                        # 应用 min_new_support 筛选
                        if fault_type_support >= min_new_support:
                            filtered_rules.append(row)
                
                rules_count = len(filtered_rules)
                avg_lift = pd.DataFrame(filtered_rules)['lift'].mean() if rules_count > 0 else 0
                max_lift = pd.DataFrame(filtered_rules)['lift'].max() if rules_count > 0 else 0

                # 保存此方法的规则数量和平均提升度
                rule_counts[method] = rules_count
                avg_lifts[method] = avg_lift

                print(
                    f"  方法 {method}: 找到 {rules_count} 条故障预测规则（已应用min_new_support={min_new_support}筛选），平均提升度: {avg_lift:.2f}，最大提升度: {max_lift:.2f}")

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

            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times[method] = execution_time
                rule_counts[method] = 0
                avg_lifts[method] = 0
                print(f"  方法 {method}: 执行失败 - {str(e)}")
                print(f"  方法 {method} 执行时间: {execution_time:.2f} 秒")

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
            print(
                f"\n最佳离散化方法是: {best_method}，生成了 {best_rules_count} 条故障预测规则，平均提升度: {best_avg_lift:.2f}")
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

        # 构建事务项 - 动态处理分类列
        for cat_col in self.dataset_config['categorical_cols']:
            if cat_col in processed.columns:
                processed[cat_col] = f'{cat_col}_' + processed[cat_col].astype(str)

        # 处理目标列
        target_col = self.dataset_config['target_col']
        normal_value = self.dataset_config['normal_value']
        if target_col in processed.columns:
            processed[target_col] = processed[target_col].apply(
                lambda x: normal_value if x == normal_value else f'{target_col}_{x}'
            )

        return processed

    def get_binning_info(self):
        """
        获取分箱信息，用于传递给其他步骤的代码

        Returns:
            dict: 包含完整分箱信息的字典，格式如下：
            {
                'feature_name': {
                    'bins': [边界值列表],
                    'labels': [标签列表],
                    'ranges': [
                        {'label': '低温度', 'min': 20.0, 'max': 40.0},
                        {'label': '中温度', 'min': 40.0, 'max': 60.0},
                        ...
                    ],
                    'feature_chinese_name': '温度'
                }
            }
        """
        binning_info = {}

        for feature, config in self.bin_config.items():
            if config['bins'] is not None:
                bins = config['bins']
                labels = config['labels']

                # 构建范围信息
                ranges = []
                for i in range(len(labels)):
                    ranges.append({
                        'label': labels[i],
                        'min': bins[i],
                        'max': bins[i + 1],
                        'range_text': f"{bins[i]:.2f} - {bins[i + 1]:.2f}"
                    })

                binning_info[feature] = {
                    'bins': bins.copy() if isinstance(bins, list) else bins.tolist(),
                    'labels': labels.copy(),
                    'ranges': ranges,
                    'feature_chinese_name': self.dataset_config['feature_names'].get(feature, feature),
                    'num_bins': len(labels)
                }

        return binning_info

    def get_categorical_info(self, df=None):
        """
        获取分类特征信息

        Args:
            df (pandas.DataFrame): 数据框，用于获取分类特征的实际值分布

        Returns:
            dict: 包含分类特征信息的字典
        """
        categorical_info = {}

        for cat_col in self.dataset_config['categorical_cols']:
            info = {
                'feature_name': cat_col,
                'feature_type': 'categorical',
                'description': f'分类特征: {cat_col}'
            }

            # 如果提供了数据框，获取实际的值分布
            if df is not None and cat_col in df.columns:
                value_counts = df[cat_col].value_counts()
                total_count = len(df)

                info.update({
                    'unique_values': value_counts.index.tolist(),
                    'value_counts': {str(k): int(v) for k, v in value_counts.to_dict().items()},
                    'value_distribution': {
                        str(val): {
                            'count': int(count),
                            'percentage': float(round((count / total_count) * 100, 2))
                        }
                        for val, count in value_counts.items()
                    },
                    'total_unique': int(len(value_counts)),
                    'most_frequent': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    'least_frequent': str(value_counts.index[-1]) if len(value_counts) > 0 else None
                })

            categorical_info[cat_col] = info

        return categorical_info

    def get_target_info(self, df=None):
        """
        获取目标变量信息

        Args:
            df (pandas.DataFrame): 数据框，用于获取目标变量的实际值分布

        Returns:
            dict: 包含目标变量信息的字典
        """
        target_col = self.dataset_config['target_col']
        normal_value = self.dataset_config['normal_value']

        target_info = {
            'target_column': target_col,
            'normal_value': normal_value,
            'feature_type': 'target',
            'description': f'目标变量: {target_col}'
        }

        # 如果提供了数据框，获取实际的值分布
        if df is not None and target_col in df.columns:
            value_counts = df[target_col].value_counts()
            total_count = len(df)

            # 分离正常值和异常值
            normal_count = value_counts.get(normal_value, 0)
            abnormal_values = {k: v for k, v in value_counts.items() if k != normal_value}
            abnormal_count = sum(abnormal_values.values())

            target_info.update({
                'unique_values': [str(x) for x in value_counts.index.tolist()],
                'value_counts': {str(k): int(v) for k, v in value_counts.to_dict().items()},
                'value_distribution': {
                    str(val): {
                        'count': int(count),
                        'percentage': float(round((count / total_count) * 100, 2)),
                        'type': 'normal' if val == normal_value else 'abnormal'
                    }
                    for val, count in value_counts.items()
                },
                'total_unique': int(len(value_counts)),
                'normal_ratio': float(round((normal_count / total_count) * 100, 2)),
                'abnormal_ratio': float(round((abnormal_count / total_count) * 100, 2)),
                'normal_count': int(normal_count),
                'abnormal_count': int(abnormal_count),
                'abnormal_types': [str(x) for x in abnormal_values.keys()],
                'class_balance': 'balanced' if abs(normal_count - abnormal_count) / total_count < 0.1 else 'imbalanced'
            })

        return target_info

    def get_normalized_data_info(self, df, processed_df=None):
        """
        获取归一化数据信息

        Args:
            df (pandas.DataFrame): 原始数据框
            processed_df (pandas.DataFrame): 处理后的数据框

        Returns:
            dict: 包含归一化数据信息的字典
        """
        normalized_info = {
            'normalization_method': 'discretization_binning',
            'description': '通过分箱离散化进行数据归一化',
            'features': {}
        }

        # 数值特征的归一化信息
        for feature in self.dataset_config['numerical_cols']:
            if feature in df.columns:
                original_stats = {
                    'min': float(df[feature].min()),
                    'max': float(df[feature].max()),
                    'mean': float(df[feature].mean()),
                    'std': float(df[feature].std()),
                    'median': float(df[feature].median()),
                    'q25': float(df[feature].quantile(0.25)),
                    'q75': float(df[feature].quantile(0.75))
                }

                feature_info = {
                    'feature_name': feature,
                    'feature_chinese_name': self.dataset_config['feature_names'].get(feature, feature),
                    'original_type': 'numerical',
                    'normalized_type': 'categorical_discrete',
                    'original_stats': original_stats,
                    'normalization_details': {
                        'method': f'{self.discretization_method}_binning',
                        'num_bins': self.num_bins,
                        'bin_labels': self.bin_config.get(feature, {}).get('labels', []),
                        'bin_boundaries': self.bin_config.get(feature, {}).get('bins', [])
                    }
                }

                # 如果有处理后的数据，添加离散化后的分布
                if processed_df is not None:
                    level_col = f"{feature}_level"
                    if level_col in processed_df.columns:
                        discrete_counts = processed_df[level_col].value_counts()
                        total_count = len(processed_df)

                        feature_info['normalized_distribution'] = {
                            label: {
                                'count': int(discrete_counts.get(label, 0)),
                                'percentage': float(round((discrete_counts.get(label, 0) / total_count) * 100, 2))
                            }
                            for label in self.bin_config.get(feature, {}).get('labels', [])
                        }

                normalized_info['features'][feature] = feature_info

        # 分类特征的归一化信息（通常不需要归一化，但记录编码信息）
        for feature in self.dataset_config['categorical_cols']:
            if feature in df.columns:
                feature_info = {
                    'feature_name': feature,
                    'original_type': 'categorical',
                    'normalized_type': 'categorical_encoded',
                    'normalization_details': {
                        'method': 'prefix_encoding',
                        'encoding_format': f'{feature}_{{value}}'
                    }
                }

                # 如果有处理后的数据，添加编码后的分布
                if processed_df is not None and feature in processed_df.columns:
                    encoded_counts = processed_df[feature].value_counts()
                    total_count = len(processed_df)

                    feature_info['normalized_distribution'] = {
                        val: {
                            'count': int(count),
                            'percentage': float(round((count / total_count) * 100, 2))
                        }
                        for val, count in encoded_counts.items()
                    }

                normalized_info['features'][feature] = feature_info

        return normalized_info

    def get_comprehensive_data_info(self, df, processed_df=None):
        """
        获取综合数据信息，包括所有类型的特征信息

        Args:
            df (pandas.DataFrame): 原始数据框
            processed_df (pandas.DataFrame): 处理后的数据框

        Returns:
            dict: 包含所有数据信息的综合字典
        """
        return {
            'binning_info': self.get_binning_info(),
            'categorical_info': self.get_categorical_info(df),
            'target_info': self.get_target_info(df),
            'normalized_data_info': self.get_normalized_data_info(df, processed_df),
            'dataset_summary': {
                'total_rows': int(len(df)),
                'total_columns': int(len(df.columns)),
                'numerical_features': int(len(self.dataset_config['numerical_cols'])),
                'categorical_features': int(len(self.dataset_config['categorical_cols'])),
                'id_columns': int(len(self.dataset_config['id_cols'])),
                'target_column': str(self.dataset_config['target_col']),
                'discretization_method': str(self.discretization_method),
                'num_bins': int(self.num_bins)
            }
        }

    def _convert_to_json_serializable(self, obj):
        """
        将对象转换为JSON可序列化的格式

        Args:
            obj: 要转换的对象

        Returns:
            JSON可序列化的对象
        """
        import numpy as np

        if isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj

    def export_binning_config(self, output_path=None, df=None, processed_df=None):
        """
        导出分箱配置到JSON文件，便于其他程序使用

        Args:
            output_path (str): 输出文件路径，如果为None则使用默认路径
            df (pandas.DataFrame): 原始数据框，用于获取详细统计信息
            processed_df (pandas.DataFrame): 处理后的数据框，用于获取归一化信息

        Returns:
            str: 导出文件的路径
        """
        import json

        if output_path is None:
            # 默认将JSON文件放在 result/apriori_results 目录
            output_dir = self.get_result_dir()
            output_path = os.path.join(output_dir, '分箱配置.json')

        # 获取所有信息
        if df is not None:
            comprehensive_info = self.get_comprehensive_data_info(df, processed_df)
        else:
            # 如果没有提供数据框，只导出基本的分箱信息
            comprehensive_info = {
                'binning_info': self.get_binning_info(),
                'categorical_info': self.get_categorical_info(),
                'target_info': self.get_target_info(),
                'normalized_data_info': {'features': {}},
                'dataset_summary': {
                    'discretization_method': self.discretization_method,
                    'num_bins': self.num_bins
                }
            }

        # 添加元数据
        export_data = {
            'metadata': {
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'export_version': '2.0',
                'num_bins': int(self.num_bins),
                'discretization_method': str(self.discretization_method),
                'dataset_config': self._convert_to_json_serializable(self.dataset_config),
                'rule_config': self._convert_to_json_serializable(self.rule_config),
                'cleaning_report': self._convert_to_json_serializable(
                    self.cleaning_report if hasattr(self, 'cleaning_report') else {})
            },
            'data_info': self._convert_to_json_serializable(comprehensive_info)
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 完整数据配置已导出到: {output_path}")
        return output_path

    def export_comprehensive_config(self, output_dir=None, df=None, processed_df=None):
        """
        导出完整的数据配置信息，包括分箱、分类特征、目标变量和归一化信息

        Args:
            output_dir (str): 输出目录路径，如果为None则使用默认路径
            df (pandas.DataFrame): 原始数据框
            processed_df (pandas.DataFrame): 处理后的数据框

        Returns:
            dict: 包含所有导出文件路径的字典
        """
        import json

        if output_dir is None:
            # 默认输出目录为result/apriori_results
            output_dir = self.get_result_dir()

        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {}

        # 导出完整配置到result目录
        comprehensive_path = os.path.join(output_dir, '完整数据配置.json')
        exported_files['comprehensive_config'] = self.export_binning_config(comprehensive_path, df, processed_df)

        if df is not None:
            # 3. 单独导出各类信息到result目录

            # 分箱信息
            binning_path = os.path.join(output_dir, '分箱配置.json')
            with open(binning_path, 'w', encoding='utf-8') as f:
                json.dump(self._convert_to_json_serializable({
                    'metadata': {
                        'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'binning_config'
                    },
                    'binning_info': self.get_binning_info()
                }), f, ensure_ascii=False, indent=2)
            exported_files['binning_config'] = binning_path

            # 分类特征信息
            categorical_path = os.path.join(output_dir, '分类特征信息.json')
            with open(categorical_path, 'w', encoding='utf-8') as f:
                json.dump(self._convert_to_json_serializable({
                    'metadata': {
                        'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'categorical_info'
                    },
                    'categorical_info': self.get_categorical_info(df)
                }), f, ensure_ascii=False, indent=2)
            exported_files['categorical_info'] = categorical_path

            # 目标变量信息
            target_path = os.path.join(output_dir, '目标变量信息.json')
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self._convert_to_json_serializable({
                    'metadata': {
                        'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'target_info'
                    },
                    'target_info': self.get_target_info(df)
                }), f, ensure_ascii=False, indent=2)
            exported_files['target_info'] = target_path

            # 归一化数据信息
            normalized_path = os.path.join(output_dir, '归一化数据信息.json')
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(self._convert_to_json_serializable({
                    'metadata': {
                        'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'normalized_data_info'
                    },
                    'normalized_data_info': self.get_normalized_data_info(df, processed_df)
                }), f, ensure_ascii=False, indent=2)
            exported_files['normalized_info'] = normalized_path

            # 3. 导出CSV格式的汇总信息
            self._export_summary_csv(output_dir, df, processed_df)
            exported_files['summary_csv'] = os.path.join(output_dir, '数据特征汇总.csv')

        print(f"\n📁 完整数据配置导出完成:")
        for config_type, file_path in exported_files.items():
            print(f"  {config_type}: {file_path}")

        return exported_files

    def _export_summary_csv(self, output_dir, df, processed_df=None):
        """
        导出数据特征汇总的CSV文件

        Args:
            output_dir (str): 输出目录
            df (pandas.DataFrame): 原始数据框
            processed_df (pandas.DataFrame): 处理后的数据框
        """
        summary_data = []

        # 数值特征汇总
        for feature in self.dataset_config['numerical_cols']:
            if feature in df.columns:
                feature_chinese = self.dataset_config['feature_names'].get(feature, feature)

                row = {
                    '特征名称': str(feature),
                    '中文名称': str(feature_chinese),
                    '特征类型': '数值型',
                    '原始最小值': float(df[feature].min()),
                    '原始最大值': float(df[feature].max()),
                    '原始均值': float(round(df[feature].mean(), 2)),
                    '原始标准差': float(round(df[feature].std(), 2)),
                    '分箱数量': int(self.num_bins),
                    '离散化方法': str(self.discretization_method),
                    '分箱标签': ', '.join(self.bin_config.get(feature, {}).get('labels', []))
                }

                # 添加离散化后的分布
                if processed_df is not None:
                    level_col = f"{feature}_level"
                    if level_col in processed_df.columns:
                        discrete_counts = processed_df[level_col].value_counts()
                        total_count = len(processed_df)
                        distribution = []
                        for label in self.bin_config.get(feature, {}).get('labels', []):
                            count = discrete_counts.get(label, 0)
                            percentage = round((count / total_count) * 100, 1)
                            distribution.append(f"{label}:{percentage}%")
                        row['离散化分布'] = ', '.join(distribution)

                summary_data.append(row)

        # 分类特征汇总
        for feature in self.dataset_config['categorical_cols']:
            if feature in df.columns:
                value_counts = df[feature].value_counts()
                total_count = len(df)

                row = {
                    '特征名称': str(feature),
                    '中文名称': str(feature),
                    '特征类型': '分类型',
                    '唯一值数量': int(len(value_counts)),
                    '最频繁值': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    '最频繁值占比': f"{round((value_counts.iloc[0] / total_count) * 100, 1)}%" if len(
                        value_counts) > 0 else None,
                    '所有值': ', '.join([f"{val}({count})" for val, count in value_counts.head(5).items()])
                }
                summary_data.append(row)

        # 目标变量汇总
        target_col = self.dataset_config['target_col']
        if target_col in df.columns:
            value_counts = df[target_col].value_counts()
            total_count = len(df)
            normal_value = self.dataset_config['normal_value']
            normal_count = value_counts.get(normal_value, 0)
            abnormal_count = total_count - normal_count

            row = {
                '特征名称': str(target_col),
                '中文名称': '目标变量',
                '特征类型': '目标变量',
                '正常值': str(normal_value),
                '正常样本数': int(normal_count),
                '正常样本占比': f"{round((normal_count / total_count) * 100, 1)}%",
                '异常样本数': int(abnormal_count),
                '异常样本占比': f"{round((abnormal_count / total_count) * 100, 1)}%",
                '类别平衡性': '平衡' if abs(normal_count - abnormal_count) / total_count < 0.1 else '不平衡'
            }
            summary_data.append(row)

        # 保存CSV
        summary_df = pd.DataFrame(summary_data)
        summary_path = os.path.join(output_dir, '数据特征汇总.csv')
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
        print(f"  数据特征汇总CSV: {summary_path}")

    def load_binning_config(self, config_path):
        """
        从JSON文件加载分箱配置

        Args:
            config_path (str): 配置文件路径
        """
        import json

        with open(config_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)

        # 恢复分箱配置
        binning_info = export_data['binning_info']
        self.bin_config = {}

        for feature, info in binning_info.items():
            self.bin_config[feature] = {
                'bins': info['bins'],
                'labels': info['labels']
            }

        # 恢复其他配置
        if 'metadata' in export_data:
            metadata = export_data['metadata']
            self.num_bins = metadata.get('num_bins', self.num_bins)
            self.discretization_method = metadata.get('discretization_method', self.discretization_method)
            if 'dataset_config' in metadata:
                self.dataset_config.update(metadata['dataset_config'])

        print(f"✅ 分箱配置已从 {config_path} 加载")

    def generate_transactions(self, df):
        """
        生成事务型数据

        Args:
            df (pandas.DataFrame): 预处理后的 DataFrame

        Returns:
            list: 事务列表，每个事务是一个物品列表
        """
        features = []
        target_col = self.dataset_config['target_col']

        for row in df.itertuples():
            try:
                transaction = []

                # 添加分类特征
                for cat_col in self.dataset_config['categorical_cols']:
                    if hasattr(row, cat_col):
                        transaction.append(getattr(row, cat_col))

                # 添加数值特征（离散化后）
                for num_col in self.dataset_config['numerical_cols']:
                    level_col = f"{num_col}_level"
                    if hasattr(row, level_col):
                        transaction.append(f"{num_col}={getattr(row, level_col)}")

                # 添加目标变量
                if hasattr(row, target_col):
                    transaction.append(getattr(row, target_col))

                # 过滤掉空值
                transaction = [item for item in transaction if not pd.isna(item)]
                if transaction:  # 只添加非空事务
                    features.append(transaction)

            except AttributeError as e:
                print(f"警告: 处理行时出错，跳过: {e}")
                continue
        return features

    def analyze(self, min_support=0.05, min_new_support=0.3, min_lift=2.0, min_confidence=0.5, auto_optimize=True, interactive=False):
        """
        执行关联分析

        Args:
            min_support (float): 频繁项集的最小支持度阈值，默认为 0.05
            min_new_support (float): 最小支持度（规则占该故障类型的占比），默认为 0.3
            min_lift (float): 关联规则的最小提升度阈值，默认为 2.0
            min_confidence (float): 最小置信度阈值，默认为 0.5
            auto_optimize (bool): 是否自动优化离散化方法，默认为True
            interactive (bool): 是否使用交互式配置，默认为False

        Returns:
            pandas.DataFrame: 包含有效关联规则的 DataFrame，列有 '规则'、'完整支持度'、'故障类型支持度'、'置信度' 和 '提升度'
        """
        try:
            # 数据准备
            print("正在加载数据...")
            raw_df = self.load_data(interactive=interactive)
            print(f"数据加载完成，共 {len(raw_df)} 行")

            # 保存原始数据引用供导出使用
            self.raw_data = raw_df.copy()

            # 交互式规则配置
            if interactive:
                rule_params = self.interactive_rule_config()
                min_support = rule_params['min_support']
                min_confidence = rule_params['min_confidence']
                min_lift = rule_params['min_lift']
                auto_optimize = rule_params['auto_optimize']

            # 数据质量检测
            print("\n" + "=" * 60)
            print("🔍 开始数据质量检测和清洗")
            print("=" * 60)

            # 检测数据质量问题
            data_issues = self.detect_data_quality_issues(raw_df)

            # 执行数据清洗
            cleaned_df = self.clean_data(raw_df)

            # 打印清洗报告
            self.print_cleaning_report()

            # 是否自动优化离散化
            if auto_optimize:
                print("\n正在进行离散化方法优化...")
                optimize_start_time = time.time()
                best_method, _ = self.optimize_discretization(cleaned_df, min_support, min_new_support, min_lift, min_confidence)
                optimize_end_time = time.time()
                optimize_total_time = optimize_end_time - optimize_start_time
                print(f"离散化方法优化总耗时: {optimize_total_time:.2f} 秒")
                if best_method:
                    print(f"最终选择的离散化方法: {best_method}")

            print("\n正在预处理数据...")
            processed_df = self.preprocess(cleaned_df)
            print(f"数据预处理完成")

            # 保存处理后的数据引用供导出使用
            self.processed_data = processed_df.copy()

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

            # 过滤与目标变量相关的规则
            rule_type = "故障预测" if self.dataset_config[
                                          'target_col'] == '故障类型' else f"{self.dataset_config['target_col']}预测"
            print(f"正在过滤{rule_type}规则...")
            valid_rules = self.filter_target_related_rules(rules, min_confidence)

            # 统计目标相关规则数量
            total_rules = len(rules)
            target_rules_count = len(valid_rules)
            print(f"\n总关联规则数量：{total_rules}")
            print(f"{rule_type}规则数量：{target_rules_count}")

            if target_rules_count == 0:
                print(f"警告: 未找到任何{rule_type}规则，请尝试降低min_confidence值或检查数据质量")
                return pd.DataFrame()

            # 保存过滤后但未格式化的规则数量
            original_rule_count = len(valid_rules)

            # 计算每个故障类型的总数量（用于计算故障类型支持度）
            target_col = self.dataset_config['target_col']
            normal_value = self.dataset_config['normal_value']
            fault_type_counts = {}
            
            for _, row in processed_df.iterrows():
                fault_value = row[target_col]
                # 提取类型（去掉前缀），包含正常值
                if '_' in fault_value and fault_value.startswith(f'{target_col}_'):
                    fault_type = fault_value.split('_', 1)[1]
                else:
                    fault_type = fault_value
                fault_type_counts[fault_type] = fault_type_counts.get(fault_type, 0) + 1
            
            print(f"\n各类型样本数量（含正常）：")
            for fault_type, count in fault_type_counts.items():
                print(f"  {fault_type}: {count}")

            # 结果格式化
            results = []
            rule_identifiers = set()  # 用于检测完全相同的规则

            for _, row in valid_rules.iterrows():
                # 对 antecedents 进行排序
                antecedents = sorted([item.split('=')[1] if '=' in item else item
                                      for item in list(row['antecedents'])])

                # 处理 consequent - 支持不同的目标列（包括正常值和故障值）
                consequent_item = list(row['consequents'])[0]
                target_col = self.dataset_config['target_col']
                normal_value = self.dataset_config['normal_value']

                if consequent_item == normal_value:
                    # 如果是正常值，直接使用
                    consequent = consequent_item
                elif '_' in consequent_item and consequent_item.startswith(f'{target_col}_'):
                    # 如果是带前缀的故障值，去掉前缀
                    consequent = consequent_item.split('_', 1)[1]
                else:
                    # 其他情况直接使用
                    consequent = consequent_item

                # 创建规则文本和规则唯一标识
                rule_text = " ∧ ".join(antecedents) + " → " + consequent  # 使用简单箭头代替双箭头
                rule_id = (frozenset(antecedents), consequent)

                # 跳过重复规则
                if rule_id in rule_identifiers:
                    continue
                rule_identifiers.add(rule_id)

                # 计算故障类型支持度（规则占该故障类型的占比）
                fault_type_support = 0.0
                if consequent in fault_type_counts:
                    # 规则的支持度 = 规则支持的样本数 / 总样本数
                    # 故障类型支持度 = 规则支持的样本数 / 该故障类型的样本数
                    rule_sample_count = row['support'] * len(processed_df)
                    fault_type_support = rule_sample_count / fault_type_counts[consequent]

                results.append({
                    '规则': rule_text,
                    '完整支持度': round(row['support'], 4),
                    '故障类型支持度': round(fault_type_support, 4),
                    '置信度': round(row['confidence'], 4),
                    '提升度': round(row['lift'], 2),
                    '原始提升度': row['lift']
                })

            result_df = pd.DataFrame(results)

            # 按照故障类型支持度筛选
            print(f"\n应用最小支持度筛选 (min_new_support={min_new_support})...")
            result_df = result_df[result_df['故障类型支持度'] >= min_new_support]
            print(f"筛选后剩余 {len(result_df)} 条规则")

            # 直接按原始提升度降序排序
            result_df = result_df.sort_values(by='原始提升度', ascending=False)

            # 删除辅助列
            if '原始提升度' in result_df.columns:
                result_df = result_df.drop(columns=['原始提升度'])

            print(f"分析完成，共生成 {len(result_df)} 条{rule_type}规则")

            # 分析丢失的规则数量
            rules_lost = original_rule_count - len(result_df)
            if rules_lost > 0:
                print(
                    f"注意: 格式化、去重和筛选过程中过滤了 {rules_lost} 条规则")

            self.save_top_rules_plot(result_df)

            return result_df

        except Exception as e:
            print(f"错误: 分析过程中出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def save_top_rules_plot(self, result_df, top_n=10):
        """根据结果数据生成提升度对比图"""
        if result_df is None or result_df.empty:
            return
        try:
            top_rules = result_df.head(min(top_n, len(result_df)))
            if top_rules.empty:
                return

            plt.figure(figsize=(12, 8))
            plt.barh(top_rules['规则'][::-1], top_rules['提升度'][::-1], color='skyblue')
            plt.xlabel('提升度')
            plt.ylabel('故障预测规则')
            plt.title('设备故障预测规则分析 - 提升度排名')
            plt.tight_layout()

            image_path = os.path.join(self.get_result_dir(), "故障预测规则提升度.png")
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"已生成故障预测规则提升度图表，保存为'{image_path}'")
        except Exception as exc:
            print(f"警告: 无法生成故障预测规则提升度图表: {exc}")


if __name__ == "__main__":
    try:
        total_start_time = time.time()  # 记录总运行开始时间

        # 询问是否使用交互式模式
        print("🚀 关联规则分析器")
        print("=" * 50)
        mode_choice = input(
            "选择运行模式:\n  1. 交互式模式（终端配置）\n  2. 自动模式（默认配置）\n请选择 (1/2，直接回车使用自动模式): ").strip()

        interactive_mode = mode_choice == '1'

        if interactive_mode:
            print("\n🔧 交互式模式已启用")
            # 交互式选择文件
            print("\n📁 请选择数据文件:")
            print("  1. 使用默认文件")
            print("  2. 输入自定义文件路径")

            file_choice = input("请选择 (1/2，直接回车使用默认): ").strip()

            if file_choice == '2':
                file_path = input("请输入CSV文件路径: ").strip()
                if not file_path:
                    print("❌ 未输入文件路径，使用默认文件")
                    file_path = r'..\datas\generated_dataset_2000.csv'
            else:
                file_path = r'..\datas\generated_dataset_2000.csv'
        else:
            print("\n🤖 自动模式已启用")
            file_path = r'..\datas\generated_dataset_2000.csv'

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在，请检查路径")
            # 尝试查找当前目录下的CSV文件
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
            if csv_files:
                print(f"在当前目录找到以下CSV文件：{csv_files}")
                if interactive_mode:
                    print("可选文件:")
                    for i, f in enumerate(csv_files):
                        print(f"  {i + 1}. {f}")
                    try:
                        choice = input(f"请选择文件 (1-{len(csv_files)}): ").strip()
                        if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
                            file_path = csv_files[int(choice) - 1]
                        else:
                            file_path = csv_files[0]
                    except:
                        file_path = csv_files[0]
                else:
                    file_path = csv_files[0]
                print(f"使用 {file_path} 作为替代")
            else:
                print("在当前目录下未找到任何CSV文件")
                exit(1)

        analyzer = EquipmentAnalyzer(file_path, num_bins=5)  # 可以修改分箱个数

        if interactive_mode:
            # 交互式分析
            results = analyzer.analyze(interactive=True)
        else:
            # 自动分析
            # 参数设置建议：
            # 小数据集(1000行)：min_support=0.03
            # 大数据集(1万+行)：min_support=0.01
            # min_new_support: 最小支持度（规则占该故障类型的占比），建议0.1-0.3
            # auto_optimize=True会自动尝试不同的分箱方法找出最佳规则
            results = analyzer.analyze(min_support=0.005, min_new_support=0.1, min_confidence=0.5, min_lift=1.2, auto_optimize=True)

        if results.empty:
            print("\n未找到符合条件的故障预测规则，请尝试调整参数")
        else:
            print("\n设备故障预测规则分析结果（按关联强度从高到低排列）：")
            print(f"共找到 {len(results)} 条故障预测规则")

            # 设置支持度和置信度显示4位小数
            pd.options.display.float_format = '{:.5f}'.format
            print(results.to_markdown(index=False))

            # 保存结果到CSV文件（使用UTF-8编码确保中文正确显示）
            result_dir = analyzer.get_result_dir()
            os.makedirs(result_dir, exist_ok=True)
            result_path = os.path.join(result_dir, "关联规则分析结果.csv")
            results.to_csv(result_path, index=False, encoding='utf-8-sig')
            print(f"结果已保存到 '{result_path}'")

            # 导出完整的数据配置信息
            try:
                # 使用分析过程中保存的数据引用
                raw_data = getattr(analyzer, 'raw_data', None)
                processed_data = getattr(analyzer, 'processed_data', None)

                exported_files = analyzer.export_comprehensive_config(result_dir, raw_data, processed_data)

                # 显示数据信息摘要
                if raw_data is not None:
                    comprehensive_info = analyzer.get_comprehensive_data_info(raw_data, processed_data)
                else:
                    comprehensive_info = {
                        'binning_info': analyzer.get_binning_info(),
                        'categorical_info': {},
                        'target_info': {},
                        'normalized_data_info': {}
                    }
            except Exception as e:
                print(f"导出配置信息时出错: {e}")
                # 至少导出基本的分箱信息到Apriori目录
                apriori_dir = analyzer.get_apriori_dir()
                analyzer.export_binning_config(os.path.join(apriori_dir, "分箱配置.json"))
                comprehensive_info = {'binning_info': analyzer.get_binning_info()}

            # 分箱信息摘要
            binning_info = comprehensive_info['binning_info']
            print(f"\n📊 分箱信息摘要:")
            for feature, info in binning_info.items():
                print(f"  {info['feature_chinese_name']} ({feature}):")
                for range_info in info['ranges']:
                    print(f"    {range_info['label']}: {range_info['range_text']}")
                print()

            # 分类特征信息摘要
            categorical_info = comprehensive_info['categorical_info']
            if categorical_info:
                print(f"🏷️  分类特征信息摘要:")
                for feature, info in categorical_info.items():
                    if 'unique_values' in info:
                        print(f"  {feature}: {info['total_unique']} 个唯一值")
                        print(
                            f"    最频繁: {info['most_frequent']} ({info['value_distribution'][info['most_frequent']]['percentage']}%)")
                print()

            # 目标变量信息摘要
            target_info = comprehensive_info['target_info']
            if 'normal_ratio' in target_info:
                print(f"🎯 目标变量信息摘要:")
                print(f"  目标列: {target_info['target_column']}")
                print(f"  正常样本: {target_info['normal_count']} ({target_info['normal_ratio']}%)")
                print(f"  异常样本: {target_info['abnormal_count']} ({target_info['abnormal_ratio']}%)")
                print(f"  异常类型: {', '.join(target_info['abnormal_types'])}")
                print(f"  类别平衡性: {target_info['class_balance']}")
                print()

            # 如果需要生成可视化图表

        # 输出总运行时间
        total_end_time = time.time()
        total_runtime = total_end_time - total_start_time
        print(f"\n程序总运行时间: {total_runtime:.2f} 秒 ({total_runtime / 60:.2f} 分钟)")

    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback

        traceback.print_exc()
