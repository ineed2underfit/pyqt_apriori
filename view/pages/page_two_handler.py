from PySide6.QtCore import QObject, QThread
from components.log_dialog import LogDialog
from workers.apriori_worker import AprioriWorker

class PageTwoHandler(QObject):
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

        # 禁用按钮，防止重复点击
        self._parent.pushButton_2.setEnabled(False)

        try:
            self.log_dialog = LogDialog(self._parent)
            self.log_dialog.show()

            # 1. 创建一个 QThread 实例
            self.thread = QThread()
            
            # 2. 获取参数并创建 Worker 实例
            params = {
                'min_support': self._parent.doubleSpinBox_2.value(),
                'min_confidence': self._parent.doubleSpinBox_3.value(),
                'min_lift': self._parent.doubleSpinBox.value(),
                'auto_optimize': True
            }
            self.worker = AprioriWorker(self._parent.dataset_path, params)

            # 3. 将 worker 移动到子线程
            self.worker.moveToThread(self.thread)

            # 4. 连接信号和槽
            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_dialog.append_log)
            self.worker.progress_updated.connect(self._parent.update_progress)
            self.worker.analysis_succeeded.connect(self.on_analysis_success)
            self.worker.analysis_failed.connect(self.on_analysis_error)
            
            # 任务结束后（无论成功失败），都清理线程
            self.worker.analysis_succeeded.connect(self.cleanup_thread)
            self.worker.analysis_failed.connect(self.cleanup_thread)
            
            # 线程结束后也自行清理
            self.thread.finished.connect(self.thread.deleteLater)


            # 5. 启动线程
            self.thread.start()

        except Exception as e:
            self._parent.on_common_error(f"启动分析时出错: {str(e)}")
            self._parent.pushButton_2.setEnabled(True)

    def on_analysis_success(self, results_df):
        """处理分析成功的结果"""
        try:
            output = "设备故障预测规则分析结果（按关联强度从高到低排列）：\n\n"
            output += results_df.to_markdown(index=False)

            # 在textEdit中显示结果
            self._parent.textEdit_3.setText(output)
            self._parent.textEdit_3.verticalScrollBar().setValue(0)

        except Exception as e:
            self._parent.on_common_error(f"处理结果时出错: {str(e)}")

    def on_analysis_error(self, error_message):
        """处理分析失败的情况"""
        self._parent.on_common_error(f"分析过程出错: {error_message}")
        self._parent.progressBar.setValue(0)

    def cleanup_thread(self):
        """清理并退出线程"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        self.thread = None
        self.worker = None
        # 重新启用按钮
        if self._parent:
            self._parent.pushButton_2.setEnabled(True)

    def on_parameter_changed(self):
        """参数变化时可以做一些事，目前为空"""
        pass
