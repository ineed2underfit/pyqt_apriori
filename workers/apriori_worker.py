from PySide6.QtCore import QObject, Signal
from apriori.apriori1 import EquipmentAnalyzer

class AprioriWorker(QObject):
    """
    Apriori 分析器的工作线程对象，用于在后台执行耗时任务。
    """
    # 转发 EquipmentAnalyzer 的信号
    log_message = Signal(str)
    progress_updated = Signal(int, str)
    analysis_succeeded = Signal(object)
    analysis_failed = Signal(str)

    def __init__(self, dataset_path, params):
        super().__init__()
        self.dataset_path = dataset_path
        self.params = params
        self.analyzer = None
        self._is_running = True

    def run(self):
        """这个方法将在子线程中执行"""
        try:
            if not self._is_running:
                return

            self.analyzer = EquipmentAnalyzer(self.dataset_path)

            # 转发信号：将analyzer的信号连接到worker自己的信号上
            self.analyzer.log_message.connect(self.log_message)
            self.analyzer.progress_updated.connect(self.progress_updated)

            # 执行耗时任务
            results_df = self.analyzer.analyze(**self.params)

            if not self._is_running:
                return

            if results_df.empty:
                self.analysis_failed.emit("分析完成，但未找到任何规则。")
            else:
                self.analysis_succeeded.emit(results_df)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.analysis_failed.emit(f"分析过程中发生严重错误: {str(e)}")

    def stop(self):
        self._is_running = False

