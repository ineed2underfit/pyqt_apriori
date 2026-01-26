import os
import sys
import pickle
import json
import warnings
import platform
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from pgmpy.inference import VariableElimination
from joblib import parallel_backend

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# 引入健康度评价模块
try:
    from health_assessment import HealthAssessor
except ImportError:
    HealthAssessor = None

warnings.filterwarnings("ignore")

# ==========================================
# 0. 绘图字体配置
# ==========================================
system_name = platform.system()
if system_name == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei']
elif system_name == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 全局路径配置
# ==========================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(PROJECT_ROOT, "Bayesian", "models", "final_bn_model.pkl")
DATA_PATH = os.path.join(PROJECT_ROOT, "datas", "device_HP30_data.csv")

BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
RULES_JSON_PATH = os.path.join(PROJECT_ROOT, "result", "bayesian_results", "network_rules_with_mapping.json")
RULES_CSV_PATH = os.path.join(PROJECT_ROOT, "result", "apriori_results", "关联规则分析结果.csv")

RESULT_DIR = os.path.join(PROJECT_ROOT, "result", "bayesian_results")
os.makedirs(RESULT_DIR, exist_ok=True)


# ==========================================
# 2. 资源加载函数
# ==========================================

def load_binning_config(path):
    if not os.path.exists(path): raise FileNotFoundError(f"配置文件缺失: {path}")
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)


def load_network_rules(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)


def load_model(path):
    if not os.path.exists(path): raise FileNotFoundError(f"模型文件缺失: {path}")
    print(f"正在加载模型: {os.path.basename(path)}")
    with open(path, 'rb') as f: return pickle.load(f)


# ==========================================
# 3. 核心功能: 离散化与预测
# ==========================================

def infer_single_sample(model, discrete_input, target_col):
    """单样本精确推理"""
    try:
        try:
            nodes = set(model.nodes())
        except:
            nodes = set(model.nodes)

        evidence = {}
        for k, v in discrete_input.items():
            if str(v) in nodes:
                evidence[str(v)] = 1
            elif f"{k}_{v}" in nodes:
                evidence[f"{k}_{v}"] = 1

        if not evidence: return None, {}

        infer = VariableElimination(model)
        result = infer.query(variables=[target_col], evidence=evidence)
        state_names = result.state_names[target_col]
        probs = result.values
        prob_dict = {s: p for s, p in zip(state_names, probs)}
        return max(prob_dict, key=prob_dict.get), prob_dict
    except:
        return None, {}


def discretize_using_json(raw_dict, binning_config, debug=False):
    """单样本离散化"""
    res = {}
    data_info = binning_config['data_info']['binning_info']
    dataset_config = binning_config['metadata']['dataset_config']

    if debug: print("\n[调试] 执行离散化...")

    for col in dataset_config['numerical_cols']:
        val = raw_dict.get(col)
        if val is None: continue

        if col in data_info:
            config = data_info[col]
            bins = config.get('bins') or config.get('ranges')
            labels = config.get('labels')
            if bins and labels:
                found = False
                for i in range(len(labels)):
                    if i + 1 < len(bins) and bins[i] <= val <= bins[i + 1]:
                        res[col] = labels[i];
                        found = True;
                        break
                if not found:
                    res[col] = labels[0] if val < bins[0] else labels[-1]
            else:
                res[col] = str(val)

    for col in dataset_config['categorical_cols']:
        res[col] = raw_dict.get(col)

    return res


def batch_discretize(df, binning_config):
    """批量离散化"""
    df_res = df.copy()
    data_info = binning_config['data_info']['binning_info']
    dataset_config = binning_config['metadata']['dataset_config']

    print("正在执行批量离散化...")
    for col in dataset_config['numerical_cols']:
        if col in df.columns and col in data_info:
            config = data_info[col]
            bins = config.get('bins') or config.get('ranges')
            labels = config.get('labels')
            if bins and labels:
                try:
                    df_res[col] = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)
                    df_res[col] = df_res[col].astype(str)
                    mask_low = df[col] < bins[0]
                    mask_high = df[col] > bins[-1]
                    if mask_low.any(): df_res.loc[mask_low, col] = labels[0]
                    if mask_high.any(): df_res.loc[mask_high, col] = labels[-1]
                    df_res[col] = df_res[col].replace('nan', labels[0])
                except Exception as e:
                    print(f"列 {col} 离散化警告: {e}")
            else:
                df_res[col] = df_res[col].astype(str)

    for col in dataset_config['categorical_cols']:
        if col in df.columns:
            df_res[col] = df_res[col].astype(str)
    return df_res


