from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap
from workers.bayesian_worker import BayesianWorker
from components.log_dialog import LogDialog
import os

class PageThreeHandler(QObject):
    def __init__(self, parent: 'Page3'):
        super().__init__(parent)
        self._parent = parent
        self.thread = None
        self.worker = None
        self.log_dialog = None

    def build_bayesian_network(self):
        """启动后台线程来构建贝叶斯网络"""
        main_window = self._parent.window()

        dataset_path = main_window.dataset_path
        if not dataset_path or main_window.optimized_rules_df is None:
            self._parent.on_common_error("请先在页面一选择数据集，并在页面二完成规则优化。")
            return

        self._parent.pushButton.setEnabled(False)
        # 重置进度条为0
        self._parent.progressBar.setValue(0)

        try:
            self.log_dialog = LogDialog(title="贝叶斯网络构建日志", parent=self._parent)
            self.log_dialog.show()

            project_root = os.getcwd()
            rules_path = os.path.join(project_root, "new_bayesian", "dataset", "optimal_rules.csv")
            output_dir = os.path.join(project_root, "new_bayesian", "result", "bayesian_result")
            os.makedirs(output_dir, exist_ok=True)
            network_path = os.path.join(output_dir, "network_structure.png")
            cm_path = os.path.join(output_dir, "confusion_matrix.png")

            self.thread = QThread()
            self.worker = BayesianWorker(dataset_path, rules_path, network_path, cm_path, output_dir)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_dialog.append_log) # 连接日志信号
            self.worker.progress_updated.connect(self._parent.update_progress) # 连接进度更新信号
            self.worker.finished.connect(self.on_build_finished)
            self.worker.error.connect(self.on_build_error)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            self._parent.on_common_error(f"启动分析时出错: {str(e)}")
            self.cleanup_thread()

    def on_build_finished(self, confusion_matrix_path, network_structure_path):
        """构建成功后，在UI上显示图片"""
        self._parent.update_progress(100, "构建成功！")
        self._parent.display_images(confusion_matrix_path, network_structure_path)
        self._parent.on_common_error("贝叶斯网络构建成功！")
        self.cleanup_thread()

    def on_build_error(self, error_message):
        """构建失败的回调"""
        self._parent.progressBar.setRange(0, 100)
        self._parent.progressBar.setValue(0)
        self._parent.on_common_error(f"构建失败: {error_message}")
        self.cleanup_thread()

    def cleanup_thread(self):
        """清理线程资源"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self._parent:
            self._parent.pushButton.setEnabled(True)
