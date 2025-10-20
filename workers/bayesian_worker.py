from PySide6.QtCore import QObject, Signal
import sys
import os

sys.path.append(os.path.abspath("E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/new_bayesian/BN_new"))
from bn_bayesian import run_analysis

class Stream(QObject):
    new_text = Signal(str)
    def write(self, text):
        self.new_text.emit(str(text))
    def flush(self):
        pass

class BayesianWorker(QObject):
    finished = Signal(str, str)
    error = Signal(str)
    log_message = Signal(str)
    progress_updated = Signal(int, str) # 新增进度信号

    def __init__(self, dataset_path, rules_path, network_path, cm_path, report_dir):
        super().__init__()
        self.dataset_path = dataset_path
        self.rules_path = rules_path
        self.network_path = network_path
        self.cm_path = cm_path
        self.report_dir = report_dir

    def run(self):
        stream = Stream()
        stream.new_text.connect(self._process_log_line)
        original_stdout = sys.stdout
        sys.stdout = stream

        try:
            run_analysis(self.dataset_path, self.rules_path, self.network_path, self.cm_path, self.report_dir)

            if not os.path.exists(self.cm_path) or not os.path.exists(self.network_path):
                raise FileNotFoundError("脚本执行完毕，但未找到预期的结果图片文件。")

            self.finished.emit(self.cm_path, self.network_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            sys.stdout = original_stdout

    def _process_log_line(self, text):
        text = text.strip()
        if not text:
            return
        
        self.log_message.emit(text)

        # 根据日志内容判断进度
        if "正在加载数据" in text:
            self.progress_updated.emit(10, "正在加载数据...")
        elif "开始数据预处理" in text:
            self.progress_updated.emit(25, "正在预处理数据...")
        elif "正在加载规则" in text:
            self.progress_updated.emit(40, "正在加载规则...")
        elif "开始处理规则" in text:
            self.progress_updated.emit(50, "正在构建网络结构...")
        elif "开始构建贝叶斯网络" in text:
            self.progress_updated.emit(60, "正在构建贝叶斯网络...")
        elif "开始可视化网络结构" in text:
            self.progress_updated.emit(70, "正在生成网络结构图...")
        elif "开始进行贝叶斯参数估计" in text:
            self.progress_updated.emit(80, "正在估计参数并生成报告...")
