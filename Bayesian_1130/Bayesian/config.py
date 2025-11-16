import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BINNING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "Apriori", "分箱配置.json")
RULES_CSV_PATH = os.path.join(PROJECT_ROOT, "result", "apriori_results", "关联规则分析结果.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "datas")
MODEL_SAVE_DIR = os.path.join(PROJECT_ROOT, "Bayesian", "models")
BAYESIAN_RESULT_DIR = os.path.join(PROJECT_ROOT, "result", "bayesian_results")

os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
os.makedirs(BAYESIAN_RESULT_DIR, exist_ok=True)