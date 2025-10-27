from PySide6.QtCore import QObject, Signal
import sys
import os
import pandas as pd

# 将脚本所在的目录添加到 sys.path 以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
predict_path = os.path.join(project_root, "new_bayesian", "predict")
sys.path.append(os.path.abspath(predict_path))
from predict import main as run_batch_prediction, predict_single, load_model

class PredictionWorker(QObject):
    """在后台执行预测任务的工作者（支持批量和单次）"""
    batch_finished = Signal(str)   # 批量任务完成信号，返回报告文本
    single_prediction_finished = Signal(str, object, object) # 单次预测完成信号，返回预测结果字符串、原始输入数据字典和概率分布字典
    error = Signal(str)      # 任务失败信号
    progress_updated = Signal(int)  # 进度更新信号，传递进度值(0-100)

    def __init__(self, model_path, data):
        super().__init__()
        self.model_path = model_path
        self.data = data # data可以是文件路径(str)或数据字典(dict)

    def run(self):
        try:
            if isinstance(self.data, str): # --- 批量预测模式 ---
                # 调用核心批量预测函数
                run_batch_prediction(self.model_path, self.data)

                # 脚本执行成功后，找到并读取生成的报告文件
                project_root = os.getcwd()
                report_path = os.path.join(project_root, "new_bayesian", "predict", "results", "evaluation_report.txt")

                if not os.path.exists(report_path):
                    raise FileNotFoundError("预测脚本执行完毕，但未找到结果报告文件。")

                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                self.batch_finished.emit(report_content)

            elif isinstance(self.data, dict): # --- 单次预测模式 ---
                # 0-20%: 初始化
                self.progress_updated.emit(10)
                
                # 20-50%: 加载模型和分箱配置
                self.progress_updated.emit(20)
                model, bin_config = load_model(self.model_path)
                self.progress_updated.emit(50)
                
                # 50-90%: 执行预测
                self.progress_updated.emit(60)
                prediction_result, probability_dist = predict_single(model, self.data, bin_config)
                self.progress_updated.emit(90)
                
                # 90-100%: 完成
                self.progress_updated.emit(100)
                self.single_prediction_finished.emit(prediction_result, self.data, probability_dist) # 发送预测结果、原始输入数据和概率分布

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
