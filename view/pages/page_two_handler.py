from PySide6.QtCore import QObject, QThread, Signal
from components.log_dialog import LogDialog
from workers.apriori_worker import AprioriWorker
from common.utils import show_dialog
import os

# 导入优化脚本中的核心函数
from new_bayesian.dataset.optimal_rules import filter_optimal_rules, get_best_rule_per_fault

class PageTwoHandler(QObject):
    initial_rules_ready = Signal(object)  # 初始规则分析完成信号
    optimized_rules_ready = Signal(object) # 优化规则完成信号

    def __init__(self, parent: 'PageTwo'):
        super().__init__(parent)
        self._parent = parent
        self.log_dialog = None
        self.thread = None
        self.worker = None

    def start_mining(self):
        """开始挖掘规则 (使用线程)"""
        if not self._parent.dataset_path:
            self._parent.on_common_error("请先选择数据集！")
            return

        self._parent.pushButton_2.setEnabled(False)
        self._parent.pushButton.setEnabled(False) # 禁用优化按钮

        try:
            self.log_dialog = LogDialog(title="规则挖掘日志", parent=self._parent)
            self.log_dialog.show()

            self.thread = QThread()
            params = {
                'min_support': self._parent.doubleSpinBox_2.value(),
                'min_confidence': self._parent.doubleSpinBox_3.value(),
                'min_lift': self._parent.doubleSpinBox.value(),
                'auto_optimize': True
            }
            self.worker = AprioriWorker(self._parent.dataset_path, params)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_dialog.append_log)
            self.worker.progress_updated.connect(self._parent.update_progress)
            self.worker.analysis_succeeded.connect(self.on_analysis_success)
            self.worker.analysis_failed.connect(self.on_analysis_error)
            self.worker.analysis_succeeded.connect(self.cleanup_thread)
            self.worker.analysis_failed.connect(self.cleanup_thread)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            self._parent.on_common_error(f"启动分析时出错: {str(e)}")
            self._parent.pushButton_2.setEnabled(True)

    def optimize_rules(self):
        """执行规则优化"""
        main_window = self._parent.window()
        initial_rules = main_window.initial_rules_df

        if initial_rules is None or initial_rules.empty:
            show_dialog(self._parent, "没有可优化的规则，请先提取语料。", "提示")
            return

        # 更新进度条和状态，提供即时反馈
        self._parent.update_progress(0, "准备优化规则...")

        try:
            # 1. 在内存中直接调用优化函数
            optimal_rules = filter_optimal_rules(initial_rules)
            best_rules_df = get_best_rule_per_fault(optimal_rules, by='提升度')

            # 2. 保存优化后的规则到指定文件，为Page3做准备
            save_path = "E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/new_bayesian/dataset/optimal_rules.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            best_rules_df.to_csv(save_path, index=False, encoding='utf-8-sig')

            # 3. 发出信号，将优化后的DataFrame传递给MainWindow
            self.optimized_rules_ready.emit(best_rules_df)

            # 4. 更新PageTwo的UI
            output = "已生成优化规则：\n\n" + best_rules_df.to_markdown(index=False)
            self._parent.textEdit_3.setText(output)
            
            # 5. 更新进度条并显示成功信息
            self._parent.update_progress(100, "规则优化完成")
            show_dialog(self._parent, f"规则优化成功！\n已保存到 {save_path}", "成功")

        except Exception as e:
            self._parent.on_common_error(f"规则优化时出错: {str(e)}")
            self._parent.update_progress(0, "优化失败")

    def on_analysis_success(self, results_df):
        """处理分析成功的结果"""
        # 发送信号给MainWindow，使其可以存储这份原始数据
        self.initial_rules_ready.emit(results_df)
        # 启用优化按钮
        self._parent.pushButton.setEnabled(True)

        try:
            output = "初始规则提取完成：\n\n" + results_df.to_markdown(index=False)
            self._parent.textEdit_3.setText(output)
            self._parent.textEdit_3.verticalScrollBar().setValue(0)

        except Exception as e:
            self._parent.on_common_error(f"处理结果时出错: {str(e)}")

    def on_analysis_error(self, error_message):
        self._parent.on_common_error(f"分析过程出错: {error_message}")
        self._parent.progressBar.setValue(0)

    def cleanup_thread(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self._parent:
            self._parent.pushButton_2.setEnabled(True)

    def on_parameter_changed(self):
        pass