def batch_predict(model, df_discrete, dataset_config):
    """批量预测 (自动One-Hot映射)"""
    try:
        target_col = dataset_config['target_col']
        try:
            model_nodes = list(model.nodes())
        except:
            model_nodes = list(model.nodes)

        print(f"正在转换数据为 One-Hot 格式 (模型节点数: {len(model_nodes)})...")
        encoded_data = pd.DataFrame(0, index=df_discrete.index, columns=model_nodes)

        for col in df_discrete.columns:
            if col == target_col: continue
            series = df_discrete[col]
            if col in dataset_config['numerical_cols']:
                dummies = pd.get_dummies(series)
                valid_cols = dummies.columns.intersection(model_nodes)
                if not valid_cols.empty: encoded_data[valid_cols] = dummies[valid_cols]
            elif col in dataset_config['categorical_cols']:
                dummies = pd.get_dummies(series, prefix=col)
                valid_cols = dummies.columns.intersection(model_nodes)
                if not valid_cols.empty: encoded_data[valid_cols] = dummies[valid_cols]

        if target_col in encoded_data.columns:
            encoded_data = encoded_data.drop(columns=[target_col])

        print(f"开始贝叶斯推理 (输入维度: {encoded_data.shape})...")
        try:
            with parallel_backend("threading", n_jobs=1):
                y_pred_df = model.predict(encoded_data, show_progress=False)
        except Exception:
            with parallel_backend("threading", n_jobs=1):
                y_pred_df = model.predict(encoded_data)

        if target_col in y_pred_df.columns:
            y_pred = y_pred_df[target_col].tolist()
        else:
            y_pred = y_pred_df.iloc[:, 0].tolist()
        return y_pred, []
    except Exception as e:
        print(f"批量预测失败: {e}");
        return [], []


def diagnose_fault(current_status, discrete_input, rules):
    """
    故障诊断 - 修改版: 返回诊断报告字符串
    """
    header = f"\n>>> [故障回溯] 分析 '{current_status}' 成因..."
    print(header)

    logs = [header]  # 用于保存到文件

    relevant = [r for r in rules if r['consequent'] == current_status]
    relevant.sort(key=lambda x: x['confidence'], reverse=True)

    if not relevant:
        msg = "未找到匹配规则。"
        print(msg)
        logs.append(msg)
        return "\n".join(logs)

    found = False
    for rule in relevant:
        is_match = True
        matched_str = []
        for ante in rule['antecedents_mapped']:
            col = ante['original_column']
            rule_val = ante['node_name']
            actual = discrete_input.get(col)
            if actual is None or (str(actual) not in str(rule_val) and str(rule_val) not in str(actual)):
                is_match = False;
                break
            matched_str.append(f"{col}={rule_val}")
        if is_match:
            msg = f"  [√] {' + '.join(matched_str)} (置信度: {rule['confidence']:.0%})"
            print(msg)
            logs.append(msg)
            found = True
            # 如果只想显示第一条匹配的最强规则，可以在这里 break
            # 暂时显示所有匹配的规则，以便详尽分析

    if not found:
        msg = "  [?] 未能精确匹配特征组合，可能是未收录的复杂模式。"
        print(msg)
        logs.append(msg)

    return "\n".join(logs)


def get_user_input(binning_config):
    dataset_config = binning_config['metadata']['dataset_config']
    input_data = {}
    print("\n" + "=" * 50 + "\n   请输入设备当前参数\n" + "=" * 50)
    for col in dataset_config['numerical_cols']:
        while True:
            val = input(f" >> {col}: ")
            if not val: input_data[col] = 0.0; break
            try:
                input_data[col] = float(val); break
            except:
                pass
    for col in dataset_config['categorical_cols']:
        val = input(f" >> {col}: ")
        input_data[col] = val.strip() if val else "生产部B"
    return input_data


# ==========================================
# 4. 主程序入口
# ==========================================

