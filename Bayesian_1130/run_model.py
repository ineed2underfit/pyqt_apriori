import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置参数（可在代码中直接修改）
DEFAULT_DATA_FILENAME = "device_PA40_data.csv"
DEFAULT_MODEL_NAME = "final_bn_model.pkl"

def main():
    try:
        from Bayesian.build_model import build_and_save_bayesian_model
        print(f"🚀 开始构建贝叶斯网络模型，使用数据: {DEFAULT_DATA_FILENAME}")
        model_path = build_and_save_bayesian_model(DEFAULT_DATA_FILENAME, DEFAULT_MODEL_NAME)
        print(f"\n✅ 模型构建成功！路径: {model_path}")
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()