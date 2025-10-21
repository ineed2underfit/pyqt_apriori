from PySide6.QtCore import QObject, Signal
import sys
import os
import pandas as pd

# 将脚本所在的目录添加到 sys.path 以便导入
sys.path.append(os.path.abspath("E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/new_bayesian/predict"))
from predict import main as run_batch_prediction, predict_single, load_model

class PredictionWorker(QObject):
    """在后台执行预测任务的工作者（支持批量和单次）"""
    batch_finished = Signal(str)   # 批量任务完成信号，返回报告文本
    single_prediction_finished = Signal(str, object) # 单次预测完成信号，返回预测结果字符串和原始输入数据字典
    error = Signal(str)      # 任务失败信号

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
                # 加载模型
                model = load_model(self.model_path)
                # 调用单次预测函数
                prediction_result = predict_single(model, self.data)
                self.single_prediction_finished.emit(prediction_result, self.data) # 发送预测结果和原始输入数据

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