def run_single_assessment(raw_input, history_data_path, model_path=None,
    binning_config_path=None, rules_json_path=None, rules_csv_path=None, result_dir=None):
    """Run a single assessment using UI-provided input and a history dataset."""
    if not history_data_path:
        raise FileNotFoundError("缺少历史数据路径，请先在 Page1 导入数据集")
    if not os.path.exists(history_data_path):
        raise FileNotFoundError(f"历史数据集不存在: {history_data_path}")

    model_path = model_path or MODEL_PATH
    binning_config_path = binning_config_path or BINNING_CONFIG_PATH
    rules_json_path = rules_json_path or RULES_JSON_PATH
    rules_csv_path = rules_csv_path or RULES_CSV_PATH
    result_dir = result_dir or RESULT_DIR
    os.makedirs(result_dir, exist_ok=True)

    binning_config = load_binning_config(binning_config_path)
    json_rules = load_network_rules(rules_json_path)
    model = load_model(model_path)

    dataset_config = binning_config['metadata']['dataset_config']
    target_col = dataset_config['target_col']
    normal_val = dataset_config.get('normal_value')

    user_input_discrete = discretize_using_json(raw_input, binning_config, debug=False)
    status, prob_dict = infer_single_sample(model, user_input_discrete, target_col)
    if not status:
        raise RuntimeError("预测失败")

    if status == normal_val:
        if not HealthAssessor:
            raise RuntimeError("健康度评估模块不可用")

        assessor = HealthAssessor(history_data_path, binning_config_path, rules_csv_path)

        def predict_cb(disc):
            _, p = infer_single_sample(model, disc, target_col)
            return p.get(normal_val, 0) if p else 0

        def disc_cb(raw):
            return discretize_using_json(raw, binning_config)

        res = assessor.assess(raw_input, user_input_discrete, prob_dict.get(normal_val, 0.0), predict_cb, disc_cb)
        grade = assessor.get_grade(res['score'])

        report_path = os.path.join(result_dir, "health_assessment_single_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== 单机健康度评估报告 ===\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"设备状态: {status}\n")
            f.write(f"综合得分: {res['score']:.1f}\n")
            f.write(f"等级评定: {grade}\n")
            f.write("-" * 30 + "\n")
            f.write(f"CI (置信度): {res['metrics']['CI']:.4f}\n")
            f.write(f"RI (风险度): {res['metrics']['RI']:.4f}\n")
            f.write(f"FMI (裕度): {res['metrics']['FMI']:.4f}\n")
            f.write(f"RSI (稳定性): {res['metrics']['RSI']:.4f}\n")
            f.write("-" * 30 + "\n")
            f.write(f"原始输入: {raw_input}\n")
            f.write(f"离散特征: {user_input_discrete}\n")
    else:
        diagnosis_log = diagnose_fault(status, user_input_discrete, json_rules)
        report_path = os.path.join(result_dir, "fault_diagnosis_single_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== 单机故障诊断报告 ===\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"预测结论: {status}\n")
            f.write(f"故障概率: {prob_dict.get(status, 0.0):.2%}\n")
            f.write("-" * 30 + "\n")
            f.write(f"原始输入: {raw_input}\n")
            f.write(f"离散特征: {user_input_discrete}\n")
            f.write("-" * 30 + "\n")
            f.write(diagnosis_log)

    return status, prob_dict

def main_one():
    """单机交互模式"""
    print("\n>>> 启动单机诊断 (Single Mode) <<<")
    try:
        binning_config = load_binning_config(BINNING_CONFIG_PATH)
        json_rules = load_network_rules(RULES_JSON_PATH)
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"初始化失败: {e}");
        return

    dataset_config = binning_config['metadata']['dataset_config']
    target_col = dataset_config['target_col']
    normal_val = dataset_config['normal_value']

    assessor = None
    if HealthAssessor:
        print("正在加载健康度评估模块...")
        try:
            assessor = HealthAssessor(DATA_PATH, BINNING_CONFIG_PATH, RULES_CSV_PATH)
        except:
            pass

    # 1. 交互输入
    user_input_raw = get_user_input(binning_config)
    user_input_discrete = discretize_using_json(user_input_raw, binning_config, debug=False)
    print(f"\n[离散化特征] {user_input_discrete}")

    # 2. 推理
    print("\n[推理] 正在计算状态概率...")
    status, prob_dict = infer_single_sample(model, user_input_discrete, target_col)

    if not status: print("预测失败。"); return

    # 3. 动态显示概率
    print(f"  预测结论: [{status}]")
    if status == normal_val:
        prob = prob_dict.get(normal_val, 0.0)
        print(f"  正常概率: {prob:.4f}")
    else:
        prob = prob_dict.get(status, 0.0)
        print(f"  故障概率: {prob:.2%} (置信度)")

    # 4. 分支处理
    # Case A: 正常 -> 健康度评估
    if status == normal_val and assessor:
        print("\n=== 进入健康度评价 (Health Assessment) ===")

        def predict_cb(disc):
            _, p = infer_single_sample(model, disc, target_col)
            return p.get(normal_val, 0) if p else 0

        def disc_cb(raw):
            return discretize_using_json(raw, binning_config)

        res = assessor.assess(user_input_raw, user_input_discrete, prob_dict.get(normal_val, 0.0), predict_cb, disc_cb)
        grade = assessor.get_grade(res['score'])

        print(f"  综合得分: {res['score']:.1f} / 100")
        print(f"  等级评定: {grade}")
        print(f"  详情: CI={res['metrics']['CI']:.2f}, RI={res['metrics']['RI']:.2f}, "
              f"FMI={res['metrics']['FMI']:.2f}, RSI={res['metrics']['RSI']:.2f}")

        # 保存健康度报告
        report_path = os.path.join(RESULT_DIR, "health_assessment_single_report.txt")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 单机健康度评估报告 ===\n")
                f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"设备状态: {status}\n")
                f.write(f"综合得分: {res['score']:.1f}\n")
                f.write(f"等级评定: {grade}\n")
                f.write("-" * 30 + "\n")
                f.write(f"CI (置信度): {res['metrics']['CI']:.4f}\n")
                f.write(f"RI (风险度): {res['metrics']['RI']:.4f}\n")
                f.write(f"FMI (裕度): {res['metrics']['FMI']:.4f}\n")
                f.write(f"RSI (稳定性): {res['metrics']['RSI']:.4f}\n")
                f.write("-" * 30 + "\n")
                f.write(f"原始输入: {user_input_raw}\n")
                f.write(f"离散特征: {user_input_discrete}\n")
            print(f"\n[提示] 健康度报告已保存至: {report_path}")
        except Exception as e:
            print(f"报告保存失败: {e}")

    # Case B: 故障 -> 故障诊断
    elif status != normal_val:
        # 调用诊断并获取日志字符串
        diagnosis_log = diagnose_fault(status, user_input_discrete, json_rules)

        # [新增] 保存故障诊断报告
        report_path = os.path.join(RESULT_DIR, "fault_diagnosis_single_report.txt")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 单机故障诊断报告 ===\n")
                f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"预测结论: {status}\n")
                f.write(f"故障概率: {prob_dict.get(status, 0.0):.2%}\n")
                f.write("-" * 30 + "\n")
                f.write(f"原始输入: {user_input_raw}\n")
                f.write(f"离散特征: {user_input_discrete}\n")
                f.write("-" * 30 + "\n")
                f.write(diagnosis_log)  # 写入回溯详情
            print(f"\n[提示] 故障诊断报告已保存至: {report_path}")
        except Exception as e:
            print(f"报告保存失败: {e}")


