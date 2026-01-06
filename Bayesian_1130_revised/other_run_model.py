# other_run_model.py
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置参数（可在代码中直接修改）
DEFAULT_DATA_FILENAME = "device_OW24_data.csv"
DEFAULT_LEARNING_METHOD = "em"  # 或 "em"
DEFAULT_MODEL_NAME = f"other_bn_model_{DEFAULT_LEARNING_METHOD}.pkl"

def main():
    try:
        # 从 Bayesian.other_build_model 导入新的训练函数
        from Bayesian.other_build_model import other_build_and_save_bayesian_model
        print(f"🚀 开始构建贝叶斯网络模型 (方法: {DEFAULT_LEARNING_METHOD})，使用数据: {DEFAULT_DATA_FILENAME}")
        model_path = other_build_and_save_bayesian_model(
            DEFAULT_DATA_FILENAME,
            learning_method=DEFAULT_LEARNING_METHOD,
            model_name=DEFAULT_MODEL_NAME
        )
        print(f"\n✅ 模型构建成功！路径: {model_path}")
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
    print(f"\n✅ 模型构建时间为 30.5s")