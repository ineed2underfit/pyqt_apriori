from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QFileDialog
from common.utils import show_dialog
from workers.prediction_worker import PredictionWorker
import os

class PageFourHandler(QObject):
    def __init__(self, parent: 'Page4'):
        super().__init__(parent)
        self._parent = parent
        self.test_data_path = None
        self.thread = None
        self.worker = None

    # --- 批量评估功能 ---
    def select_test_file(self):
        """打开文件对话框，让用户选择测试数据集"""
        try:
            project_root = os.getcwd()
            default_dir = os.path.join(project_root, "new_bayesian", "dataset", "testdata_info")
            file_path, _ = QFileDialog.getOpenFileName(
                self._parent, "选择测试数据文件", default_dir, "CSV Files (*.csv);;All Files (*.*)"
            )
            if file_path:
                self.test_data_path = file_path
                self._parent.textEdit_3.setText(f"已选择测试文件进行批量评估：\n{file_path}")
                self._parent.pushButton_assessment.setEnabled(True)
        except Exception as e:
            show_dialog(self._parent, f'文件选择出错: {str(e)}', '错误')

    def start_batch_assessment(self):
        """开始批量质量评估预测"""
        if not self.test_data_path:
            show_dialog(self._parent, "请先导入测试数据集！", "错误")
            return
        self._run_prediction(self.test_data_path)

    # --- 单次评估功能 ---
    def assess_single_instance(self):
        """对UI界面上输入的数据进行单次评估"""
        print("--- assess_single_instance 方法被调用 ---") # DEBUG
        try:
            # 从UI收集数据并打包成字典
            data_dict = {
                'timestamp': self._parent.dateTimeEdit.dateTime().toString(Qt.DateFormat.ISODate),
                'device_id': self._parent.comboBox_model.currentText(),
                'department': self._parent.comboBox_apt.currentText(),
                'temp': self._parent.doubleSpinBox_temp.value(),
                'vibration': self._parent.doubleSpinBox_vibration.value(),
                'oil_pressure': self._parent.doubleSpinBox_oil.value(),
                'voltage': self._parent.doubleSpinBox_voltage.value(),
                'rpm': self._parent.doubleSpinBox_rpm.value()
            }
            print(f"--- 收集到的单次评估数据: {data_dict} ---") # DEBUG
            self._run_prediction(data_dict)
        except Exception as e:
            print(f"--- assess_single_instance 发生错误: {e} ---") # DEBUG
            show_dialog(self._parent, f'读取界面数据时出错: {str(e)}', '错误')

    # --- 公共的执行和回调逻辑 ---
    def _run_prediction(self, data_payload):
        """通用的预测执行函数，根据传入数据类型启动不同模式"""
        print("--- _run_prediction 方法被调用 ---") # DEBUG
        main_window = self._parent.window()
        model_path = main_window.model_pkl_path

        if not os.path.exists(model_path):
            show_dialog(self._parent, f"模型文件不存在，请先在Page3中构建贝叶斯网络。\n路径: {model_path}", "错误")
            return

        # 禁用所有按钮
        self._parent.pushButton_import.setEnabled(False)
        self._parent.pushButton_assessment.setEnabled(False)
        self._parent.pushButton_solely.setEnabled(False)
        show_dialog(self._parent, "正在进行预测...", "请稍候")

        self.thread = QThread()
        self.worker = PredictionWorker(model_path, data_payload)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.batch_finished.connect(self.on_batch_assessment_finished)
        self.worker.single_prediction_finished.connect(self.on_single_assessment_finished)
        self.worker.error.connect(self.on_assessment_error)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_batch_assessment_finished(self, report_text):
        """批量评估成功的回调"""
        self._parent.textEdit_3.setText(report_text)
        show_dialog(self._parent, "质量评估完成！", "成功")
        self.cleanup_thread()

    def on_single_assessment_finished(self, prediction_result, input_data_dict):
        """单次评估成功的回调"""
        output = "--- 单次故障概率评估结果 ---\n\n"
        output += "输入数据：\n"
        for key, value in input_data_dict.items():
            output += f"  {key}: {value}\n"
        output += f"\n预测故障类型为: {prediction_result}\n"
        output += "-----------------------------------"

        self._parent.textEdit_solely.setText(output)
        self.cleanup_thread()
    def on_assessment_error(self, error_message):
        """评估失败的通用回调"""
        show_dialog(self._parent, f"评估失败: {error_message}", "错误")
        self.cleanup_thread()

    def cleanup_thread(self):
        """清理线程"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self._parent:
            self._parent.pushButton_import.setEnabled(True)
            # 只有在选择了测试文件后，才重新启用批量评估按钮
            if self.test_data_path:
                self._parent.pushButton_assessment.setEnabled(True)
            self._parent.pushButton_solely.setEnabled(True)