def main():
    """批量测试模式"""
    print("\n>>> 启动批量测试 (Batch Mode) <<<")
    try:
        binning_config = load_binning_config(BINNING_CONFIG_PATH)
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"初始化失败: {e}"); return

    dataset_config = binning_config['metadata']['dataset_config']
    target_col = dataset_config['target_col']

    if not os.path.exists(DATA_PATH): print(f"错误: 找不到测试数据 {DATA_PATH}"); return
    print(f"读取测试集: {os.path.basename(DATA_PATH)}")
    df = pd.read_csv(DATA_PATH)

    df_discrete = batch_discretize(df, binning_config)
    y_true = df_discrete[target_col].tolist()

    print(f"正在预测 {len(df)} 条样本...")
    y_pred, _ = batch_predict(model, df_discrete, dataset_config)
    if not y_pred: print("预测中断。"); return

    acc = accuracy_score(y_true, y_pred)
    report_str = classification_report(y_true, y_pred)

    print("\n" + "=" * 40 + "\n      批量测试评估报告\n" + "=" * 40)
    print(f"总体准确率 (Accuracy): {acc:.4f}")
    print("-" * 40)
    print(report_str)

    report_path = os.path.join(RESULT_DIR, "prediction_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"数据源: {os.path.basename(DATA_PATH)}\n")
        f.write(f"测试时间: {datetime.now()}\n")
        f.write(f"总体准确率: {acc:.4f}\n")
        f.write("-" * 60 + "\n")
        f.write(report_str)
    print(f"完整报告已保存至: {report_path}")

    try:
        cm_path = os.path.join(RESULT_DIR, "confusion_matrix.png")
        labels = sorted(list(set(y_true + y_pred)))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
        plt.title('贝叶斯网络混淆矩阵')
        plt.xlabel('预测标签')
        plt.ylabel('真实标签')
        plt.tight_layout()
        plt.savefig(cm_path)
        print(f"混淆矩阵图已保存至: {cm_path}")
    except:
        pass


if __name__ == '__main__':
    main_one()  # 单次交互
    # main()     # 批量测试
