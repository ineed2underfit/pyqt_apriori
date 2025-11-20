from PySide6.QtCore import QObject, QThread

from workers.bayesian_worker import BayesianWorker
from components.log_dialog import LogDialog


class PageThreeHandler(QObject):
    def __init__(self, parent: 'Page3'):
        super().__init__(parent)
        self._parent = parent
        self.thread = None
        self.worker = None
        self.log_dialog = None

    def build_bayesian_network(self):
        """启动后台线程执行贝叶斯训练与预测"""
        main_window = self._parent.window()
        dataset_path = getattr(main_window, "dataset_path", None)
        rules_ready = getattr(main_window, "initial_rules_df", None)

        if not dataset_path:
            self._parent.on_common_error("请先在页面一导入数据集")
            return
        if rules_ready is None:
            self._parent.on_common_error("请先在页面二完成规则挖掘")
            return

        self._parent.pushButton.setEnabled(False)
        self._parent.progressBar.setValue(0)

        try:
            self.log_dialog = LogDialog(title="贝叶斯网络构建日志", parent=self._parent)
            self.log_dialog.show()

            self.thread = QThread()
            self.worker = BayesianWorker(dataset_path)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_dialog.append_log)
            self.worker.progress_updated.connect(self._parent.update_progress)
            self.worker.finished.connect(self.on_build_finished)
            self.worker.error.connect(self.on_build_error)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as exc:
            self._parent.on_common_error(f"启动分析时出错: {exc}")
            self.cleanup_thread()

    def on_build_finished(self, network_path):
        self._parent.update_progress(100, "构建成功")
        self._parent.display_images(network_path)
        self._parent.on_common_error("贝叶斯网络构建成功！")
        self.cleanup_thread()

    def on_build_error(self, error_message):
        self._parent.progressBar.setValue(0)
        self._parent.on_common_error(f"构建失败: {error_message}")
        self.cleanup_thread()

    def cleanup_thread(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self.log_dialog:
            self.log_dialog.append_log("=== 构建流程已结束，可手动关闭此窗口查看完整记录 ===")
            self.log_dialog = None
        if self._parent:
            self._parent.pushButton.setEnabled(True)
